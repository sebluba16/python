"""Génère les 2 STL de porte-clés coquille Saint-Jacques (cf. PDF "300 modèles et budget").
Modèle 1 : 40 x 38 x 2,4 mm, triangle dans un cercle GRAVÉ (0,48 mm), rainures radiales gravées.
Modèle 2 : 44 x 42 mm, fond 2,4 mm + relief 0,48 mm (triquetra + rayons).
Trou d'anneau 4 mm dans une base élargie (>= 3 mm de matière autour). Unités : mm.
Silhouette : éventail bombé aux festons arrondis (creux pointus adoucis), flancs qui se resserrent vers la charnière."""
import math, numpy as np, trimesh
from shapely.geometry import Point, Polygon, LineString, MultiPolygon, MultiPoint
from shapely.ops import unary_union
from shapely import affinity

T, D = 2.4, 0.48
HOLE_D, LUG_R = 4.0, 5.5
STROKE = 1.2
HY = 9.0                            # hauteur des extrémités de l éventail au-dessus du centre du trou
PHI0, PHI1 = 8.0, 172.0           # angles (depuis le centre de l'éventail) couverts par les festons

def pol(cx, cy, r, a): return (cx + r*math.cos(math.radians(a)), cy + r*math.sin(math.radians(a)))

def scallop_fan(nlobes, depth=0.12, a=20.0, b=17.0):
    """contour festonné : ellipse (a,b) dont le rayon est modulé par |sin| -> lobes ronds, creux pointus"""
    phis = np.linspace(PHI0, PHI1, 40*nlobes + 1)
    pts = []
    for p in phis:
        u = (p-PHI0)/(PHI1-PHI0)
        f = 1 - depth*(1-abs(math.sin(nlobes*math.pi*u)))
        r = (a*b)/math.hypot(b*math.cos(math.radians(p)), a*math.sin(math.radians(p)))
        pts.append((r*f*math.cos(math.radians(p)), r*f*math.sin(math.radians(p))))
    peaks = [PHI0 + (k+0.5)*(PHI1-PHI0)/nlobes for k in range(nlobes)]
    return pts, peaks

def build(W, Hh, nlobes):
    """renvoie (contour sans trou, centre du logo, angles des rayons)"""
    pts, peaks = scallop_fan(nlobes)
    fan = Polygon(pts + [(0, 0)]).buffer(0)
    left, right = pts[-1], pts[0]
    # mise à l'échelle : largeur W ; hauteur totale Hh = haut de l'éventail + base (rayon LUG_R sous le trou)
    x0, y0, x1, y1 = fan.bounds
    ybase = min(left[1], right[1])                                    # hauteur des extrémités (charnière)
    sx = W/(x1-x0)
    sy = (Hh - LUG_R - HY - (ybase-ybase)) / (y1-ybase)             # extrémités à y=2.5 au-dessus du centre du trou
    def tf(g): return affinity.translate(affinity.scale(g, sx, sy, origin=(0, ybase)), 0, HY-ybase)
    fan_s = tf(fan)
    lp = tf(Point(left)).coords[0]; rp = tf(Point(right)).coords[0]
    lug = Point(0, 0).buffer(LUG_R, 64)
    cc = tf(Point(0, 0)).coords[0]
    wedge = MultiPoint([lp, rp, cc, (-LUG_R*0.9, 0.0), (LUG_R*0.9, 0.0)]).convex_hull
    s = unary_union([fan_s, wedge, lug])
    s = s.buffer(1.0, 32).buffer(-2.0, 32).buffer(1.0, 32)          # creux et pointes arrondis
    c = tf(Point(0, 0)).coords[0]                                    # centre de l'éventail
    return s, c, peaks

def ext(geom, z0, z1):
    geoms = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    ms = []
    for g in geoms:
        if g.is_empty or g.area < 1e-6: continue
        m = trimesh.creation.extrude_polygon(g, z1-z0); m.apply_translation([0, 0, z0]); ms.append(m)
    return trimesh.util.concatenate(ms)

def union(a, b): return trimesh.boolean.union([a, b], engine="manifold")
def diff(a, b): return trimesh.boolean.difference([a, b], engine="manifold")
def stroke(line, w=STROKE): return line.buffer(w/2, 24, cap_style=1, join_style=1)

def ribs(cx, cy, r_in, safe, angs, w, logo_zone):
    out = []
    for a in angs:
        full = LineString([pol(cx, cy, r_in, a), pol(cx, cy, 60, a)]).intersection(safe).difference(logo_zone)
        if full.is_empty: continue
        segs = list(full.geoms) if hasattr(full, "geoms") else [full]
        seg = max(segs, key=lambda g: g.length)
        if seg.length > 2.5: out.append(stroke(seg, w))
    return unary_union(out)

def hole(): return Point(0, 0).buffer(HOLE_D/2, 48)

# ---------------- Modèle 1 : sobre (gravé) ----------------
def model1():
    s, (cx, cy), peaks = build(40, 38, 7)
    outline = s.difference(hole())
    hx, hy = cx, cy                                   # centre de l'éventail (origine des rayons)
    cy += 9.0                                         # centre du logo
    Rr, rt = 7.0, 5.1
    ring = Point(cx, cy).buffer(Rr+STROKE/2, 64).difference(Point(cx, cy).buffer(Rr-STROKE/2, 64))
    tri_pts = [pol(cx, cy-0.6, rt, a) for a in (90, 210, 330)]
    tri = stroke(LineString(tri_pts + [tri_pts[0]]))
    logo = unary_union([ring, tri])
    safe = s.buffer(-2.2).difference(Point(0, 0).buffer(LUG_R+2.0))
    zone = Point(cx, cy).buffer(Rr+STROKE/2+1.8)
    rays = ribs(hx, hy, 8.0, safe, peaks, 1.0, zone)
    engr = unary_union([logo, rays]).intersection(outline)
    plate = ext(outline, 0, T)
    return diff(plate, ext(engr, T-D, T+0.2)), outline, engr

# ---------------- Modèle 2 : traditionnelle (relief) ----------------
def triquetra(cx, cy, d=6.8, k=1.3):
    R = k*d
    centers = [pol(0, 0, d, a) for a in (270, 30, 150)]
    circ = [Point(*c).buffer(R, 256) for c in centers]
    lenses = [circ[0].intersection(circ[1]), circ[1].intersection(circ[2]), circ[2].intersection(circ[0])]
    tq = unary_union([stroke(l.boundary) for l in lenses])
    x0, y0, x1, y1 = tq.bounds
    return affinity.translate(tq, cx-(x0+x1)/2, cy-(y0+y1)/2)

def model2():
    s, (cx, cy), peaks = build(44, 42, 9)
    outline = s.difference(hole())
    hx, hy = cx, cy
    cy += 10.0
    tq = triquetra(cx, cy)
    safe = s.buffer(-2.2).difference(Point(0, 0).buffer(LUG_R+2.0))
    zone = tq.buffer(2.0)
    rays = ribs(hx, hy, 8.0, safe, peaks, 1.2, zone)
    relief = unary_union([tq, rays]).intersection(s.buffer(-1.0))
    plate = ext(outline, 0, T)
    return union(plate, ext(relief, T-0.2, T+D)), outline, relief

# ---------------- Modèle 3 : Bouclier de la Trinité (Scutum Fidei), relief ----------------
def scutum(cx, cy, Rv=10.2, ro=3.3):
    """triangle pointe en bas : 3 disques (anneaux) aux sommets + 1 au centre, reliés par les côtés et 3 rayons"""
    V = [pol(0, 0, Rv, a) for a in (270, 30, 150)]
    rings = [Point(*c).buffer(ro, 48).difference(Point(*c).buffer(ro-STROKE, 48)) for c in V + [(0, 0)]]
    nodes = [Point(*c).buffer(ro-0.2, 48) for c in V + [(0, 0)]]
    lines = [LineString([V[i], V[(i+1) % 3]]) for i in range(3)] + [LineString([(0, 0), v]) for v in V]
    bars = unary_union([stroke(l) for l in lines]).difference(unary_union(nodes))
    g = unary_union(rings + [bars])
    x0, y0, x1, y1 = g.bounds
    return affinity.translate(g, cx-(x0+x1)/2, cy-(y0+y1)/2)

def model3():
    s, (cx, cy), peaks = build(44, 42, 9)
    outline = s.difference(hole())
    hx, hy = cx, cy
    logo = scutum(cx, cy + 9.5)
    safe = s.buffer(-2.2).difference(Point(0, 0).buffer(LUG_R+2.0))
    rays = ribs(hx, hy, 8.0, safe, peaks, 1.2, logo.buffer(2.6))
    relief = unary_union([logo, rays]).intersection(s.buffer(-1.0))
    print("logo dans le contour (marge 1 mm):", s.buffer(-1.0).contains(logo))
    plate = ext(outline, 0, T)
    return union(plate, ext(relief, T-0.2, T+D)), outline, relief

if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path
    m1, o1, g1 = model1(); m2, o2, g2 = model2(); m3, o3, g3 = model3()
    for name, m in (("coquille_1_sobre", m1), ("coquille_2_traditionnelle", m2), ("coquille_3_bouclier_trinite", m3)):
        m.export(f"/home/user/python/coquilles/{name}.stl")
        print(name, "bbox mm:", np.round(m.extents, 2), "watertight:", m.is_watertight, "volume mm3:", round(m.volume, 1),
              "masse PLA ~g:", round(m.volume*1.24/1000, 2))
    def patch(g, **kw):
        out = []
        for p in (g.geoms if hasattr(g, "geoms") else [g]):
            vs, cs = [], []
            for ring in [p.exterior, *p.interiors]:
                c = np.array(ring.coords); vs += list(c); cs += [Path.MOVETO] + [Path.LINETO]*(len(c)-2) + [Path.CLOSEPOLY]
            out.append(PathPatch(Path(vs, cs), **kw))
        return out
    fig, axs = plt.subplots(1, 3, figsize=(18, 6.4))
    for ax, o, g, t in ((axs[0], o1, g1, "1 • Coquille sobre (gravé)"), (axs[1], o2, g2, "2 • Coquille traditionnelle (relief)"), (axs[2], o3, g3, "3 • Bouclier de la Trinité (relief)")):
        for p in patch(o, fc="#d8c08a", ec="#8a7340", lw=1): ax.add_patch(p)
        for p in patch(g, fc="#a88f58" if "gravé" in t else "#efe0b4", ec="none"): ax.add_patch(p)
        ax.set_xlim(-26, 26); ax.set_ylim(-9, 40); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(t)
    plt.savefig("/home/user/python/coquilles/apercu.png", dpi=110)
