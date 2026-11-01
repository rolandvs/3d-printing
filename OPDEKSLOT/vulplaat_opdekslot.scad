// Vulplaat voor opdekslot - parametrisch (OpenSCAD)
//
// ORIENTATIE
//   De BOVENKANT van dit model (Z = dikte) gaat TEGEN DE ACHTERKANT
//   VAN HET SLOT. De onderkant gaat tegen de deur.
//   Bovenaanzicht in OpenSCAD = de plaat zoals het slot hem "ziet"
//   (spiegelbeeld van een foto van de slot-achterkant).
//   X = breedte 95 mm (over het midden; zijkanten licht bol), Y = hoogte 93 mm.
//   Y = 0 is de kant van de voorplaat/lip (deurrand).
//
// MATEN
//   Gemeten: buitenmaten 93 x 95, boorgaten 72 x 72 (vierkant).
//   Al het andere: GESCHAT uit een foto, geschaald op het 72 mm-vierkant
//   (+/- 1 mm). Nameten, of eerst
//   een proefprint van 0,6 mm dik maken en die op het slot leggen.
//   (Bij een proefprint: zet de dikte terug op 2 voor de echte print.)
//
// Pas de waarden aan, of gebruik Window > Customizer.

/* [Plaat] */
breedte = 95;
hoogte  = 93;     // richting voorplaat
dikte   = 2;      // afstand slot tot deur
r_hoek  = 5;      // hoekradius (geschat)
bol     = 1.5;    // bolling linker- en rechterzijde per kant (geschat).
                  // breedte = maat over het midden (breedste punt).
                  // 0 = rechte zijkanten.

/* [Middengat: omtrek verhoogde schijf (doorgaand)] */
schijf_b = 42;    // in X  (blauwe omtrek uit foto)
schijf_h = 37;    // in Y
schijf_x = 44;
schijf_y = 45.2;

/* [Uitsparing schootkastje (doorgaand, open naar rand)] */
kast_aan = true;
kast_x1  = 15.5;  // 1 mm wand naast boorgat
kast_x2  = 36;
kast_h   = 21;    // vanaf rand Y = 0

/* [Gat voor schroefkopje] */
schroef_aan = true;
schroef_d   = 7;
schroef_x   = 69.7;
schroef_y   = 44.4;

/* [Boorgaten bevestiging (4x, vierkant 72 x 72)] */
boor_d   = 6;     // gaten in slot ~6,5 mm (geschat)
boor_afst = 72;   // gemeten, horizontaal en verticaal
boor_cx  = 47.5;  // midden van het vierkant in X (= midden plaat)
boor_cy  = 49.75; // midden van het vierkant in Y (GESCHAT uit foto)

/* [Kwaliteit] */
$fn = 96;

// ---------------------------------------------------------------

module omtrek() {
    // zijkanten X = 0 en X = breedte zijn cirkelbogen met pijlhoogte 'bol'
    Rb = (hoogte * hoogte / 4 + bol * bol) / (2 * bol);
    offset(r = r_hoek) offset(delta = -r_hoek)
        if (bol > 0)
            intersection() {
                square([breedte, hoogte]);
                translate([Rb, hoogte / 2]) circle(r = Rb, $fn = 2880);
                translate([breedte - Rb, hoogte / 2]) circle(r = Rb, $fn = 2880);
            }
        else
            square([breedte, hoogte]);
}

module gat(x, y, d) {
    translate([x, y, -1]) cylinder(d = d, h = dikte + 2);
}

difference() {
    linear_extrude(height = dikte) omtrek();

    for (x = [boor_cx - boor_afst/2, boor_cx + boor_afst/2],
         y = [boor_cy - boor_afst/2, boor_cy + boor_afst/2])
        gat(x, y, boor_d);

    if (schroef_aan) gat(schroef_x, schroef_y, schroef_d);

    if (kast_aan)
        translate([kast_x1, -1, -1])
            cube([kast_x2 - kast_x1, kast_h + 1, dikte + 2]);

    translate([schijf_x, schijf_y, -1])
        scale([schijf_b / 2, schijf_h / 2, 1])
            cylinder(r = 1, h = dikte + 2);
}
