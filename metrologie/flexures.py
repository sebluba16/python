"""Calculs de flexion (theorie des poutres) pour les outils de metrologie imprimes en 3D sur P1S.
Unites : mm, N, MPa (N/mm2), rad.  Valeurs materiaux = ORDRES DE GRANDEUR (plans XY, couches le long de la lame) :
a etalonner sur ta bobine (voir README, section Etalonnage)."""
import math

# E_eff [MPa] dans le plan des couches, eps_max conservateur (fatigue/fluage), CTE [1/K]
MATERIAUX = {
    "PLA":   dict(E=2500, eps=0.006, cte=68e-6),   # raide mais fluage + ramollit a ~55 C : eviter voiture/soleil
    "PETG":  dict(E=1500, eps=0.010, cte=60e-6),   # bon compromis lames flexibles
    "PA-CF": dict(E=3500, eps=0.008, cte=35e-6),   # le plus stable (sec !), imprimer P1S + buse acier trempe
}

def lame_encastree_rotation(E, b, t, l, theta):
    """lame de longueur l qui subit une rotation theta (pivot ~ milieu de la lame)
    -> raideur [N.mm/rad], deformation max de surface."""
    k = E * b * t**3 / (12 * l)
    eps = t * theta / (2 * l)
    return k, eps

def platine_parallelogramme(mat, n_lames, Z, t, L):
    """guidage par n lames paralleles de longueur L : raideur, course max, mouvement parasite"""
    E, eps = mat["E"], mat["eps"]
    k = n_lames * E * Z * t**3 / L**3            # N/mm (n lames guidees : 12EI/L3 chacune)
    dmax = eps * L**2 / (3 * t)                  # mm
    par = lambda d: 0.6 * d**2 / L               # raccourcissement (mm) pour un deplacement d
    return k, dmax, par

def rapport(bras_in, bras_out):
    return bras_in / bras_out

def derive_thermique(mat, longueur_mm, dT=1.0):
    """variation de cote en micron pour dT kelvin sur une longueur d'acier de structure en plastique"""
    return mat["cte"] * longueur_mm * dT * 1000.0
