# Fusion 360 script : Fichier > Scripts et complements > Scripts > "+" > choisir ce dossier.
# Genere 4 pieces a plat (sans support), unites cm dans l'API (mm / 10).
import adsk.core, adsk.fusion, traceback

# ---- PARAMETRES (mm) ----
L, W, H = 100.0, 70.0, 28.0     # base : longueur, largeur, hauteur
WALL = 1.6                       # paroi = 4 lignes de 0.4
FLOOR = 1.2                      # fond
JEU = 0.3                        # jeu d'assemblage
TOIT_H = 6.0                     # hauteur du cadre de toit
FENETRE = 8.0                    # marge du cadre de toit


def mm(v):
    return v / 10.0


def new_comp(root, name):
    occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    occ.component.name = name
    return occ.component


def rect_extrude(comp, x, y, w, d, z0, h, op):
    """Rectangle (x,y,w,d) a la hauteur z0, extrude de h."""
    planes = comp.constructionPlanes
    pin = planes.createInput()
    pin.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(mm(z0)))
    plane = planes.add(pin)
    sk = comp.sketches.add(plane)
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        adsk.core.Point3D.create(mm(x), mm(y), 0),
        adsk.core.Point3D.create(mm(x + w), mm(y + d), 0))
    prof = sk.profiles.item(0)
    ext = comp.features.extrudeFeatures
    inp = ext.createInput(prof, op)
    inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(h)))
    return ext.add(inp)


def circle_cut(comp, cx, cy, z0, dia, h):
    planes = comp.constructionPlanes
    pin = planes.createInput()
    pin.setByOffset(comp.xYConstructionPlane, adsk.core.ValueInput.createByReal(mm(z0)))
    plane = planes.add(pin)
    sk = comp.sketches.add(plane)
    sk.sketchCurves.sketchCircles.addByCenterRadius(
        adsk.core.Point3D.create(mm(cx), mm(cy), 0), mm(dia / 2))
    ext = comp.features.extrudeFeatures
    inp = ext.createInput(sk.profiles.item(0), adsk.fusion.FeatureOperations.CutFeatureOperation)
    inp.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm(h)))
    return ext.add(inp)


def box_hollow(comp, x, y, w, d, h, wall, floor, open_top=True):
    NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    CUT = adsk.fusion.FeatureOperations.CutFeatureOperation
    rect_extrude(comp, x, y, w, d, 0, h, NEW)
    rect_extrude(comp, x + wall, y + wall, w - 2 * wall, d - 2 * wall, floor, h - floor + 0.1, CUT)


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent
        NEW = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        CUT = adsk.fusion.FeatureOperations.CutFeatureOperation

        # 1. BASE-BAC (origine) + trou drainage + encoche cable
        base = new_comp(root, "Base_bac")
        box_hollow(base, 0, 0, L, W, H, WALL, FLOOR)
        circle_cut(base, L / 2, W / 2, -1, 3.0, FLOOR + 2)

        # 2. TOIT : cadre ouvert, glisse sur la base (jeu), film PET colle dessus
        toit = new_comp(root, "Toit_cadre")
        ox = L + 15
        tw, td = L + 2 * (WALL + JEU), W + 2 * (WALL + JEU)
        rect_extrude(toit, ox, 0, tw, td, 0, TOIT_H, NEW)
        rect_extrude(toit, ox + WALL, WALL, tw - 2 * WALL, td - 2 * WALL, -1, TOIT_H + 2, CUT)
        # cadre haut (rebord pour coller le film) : on laisse 1.2 mm de bande
        rect_extrude(toit, ox, 0, tw, td, TOIT_H, 1.2, NEW)
        rect_extrude(toit, ox + FENETRE, FENETRE, tw - 2 * FENETRE, td - 2 * FENETRE,
                     TOIT_H - 1, 3.0, CUT)

        # 3. BOITIER ELECTRONIQUE Nano : 45x25x18, trou USB + trou cable
        box = new_comp(root, "Boitier_Nano")
        by = W + 15
        box_hollow(box, 0, by, 45 + 2 * WALL, 25 + 2 * WALL, 18, WALL, FLOOR)
        circle_cut(box, 8, by + 12.5 + WALL, -1, 3.2, FLOOR + 2)       # passage fils
        # USB : fente sur le bord gauche, hauteur des cotes
        rect_extrude(box, -1, by + 12.5 - 4, WALL + 2, 8 + 2 * WALL, FLOOR + 3, 8, CUT)

        # 4. SUPPORT CAPTEURS : barre 90x10x2.4 + 2 trous (DHT22, sol)
        sup = new_comp(root, "Support_capteurs")
        sx, sy = 60, W + 15
        rect_extrude(sup, sx, sy, 90, 10, 0, 2.4, NEW)
        circle_cut(sup, sx + 20, sy + 5, -1, 3.0, 4)   # fil DHT22
        circle_cut(sup, sx + 60, sy + 5, -1, 6.0, 4)   # capteur sol capacitif

        ui.messageBox("Mini serre generee : 4 pieces a plat.\n"
                      "Clic droit sur chaque composant > Enregistrer comme maillage (STL).")
    except Exception:
        if ui:
            ui.messageBox("Erreur:\n{}".format(traceback.format_exc()))
