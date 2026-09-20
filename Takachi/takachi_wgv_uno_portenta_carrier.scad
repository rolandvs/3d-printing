
/*
Takachi WGV Carrier Plate Generator
Arduino UNO + Portenta Support
--------------------------------

Supported presets:
- WGP15-16
- WGP15-21
- WGP17-25
- WGP23-25

Supported board types:
- Arduino UNO
- Arduino Portenta H7 / X8

Features:
- Parametric enclosure sizes
- Parametric board selection
- Board mounting holes
- Optional corner holes
- Optional preview geometry

Units: mm
*/

// ======================================================
// USER SETTINGS
// ======================================================

// ENCLOSURE PRESET
// 0 = WGP15-16
// 1 = WGP15-21
// 2 = WGP17-25
// 3 = WGP23-25

preset_index = 0;

// BOARD TYPE
// 0 = Arduino UNO
// 1 = Arduino Portenta

board_type = 0;

// Plate thickness
plate_thickness = 2.0;

// Hole diameters
board_hole_diameter = 3.2;
corner_hole_diameter = 4.0;

// Corner mounting hole settings
show_corner_holes = true;
corner_offset = 8;

// Show board visualization
show_board_preview = true;

// ======================================================
// PRESET DATA
// ======================================================

plate_sizes = [
    [105,117],   // WGP15-16
    [105,167],   // WGP15-21
    [125,207],   // WGP17-25
    [185,207]    // WGP23-25
];

preset_names = [
    "WGP15-16",
    "WGP15-21",
    "WGP17-25",
    "WGP23-25"
];

// ======================================================
// BOARD DEFINITIONS
// ======================================================

// ---------- Arduino UNO ----------

uno_width  = 53.4;
uno_height = 68.6;

uno_holes = [
    [2.5, 14],
    [17.8, 66],
    [45.8, 66],
    [50.8, 14]
];

// ---------- Arduino Portenta ----------

// Approximate dimensions for Portenta H7/X8
portenta_width  = 66.0;
portenta_height = 25.0;

// Simplified 4-hole pattern
portenta_holes = [
    [3, 3],
    [63, 3],
    [3, 22],
    [63, 22]
];

// ======================================================
// BOARD SELECTOR
// ======================================================

board_width =
    (board_type == 0) ? uno_width :
    portenta_width;

board_height =
    (board_type == 0) ? uno_height :
    portenta_height;

board_holes =
    (board_type == 0) ? uno_holes :
    portenta_holes;

board_name =
    (board_type == 0) ? "Arduino UNO" :
    "Arduino Portenta";

// ======================================================
// MAIN GEOMETRY
// ======================================================

plate_x = plate_sizes[preset_index][0];
plate_y = plate_sizes[preset_index][1];

echo("Preset:", preset_names[preset_index]);
echo("Board:", board_name);

difference() {

    // Main carrier plate
    cube([plate_x, plate_y, plate_thickness]);

    // Board mounting holes
    translate([
        (plate_x - board_width)/2,
        (plate_y - board_height)/2,
        -1
    ])
    for (p = board_holes)
    {
        translate([p[0], p[1], 0])
            cylinder(
                h = plate_thickness + 2,
                d = board_hole_diameter,
                $fn = 40
            );
    }

    // Corner enclosure mounting holes
    if (show_corner_holes)
    {
        corner_positions = [
            [corner_offset, corner_offset],
            [plate_x - corner_offset, corner_offset],
            [corner_offset, plate_y - corner_offset],
            [plate_x - corner_offset, plate_y - corner_offset]
        ];

        for (c = corner_positions)
        {
            translate([c[0], c[1], -1])
                cylinder(
                    h = plate_thickness + 2,
                    d = corner_hole_diameter,
                    $fn = 40
                );
        }
    }
}

// ======================================================
// OPTIONAL BOARD PREVIEW
// ======================================================

if (show_board_preview)
{
    color([0,0.5,0])
    translate([
        (plate_x - board_width)/2,
        (plate_y - board_height)/2,
        plate_thickness
    ])
    cube([board_width, board_height, 1.6]);
}
