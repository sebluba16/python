"""Dimensionnement d'une navette electrique de campus (2 places avant + 1 blesse arriere).
Hypotheses a ajuster en haut du fichier. Unites SI sauf mention. Resultats = ordres de grandeur d'avant-projet."""
import math

G, RHO = 9.81, 1.2
# --- hypotheses ---
M_VIDE   = 340      # kg, chassis alu/acier leger + moteur + batterie (cible)
M_CHARGE = 2*80 + 80 + 10   # 2 occupants avant + blesse assis jambe platree + bequilles
M = M_VIDE + M_CHARGE
CRR, CDA = 0.012, 1.0       # pneus 145/70-12 sur bitume ; CdA m2 (cabine ouverte/legere)
V_MAX = 20/3.6              # m/s : limite campus
ETA   = 0.75                # chaine batterie->roue (controleur+moteur+transmission)
ETA_REGEN = 0.5             # part de l'energie cinetique/descente recuperable
D_TRAJET = 700.0            # m
N_TRAJETS = 10              # cas pessimiste : 10 ALLERS-RETOURS = 14 km/jour (cas optimiste : 10 trajets simples)
PENTE = 0.03                # pente moyenne (montee a l'aller, descente au retour)
P_AUX = 100.0               # W : eclairage, gyrophare, controle (pendant 12 min/h * 8 h)
H_SERVICE = 8.0

def trajet(pente):
    """Wh a la batterie pour 1 trajet de 700 m avec arret-depart (profil trapezoide a V_MAX)"""
    e_roul = M*G*CRR*D_TRAJET
    e_aero = 0.5*RHO*CDA*V_MAX**2*D_TRAJET
    e_cin  = 0.5*M*V_MAX**2
    e_pente = M*G*pente*D_TRAJET            # >0 montee, <0 descente
    if pente >= 0:
        wheel = e_roul + e_aero + e_cin + e_pente
        bat = wheel/ETA - e_cin*ETA_REGEN*ETA          # freinage regeneratif final
    else:
        wheel = e_roul + e_aero + e_cin
        gain = min(-e_pente, -e_pente)*ETA_REGEN*ETA
        bat = max(wheel/ETA - gain - e_cin*ETA_REGEN*ETA, 0)
    return bat/3600.0

def main():
    ar = trajet(PENTE) + trajet(-PENTE)
    aller = trajet(PENTE); retour = trajet(-PENTE)
    e_jour = N_TRAJETS*ar + P_AUX*H_SERVICE*0.2       # aux ~20 % du temps
    print(f"Masse en charge {M} kg ({M_VIDE} a vide)")
    print(f"Aller ({PENTE*100:.0f}% montee) {aller:.1f} Wh ; retour {retour:.1f} Wh ; A/R {ar:.1f} Wh = {ar/1.4:.0f} Wh/km")
    print(f"Energie/jour ({N_TRAJETS} A/R = {N_TRAJETS*1.4:.0f} km) : {e_jour/1000:.2f} kWh (+aux)")
    # puissances
    a = 0.7
    F_acc = M*a + M*G*CRR + 0.5*RHO*CDA*V_MAX**2
    p_acc = F_acc*V_MAX
    for p_, v_, nom in ((0.10, 15/3.6, "10 % a 15 km/h"), (0.15, 8/3.6, "15 % a 8 km/h (rampe garage)")):
        F = M*G*(p_+CRR) + 0.5*RHO*CDA*v_**2
        print(f"Puissance rampe {nom}: {F*v_/ETA/1000:.2f} kW elec, force roue {F:.0f} N")
    print(f"Acceleration {a} m/s2 jusqu'a 20 km/h : {p_acc/ETA/1000:.2f} kW elec ; force roue {F_acc:.0f} N")
    # batterie
    for u, ah in ((48, 30), (48, 50), (51.2, 50)):
        kwh = u*ah/1000
        utile = kwh*0.8
        print(f"Batterie {u:.0f} V {ah} Ah = {kwh:.2f} kWh, utile 80 % = {utile:.2f} kWh -> {utile*1000/(ar/1.4):.0f} km, {utile*1000/e_jour:.1f} jours")
    # reserve d'urgence
    print("Reserve : SOC mini conseillee 40 % pour garantir une evacuation meme si la charge de nuit a rate")
    i_crete = 3500/48
    print(f"Courant crete a 3,5 kW / 48 V : {i_crete:.0f} A -> BMS 80 A / cables 16 mm2")
    # recharge opportuniste
    print(f"Recharge nuit : 0,8 kWh/jour avec chargeur 48 V 10 A (~0,5 kW) = {e_jour/500:.1f} h")
    # brancard
    print("Freinage : decel 4 m/s2 depuis 20 km/h -> distance", round(V_MAX**2/(2*4),1), "m ; blesse assis, jambe calee (decel max 0,4 g)")

main()
