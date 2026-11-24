# Mini serre paramétrique - script Fusion 360 (Utilities > Scripts and Add-Ins > + > ce fichier)
# Tout est piloté par les paramètres utilisateur (Modify > Change Parameters).
# Crée 2 corps : "Base" (bac + passages capteurs/servo) et "Toit" (couvercle + fente de ventilation).
import adsk.core, adsk.fusion, traceback

# (nom, expression, unité, commentaire)
PARAMS = [
    ('L', '100 mm', 'mm', 'Longueur (X)'),
    ('W', '70 mm', 'mm', 'Largeur (Y)'),
    ('H', '60 mm', 'mm', 'Hauteur du bac'),
    ('wall', '1.6 mm', 'mm', 'Paroi (4 x ligne 0.4)'),
    ('floor', '1.2 mm', 'mm', 'Fond'),
    ('lid_h', '6 mm', 'mm', 'Hauteur du toit (mince = impression rapide)'),
    ('lid_clear', '0.25 mm', 'mm', 'Jeu emboîtement toit'),
    ('lip_h', '5 mm', 'mm', 'Hauteur du rebord d emboîtement'),
    ('vent_w', '40 mm', 'mm', 'Largeur fente ventilation'),
    ('vent_d', '14 mm', 'mm', 'Profondeur fente ventilation'),
    ('servo_w', '12.6 mm', 'mm', 'SG90 corps largeur (+jeu)'),
    ('servo_l', '23 mm', 'mm', 'SG90 corps longueur (+jeu)'),
    ('servo_z', '40 mm', 'mm', 'Hauteur centre fenêtre servo'),
    ('dht_d', '15 mm', 'mm', 'Trou capteur DHT22/DHT11'),
    ('dht_z', '30 mm', 'mm', 'Hauteur trou DHT'),
    ('usb_w', '10 mm', 'mm', 'Fenêtre câble USB / Nano'),
    ('usb_h', '8 mm', 'mm', 'Hauteur fenêtre USB'),
    ('flap_t', '1.6 mm', 'mm', 'Epaisseur volet'),
    ('flap_over', '6 mm', 'mm', 'Recouvrement volet autour de la fente'),
    ('horn_w', '4 mm', 'mm', 'Largeur fente palonnier SG90 dans le volet'),
    ('soil_w', '22 mm', 'mm', 'Fente sonde humidité sol'),
    ('soil_t', '3 mm', 'mm', 'Epaisseur fente sonde sol'),
]
FLIP = 1  # mettre -1 si les découpes de paroi partent du mauvais côté


def val(expr):
    return adsk.core.ValueInput.createByString(expr)


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType

        up = design.userParameters
        for n, e, u, c in PARAMS:
            if not up.itemByName(n):
                up.add(n, val(e), u, c)

        xy, xz, yz = root.xYConstructionPlane, root.xZConstructionPlane, root.yZConstructionPlane

        def offset_plane(base, expr):
            pi = root.constructionPlanes.createInput()
            pi.setByOffset(base, val(expr))
            return root.constructionPlanes.add(pi)

        def rect(sk, w_expr, l_expr):
            r = sk.sketchLines.addCenterPointRectangle(
                adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(2, 1.5, 0))
            ls = [r.item(i) for i in range(4)] if hasattr(r, 'item') else list(r)
            d = sk.sketchDimensions
            d.addDistanceDimension(ls[0].startSketchPoint, ls[0].endSketchPoint,
                adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
                adsk.core.Point3D.create(0, -3, 0)).parameter.expression = w_expr
            d.addDistanceDimension(ls[1].startSketchPoint, ls[1].endSketchPoint,
                adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
                adsk.core.Point3D.create(4, 0, 0)).parameter.expression = l_expr

        def extrude(profile, expr, op, body_name=None):
            ei = root.features.extrudeFeatures.createInput(profile, op)
            ei.setDistanceExtent(False, val(expr))
            f = root.features.extrudeFeatures.add(ei)
            if body_name:
                f.bodies.item(0).name = body_name
            return f

        def smallest_profile(sk):
            return min(sk.profiles, key=lambda p: p.areaProperties().area)

        # ---- BASE : bloc plein puis cavité ----
        sk = root.sketches.add(xy)
        sk.name = 'Base_ext'
        rect(sk, 'L', 'W')
        extrude(sk.profiles.item(0), 'H', adsk.fusion.FeatureOperations.NewBodyFeatureOperation, 'Base')

        top = offset_plane(xy, 'H')
        sk = root.sketches.add(top)
        sk.name = 'Base_cavite'
        rect(sk, 'L - 2*wall', 'W - 2*wall')
        extrude(sk.profiles.item(0), '-(H - floor)', adsk.fusion.FeatureOperations.CutFeatureOperation)

        # ---- Découpes parois (plan XZ décalé sur la paroi avant) ----
        def wall_cut(plane, sk_name, draw, depth='wall*3'):
            s = root.sketches.add(plane)
            s.name = sk_name
            draw(s)
            prof = smallest_profile(s)
            extrude(prof, '%d*(%s)' % (FLIP, depth), adsk.fusion.FeatureOperations.CutFeatureOperation)

        front = offset_plane(xz, '-W/2')  # paroi avant (y = -W/2)
        pts = adsk.core.Point3D.create

        def draw_dht(s):
            c = s.sketchCurves.sketchCircles.addByCenterRadius(pts(-2, 3, 0), 0.75)
            dm = s.sketchDimensions.addDiameterDimension(c, pts(-2, 6, 0))
            dm.parameter.expression = 'dht_d'
            # position : x = -L/4, z = dht_z
            s.sketchDimensions.addDistanceDimension(s.originPoint, c.centerSketchPoint,
                adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
                pts(-1, -1, 0)).parameter.expression = '-L/4'
            s.sketchDimensions.addDistanceDimension(s.originPoint, c.centerSketchPoint,
                adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
                pts(-5, 1, 0)).parameter.expression = 'dht_z'

        wall_cut(front, 'Trou_DHT', draw_dht)

        # ---- Fenêtre servo (paroi arrière, SG90 vissé/collé derrière, bras vers le toit) ----
        back = offset_plane(xz, 'W/2')

        def draw_servo(s):
            r = s.sketchLines.addCenterPointRectangle(pts(0, 3, 0), pts(1, 3.5, 0))
            ls = [r.item(i) for i in range(4)]
            d = s.sketchDimensions
            d.addDistanceDimension(ls[0].startSketchPoint, ls[0].endSketchPoint,
                adsk.fusion.DimensionOrientations.HorizontalDimensionOrientation,
                pts(0, 1.5, 0)).parameter.expression = 'servo_l'
            d.addDistanceDimension(ls[1].startSketchPoint, ls[1].endSketchPoint,
                adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
                pts(3, 3, 0)).parameter.expression = 'servo_w'
            d.addDistanceDimension(s.originPoint, r.item(0).startSketchPoint,
                adsk.fusion.DimensionOrientations.VerticalDimensionOrientation,
                pts(-4, 1, 0)).parameter.expression = 'servo_z - servo_w/2'

        wall_cut(back, 'Fenetre_servo', draw_servo)

        # ---- TOIT : plaque + rebord d'emboîtement + fente de ventilation ----
        sk = root.sketches.add(top)
        sk.name = 'Toit_plaque'
        rect(sk, 'L', 'W')
        f = extrude(sk.profiles.item(0), 'lid_h', adsk.fusion.FeatureOperations.NewBodyFeatureOperation, 'Toit')

        sk = root.sketches.add(top)
        sk.name = 'Toit_rebord'
        rect(sk, 'L - 2*wall - 2*lid_clear', 'W - 2*wall - 2*lid_clear')
        extrude(sk.profiles.item(0), '-lip_h', adsk.fusion.FeatureOperations.JoinFeatureOperation)

        roof_top = offset_plane(xy, 'H + lid_h')
        sk = root.sketches.add(roof_top)
        sk.name = 'Toit_vent'
        rect(sk, 'vent_w', 'vent_d')
        extrude(smallest_profile(sk), '-(lid_h)', adsk.fusion.FeatureOperations.CutFeatureOperation)

        # ---- VOLET : plaque coulissante sur la fente, tirée par le palonnier SG90 ----
        roof_top2 = offset_plane(xy, 'H + lid_h')
        sk = root.sketches.add(roof_top2)
        sk.name = 'Volet'
        rect(sk, 'vent_w + 2*flap_over', 'vent_d + 2*flap_over')
        extrude(sk.profiles.item(0), 'flap_t', adsk.fusion.FeatureOperations.NewBodyFeatureOperation, 'Volet')
        sk = root.sketches.add(offset_plane(xy, 'H + lid_h + flap_t'))
        sk.name = 'Volet_palonnier'
        rect(sk, 'horn_w', 'vent_d')
        extrude(smallest_profile(sk), '-flap_t', adsk.fusion.FeatureOperations.CutFeatureOperation)

        ui.messageBox('Serre générée. Ajuste les paramètres (Modify > Change Parameters).\n'
                      'Si une découpe de paroi est du mauvais côté : FLIP = -1 en haut du script.\n'
                      'Exporte "Base" et "Toit" en 3MF (Toit retourné à plat, face du dessus sur le plateau).')
    except Exception:
        if ui:
            ui.messageBox('Erreur:\n{}'.format(traceback.format_exc()))
