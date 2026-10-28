// ============================================================
//  SECRID-style microSD card holder
//  ISO/IEC 7810 ID-1: 85.60 x 54.00 mm
//  MicroSD (SanDisk Ultra): 15.0 x 11.0 x 1.0 mm
// ============================================================

/* ----- CARD BODY ----- */
card_w   = 85.60;
card_h   = 54.00;
card_t   =  1.00;
corner_r =  3.18;   // ISO 7810

/* ----- MICROSD SLOT (through-hole) ----- */
sd_cw   = 15.00;
sd_ch   = 11.00;
sd_clr  =  0.15;

arc_bow  =  0.60;
arc_t    =  0.50;
arc_steps = 30;

slot_w  = sd_cw + 2*sd_clr;
slot_h  = arc_t + arc_bow + sd_ch + sd_clr;

/* ----- SLOT POSITIONS ----- */
slot_y  = (card_h - slot_h) / 2;
slot1_x =  13.00;
slot2_x =  slot1_x + slot_w + 14.00;

/* ----- EMBOSSED TEXT ----- */

// Text is centred horizontally on the card,
// positioned above the gap of the two SD slots.

txt1        = "SECRID Pocketware";
txt2        = "SDCard Holder";
txt_font    = "Liberation Sans:style=Bold";
txt_size    =  4.20;    // approximate cap height in mm
txt_spacing =  1.22;    // letter spacing multiplier (wide = SECRID feel)
txt_depth   =  0.10;    // engrave depth into top face
txt_gap     =  2.20;    // vertical gap between the two text baselines

// Vertical centre of the card
txt_centre_y = card_h / 2 + 15;
// Baseline of line 1 (upper): centre + half gap
txt1_y = txt_centre_y + txt_gap / 2;
// Baseline of line 2 (lower): centre - half gap - cap height
txt2_y = txt_centre_y - txt_gap / 2 - txt_size;

$fn = 64;

/* rounded_rect_2d */
module rounded_rect_2d(w, h, r) {
    offset(r = r) square([w - 2*r, h - 2*r], center = false);
}

/* arc_spring_long_wall */
module arc_spring_long_wall() {
    w = slot_w;

    cube([1.20, arc_t, card_t]);
    translate([w - 1.20, 0, 0])
        cube([1.20, arc_t, card_t]);

    for (i = [0 : arc_steps - 1]) {
        t0 = i       / arc_steps;
        t1 = (i + 1) / arc_steps;
        x0 = t0 * w;
        x1 = t1 * w;
        y0 = arc_bow * sin(180 * t0);
        y1 = arc_bow * sin(180 * t1);

        hull() {
            translate([x0, y0, 0]) cube([0.01, arc_t, card_t]);
            translate([x1, y1, 0]) cube([0.01, arc_t, card_t]);
        }
    }
}

/* engraved_text(str)
 * Cuts text into the top face of the card.
 * halign="center" centres on card_w/2 in X.
 */
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

/* MAIN BODY */
difference() {
    // Card body
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

// Arc springs
translate([slot1_x, slot_y, 0]) arc_spring_long_wall();
translate([slot2_x, slot_y, 0]) arc_spring_long_wall();

