"""Génère les 2 STL de porte-clés coquille Saint-Jacques (cf. PDF "300 modèles et budget").
Modèle 1 : 40 x 38 x 2,4 mm, triangle dans un cercle GRAVÉ (0,48 mm), rainures radiales gravées.
Modèle 2 : 44 x 42 mm, fond 2,4 mm + relief 0,48 mm (triquetra + rayons).
Trou d'anneau 4 mm dans une base élargie (>= 3 mm de matière autour). Unités : mm."""
import math, numpy as np, trimesh
from shapely.geometry import Point, Polygon, LineString, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity

T, D = 2.4, 0.48          # épaisseur fond, profondeur / hauteur de relief
HOLE_D, LUG_R = 4.0, 5.5  # trou 4 mm, matière autour 3,5 mm
STROKE = 1.2              # traits 1-1,2 mm

def pol(cx, cy, r, a): return (cx + r*math.cos(math.radians(a)), cy + r*math.sin(math.radians(a)))

def shell(Rc, spread, nlobes, hinge_y, sx=1.0, sy=1.0):
    """éventail arrondi (sans la base), centré sur x=0, sommet de l'éventail en (0,hinge_y)"""
    H = (0, hinge_y)
    angs = np.linspace(90-spread/2, 90+spread/2, nlobes)
    step = math.radians(spread/(nlobes-1))
    rl = Rc*math.sin(step/2)*1.12
    Rs = Rc - rl*0.55                                           # centre des festons
    sector = Polygon([H] + [pol(H[0], H[1], Rs, a) for a in np.linspace(90-spread/2, 90+spread/2, 80)])
    lobes = [Point(*pol(H[0], H[1], Rs, a)).buffer(rl, 64) for a in angs]
    belly = Point(0, hinge_y + Rc*0.50).buffer(Rc*0.50, 64)     # flancs arrondis
    s = unary_union([sector, belly, *lobes])
    s = s.buffer(1.2, 32).buffer(-1.2, 32)                       # creux entre festons arrondis
    return affinity.scale(s, sx, sy, origin=(0, hinge_y))

def build(W, Hh, nlobes, spread=118.0, hinge_y=1.5):
    """ajuste l'éventail pour que (éventail + base/trou) fasse exactement W x Hh"""
    Hfan = Hh - LUG_R - hinge_y + 1.0                            # hauteur utile au-dessus de la base
    s0 = shell(14.0, spread, nlobes, hinge_y)
    x0, y0, x1, y1 = s0.bounds
    sx, sy = W/(x1-x0), (Hh - LUG_R - 0.0 - y0 + hinge_y*0 )/(y1-y0)
    # hauteur totale = y1' - (-LUG_R) = Hh ; y0 (= hinge) est englobé par la base
    sy = (Hh - LUG_R - hinge_y)/(y1-hinge_y)
    s = shell(14.0, spread, nlobes, hinge_y, sx, sy)
    lug = Point(0, 0).buffer(LUG_R, 64)
    s = unary_union([s, lug])
    return s, spread

def fit(W, Hh, nlobes, hinge_y=2.0):
    s, sp = build(W, Hh, nlobes, hinge_y=hinge_y)
    return s, 0, sp

def ext(geom, z0, z1):
    """extrude un Polygon/MultiPolygon entre z0 et z1"""
    geoms = geom.geoms if isinstance(geom, MultiPolygon) else [geom]
    ms = []
    for g in geoms:
        if g.is_empty or g.area < 1e-6: continue
        m = trimesh.creation.extrude_polygon(g, z1-z0); m.apply_translation([0, 0, z0]); ms.append(m)
    return trimesh.util.concatenate(ms)

def union(a, b): return trimesh.boolean.union([a, b], engine="manifold")
def diff(a, b): return trimesh.boolean.difference([a, b], engine="manifold")

def stroke(line, w=STROKE): return line.buffer(w/2, 24, cap_style=1, join_style=1)

def radial(cy, r_in, r_out, angs, w=STROKE, hinge=(0, 0)):
    return unary_union([stroke(LineString([pol(hinge[0], hinge[1], r_in, a), pol(hinge[0], hinge[1], r_out, a)]), w) for a in angs])


def rays_from(cx, cy, r_in, safe, angs, w):
    out = []
    for a in angs:
        full = LineString([pol(cx, cy, r_in, a), pol(cx, cy, 60, a)]).intersection(safe)
        if full.is_empty: continue
        segs = list(full.geoms) if hasattr(full, "geoms") else [full]
        seg = max(segs, key=lambda g: g.length)
        if seg.length > 2.5: out.append(stroke(seg, w))
    return unary_union(out)

def finish(body_outline, name):
    return body_outline

# ---------------- Modèle 1 : sobre ----------------
def model1():
    s, Rc, sp = fit(40, 38, 7, 2.0)
    hole = Point(0, 0).buffer(HOLE_D/2, 48)
    outline = s.difference(hole)
    x0, y0, x1, y1 = s.bounds
    cx, cy = 0, y0 + (y1-y0)*0.52 + 1.0               # centre du logo
    # cercle + triangle équilatéral inscrit (traits 1,2 mm)
    Rr = 7.4
    ring = Point(cx, cy).buffer(Rr+STROKE/2, 64).difference(Point(cx, cy).buffer(Rr-STROKE/2, 64))
    rt = 5.4  # rayon circonscrit du triangle
    tri_pts = [pol(cx, cy-0.6, rt, a) for a in (90, 210, 330)]
    tri = stroke(LineString(tri_pts + [tri_pts[0]]))
    logo = unary_union([ring, tri])
    # rainures radiales qui s'arrêtent avant le logo et avant le bord
    safe = s.buffer(-2.2).difference(Point(0, 0).buffer(LUG_R+2.0))
    rays = rays_from(cx, cy, Rr+STROKE/2+1.8, safe, [90+d for d in (-72,-48,-24,0,24,48,72)], 1.0)
    engr = unary_union([logo, rays])
    plate = ext(outline, 0, T)
    cut = ext(engr.intersection(outline), T-D, T+0.2)
    return diff(plate, cut), outline, engr.intersection(outline)

# ---------------- Modèle 2 : traditionnelle ----------------
def triquetra(cx, cy, d=6.8, k=1.3):
    """3 lentilles (intersections de 3 cercles de rayon R=k*d centrés sur un triangle de côté d*sqrt3),
    dont on ne garde que le contour : lobes entrelacés, pointes vers le haut / bas-gauche / bas-droite."""
    R = k*d
    centers = [pol(0, 0, d, a) for a in (270, 30, 150)]
    circ = [Point(*c).buffer(R, 256) for c in centers]
    lenses = [circ[0].intersection(circ[1]), circ[1].intersection(circ[2]), circ[2].intersection(circ[0])]
    tq = unary_union([stroke(l.boundary) for l in lenses])
    x0, y0, x1, y1 = tq.bounds
    return affinity.translate(tq, cx-(x0+x1)/2, cy-(y0+y1)/2)

def model2():
    s, Rc, sp = fit(44, 42, 9, 2.0)
    hole = Point(0, 0).buffer(HOLE_D/2, 48)
    outline = s.difference(hole)
    x0, y0, x1, y1 = s.bounds
    cx, cy = 0, y0 + (y1-y0)*0.58 + 1.0
    tq = triquetra(cx, cy)
    safe = s.buffer(-2.2).difference(Point(0, 0).buffer(LUG_R+2.0))
    rays = rays_from(cx, cy, 10.8, safe, [90+d for d in (-72,-48,-24,0,24,48,72)], 1.2)
    relief = unary_union([tq, rays]).intersection(s.buffer(-1.0))
    plate = ext(outline, 0, T)
    top = ext(relief, T-0.2, T+D)                     # léger recouvrement pour fusion propre
    return union(plate, top), outline, relief

if __name__ == "__main__":
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path
    m1, o1, g1 = model1(); m2, o2, g2 = model2()
    for name, m in (("coquille_1_sobre", m1), ("coquille_2_traditionnelle", m2)):
        m.export(f"/home/user/python/coquilles/{name}.stl")
        print(name, "bbox mm:", np.round(m.extents, 2), "watertight:", m.is_watertight, "volume mm3:", round(m.volume, 1),
              "masse PLA ~g:", round(m.volume*1.24/1000, 2))
    def patch(g, **kw):
        gs = g.geoms if hasattr(g, "geoms") else [g]; out = []
        for p in gs:
            vs, cs = [], []
            for ring in [p.exterior, *p.interiors]:
                c = np.array(ring.coords); vs += list(c); cs += [Path.MOVETO] + [Path.LINETO]*(len(c)-2) + [Path.CLOSEPOLY]
            out.append(PathPatch(Path(vs, cs), **kw))
        return out
    fig, axs = plt.subplots(1, 2, figsize=(12, 6.4))
    for ax, o, g, t in ((axs[0], o1, g1, "1 • Coquille sobre (gravé)"), (axs[1], o2, g2, "2 • Coquille traditionnelle (relief)")):
        for p in patch(o, fc="#d8c08a", ec="#8a7340", lw=1): ax.add_patch(p)
        for p in patch(g, fc="#a88f58" if "gravé" in t else "#efe0b4", ec="none"): ax.add_patch(p)
        ax.set_xlim(-26, 26); ax.set_ylim(-9, 40); ax.set_aspect("equal"); ax.axis("off"); ax.set_title(t)
    plt.savefig("/home/user/python/coquilles/apercu.png", dpi=110)
