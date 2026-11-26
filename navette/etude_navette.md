# Étude : navette électrique de campus (2 places avant + 1 blessé assis, jambe plâtrée, à l'arrière)

> Avant-projet. Les chiffres viennent de `navette_calc.py` (hypothèses modifiables en tête du fichier). Ce n'est **pas** un dossier de fabrication : voir « Réglementation et responsabilité ».

## 1. Besoin
- Trajet : **700 m**, **10 fois par jour**. Hypothèse prudente : 10 aller-retour = **14 km/jour** (si ce sont 10 trajets simples : 7 km, tout est divisé par 2).
- Usage : 2 personnes devant ; à l'arrière, **un blessé assis, jambe plâtrée tendue** (béquilles) ; déplacement lent, en site propre (collège).
- Contraintes : sûreté des élèves, démarrage fiable à tout moment (urgence), entretien minimal, silence.
- Conséquence clé : **usage très faible en énergie** (≈ 1 kWh/jour), mais **fiabilité et sécurité** priment sur la performance.

## 2. Cahier des charges proposé
| Critère | Valeur |
|---|---|
| Vitesse max (limiteur) | **20 km/h** (12 km/h à l'approche du bâtiment) |
| Places | 2 avant (ceintures) + 1 arrière blessé assis, jambe plâtrée tendue sur repose-jambe |
| Charge utile | 250 kg (2×80 + blessé 80 + béquilles 10) |
| Rampe | 10 % à 15 km/h ; 15 % à 8 km/h (rampe de garage) |
| Autonomie | ≥ 2 jours sans recharge (réserve d'urgence) |
| Freinage | hydraulique 4 roues + frein de parking + récupération |
| Accès arrière | côté ou arrière, ouverture ≥ 70 cm, marchepied bas ≤ 30 cm, poignée d'appui, siège à ~45 cm |

## 3. Concept retenu : navette banquette avec repose-jambe
Le blessé est **assis**, jambe plâtrée **tendue et surélevée** : plus besoin de brancard ni de plancher de 1,9 m. Le véhicule peut être **court et léger** (≈ 2,7 m, 1,2 m de large, passe une porte de 1,4 m).
- **Banquette avant** 2 places, ceintures.
- **Arrière** : un siège (ou banquette 2 places dont une côté jambe plâtrée) face route, **repose-jambe** rembourré et réglable (plâtre à l'horizontale, ou légèrement relevé), sangle de maintien de la jambe, **ceinture 3 points**, poignée de maintien, **rangement des béquilles** (rails latéraux).
- **Montée/descente** : plancher bas, marchepied large, ouverture côté trottoir, une personne aide le blessé.
- Option : siège pivotant à 45° côté porte pour entrer jambe tendue.
- Alternative pour blessé plus lourd/plâtre cuisse : plateau arrière long avec 2 sièges tournés vers l'intérieur (plus long : ≈ 3,2 m).

```
Vue de dessus, ≈ 2,7 m                    Avant ──►
 ┌───────────────────────────────────┐
 │[volant][siège][siège] │ siège blessé + repose-jambe │ ◄ ouverture côté
 │ roues AV  batterie sous plancher      roues AR (moteur) │
 └───────────────────────────────────┘
```

## 4. Dimensionnement (résultats du script)
Masse en charge **590 kg** (340 kg à vide visé), CRR 0,012, CdA 1,0 m², rendement 75 %.

| Grandeur | Résultat |
|---|---|
| Consommation | ≈ 59 Wh/km (aller 3 % montée 70 Wh, retour 13 Wh) |
| Énergie par jour (14 km + auxiliaires) | **≈ 1,0 kWh** |
| Puissance accélération (0,7 m/s² → 20 km/h) | ≈ 3,7 kW électrique (crête) |
| Puissance rampe 10 % à 15 km/h | ≈ 3,7 kW |
| Distance de freinage (4 m/s², 20 km/h) | ≈ 3,9 m |

**Choix proposés**
- **Moteur** : BLDC 48 V, 3 kW nominal / 5 kW crête (moyeu arrière ou moteur + chaîne). Couple roue ≥ 1000 N pour la rampe.
- **Batterie** : **LiFePO4 48 V 50 Ah = 2,4 kWh** → ≈ 32 km utiles ≈ 1,9 jour. Cycles : un cycle partiel par jour → >10 ans. Pourquoi LiFePO4 : sûre, tolère le charge/décharge partielle.
- **BMS** 80 A, coupe-circuit d'urgence accessible, fusible 100 A.
- **Chargeur** 48 V 10 A : recharge de 0,5–1 kWh en **2 h environ** (nuit ou pause midi). Prise sur un circuit protégé 16 A + différentiel 30 mA.
- **Limiteur de vitesse** réglé par contrôleur ; option clé « mode urgence » 25 km/h.
- **Aux 12 V** : convertisseur DC-DC 48→12 V (feux, gyrophare, avertisseur de recul, ventilateur).

## 5. Châssis, sécurité, blessé
- Châssis : tubes acier/alu soudés, **cage anti-retournement** (ROPS) et arceau sur cabine ouverte ; pare-chocs mousse. Empattement long + centre de gravité bas (batterie sous plancher) → stabilité.
- Suspension : amortisseurs simples (arrière) + ressort ; sièges amortis (blessé).
- Direction : crémaillère de kart/quad ; rayon de braquage ≤ 3,5 m.
- Freins : disques hydrauliques (avant + arrière), **frein de parking à câble**, régénération douce (pas d'arrêt brusque sur le blessé).
- Blessé : siège avec ceinture 3 points, **jambe plâtrée calée et sanglée** sur le repose-jambe, béquilles rangées (jamais en vrac), conduite douce (décélération ≤ 0,4 g, pas de coup de frein), **bouton d'appel vers le conducteur**, trousse de secours, extincteur.
- Visibilité : feux, clignotants, gyrophare orange, avertisseur de recul, bandes rétro-réfléchissantes.
- Vitesse en site scolaire : **20 km/h max**, 10 km/h aux abords des élèves.

## 6. Acheter ou construire ?
| Option | Atouts | Limites | Coût (ordre de grandeur) |
|---|---|---|---|
| **Voiturette électrique d'occasion** (type voiturette de golf ou utilitaire de site, ex. Goupil, Club Car, Garia) puis aménagement arrière | rapide, fiable, pièces disponibles ; certains modèles existent en version plateau/ambulance | tarif neuf élevé ; modèles de golf peu stables pour blessé | 5–15 k€ |
| **Projet pédagogique (élèves + atelier)** sur base de kit/châssis | très formateur, sur mesure | responsabilité forte ; délai long | 6–10 k€ en matériaux |
| **Quadricycle léger de série** (type Ami, L6e) | homologué, 2 places | pas d'arrière blessé, 45 km/h inutile | 7–10 k€ |

**Recommandation** : acheter une base **robuste d'occasion** (voiturette 4 places (2 avant + banquette arrière) ou plateau 2 places, charge ≥ 300 kg) et faire **aménager l'arrière** (siège + repose-jambe + ceinture) par un carrossier, avec les élèves en projet d'accompagnement. On garde les points de sécurité structurels (freins, direction, châssis) d'un constructeur.

## 7. Réglementation et responsabilité (à vérifier)
- **Site fermé (cour du collège)** : pas d'immatriculation, mais le chef d'établissement porte une **responsabilité** (sécurité, assurance, personnel formé). Prévenir l'assurance **avant** mise en service.
- **Traversée de voie publique** : il faut un véhicule **homologué** (quadricycle L6e/L7e ou voiture) → exclut le fait-maison.
- **Blessé** : une navette de collège ne remplace **pas** les secours : pour un blessé grave, appeler le **15**. L'usage décrit = blessé léger vers l'infirmerie/portail.
- Fabrication artisanale : possible marquage CE de machine, vérification par organisme de contrôle. Contacter la collectivité/le rectorat. **Je n'ai pas vérifié les textes à jour** : à confirmer avec l'assurance et la collectivité propriétaire.

## 8. Risques principaux
| Risque | Parade |
|---|---|
| Blessé mal maintenu / plâtre qui tape | ceinture, calage jambe, conduite douce, sol sans bosses |
| Panne batterie à l'instant critique | SOC ≥ 40 %, recharge quotidienne, voyant, 2e personne avec téléphone |
| Excès de vitesse près des élèves | limiteur 20 km/h, parcours balisé, formation, clé |
| Incendie batterie | LiFePO4, BMS, fusible, local ventilé, extincteur |
| Hiver : froid | LiFePO4 ne se charge pas <0 °C : chargeur en local hors gel |

## 9. Planning proposé
1. **Validation** (2 sem.) : trajet réel (pentes, passage de portes, nombre exact de rotations), assurance, chef d'établissement.
2. **Choix de base** (4 sem.) : devis occasion/neuf, essai.
3. **Aménagement arrière + sécurité** (6–8 sem.).
4. **Essais à vide puis chargé** (2 sem.), formation conducteurs, procédure d'urgence écrite.

## 10. Questions ouvertes (changent le dimensionnement)
- 10 trajets = 10 aller-retour ou 10 trajets simples ?
- Dénivelé réel et état du sol (bitume, gravier, pavés) ?
- Largeur des passages / portes ; trottoirs à franchir ?
- Qui conduit (adulte formé uniquement) ? Budget disponible ?
- Une voie publique est-elle traversée ?
