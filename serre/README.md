# Mini serre Arduino Nano - impression < 1h30

## Fichiers
- `fusion360/mini_serre.py` : script Fusion 360 (4 pieces a plat, parametres en haut du fichier)
- `arduino/serre/serre.ino` : code Nano (ventilation, arrosage, LED)

## Pieces et estimation d'impression (PLA/PETG, buse 0.4)
| Piece | Taille mm | ~Volume | ~Temps |
|---|---|---|---|
| Base_bac | 100x70x35 | 28 g | 40 min |
| Toit_cadre | 103x73x7 | 7 g | 12 min |
| Boitier_Nano | 48x28x18 | 6 g | 10 min |
| Support_capteurs | 90x10x2.4 | 1 g | 3 min |
Total ~ 65 min a plat (marge pour < 1h30). Verifier dans le slicer.

## Reglages slicer (Cura / PrusaSlicer)
Couche 0.28 mm, 2 parois (1.6 mm cote base), remplissage 10 % gyroid, 80-100 mm/s,
pas de support, pas de brim, ventilateur 100 %. Imprimer les 4 pieces sur le meme plateau.
Si le total depasse 1h30 : couche 0.32 mm ou remplissage 5 %.

## Cablage Nano
| Composant | Broche |
|---|---|
| DHT22 data (+10k vers 5V) | D2 |
| Sol capacitif | A0 |
| Ventilateur 5V (MOSFET IRLZ44N / grille via 220R) | D5 |
| Pompe 5V (MOSFET + diode de roue libre 1N4007) | D6 |
| LED 5V (MOSFET) | D9 |
Alim 5 V externe (>=2 A) si pompe, GND commun avec le Nano.

## Fusion 360
1. Utilitaires > Scripts et complements > "+" > dossier `fusion360`.
2. Executer `mini_serre`. Changer `L, W, H, WALL, JEU` en haut du script si besoin.
3. Clic droit sur chaque composant > Enregistrer comme maillage > STL.
4. Toit : coller film PET transparent sur le cadre. Boitier : se pose a cote de la base.

## Calibration
Sol : lire `sol` au serie, air sec = valeur haute, eau = valeur basse, regler `SOL_SEC`.
