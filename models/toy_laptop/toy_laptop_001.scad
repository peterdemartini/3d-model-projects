// ============================================================================
// toy_laptop_001.scad — Print-in-Place Toy Laptop
// Target printer : Bambu Lab H2D
// Print pose     : 90° interior hinge angle (lid perpendicular to base)
// Hinge          : Interleaved-knuckle print-in-place (7 knuckles, captive pin)
//                  Pin integrated with lid; rotates inside base knuckle bores.
// No supports required at this pose.
// ============================================================================

// ── Resolution ────────────────────────────────────────────────────────────────
$fn = 64;   // cylinder/sphere facets — ≥60 prevents degenerate faces

// ── Overall dimensions ────────────────────────────────────────────────────────
base_w  = 250;   // X — laptop width  (mm)
base_d  = 180;   // Y — base depth    (mm)
base_h  = 10;    // Z — base body thickness (mm)
lid_h   = 8;     // Z — lid  body thickness (mm)

// ── Screen / bezel parameters (defined here so kb_y0 can reference bezel) ────
bezel        = 15;    // bezel width all sides (mm)
screen_depth = 2.5;   // pocket depth into lid inner face (mm)
screen_w     = base_w - 2 * bezel;   // 220 mm
screen_h_val = base_d - 2 * bezel;   // 150 mm

// ── Hinge parameters ─────────────────────────────────────────────────────────
pin_d            = 4.0;   // pin diameter                (mm)
bore_d           = 5.0;   // bore inner diameter — 0.5 mm radial clearance each side
barrel_od        = 12.0;  // barrel outer diameter; wall=(12-5)/2=3.5 mm > 1.2 mm min
barrel_r         = barrel_od / 2;
bore_r           = bore_d / 2;
pin_r            = pin_d / 2;
pin_head_r       = bore_r - 0.15; // head fits inside bore with 0.15 mm clearance = 2.35 mm
pin_head_h       = 2.0;           // axial extent of each end cap on the pin
hinge_angle      = 90;   // print-pose interior angle: 90° = lid perpendicular to base
hard_stop_angle  = 135;  // absolute max opening
stop_lug_h       = 2.5;  // shoulder height on base side barrel collar
stop_lug_w       = 4.0;  // shoulder width (mm)

// ── Knuckle parameters (interleaved print-in-place hinge) ───────────────────
n_knuckles    = 7;       // total knuckles (odd count: base gets 4, lid gets 3)
knuckle_gap   = 0.5;     // axial clearance between adjacent knuckles (mm)
knuckle_w     = (base_w - (n_knuckles - 1) * knuckle_gap) / n_knuckles;
                          // ≈ 35.29 mm per knuckle

// ── Keyboard parameters ───────────────────────────────────────────────────────
key_w      = 14.0;   // keycap width  (mm)
key_d      = 14.0;   // keycap depth  (mm)
key_h      = 2.5;    // keycap height above bed surface (mm)
key_gap    = 1.5;    // gap between keycaps (mm)
bed_depth  = 1.5;    // depth of keyboard bed recess below base top surface (mm)
kb_bed_margin = 4;   // extra margin around key grid in the recessed bed
n_kb_rows  = 5;      // number of key rows (num, tab, cap, sft, bot)

// Total Y extent of the keyboard bed (keys + gaps + margins)
bed_d_total = n_kb_rows * (key_d + key_gap) - key_gap + 2 * kb_bed_margin;

// Keyboard grid origin (from base front-left corner, on top surface).
// kb_y0 is computed so the fn row (back row) sits exactly `bezel` mm from the
// hinge edge — matching the screen-pocket inset on the lid for clean closure.
// bed back edge = kb_y0 - kb_bed_margin + bed_d_total  =  base_d - bezel
kb_x0  = 10;   // left edge of keyboard area from base left
kb_y0  = base_d - bezel - bed_d_total + kb_bed_margin;

// ── Trackpad parameters ───────────────────────────────────────────────────────
tp_w     = 80;    // trackpad width  (mm)
tp_d     = 55;    // trackpad depth  (mm)
tp_depth = 0.5;   // recess depth below base top surface (mm)
tp_x     = (base_w - tp_w) / 2;
tp_y     = 15;    // from base front edge

// ── Key layout row widths (unit = 1× key_w) ───────────────────────────────────
// Each inner list is one row of keycap widths. Rows are ordered back-to-front
// (index 0 = function row near hinge, index 5 = bottom row near trackpad).
row_num = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.0];    // 13 + backspace
row_tab = [1.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0];    // tab + 12 keys
row_cap = [1.75, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.25];             // caps + 11 + enter
row_sft = [2.25, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.75];                        // lshift + 9 + rshift
row_bot = [1.25, 1.25, 1.25, 6.25, 1.25, 1.25, 1.25];                                   // ctrl win alt space alt fn ctrl

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

// Sum of widths[0 .. n-1]
function sum_w(v, n) = (n <= 0) ? 0 : sum_w(v, n-1) + v[n-1];

// X-position of the start of knuckle i (0-indexed)
function knuckle_x(i) = i * (knuckle_w + knuckle_gap);

// Total row width in mm (last gap not counted)
function row_mm(v) = sum_w(v, len(v)) * (key_w + key_gap) - key_gap;

// ============================================================================
// KEYCAP MODULE
// Tapered keycap. Origin = front-left corner of keycap footprint, Z=0 is bed.
// Uses polyhedron-based hull to avoid zero-area degenerate faces.
// ============================================================================
module keycap(w, d, h) {
    // Bottom face inset and top face inset from the outer footprint
    b = 0.4;   // bottom inset (each side)
    t = 0.7;   // top inset (each side) — creates the taper

    // Use linear_extrude with scale parameter to create tapered shape
    // scale = ratio of top width to bottom width at full height
    bw = w - 2*b;
    bd_val = d - 2*b;
    scale_x = (w - 2*t) / bw;
    scale_y = (d - 2*t) / bd_val;

    translate([b, b, 0])
        linear_extrude(height=h, scale=[scale_x, scale_y])
            square([bw, bd_val]);
}

// ============================================================================
// KEYBOARD BED RECESS (subtracted from base)
// Returns a solid box that will be cut from the base to form the recessed bed.
// ============================================================================
module kb_bed_recess() {
    // widest row determines bed width; bed_d_total and n_kb_rows are module-level
    bed_w = row_mm(row_num) + 2 * kb_bed_margin;
    cube([bed_w, bed_d_total, bed_depth + 0.01]);  // slight overshoot for clean cut
}

// ============================================================================
// KEYCAP ROWS (added on top of base after recess)
// Returns all keycap geometry. Origin matches kb_bed_recess origin.
// Z=0 here corresponds to the bottom of the bed recess (= base top - bed_depth).
// ============================================================================
module kb_keycaps() {
    rows      = [row_num, row_tab, row_cap, row_sft, row_bot];
    max_row_w = row_mm(row_num);   // widest row sets the reference width
    for (ri = [0 : n_kb_rows - 1]) {
        // Row 0 (fn row) is furthest back (largest Y), row 5 is closest to trackpad
        y_off    = kb_bed_margin + (n_kb_rows - 1 - ri) * (key_d + key_gap);
        // Shift each row right so it is centred relative to the widest row
        center_x = kb_bed_margin + (max_row_w - row_mm(rows[ri])) / 2;
        translate([center_x, y_off, 0]) {
            for (ki = [0 : len(rows[ri]) - 1]) {
                x_off = sum_w(rows[ri], ki) * (key_w + key_gap);
                w_key = rows[ri][ki] * key_w + (rows[ri][ki] - 1) * key_gap;
                translate([x_off, 0, 0])
                    keycap(w_key, key_d, key_h);
            }
        }
    }
}

// ============================================================================
// BASE MODULE
// NOTE: keycaps are NOT included here — they are added at assembly level
// as a separate colored object so they can be rendered black independently.
// ============================================================================
module base() {
    difference() {
        union() {
            // ── Main base plate ──────────────────────────────────────────
            cube([base_w, base_d, base_h]);

            // ── Hinge barrel knuckles (base side: even indices 0, 2, 4, 6) ──
            // Full cylinders centered at hinge axis (Y=base_d, Z=base_h).
            for (i = [0 : 2 : n_knuckles - 1]) {
                translate([knuckle_x(i), base_d, base_h])
                    rotate([0, 90, 0])
                        cylinder(r=barrel_r, h=knuckle_w, $fn=$fn);
            }

            // ── Hard-stop shoulders (on inner base knuckles 2 and 4) ─────
            for (i = [2, 4]) {
                translate([knuckle_x(i), base_d + barrel_r * 0.5, base_h + barrel_r - 1])
                    cube([knuckle_w, stop_lug_h, stop_lug_w]);
            }
        }

        // ── All subtractive cuts ─────────────────────────────────────────

        // Keyboard bed recess (cut from top surface)
        translate([kb_x0 - kb_bed_margin, kb_y0 - kb_bed_margin, base_h - bed_depth])
            kb_bed_recess();

        // Trackpad recess (cut from top surface)
        translate([tp_x, tp_y, base_h - tp_depth])
            cube([tp_w, tp_d, tp_depth + 0.1]);

        // ── Bore through each base knuckle (lid's pin rotates here) ─────
        for (i = [0 : 2 : n_knuckles - 1]) {
            translate([knuckle_x(i) - 0.1, base_d, base_h])
                rotate([0, 90, 0])
                    cylinder(r=bore_r, h=knuckle_w + 0.2, $fn=$fn);
        }

        // ── Slots for lid knuckles to rotate through the base rear edge ─
        // At lid knuckle X positions (odd indices 1, 3, 5), cut a slot
        // so the full-cylinder lid knuckle can sweep through 0°–135°.
        // Extra 0.5 mm clearance in Y and Z to prevent binding.
        for (i = [1 : 2 : n_knuckles - 1]) {
            translate([knuckle_x(i) - knuckle_gap, base_d - barrel_r - 0.5, base_h - barrel_r - 0.5])
                cube([knuckle_w + 2 * knuckle_gap, barrel_r + 1.5, barrel_od + 3.0]);
        }
    }
}

// ============================================================================
// LID MODULE
// Local coordinate system:
//   - Hinge axis at Y=0, Z=0
//   - Lid body extends in +Y direction (away from hinge)
//   - Outer (back) face at Z=-lid_h  (pointing toward -Z, i.e. downward in
//     the closed position)
//   - Inner (screen) face at Z=0     (facing toward base when closed)
//
// When assembled: translate to (hinge_y, hinge_z) then rotate.
// The inner face (Z=0) faces the base top surface when closed.
// ============================================================================
module lid() {
    difference() {
        union() {
            // ── Main lid plate ────────────────────────────────────────────
            // Placed so inner face is at Z=0, outer face at Z=-lid_h
            translate([0, 0, -lid_h])
                cube([base_w, base_d, lid_h]);

            // ── Hinge barrel knuckles (lid side: odd indices 1, 3, 5) ────
            // Full cylinders at Y=0, Z=0 (hinge axis). These interleave
            // with base knuckles at even indices.
            for (i = [1 : 2 : n_knuckles - 1]) {
                translate([knuckle_x(i), 0, 0])
                    rotate([0, 90, 0])
                        cylinder(r=barrel_r, h=knuckle_w, $fn=$fn);
            }

            // ── Integrated pin shaft ──────────────────────────────────────
            // Pin runs through all base knuckle bores (even indices 0–6).
            // Spans from inside knuckle 0 to inside knuckle 6 so the
            // interleaving provides end retention.
            pin_start = knuckle_gap;
            pin_end   = base_w - knuckle_gap;
            translate([pin_start, 0, 0])
                rotate([0, 90, 0])
                    cylinder(r=pin_r, h=pin_end - pin_start, $fn=$fn);

            // ── Pin retention caps ────────────────────────────────────────
            // Enlarged ends inside the outermost base knuckles (0 and 6).
            // Head radius = bore_r - 0.05: fits inside bore but cannot
            // pass out through a knuckle end face.
            // Left cap (inside base knuckle 0)
            translate([knuckle_gap, 0, 0])
                rotate([0, 90, 0])
                    cylinder(r=pin_head_r, h=pin_head_h, $fn=$fn);
            // Right cap (inside base knuckle 6)
            translate([base_w - knuckle_gap - pin_head_h, 0, 0])
                rotate([0, 90, 0])
                    cylinder(r=pin_head_r, h=pin_head_h, $fn=$fn);

            // ── Stop lug on middle lid knuckle (index 3) ─────────────────
            // Contacts base hard-stop shoulder when lid reaches hard_stop_angle.
            translate([knuckle_x(3), -stop_lug_h, 0])
                cube([knuckle_w, stop_lug_h, stop_lug_w]);

        }

        // ── Screen pocket (on inner face — Z = 0, cut toward Z = -screen_depth) ─
        translate([bezel, bezel, -screen_depth])
            cube([screen_w, screen_h_val, screen_depth]);
    }
}

// ============================================================================
// LID (white body only — screen indicator plate is separate below)
// ============================================================================
module lid_body() {
    lid();
}

// ============================================================================
// SCREEN INDICATOR PLATE
// A thin black plate flush with the inner face of the lid, placed inside the
// screen pocket recess. In the 90° print pose the inner face faces -Y (toward
// the viewer), so this plate faces the viewer as the "screen".
// Thickness is 0.4 mm (1 layer) — sits at Z = -screen_depth + 0.4 from inner face.
// In lid-local coords: inner face is Z=0; plate sits at Z = -(screen_depth - 0.4).
// ============================================================================
module screen_plate() {
    plate_thick = 0.4;
    translate([bezel, bezel, -(screen_depth - plate_thick)])
        cube([screen_w, screen_h_val, plate_thick]);
}

// ============================================================================
// TRACKPAD INDICATOR PLATE
// A thin black plate flush with the base top surface inside the trackpad recess.
// Thickness = 0.4 mm sitting at Z = base_h - tp_depth + 0.
// ============================================================================
module trackpad_plate() {
    plate_thick = 0.4;
    translate([tp_x, tp_y, base_h - tp_depth])
        cube([tp_w, tp_d, plate_thick]);
}

// ============================================================================
// MAIN ASSEMBLY
// ============================================================================
//
// Coordinate system for assembly:
//   Base is flat on XY plane, Z=0 is the print bed.
//   Hinge axis: X-axis at Y=base_d, Z=base_h.
//
// Lid rotation:
//   Interior hinge angle = 90° (print pose: lid perpendicular to base).
//   In lid-local coords: hinge axis at Y=0 Z=0; inner face at Z=0 (screen);
//   lid body extends in +Y; outer face at Z=-lid_h.
//
//   Rotation around X by +(180 - hinge_angle) = +90°:
//     local +Y  →  global +Z   (lid rises straight up)
//     local +Z  →  global -Y   (inner face / screen faces toward viewer, -Y)
//   This is the correct open-laptop pose: base flat, lid vertical, screen
//   facing forward (−Y = toward the person sitting in front of the printer).
//
// Z-axis rotation:
//   The whole assembly is rotated 90° around Z so the long axis (base_w=250mm)
//   runs along Y instead of X. Translated by [base_w, 0, 0] first so that after
//   90° CCW rotation the model stays in the positive-XYZ octant.
//   New footprint: X = base_d = 180 mm, Y = base_w = 250 mm, Z = 190 mm.
//
// ── Color export control ──────────────────────────────────────────────────────
// RENDER_COLOR controls which color body is rendered/exported.
//   "all"   — full model with color() wrappers (default; used for OpenSCAD GUI preview)
//   "white" — only white parts (base, lid body with integrated pin); for per-color 3MF export
//   "black" — only black parts (keycaps, trackpad plate, screen plate); for per-color export
//
// Usage:
//   openscad --export-format 3mf toy_laptop_001.scad                      → full preview
//   openscad --export-format 3mf -D 'RENDER_COLOR="white"' ... → white body only
//   openscad --export-format 3mf -D 'RENDER_COLOR="black"' ... → black body only
//
// After exporting both bodies, run scripts/colorize_3mf.py to merge them into a
// single Bambu-compatible multi-object 3MF with <m:colorgroup> assignments.
RENDER_COLOR = "all";   // "all" | "white" | "black"

// Barrel/pin axis is at Y=base_d, Z=base_h (rear top edge of base)
hinge_y = base_d;
hinge_z = base_h;

// ── Wrap entire assembly in Z-rotation ────────────────────────────────────────
// translate([base_w, 0, 0]) moves origin to X=250 before rotation so after
// 90° CCW rotation the part stays in positive-XY quadrant.
translate([base_w, 0, 0])
rotate([0, 0, 90]) {

    // ── WHITE parts ─────────────────────────────────────────────────────
    if (RENDER_COLOR == "all" || RENDER_COLOR == "white") {
        // Base body (without keycaps) — includes base-side barrel knuckles
        color("white")
            base();

        // Lid body (without screen plate) — includes lid-side barrel knuckles
        // and integrated pin shaft (print-in-place captive pin)
        color("white")
            translate([0, hinge_y, hinge_z])
                rotate([(180 - hinge_angle), 0, 0])
                    lid_body();
    }

    // ── BLACK parts ─────────────────────────────────────────────────────
    if (RENDER_COLOR == "all" || RENDER_COLOR == "black") {
        // Keycap tops — placed at keyboard bed origin (same as kb_bed_recess origin)
        color("black")
            translate([kb_x0 - kb_bed_margin, kb_y0 - kb_bed_margin, base_h - bed_depth])
                kb_keycaps();

        // Trackpad indicator (black plate in trackpad recess)
        color("black")
            trackpad_plate();

        // Screen indicator (black plate inside screen pocket)
        color("black")
            translate([0, hinge_y, hinge_z])
                rotate([(180 - hinge_angle), 0, 0])
                    screen_plate();
    }

} // end rotate Z
