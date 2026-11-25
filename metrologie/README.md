# Metrologie micron en impression 3D (Bambu Lab P1S)

**Principe : le micron vient du mécanisme, pas de l'imprimante.** La P1S imprime à ~±0,05–0,1 mm. Pour mesurer au micron on utilise :
lames flexibles (zéro jeu, zéro frottement) + rapport de levier + **pas de vis M3 (0,5 mm, standard ISO)**.

| Fichier | Rôle | Chiffres (calcul, `python3 make_stl.py`) |
|---|---|---|
| `01_comparateur_a_levier.stl` | comparateur à levier (renvoi d'angle sur lame), aiguille sur échelle gravée | rapport 25:1, 1 graduation = 40 µm, lecture loupe/macro ≈ 8 µm, étendue ±160 µm |
| `02_platine_micrometrique.stl` | platine à parallélogramme + levier réducteur 10:1 poussé par vis M3 | 1 tour = 50 µm, 1/36 tour = 1,4 µm, course ≈ ±0,2 mm, mouvement parasite < 0,2 µm |
| `03_coupons_flexion.stl` | lames 0,6→1,2 mm | mesurer épaisseur réelle + raideur de TA bobine |

## Impression (indispensable)
- **À plat**, tel quel (couches parallèles au dessin). PETG (souple, ok) ; PA-CF = plus stable thermiquement (sécher, buse acier).
- Buse 0,4, couche 0,16–0,2, **2 parois min.** (lame = 0,8 mm = 2 filets), détection parois fines ON, remplissage 30 %+, vitesse 60–100 mm/s, **ventilation basse**, imprimer dans l'enceinte fermée.
- Compensation « elephant foot » 0,1–0,15 mm. Pas de bordure (brim) collée aux lames : la retirer au cutter sous loupe.
- **Cube de calibration d'abord** : imprime `03_coupons_flexion.stl`, mesure les lames au pied à coulisse/micromètre. La raideur varie en **t³** : ±0,05 mm sur 0,8 mm = ±20 % de raideur. Ajuste `T_LAME` dans `make_stl.py` si besoin.

## Montage
- Platine : inserts laiton M3 à chaud dans les 3 trous Ø4,1 de la plaque mobile, et dans le canal Ø4,1 du mur droit (vis M3×20 bout rond ou bille). Fixer sur socle par 2 vis M4.
- Comparateur : 2 vis M3 dans le bloc de gauche. Palpeur à bille R1 en bas. Mettre l'ensemble à plat (la gravité n'agit pas dans le plan).
- Ne **jamais** forcer le levier à la main (pas de butées intégrées) : lame cassée = 5 min de réimpression.

## Étalonnage mutuel (sans instrument de référence)
1. Pousse le palpeur du comparateur avec la platine : 1 tour de vis M3 = 0,5 mm / 10 = 50 µm → relève les graduations de l'aiguille → rapport réel du comparateur (le pas ISO est ton étalon).
2. Vérification absolue : cales étalons / jauges d'épaisseur (feeler gauge 0,02–0,10 mm) entre palpeur et butée.

## Limites honnêtes (à lire)
- **Résolution ≠ exactitude.** Tu liras quelques µm en *relatif*, sur de courtes durées. Hystérésis, fluage plastique (revenir au zéro, ne pas laisser sous charge), jeu du filetage de la vis.
- **Température** : dilatation PETG ≈ 60e‑6/K → ~6 µm/K sur 100 mm de structure. Travailler à température stable, laisser stabiliser 30 min, ne pas toucher à mains nues. Valeurs matériau de `flexures.py` = ordres de grandeur.
- Ces outils servent à *comparer* (cales, pièces, vis de réglage, mesure de déformation), pas à remplacer un micromètre calibré.

Régénérer : `pip install trimesh shapely manifold3d mapbox-earcut` puis `python3 make_stl.py` (dans ce dossier).
