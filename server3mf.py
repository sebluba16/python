#!/usr/bin/env python3
"""Serveur web de fichiers 3MF : index, tags, aperçu, description, ouverture Bambu Studio.

Usage: python3 server3mf.py [DOSSIER_3MF] [--port 8000] [--host 0.0.0.0]
Sans dépendance externe (stdlib uniquement).
"""
import argparse, json, mimetypes, os, re, sqlite3, threading, zipfile
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

THUMBS = ["Metadata/plate_1.png", "Metadata/thumbnail.png", "Metadata/top_1.png",
          "Metadata/plate_no_light_1.png", "Metadata/pick_1.png",
          "Thumbnails/thumbnail.png", "/Metadata/plate_1.png"]
LOCK = threading.Lock()
ROOT = "."
DB = None


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS files(
            id INTEGER PRIMARY KEY, path TEXT UNIQUE, name TEXT, size INTEGER,
            mtime REAL, thumb BLOB, description TEXT DEFAULT '', tags TEXT DEFAULT '');
        """)


def extract_thumb(path):
    try:
        with zipfile.ZipFile(path) as z:
            names = set(z.namelist())
            for t in THUMBS:
                if t in names:
                    return z.read(t)
            pngs = sorted(n for n in names if n.lower().endswith(".png"))
            if pngs:
                return z.read(pngs[0])
    except Exception:
        pass
    return None


def scan():
    """Indexe récursivement ROOT. Garde tags/description, retire les fichiers disparus."""
    found = set()
    with LOCK, db() as c:
        for d, _, fs in os.walk(ROOT):
            for f in fs:
                if not f.lower().endswith(".3mf"):
                    continue
                full = os.path.join(d, f)
                rel = os.path.relpath(full, ROOT)
                found.add(rel)
                st = os.stat(full)
                row = c.execute("SELECT id,mtime,size FROM files WHERE path=?", (rel,)).fetchone()
                if row and row["mtime"] == st.st_mtime and row["size"] == st.st_size:
                    continue
                th = extract_thumb(full)
                if row:
                    c.execute("UPDATE files SET name=?,size=?,mtime=?,thumb=? WHERE id=?",
                              (f, st.st_size, st.st_mtime, th, row["id"]))
                else:
                    c.execute("INSERT INTO files(path,name,size,mtime,thumb) VALUES(?,?,?,?,?)",
                              (rel, f, st.st_size, st.st_mtime, th))
        for r in c.execute("SELECT id,path FROM files").fetchall():
            if r["path"] not in found:
                c.execute("DELETE FROM files WHERE id=?", (r["id"],))
    return len(found)


def row_json(r):
    return {"id": r["id"], "name": r["name"], "path": r["path"], "size": r["size"],
            "description": r["description"],
            "tags": [t for t in r["tags"].split(",") if t],
            "has_thumb": r["thumb"] is not None}


def clean_tags(tags):
    out = []
    for t in tags:
        t = re.sub(r"[,\s]+", " ", str(t)).strip().lower()
        if t and t not in out:
            out.append(t)
    return out


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json", extra=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        p = u.path
        q = parse_qs(u.query)
        if p == "/":
            return self.send(200, PAGE, "text/html; charset=utf-8")
        if p == "/api/files":
            s = (q.get("q", [""])[0]).lower()
            tag = q.get("tag", [""])[0]
            with db() as c:
                rows = [row_json(r) for r in c.execute("SELECT * FROM files ORDER BY name COLLATE NOCASE")]
            if s:
                rows = [r for r in rows if s in (r["name"] + " " + r["description"] + " " + " ".join(r["tags"])).lower()]
            if tag:
                rows = [r for r in rows if tag in r["tags"]]
            return self.send(200, rows)
        if p == "/api/tags":
            cnt = {}
            with db() as c:
                for r in c.execute("SELECT tags FROM files"):
                    for t in r["tags"].split(","):
                        if t:
                            cnt[t] = cnt.get(t, 0) + 1
            return self.send(200, sorted(cnt.items()))
        m = re.match(r"^/thumb/(\d+)$", p)
        if m:
            with db() as c:
                r = c.execute("SELECT thumb FROM files WHERE id=?", (m.group(1),)).fetchone()
            if r and r["thumb"]:
                return self.send(200, r["thumb"], "image/png", {"Cache-Control": "max-age=3600"})
            return self.send(404, "no thumb", "text/plain")
        m = re.match(r"^/files/(\d+)/", p)
        if m:  # /files/<id>/<nom>.3mf  (URL lue par Bambu Studio)
            with db() as c:
                r = c.execute("SELECT path FROM files WHERE id=?", (m.group(1),)).fetchone()
            if not r:
                return self.send(404, "not found", "text/plain")
            full = os.path.join(ROOT, r["path"])
            size = os.path.getsize(full)
            self.send_response(200)
            self.send_header("Content-Type", "model/3mf")
            self.send_header("Content-Length", str(size))
            self.send_header("Content-Disposition", 'attachment; filename="%s"' % os.path.basename(full))
            self.end_headers()
            with open(full, "rb") as f:
                while chunk := f.read(1 << 16):
                    self.wfile.write(chunk)
            return
        self.send(404, "not found", "text/plain")

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        p = urlparse(self.path).path
        n = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(n) or b"{}")
        if p == "/api/rescan":
            return self.send(200, {"count": scan()})
        m = re.match(r"^/api/files/(\d+)$", p)
        if m:
            tags = ",".join(clean_tags(data.get("tags", [])))
            with db() as c:
                c.execute("UPDATE files SET description=?, tags=? WHERE id=?",
                          (str(data.get("description", "")), tags, m.group(1)))
            return self.send(200, {"ok": True})
        self.send(404, {"error": "not found"})


PAGE = r"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Bibliothèque 3MF</title>
<style>
:root{--bg:#14161a;--card:#1e2128;--fg:#e8eaed;--mut:#8b93a1;--acc:#00ae42}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px system-ui,sans-serif}
header{position:sticky;top:0;background:#0e1013;padding:12px 16px;display:flex;gap:10px;align-items:center;flex-wrap:wrap;z-index:5}
h1{font-size:18px;margin:0 8px 0 0}
input,textarea,button{font:inherit;color:var(--fg);background:var(--card);border:1px solid #333a45;border-radius:8px;padding:8px 10px}
button{cursor:pointer}button.pri{background:var(--acc);border-color:var(--acc);color:#fff;font-weight:600}
#q{flex:1;min-width:180px}
#tags{padding:10px 16px;display:flex;gap:6px;flex-wrap:wrap}
.tag{background:#2a303a;border-radius:99px;padding:3px 10px;font-size:13px;cursor:pointer}
.tag.on{background:var(--acc)}
#grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px;padding:16px}
.card{background:var(--card);border-radius:12px;overflow:hidden;cursor:pointer;display:flex;flex-direction:column}
.card:hover{outline:2px solid var(--acc)}
.card img,.noimg{width:100%;aspect-ratio:1;object-fit:contain;background:#2b2f38}
.noimg{display:grid;place-items:center;color:var(--mut)}
.card .t{padding:8px 10px;font-size:13px;word-break:break-word}
.card .tg{padding:0 10px 10px;display:flex;gap:4px;flex-wrap:wrap}
.card .tg span{background:#2a303a;border-radius:99px;padding:1px 8px;font-size:11px;color:var(--mut)}
#modal{position:fixed;inset:0;background:#000b;display:none;place-items:center;z-index:10;padding:16px}
#modal.on{display:grid}
.box{background:var(--card);border-radius:14px;max-width:900px;width:100%;max-height:95vh;overflow:auto;display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:16px}
@media(max-width:700px){.box{grid-template-columns:1fr}}
.box img{width:100%;background:#2b2f38;border-radius:10px;object-fit:contain}
.f{display:flex;flex-direction:column;gap:10px}
textarea{min-height:110px;resize:vertical;width:100%}
.row{display:flex;gap:8px;flex-wrap:wrap}.mut{color:var(--mut);font-size:13px;word-break:break-all}
a.btn{display:inline-block;text-decoration:none;background:var(--acc);color:#fff;font-weight:700;padding:10px 14px;border-radius:8px}
a.btn.sec{background:#2a303a}
</style></head><body>
<header><h1>📦 3MF</h1><input id="q" placeholder="Rechercher (nom, tag, description)…">
<button id="scan">Réindexer</button><span class="mut" id="cnt"></span></header>
<div id="tags"></div><div id="grid"></div>
<div id="modal"><div class="box" id="box"></div></div>
<script>
let files=[],tag="",cur=null;
const $=s=>document.querySelector(s),esc=s=>s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
async function load(){
  const r=await fetch('/api/files?q='+encodeURIComponent($('#q').value)+'&tag='+encodeURIComponent(tag));
  files=await r.json();$('#cnt').textContent=files.length+' fichier(s)';
  $('#grid').innerHTML=files.map(f=>`<div class="card" data-id="${f.id}">
    ${f.has_thumb?`<img loading="lazy" src="/thumb/${f.id}">`:'<div class="noimg">pas d\'image</div>'}
    <div class="t">${esc(f.name)}</div><div class="tg">${f.tags.map(t=>`<span>${esc(t)}</span>`).join('')}</div></div>`).join('');
  const tr=await (await fetch('/api/tags')).json();
  $('#tags').innerHTML=tr.map(([t,n])=>`<span class="tag ${t===tag?'on':''}" data-t="${esc(t)}">${esc(t)} (${n})</span>`).join('');
}
$('#grid').onclick=e=>{const c=e.target.closest('.card');if(c)open(+c.dataset.id)};
$('#tags').onclick=e=>{const t=e.target.closest('.tag');if(t){tag=tag===t.dataset.t?'':t.dataset.t;load()}};
$('#q').oninput=()=>load();
$('#scan').onclick=async()=>{$('#scan').textContent='…';await fetch('/api/rescan',{method:'POST',body:'{}'});$('#scan').textContent='Réindexer';load()};
function open(id){
  cur=files.find(f=>f.id===id);
  const url=location.origin+'/files/'+cur.id+'/'+encodeURIComponent(cur.name);
  const bs='bambustudio://open?file='+encodeURIComponent(url);
  $('#box').innerHTML=`<div>${cur.has_thumb?`<img src="/thumb/${cur.id}">`:''}</div>
  <div class="f"><b>${esc(cur.name)}</b><span class="mut">${esc(cur.path)} · ${(cur.size/1048576).toFixed(2)} Mo</span>
  <div class="row"><a class="btn" href="${bs}">🖨 Ouvrir dans Bambu Studio</a><a class="btn sec" href="${url}">Télécharger</a></div>
  <label>Tags (séparés par des virgules)<input id="etags" style="width:100%" value="${esc(cur.tags.join(', '))}"></label>
  <label>Description<textarea id="edesc">${esc(cur.description)}</textarea></label>
  <div class="row"><button class="pri" id="save">Enregistrer</button><button id="close">Fermer</button></div></div>`;
  $('#modal').classList.add('on');
  $('#close').onclick=close;
  $('#save').onclick=async()=>{
    await fetch('/api/files/'+cur.id,{method:'POST',body:JSON.stringify({description:$('#edesc').value,tags:$('#etags').value.split(',')})});
    close();load()};
}
function close(){$('#modal').classList.remove('on')}
$('#modal').onclick=e=>{if(e.target.id==='modal')close()};
document.onkeydown=e=>{if(e.key==='Escape')close()};
load();
</script></body></html>"""


def main():
    global ROOT, DB
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=os.environ.get("MF_ROOT", "./3mf"))
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8000)
    a = ap.parse_args()
    ROOT = os.path.abspath(a.root)
    os.makedirs(ROOT, exist_ok=True)
    DB = os.path.join(ROOT, ".library.db")
    init_db()
    print("Indexation de %s : %d fichier(s)" % (ROOT, scan()))
    print("http://%s:%d" % ("localhost" if a.host == "0.0.0.0" else a.host, a.port))
    ThreadingHTTPServer((a.host, a.port), H).serve_forever()


if __name__ == "__main__":
    main()
