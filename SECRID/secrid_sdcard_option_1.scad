// ============================================================
//  SECRID-style microSD card holder
//  ISO/IEC 7810 ID-1: 85.60 x 54.00 mm
//  MicroSD (SanDisk Ultra): 15.0 x 11.0 x 1.0 mm
// ============================================================
//
//  Retention: lateral arc spring — a bowed strip anchored at
//  both ends along one long wall of the slot. At rest it bows
//  inward by `arc_bow` mm, pressing against the SD card's long
//  edge. The opposite slot wall is the rigid backstop.
//
//  Insertion: slide card in from the open short-edge side.
//  Ejection: push card inward (SIM-tray style) or flex arc open.
//
// ============================================================

/* ----- CARD BODY ----- */
card_w   = 85.60;
card_h   = 54.00;
card_t   =  1.00;   // thickness must match that of the SD CARD
corner_r =  3.18;   // ISO 7810

/* ----- MICROSD SLOT (through-hole) ----- */
// Real microSD: 15.0 x 11.0 mm footprint
sd_cw   = 15.00;   // SD card actual width  (long side, along X)
sd_ch   = 11.00;   // SD card actual height (short side, along Y)
sd_clr  =  0.15;   // clearance per rigid wall

// Arc spring parameters
// The arc lives on the LEFT side of the slot (low-X wall).
// SD card is pressed against the RIGHT wall.
arc_bow =  0.60;   // how far arc mid-span bows into slot (pre-stress)
arc_t   =  0.50;   // arc strip thickness — thin = more flex
arc_steps = 30;    // segments for smooth sine curve

// Slot total X = arc strip + arc bow pocket + sd card + clearance (right side only)
slot_w  = arc_t + arc_bow + sd_cw + sd_clr;   // ~16.25 mm
slot_h  = sd_ch + 2*sd_clr;                   // ~11.30 mm

/* ----- SLOT POSITIONS ----- */
slot_y  = (card_h - slot_h) / 2;   // centred vertically on card
slot1_x =  13.00;
slot2_x =  slot1_x + slot_w + 13.00;

/* ----- EMBOSSED TEXT ----- */
// Text is centred horizontally and vertically on the card,
// positioned in the gap between the two SD slots.

txt1        = "SECRID Pocketware";
txt2        = "SDCard Holder";
txt_font    = "Liberation Sans:style=Bold";
txt_size    =  4.20;    // approximate cap height in mm
txt_spacing =  1.22;    // letter spacing multiplier (wide = SECRID feel)
txt_depth   =  0.1;     // engrave depth into top face
txt_gap     =  2.20;    // vertical gap between the two text baselines

// Vertical centre of the card
txt_centre_y = card_h / 2 + 15;
// Baseline of line 1 (upper): centre + half gap
txt1_y = txt_centre_y + txt_gap / 2;
// Baseline of line 2 (lower): centre - half gap - cap height
txt2_y = txt_centre_y - txt_gap / 2 - txt_size;

$fn = 64;

/* ============================================================
   rounded_rect_2d
   ============================================================ */
module rounded_rect_2d(w, h, r) {
    offset(r = r) square([w - 2*r, h - 2*r], center = false);
}

/* ============================================================
   lateral_arc_spring
   A bowed strip along the left wall of one slot.
   Local origin = slot bottom-left corner (slot1_x, slot_y, 0).

   X layout inside one slot:
     [0 .. arc_t+arc_bow]           arc strip (relaxed bow)
     [arc_t+arc_bow .. slot_w]      SD card + right clearance
     slot_w                         right wall

   The arc is anchored at both Y ends (top+bottom of slot).
   Its mid-span bows arc_bow=0.60 mm rightward into the slot.
   The SD card is squeezed between arc and right wall.
   Slide card out toward the open short edge to eject.
   ============================================================ */
module lateral_arc_spring() {
    h = slot_h;

    // Bottom anchor
    cube([arc_t, 1.20, card_t]);
    // Top anchor
    translate([0, h - 1.20, 0])
        cube([arc_t, 1.20, card_t]);

    // Bowed beam — half-sine profile in X as a function of Y
    for (i = [0 : arc_steps - 1]) {
        t0 = i       / arc_steps;
        t1 = (i + 1) / arc_steps;
        y0 = t0 * h;
        y1 = t1 * h;
        x0 = arc_bow * sin(180 * t0);
        x1 = arc_bow * sin(180 * t1);

        hull() {
            translate([x0, y0, 0]) cube([arc_t, 0.01, card_t]);
            translate([x1, y1, 0]) cube([arc_t, 0.01, card_t]);
        }
    }
}


/* ============================================================
   engraved_text(str)
   Cuts text into the top face of the card.
   halign="center" centres on card_w/2 in X.
   ============================================================ */
module engraved_text(str, y_pos) {
    translate([card_w / 2, y_pos, card_t - txt_depth])
        linear_extrude(height = txt_depth + 0.01)
            text(
                str,
                size    = txt_size,
                font    = txt_font,
                spacing = txt_spacing,
                halign  = "center",
                valign  = "baseline"
            );
}



/* ============================================================
   MAIN BODY
   ============================================================ */
difference() {
    // Card body — ISO 7810 footprint
    linear_extrude(height = card_t)
        rounded_rect_2d(card_w, card_h, corner_r);

    // Slot 1 — full through-cutout
    translate([slot1_x, slot_y, -0.1])
        cube([slot_w, slot_h, card_t + 0.2]);

    // Slot 2 — full through-cutout
    translate([slot2_x, slot_y, -0.1])
        cube([slot_w, slot_h, card_t + 0.2]);
    
        // Engraved text — cut into top face
    engraved_text(txt1, txt1_y);
    engraved_text(txt2, txt2_y);

    
    
}

// Arc springs — positive geometry placed at left edge of each slot
translate([slot1_x, slot_y, 0]) lateral_arc_spring();
translate([slot2_x, slot_y, 0]) lateral_arc_spring();
