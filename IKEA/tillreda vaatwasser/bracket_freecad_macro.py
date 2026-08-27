# -*- coding: utf-8 -*-
"""
FreeCAD-macro: bouwt het beugeltje op als ECHTE solid (geen mesh).
Gebruik: FreeCAD -> Macro -> Macro's... -> Maken -> deze code plakken -> Uitvoeren.
Daarna Bestand -> Opslaan als -> .FCStd

Alle maten in mm, hetzelfde parameterblok als het Python-model.
"""
import FreeCAD as App
import Part

# ----------------------------- PARAMETERS -----------------------------------
# Oorsprong = hart centraal gat, +y = ronde kant, x = langs de rechte onderrand.
EAR_L_XY    = (-13.50, -0.46)   # hart schroefgat links  (de oren staan versprongen!)
EAR_R_XY    = ( 13.15, -4.77)   # hart schroefgat rechts (h.o.h. 27,0)
R_EAR       = 5.80              # oor D11,6
D_SCREW     = 4.0
D_CS_EAR    = 6.5
D_SCREW_MID = 4.0
D_CS_MID    = 6.0

PLATE_R     = 11.15             # grote lob, concentrisch met het middengat
PLATE_FLAT  = 7.90              # rechte onderrand onder het middengat

HEAD_CY     = 2.50              # hart ronde kant van kop/hals
HEAD_W      = 14.0
HEAD_R      = 7.0
HEAD_FLAT   = 6.40              # HEAD_CY -> rechte kant
R_NECK      = 4.0               # hals D8, vlak met de kop

T_PLATE     = 3.0
H_NECK      = 3.0
H_HEAD      = 3.0

MIRROR      = False             # True = het gespiegelde exemplaar (om de kop-as)
# -----------------------------------------------------------------------------

V = App.Vector
Z1, Z2, Z3 = T_PLATE, T_PLATE + H_NECK, T_PLATE + H_NECK + H_HEAD


def d_solid(radius, flat, half_w, z0, h):
    """D-vorm rond (0, HEAD_CY): halve cilinder + blok tot 'flat' eronder"""
    cyl = Part.makeCylinder(radius, h, V(0, HEAD_CY, z0))
    box = Part.makeBox(2 * half_w, flat, h, V(-half_w, HEAD_CY - flat, z0))
    return cyl.fuse(box)


def screw_hole(x, y, d, d_cs, z_top, z_bottom=-1.0):
    depth = (d_cs - d) / 2.0
    hole = Part.makeCylinder(d / 2.0, z_top - z_bottom + 1.0, V(x, y, z_bottom))
    cone = Part.makeCone(d / 2.0, d_cs / 2.0, depth, V(x, y, z_top - depth))
    top = Part.makeCylinder(d_cs / 2.0, 1.0, V(x, y, z_top))
    return hole.fuse(cone).fuse(top)


# --- plaat: grote lob (recht afgesneden) + twee versprongen oren -------------
lobe = Part.makeCylinder(PLATE_R, T_PLATE, V(0, 0, 0))
keep = Part.makeBox(4 * PLATE_R, 4 * PLATE_R, T_PLATE,
                    V(-2 * PLATE_R, -PLATE_FLAT, 0))
plate = lobe.common(keep)
for (ex, ey) in (EAR_L_XY, EAR_R_XY):
    plate = plate.fuse(Part.makeCylinder(R_EAR, T_PLATE, V(ex, ey, 0)))

neck = d_solid(R_NECK, HEAD_FLAT, R_NECK, Z1, H_NECK)
head = d_solid(HEAD_R, HEAD_FLAT, HEAD_W / 2.0, Z2, H_HEAD)

body = plate.fuse(neck).fuse(head).removeSplitter()

for c in (screw_hole(EAR_L_XY[0], EAR_L_XY[1], D_SCREW, D_CS_EAR, T_PLATE),
          screw_hole(EAR_R_XY[0], EAR_R_XY[1], D_SCREW, D_CS_EAR, T_PLATE),
          screw_hole(0, 0, D_SCREW_MID, D_CS_MID, Z3)):
    body = body.cut(c)

body = body.removeSplitter()
if MIRROR:
    body = body.mirror(V(0, 0, 0), V(1, 0, 0))

doc = App.ActiveDocument or App.newDocument("Beugel")
obj = doc.addObject("Part::Feature", "Beugel_gespiegeld" if MIRROR else "Beugel")
obj.Shape = body
doc.recompute()

try:
    import FreeCADGui
    FreeCADGui.SendMsgToActiveView("ViewFit")
except Exception:
    pass

print("Volume: %.1f mm3   bbox: %s" % (body.Volume, body.BoundBox))
