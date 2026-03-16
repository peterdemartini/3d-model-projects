// ============================================================================
// Spa Headrest v001 — Pillow-Style with Tile Friction Clip
// Compact pillow-shaped pad with tile slot, triangle supports, flowing contour
// Material: PETG  |  Printer: Bambu Lab H2D
// ============================================================================
//
// Coordinate system (2D profile in XY, extruded along Z):
//   X = depth (0 at back/tile side, positive toward person)
//   Y = height (0 at bottom, positive upward)
//   Z = width (along tile edge, 0 to pad_width)
//
// Side view (XY plane): person is on the +X side
// After extrusion, rotate for print orientation (bottom on bed).
// ============================================================================

$fn = 64;

// ── Tile parameters ─────────────────────────────────────────────────────────
tile_thickness    = 29.32;   // measured tile thickness (mm)
tile_overhang     = 40;      // tile overhang into spa (mm)

// ── Slot (clip) parameters ──────────────────────────────────────────────────
slot_gap          = tile_thickness - 0.52;  // interference fit gap (mm)
slot_depth        = 40;      // outer slot depth incl. spine (mm)
slot_arm_thick    = 5;       // top and bottom arm thickness (mm)
slot_chamfer      = 2;       // entry flare on slot opening (mm)
fric_rib_h        = 0.4;     // friction rib height (mm)
fric_rib_spacing  = 2;       // friction rib center-to-center (mm)
fric_rib_w        = 1.0;     // friction rib width (mm)

// ── Pad parameters ──────────────────────────────────────────────────────────
pad_width         = 250;     // width along tile edge — Z axis (mm)
pad_height        = 200;     // vertical height — Y axis (mm)
pad_depth         = 80;      // depth from back to contour peak — X axis (mm)
wall_thick        = 6;       // shell wall thickness (mm)
corner_radius     = 40;      // top corner radius in XY profile (mm)

// ── Contour parameters ──────────────────────────────────────────────────────
head_bulge        = 10;      // convex bump at head zone (mm)
neck_dip          = 12;      // concave dip at neck zone (mm)
head_center_frac  = 0.30;    // head zone center as fraction of pad_height (from top)
neck_center_frac  = 0.60;    // neck zone center as fraction of pad_height (from top)
head_sigma_frac   = 0.18;    // head zone Gaussian spread
neck_sigma_frac   = 0.15;    // neck zone Gaussian spread

// ── Drainage ────────────────────────────────────────────────────────────────
drain_hole_d      = 8;       // bottom drain hole diameter (mm)
drain_hole_n      = 3;       // number of bottom drain holes

// ── Internal ribs ───────────────────────────────────────────────────────────
int_rib_n         = 3;       // number of internal structural ribs
int_rib_t         = 3;       // internal rib thickness in Z (mm)

// ── Derived ─────────────────────────────────────────────────────────────────
slot_total_h      = 2 * slot_arm_thick + slot_gap;  // total slot height
slot_insert_depth = slot_depth - slot_arm_thick;     // usable tile insertion depth
slot_center_y     = pad_height / 2;                  // slot centered vertically
slot_bot_y        = slot_center_y - slot_total_h / 2;
slot_top_y        = slot_center_y + slot_total_h / 2;
slot_inner_bot_y  = slot_bot_y + slot_arm_thick;     // inner gap bottom
slot_inner_top_y  = slot_inner_bot_y + slot_gap;     // inner gap top
back_x            = 0;                               // back face X position

// Contour centers (measured from bottom, Y=0)
head_center_y     = pad_height * (1 - head_center_frac);  // upper zone
neck_center_y     = pad_height * (1 - neck_center_frac);  // mid zone
head_sigma        = pad_height * head_sigma_frac;
neck_sigma        = pad_height * neck_sigma_frac;

// Assertions
assert(slot_insert_depth <= tile_overhang, "Slot insertion depth exceeds tile overhang");
assert(pad_depth > wall_thick * 2, "Pad depth must exceed 2x wall thickness");
assert(slot_total_h < pad_height, "Slot total height exceeds pad height");

// ============================================================================
// FUNCTION: front contour X at height Y
// Smooth flowing curve: convex at head, concave at neck
// Returns X offset from pad_depth baseline
// ============================================================================
function contour_x(y) =
    pad_depth
    + head_bulge * exp(-pow((y - head_center_y) / head_sigma, 2))
    - neck_dip   * exp(-pow((y - neck_center_y) / neck_sigma, 2));

// ============================================================================
// MODULE: pad_profile_2d — outer 2D profile of the pad body
// Single polygon: flat back, contoured front, rounded corners via arc points
// ============================================================================
module pad_profile_2d() {
    contour_steps = 80;
    corner_steps  = 16;

    // Front contour points (bottom to top, stopping at corner transition)
    contour_top_y = pad_height - corner_radius;
    front_pts = [
        for (i = [1:contour_steps-1])
            let(y = i * contour_top_y / contour_steps)
            [contour_x(y), y]
    ];

    // Top-right rounded corner: arc from 0° to 90°
    // Arc center X is set so the arc starts at the contour endpoint
    tr_cx = contour_x(contour_top_y) - corner_radius;
    tr_cy = contour_top_y;
    top_right_arc = [
        for (i = [0:corner_steps])
            let(a = 90 * i / corner_steps)
            [tr_cx + corner_radius * cos(a), tr_cy + corner_radius * sin(a)]
    ];

    // Top-left rounded corner: arc from 90° to 180°
    tl_cx = corner_radius;
    tl_cy = pad_height - corner_radius;
    top_left_arc = [
        for (i = [0:corner_steps])
            let(a = 90 + 90 * i / corner_steps)
            [tl_cx + corner_radius * cos(a), tl_cy + corner_radius * sin(a)]
    ];

    // Bottom corners are square (flat base for print bed and clean
    // union with triangular supports that share the back edge at Y=0)
    polygon(concat(
        [[back_x, 0]],                    // bottom-left (back)
        [[contour_x(0), 0]],              // bottom-right (front)
        front_pts,                         // contour from bottom to top
        [[contour_x(contour_top_y), contour_top_y]],  // explicit endpoint at arc join
        top_right_arc,                     // top-right rounded corner
        top_left_arc                       // top-left rounded corner
    ));
}

// ============================================================================
// MODULE: pad_inner_2d — inner cavity (offset inward by wall_thick)
// ============================================================================
module pad_inner_2d() {
    offset(r = -wall_thick)
        pad_profile_2d();
}

// ============================================================================
// MODULE: triangle_top_2d — top triangular gusset
// From top of pad down to slot top
// ============================================================================
module triangle_top_2d() {
    eps = 0.1;  // overlap into pad body to prevent coplanar faces
    // Cap at pad_height - corner_radius so triangle stays within pad profile
    // (the back edge curves away above this Y due to the top-left arc)
    top_y = pad_height - corner_radius;
    polygon([
        [back_x + eps, slot_top_y],           // at slot top, slightly into pad
        [back_x + eps, top_y],                // at pad back edge limit
        [-slot_depth, slot_inner_top_y]        // extends backward to slot depth
    ]);
}

// ============================================================================
// MODULE: triangle_bot_2d — bottom triangular gusset
// From slot bottom down to bottom of pad
// ============================================================================
module triangle_bot_2d() {
    eps = 0.1;  // overlap into pad body to prevent coplanar faces
    polygon([
        [back_x + eps, slot_bot_y],           // at slot bottom, slightly into pad
        [back_x + eps, 0],                    // at pad bottom, slightly into pad
        [-slot_depth, slot_inner_bot_y]        // extends backward to slot depth
    ]);
}

// ============================================================================
// MODULE: slot_2d — tile slot cross-section (C-shape opening to the right)
// ============================================================================
module slot_2d() {
    eps = 0.1;  // overlap into pad body to prevent coplanar faces
    // Bottom arm (extends eps into pad body)
    translate([-slot_depth, slot_bot_y])
        square([slot_depth + eps, slot_arm_thick]);

    // Top arm (extends eps into pad body)
    translate([-slot_depth, slot_inner_top_y])
        square([slot_depth + eps, slot_arm_thick]);

    // Spine (connects arms at back, inside the pad body)
    translate([-slot_depth, slot_bot_y])
        square([slot_arm_thick, slot_total_h]);
}

// ============================================================================
// MODULE: slot_chamfers_2d — entry chamfer cuts at slot opening
// ============================================================================
module slot_chamfers_2d() {
    c = slot_chamfer;

    // Bottom arm chamfer (top-right corner)
    translate([-c, slot_inner_bot_y - c])
        polygon([[0, 0], [c, 0], [c, c]]);

    // Top arm chamfer (bottom-right corner)
    translate([-c, slot_inner_top_y])
        polygon([[0, c], [c, 0], [c, c]]);
}

// ============================================================================
// MODULE: friction_ribs — bumps on slot inner surfaces
// ============================================================================
module friction_ribs() {
    // Bottom arm ribs (top surface, facing tile)
    num_ribs = floor((slot_depth - slot_arm_thick - 4) / fric_rib_spacing);
    for (i = [1:num_ribs]) {
        x = -(slot_arm_thick + i * fric_rib_spacing);
        if (x - fric_rib_w/2 >= -slot_depth) {
            // Bottom arm: ribs on top surface (protrude upward into gap)
            translate([x, slot_inner_bot_y, 0])
                cube([fric_rib_w, fric_rib_h, pad_width]);
            // Top arm: ribs on bottom surface (protrude downward into gap)
            translate([x, slot_inner_top_y - fric_rib_h, 0])
                cube([fric_rib_w, fric_rib_h, pad_width]);
        }
    }
}

// ============================================================================
// MODULE: drain_holes — cylindrical holes through pad bottom
// ============================================================================
module drain_holes() {
    spacing = pad_width / (drain_hole_n + 1);
    hole_x = pad_depth / 2;

    for (i = [1:drain_hole_n]) {
        z = i * spacing;
        translate([hole_x, -1, z])
            rotate([-90, 0, 0])
                cylinder(d = drain_hole_d, h = wall_thick + 2);
    }
}

// ============================================================================
// MODULE: internal_ribs — structural ribs across the width
// ============================================================================
module internal_ribs() {
    spacing = pad_width / (int_rib_n + 1);
    notch_w = drain_hole_d * 1.5;
    notch_h = wall_thick + 4;

    for (i = [1:int_rib_n]) {
        z = i * spacing - int_rib_t / 2;
        translate([0, 0, z])
            linear_extrude(int_rib_t)
                difference() {
                    pad_inner_2d();
                    // Drainage notch at bottom
                    translate([pad_depth/2 - notch_w/2, 0])
                        square([notch_w, notch_h]);
                }
    }
}

// ============================================================================
// MODULE: spa_headrest — complete 3D assembly (before rounding)
// Build as solid outer shell minus inner cavity (not extruded ring) so that
// the front contour face, back face, and side faces are all continuous shell.
// ============================================================================
module spa_headrest_raw() {
    union() {
        // Pad body: solid outer minus inner cavity (keeps all 6 faces as shell)
        difference() {
            linear_extrude(pad_width)
                pad_profile_2d();
            // Inner cavity inset from all 6 faces by wall_thick
            translate([0, 0, wall_thick])
                linear_extrude(pad_width - 2 * wall_thick)
                    pad_inner_2d();
            // Drain holes through bottom
            drain_holes();
        }
        // Solid triangular supports (no cavity)
        linear_extrude(pad_width) {
            triangle_top_2d();
            triangle_bot_2d();
        }
        // Solid tile slot minus chamfers
        linear_extrude(pad_width)
            difference() {
                slot_2d();
                slot_chamfers_2d();
            }
        // Friction ribs on slot inner surfaces
        friction_ribs();
        // Internal structural ribs inside the cavity
        internal_ribs();
    }
}

// ============================================================================
// MODULE: spa_headrest — top-level assembly
// Edge rounding deferred to slicer settings or post-processing
// ============================================================================
module spa_headrest() {
    spa_headrest_raw();
}

// ============================================================================
// RENDER — print orientation
// Model space: X=depth, Y=height, Z=width
// rotate([90,0,0]): X→X, Y→-Z, Z→Y → print: X=depth, Y=width, Z=height
// Translate X by +slot_depth so slot geometry (at negative X) starts at 0.
// Translate Y by +pad_width so rotated Z→Y stays positive.
// ============================================================================
translate([slot_depth, pad_width, 0])
    rotate([90, 0, 0])
        spa_headrest();
