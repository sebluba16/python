"""Genere les STL d'outils de metrologie a flexions (ordre du micron) pour Bambu Lab P1S (plateau 256 mm).
  01_comparateur_a_levier.stl  : renvoi d'angle a lame flexible, rapport 25:1, pointe de lecture sur echelle gravee
  02_platine_micrometrique.stl : platine a parallelogramme + levier de reduction 10:1 poussee par vis M3 (0,5 mm/tour -> 50 um/tour)
  03_coupons_flexion.stl       : lames de 0,6 a 1,2 mm pour mesurer l'epaisseur REELLE imprimee et la raideur
Le micron vient du MECANISME (flexions sans jeu ni frottement + rapport de levier + pas de vis), pas de la precision de l'imprimante (~0,05-0,1 mm).
Imprimer A PLAT (couches paralleles au plan XY du dessin). Unites : mm."""
import math, numpy as np, trimesh
from shapely.geometry import box, Point, Polygon
from shapely.ops import unary_union
from flexures import MATERIAUX, platine_parallelogramme, lame_encastree_rotation, derive_thermique

T_LAME = 0.8      # = 2 filets de 0,4 mm : mince, mais imprimable proprement
BED = 256.0

def ext(geom, z):
    geoms = list(geom.geoms) if hasattr(geom, "geoms") else [geom]
    ms = []
    for g in geoms:
        if g.is_empty or g.area < 1e-6: continue
        ms.append(trimesh.creation.extrude_polygon(g, z))
    return trimesh.util.concatenate(ms)

def cyl_x(x0, x1, y, z, d):
    c = trimesh.creation.cylinder(radius=d/2, height=x1-x0, sections=48)
    c.apply_transform(trimesh.transformations.rotation_matrix(math.pi/2, [0, 1, 0]))
    c.apply_translation([(x0+x1)/2, y, z])
    return c

def diff(a, b): return trimesh.boolean.difference([a, b], engine="manifold")

def hole(x, y, d): return Point(x, y).buffer(d/2, 48)

# ---------------------------------------------------------------- 1. comparateur a levier
def comparateur(ratio=25.0, bras=6.4, Z=8.0, t=T_LAME, lp=8.0, pitch=1.0):
    pivot_x = -4 - lp/2                       # centre de rotation ~ milieu de la lame
    xt = pivot_x + ratio*bras                 # pointe de l'aiguille
    hub = box(-4, -4, 4, 4)
    aiguille = Polygon([(3, -3), (xt-6, -0.7), (xt, 0), (xt-6, 0.7), (3, 3)])
    palpeur = unary_union([Polygon([(-2, -3), (2, -3), (0.9, -bras+1), (-0.9, -bras+1)]),
                           Point(0, -bras+1).buffer(1.0, 32)])           # bille de pointe R1, point bas a y=-bras
    lame = box(-4-lp, -t/2, -4, t/2)
    bloc = box(-28, -3, -4-lp, 22)
    barre = box(-28, 16, xt+10, 22)
    jambe = box(xt+1.2, -7, xt+10, 22)
    # echelle : rainures de 0,5 mm de large, pas pitch, creusees dans la face de la jambe (cote aiguille)
    rain = []
    for k in range(-8, 9):
        long_ = 1.8 if k % 5 == 0 else 1.0
        rain.append(box(xt+1.2, k*pitch-0.25, xt+1.2+long_, k*pitch+0.25))
    f = unary_union([bloc, barre, jambe, lame, hub, aiguille, palpeur])
    f = f.difference(unary_union(rain))
    f = f.difference(hole(-20, 2, 3.4)).difference(hole(-20, 12, 3.4))   # vis M3 de fixation
    return f, xt, ratio, bras, Z, t, lp

# ---------------------------------------------------------------- 2. platine micrometrique
def platine(Z=10.0, t=T_LAME, L=10.0):
    stage = box(20, 12, 60, 42)
    lames = [box(x-t/2, 2, x+t/2, 12) for x in (24, 56)] + [box(x-t/2, 42, x+t/2, 52) for x in (24, 56)]
    frame = unary_union([box(-5, -3, 100, 2), box(-5, -3, 0, 57), box(-5, 52, 66, 57), box(90, -3, 100, 80)])
    levier = box(70, 12, 78, 76)
    pivot = box(74-t/2, 2, 74+t/2, 12)                    # centre y=7
    lien = box(60, 13-t/2, 70, 13+t/2)                    # bras de sortie 6 (de y=7 a y=13)
    p = unary_union([frame, stage, levier, pivot, lien] + lames).simplify(0.002)
    for x, y in ((30, 27), (50, 27), (40, 36)): p = p.difference(hole(x, y, 4.1))      # inserts M3 sur la platine
    for y in (10, 45): p = p.difference(hole(95, y, 4.4))                                # fixation M4 sur le socle
    return p, dict(Z=Z, t=t, L=L, bras_in=67-7, bras_out=13-7, pas=0.5)

# ---------------------------------------------------------------- 3. coupons
def coupons(Z=10.0):
    ts = [0.6, 0.7, 0.8, 0.9, 1.0, 1.2]
    parts = [box(0, 0, 8*len(ts)+6, 4)]
    for i, tt in enumerate(ts):
        x = 4 + 8*i
        parts.append(box(x, 4, x+tt, 24))                   # lame en porte-a-faux
        parts.append(box(x-1, 24, x+tt+1, 28))                   # tete de pousse
    return unary_union(parts), ts

def main():
    out = "."
    # 1
    f, xt, ratio, bras, Z, t, lp = comparateur()
    m = ext(f, 8.0); m.export("01_comparateur_a_levier.stl")
    print(f"01 comparateur : {m.bounds[1]-m.bounds[0]} mm, watertight={m.is_watertight}")
    # 2
    p, g = platine()
    m = ext(p, 10.0)
    for y in (67,):                                              # canal de la vis M3 (inserts laiton cote mur)
        m = diff(m, cyl_x(88, 101, y, 5.0, 4.1))
    m.export("02_platine_micrometrique.stl")
    print(f"02 platine : {m.bounds[1]-m.bounds[0]} mm, watertight={m.is_watertight}")
    # 3
    c, ts = coupons()
    m = ext(c, 10.0); m.export("03_coupons_flexion.stl")
    print(f"03 coupons : {m.bounds[1]-m.bounds[0]} mm, watertight={m.is_watertight}")
    # ---------------- rapport de dimensionnement
    print("\n=== Dimensionnement (ordres de grandeur, a etalonner) ===")
    for nom, mat in MATERIAUX.items():
        k, dmax, par = platine_parallelogramme(mat, 4, g["Z"], g["t"], g["L"])
        r = g["bras_in"]/g["bras_out"]
        kr, eps = lame_encastree_rotation(mat["E"], Z, t, lp, 4.0/(ratio*bras))
        print(f"{nom:6s} platine: k={k:5.2f} N/mm | course max {dmax*1000:5.0f} um | parasite a 50 um: {par(0.05)*1000:5.2f} um"
              f" | 1 tour M3 = {g['pas']/r*1000:.0f} um (1/36 tour = {g['pas']/r*1000/36:.2f} um)"
              f" | comparateur: eps pivot a +-4 mm pointe = {eps*100:.2f} % (limite {mat['eps']*100:.1f} %), etendue +-{4/ratio*1000:.0f} um"
              f" | derive 1 K sur 100 mm : {derive_thermique(mat,100):.1f} um")
    print(f"\nComparateur : rapport {ratio:.0f}:1, 1 graduation (pas 1,0 mm) = {1.0/ratio*1000:.0f} um ; lecture a la loupe/macro ~ 1/5 graduation = {1.0/ratio*1000/5:.0f} um")

if __name__ == "__main__":
    main()
