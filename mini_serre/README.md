# Mini serre imprimée 3D (< 2 h)

Matériel : Arduino Nano, SG90, DHT22 (ou DHT11), sonde humidité sol capacitive, LDR + R 10k.

## Fichiers
- `fusion360_serre.py` : script Fusion 360, 19 paramètres utilisateur (L, W, H, wall, vent_w, servo_*, dht_*...).
  Tout change via *Modify > Change Parameters*.
- `firmware/serre.ino` : régulation T° -> SG90 ouvre/ferme la fente du toit, mesures sol + lumière.

## Câblage
DHT22 data -> D2 | SG90 signal -> D9 (5 V externe conseillé) | sol -> A0 | LDR (pont diviseur) -> A1.
Servo : bras collé sur le palonnier qui soulève un volet/toit au-dessus de la fente.

## Réglages Bambu Studio (cible ~ 1h30 total, Base + Toit sur 1 plateau)
- Buse 0.4, couche 0.28 mm (Standard 0.28 / Draft), 2 parois, 10 % gyroïde, 0 support.
- Toit : posé face plate vers le bas ; Base : ouverture vers le haut. Orienter la fenêtre servo sans surplomb (<= 45°).
- Vitesse : profil "0.28mm Extra Draft" sur P1/X1/A1 ; PLA, pas de bordure sauf besoin.
- Si > 2 h : réduire H (60 -> 45) ou L/W, passer wall à 1.2 mm : tout se recalcule.

## Estimation temps (calcul, non tranché)
Base ~41 cm3 + Toit 6 mm ~17 cm3 + Volet ~2 cm3 = ~60 cm3 (~75 g PLA), débit effectif ~12 mm3/s en 0.28 mm => ~85 min (< 2 h).
Volet : 3e corps (à plat), glisse sur le toit ; le palonnier SG90 entre dans sa fente `horn_w`. Le SG90 se colle derrière la fenêtre arrière.
**A vérifier** en tranchant dans Bambu Studio : si > 2 h, réduire H ou L/W.

## Notes
- Script non testé sur ta version de Fusion : si une découpe de paroi part du mauvais côté, `FLIP = -1`.
- Calibrer SOL_SEC / SOL_HUMIDE (sonde dans l'air vs dans l'eau).
