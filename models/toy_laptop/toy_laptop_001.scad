// ============================================================================
// toy_laptop_001.scad — Print-in-Place Toy Laptop
// Target printer : Bambu Lab H2D
// Print pose     : 90° interior hinge angle (lid perpendicular to base)
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
pin_d            = 3.0;   // pin diameter                (mm)
bore_d           = 3.4;   // bore inner diameter — 0.2 mm radial clearance each side
barrel_od        = 8.0;   // barrel outer diameter; wall=(8-3.4)/2=2.3 mm > 1.2 mm min
barrel_r         = barrel_od / 2;
bore_r           = bore_d / 2;
pin_r            = pin_d / 2;
pin_head_r       = bore_r - 0.05; // head fits inside bore with tiny clearance
pin_head_h       = 2.0;           // axial extent of each end cap on the pin
hinge_angle      = 90;   // print-pose interior angle: 90° = lid perpendicular to base
hard_stop_angle  = 135;  // absolute max opening
stop_lug_h       = 2.5;  // shoulder height on base side barrel collar
stop_lug_w       = 4.0;  // shoulder width (mm)

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

// ── Bump-stop parameters ──────────────────────────────────────────────────────
stop_d      = 3.0;   // dome diameter (mm)
stop_h_dome = 1.0;   // dome height   (mm)
stop_r      = stop_d / 2;
stop_inset  = 8;     // inset from screen pocket corner

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
    union() {
        // ── Main base plate with cutouts ─────────────────────────────────
        difference() {
            cube([base_w, base_d, base_h]);

            // Keyboard bed recess (cut from top surface)
            translate([kb_x0 - kb_bed_margin, kb_y0 - kb_bed_margin, base_h - bed_depth])
                kb_bed_recess();

            // Trackpad recess (cut from top surface)
            translate([tp_x, tp_y, base_h - tp_depth])
                cube([tp_w, tp_d, tp_depth + 0.1]);

            // Bore through the barrel (overshoot 1 mm each side)
            translate([-1, base_d, base_h])
                rotate([0, 90, 0])
                    cylinder(r=bore_r, h=base_w + 2, $fn=$fn);
        }

        // ── Hinge barrel (base side) ──────────────────────────────────────
        // Full cylinder at Y=base_d, Z=base_h (the hinge axis).
        // The lower half of the cylinder merges into the base cube.
        // The upper half protrudes above. The bore cuts through it.
        // We don't clip the cylinder to avoid T-junction issues.
        translate([0, base_d, base_h])
            rotate([0, 90, 0])
                cylinder(r=barrel_r, h=base_w, $fn=$fn);

        // ── Hard-stop shoulder ────────────────────────────────────────────
        // Rectangular lug protruding from the top of the base barrel.
        // Located at Y > barrel axis, above base_h.
        // Starts at Z = base_h + barrel_r - 1 (just below top of barrel)
        // to avoid creating coplanar faces.
        translate([0, base_d + barrel_r * 0.5, base_h + barrel_r - 1])
            cube([base_w, stop_lug_h, stop_lug_w]);
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

            // ── Hinge barrel (lid half — upper semicylinder) ──────────────
            // Barrel axis at Y=0, Z=0 (same as hinge axis).
            // The lid's barrel half is the part with Z ≥ 0 (pointing toward base).
            // This is the upper half from the lid's perspective.
            rotate([0, 90, 0])
                intersection() {
                    cylinder(r=barrel_r, h=base_w, $fn=$fn);
                    // Keep Z ≥ 0 half (above hinge axis, toward base)
                    translate([-barrel_r - 1, -barrel_r - 1, 0])
                        cube([barrel_od + 2, barrel_od + 2, barrel_r + 1]);
                }

            // ── Stop lug on lid barrel collar ─────────────────────────────
            // Protrudes from the lid barrel in the +Z direction.
            // Contacts base hard-stop shoulder when lid reaches hard_stop_angle.
            translate([0, -stop_lug_h, 0])
                cube([base_w, stop_lug_h, stop_lug_w]);

            // ── Bump stops (2 domes on OUTER face at Z=-lid_h) ────────────
            // Moved from inner face to outer face so they print overhang-free.
            // In the 90° print pose the outer face faces upward (+Y world),
            // so domes on it point straight up — no overhang.
            // Functionally identical: the outer face contacts the base top
            // when the lid is closed, and these domes keep the lid from
            // pressing directly on the keycaps.
            //
            // Dome protrudes OUTWARD from outer face = in the -Z direction
            // (lid-local -Z → global +Y in print pose = upward, printable).
            // Hull between a flat disk flush with the outer face and a raised
            // scaled sphere avoids tangent-face non-manifold edges.
            bump_xl = bezel + stop_inset;
            bump_xr = base_w - bezel - stop_inset;
            bump_y  = base_d - bezel - stop_inset;
            for (bx = [bump_xl, bump_xr]) {
                translate([bx, bump_y, -lid_h])
                    hull() {
                        // Flat disk flush with outer face (at Z=0 in local-to-outer coords)
                        cylinder(r=stop_r, h=0.01, $fn=$fn);
                        // Sphere offset outward (−Z = away from lid body)
                        translate([0, 0, -stop_h_dome])
                            scale([1, 1, 0.3])
                                sphere(r=stop_r, $fn=$fn);
                    }
            }
        }

        // ── Bore through the lid barrel (axis at Y=0, Z=0) ────────────────
        translate([-1, 0, 0])
            rotate([0, 90, 0])
                cylinder(r=bore_r, h=base_w + 2, $fn=$fn);

        // ── Screen pocket (on inner face — Z = 0, cut toward Z = -screen_depth) ─
        // Inner face is at Z=0; cut goes into the lid body (toward -Z).
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
// HINGE PIN MODULE
// Full-width pin with enlarged end caps to prevent axial escape.
// The pin sits inside the bore with 0.2 mm radial clearance.
// ============================================================================
module hinge_pin() {
    union() {
        // Pin shaft
        translate([0, 0, 0])
            rotate([0, 90, 0])
                cylinder(r=pin_r, h=base_w, $fn=$fn);

        // End caps
        for (x_cap = [0, base_w - pin_head_h]) {
            translate([x_cap, 0, 0])
                rotate([0, 90, 0])
                    cylinder(r=pin_head_r, h=pin_head_h, $fn=$fn);
        }
    }
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
//   "white" — only white parts (base, hinge pin, lid body); for per-color 3MF export
//   "black" — only black parts (keycaps, trackpad plate, screen plate); for per-color export
//
// Usage:
//   openscad --export-format 3mf toy_laptop_001.scad                      → full preview
//   openscad --export-format 3mf -D 'RENDER_COLOR="white"' ... → white body only
//   openscad --export-format 3mf -D 'RENDER_COLOR="black"' ... → black body only
//
// After exporting both bodies, run scripts/colorize_3mf.py to merge them into a
// single Bambu-compatible multi-object 3MF with <m:basematerials> assignments.
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
        // Base body (without keycaps)
        color("white")
            base();

        // Hinge pin
        color("white")
            translate([0, hinge_y, hinge_z])
                hinge_pin();

        // Lid body (without screen plate)
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
