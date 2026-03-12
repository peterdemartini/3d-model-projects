// ============================================================================
// Spa Neck Rest — v003
// Wraps around overhanging spa tile, provides contoured neck support
// Material: PETG  |  Printer: Bambu Lab H2D
// ============================================================================
//
// Coordinate system (2D profile in XY, extruded along Z):
//   X = depth (0 at clip spine, positive toward person/spa interior)
//   Y = height (0 at rest bottom, positive upward)
//   Z = width (0 to rest_width, along tile edge)
//
// v003 layout: rest wraps ABOVE and BELOW the tile, clip in the middle.
//   Y=0            rest bottom (hangs below tile)
//   Y=rest_below   clip bottom arm
//   Y=tile_top_y   tile top surface (flush point)
//   Y=clip_y_end   clip top arm end
//   Y=model_height rest top (above tile)
//
// Construction: The shell cross-section is ONE polygon with three paths
// (outer boundary, inner cavity, clip gap). No 2D boolean operations.
// Entry chamfers are integrated into the gap polygon to avoid CGAL
// T-junction issues during 3D boolean operations.
//
// After extrusion, rotate so Y->Z for print orientation (bottom on bed).
// ============================================================================

$fn = 64;

// ── Tile parameters ─────────────────────────────────────────────────────────
tile_thickness    = 29.32;   // measured tile thickness (mm)
tile_overhang     = 40;      // tile overhang into spa (mm)
clip_interference = 0.52;    // total interference fit (0.26 mm/side)

// ── Clip parameters ─────────────────────────────────────────────────────────
clip_gap          = tile_thickness - clip_interference; // derived gap (mm)
clip_top_arm      = 15;      // top arm length from spine (mm)
clip_bot_arm      = 30;      // bottom arm length from spine (mm)
clip_arm_thick    = 4;       // arm thickness (mm)
clip_chamfer      = 2;       // entry flare on gap opening (mm)
fric_rib_h        = 0.4;     // friction rib height (mm)
fric_rib_spacing  = 2;       // friction rib center-to-center (mm)
fric_rib_w        = 1.0;     // friction rib width (mm)

// ── Rest surface parameters ─────────────────────────────────────────────────
rest_width        = 250;     // width along tile edge — Z axis (mm)
rest_height       = 80;      // usable rest surface height — Y axis (mm)
rest_depth        = 80;      // depth from back wall to front baseline — X axis (mm)
wall_thick        = 6;       // shell wall thickness (mm)

// ── Contour parameters (neck-only, no head cradle) ──────────────────────────
neck_bump         = 15;      // peak of neck roll convex bump (mm)

// ── Drainage ────────────────────────────────────────────────────────────────
drain_slot_w      = 8;       // clip drain slot width in X (mm)
drain_slot_l      = 20;      // clip drain slot length in Z (mm)
drain_slot_n      = 4;       // number of clip drain slots
drain_hole_d      = 8;       // bottom drain hole diameter (mm)
drain_hole_n      = 3;       // number of bottom drain holes

// ── Internal ribs ───────────────────────────────────────────────────────────
int_rib_n         = 3;       // number of internal structural ribs
int_rib_t         = 3;       // internal rib thickness in Z (mm)

// ── Derived ─────────────────────────────────────────────────────────────────
back_x            = clip_bot_arm;              // rest body back wall X position
front_x           = clip_bot_arm + rest_depth; // rest body front baseline X
clip_total_h      = 2 * clip_arm_thick + clip_gap; // total clip height
rest_below        = rest_height / 2;           // rest surface below clip (40 mm)
rest_above        = rest_height / 2;           // rest surface above clip (40 mm)
clip_y_start      = rest_below;                // Y where clip bottom arm begins
clip_y_end        = rest_below + clip_total_h; // Y where clip top arm ends
model_height      = rest_below + clip_total_h + rest_above; // total model height
tile_top_y        = clip_y_start + clip_arm_thick + clip_gap; // tile top surface Y

assert(clip_bot_arm <= tile_overhang, "Bottom arm exceeds tile overhang");

// ── Contour centers ─────────────────────────────────────────────────────────
neck_center_y     = model_height / 2;          // centered on model (58.4 mm)
neck_sigma        = model_height * 0.30;       // spread across model height (35 mm)

// ── Inner cavity derived ────────────────────────────────────────────────────
inner_back_x      = back_x + wall_thick;       // inner cavity back wall (36 mm)
inner_bottom_y    = wall_thick;                 // inner cavity bottom (6 mm)
inner_top_y       = model_height - wall_thick;  // inner cavity top (110.8 mm)

// ============================================================================
// FUNCTION: contour X position at a given Y height
// Single Gaussian bump for neck support — no head cradle
// ============================================================================
function contour_x(y) =
    front_x
    + neck_bump * exp(-pow((y - neck_center_y) / neck_sigma, 2));

// ============================================================================
// FUNCTION: inner contour X position (approximates offset(r=-wall_thick))
// For convex front contour, offset inward = contour - wall_thick
// ============================================================================
function inner_contour_x(y) =
    contour_x(y) - wall_thick;

// ============================================================================
// MODULE: rest_body_2d — solid 2D profile of rest body (used by internal ribs)
// Back wall at X=back_x, contoured front, Y from 0 to model_height
// ============================================================================
module rest_body_2d() {
    steps = 80;
    front_pts = [
        for (i = [0:steps])
            let(y = i * model_height / steps)
            [contour_x(y), y]
    ];
    polygon(concat(
        [[back_x, 0]],                    // back-bottom
        front_pts,                         // contour from bottom to top
        [[back_x, model_height]]           // back-top
    ));
}

// ============================================================================
// MODULE: shell_2d — complete shell cross-section as a SINGLE polygon
//
// Three paths define the cross-section with NO 2D boolean operations:
//   Path 0 (outer): rest body contour + clip spine + support braces
//   Path 1 (hole): inner cavity (manually computed, matches offset -wall_thick)
//   Path 2 (hole): clip gap with integrated entry chamfers
//
// This avoids CGAL 2D boolean artifacts that caused "mesh not closed" errors
// when using difference(rest_body, offset(rest_body)) + union(clip, braces).
// ============================================================================
module shell_2d() {
    steps = 80;
    brace_drop = clip_bot_arm - clip_arm_thick; // 26 mm
    bot_inner_y = clip_y_start + clip_arm_thick;        // 44
    top_inner_y = clip_y_start + clip_arm_thick + clip_gap; // 72.8

    // ── Path 0: Outer boundary ────────────────────────────────────────────
    // Traces: rest body contour → back wall → upper brace → clip spine →
    //         lower brace → back to start
    front_pts = [
        for (i = [0:steps])
            let(y = i * model_height / steps)
            [contour_x(y), y]
    ];

    outer = concat(
        [[back_x, 0]],                              // rest back-bottom
        front_pts,                                   // contour: bottom to top
        [[back_x, model_height]],                    // rest back-top
        [[back_x, clip_y_end + brace_drop]],         // upper brace: rest wall
        [[clip_arm_thick, clip_y_end]],               // upper brace: spine edge
        [[0, clip_y_end]],                            // clip spine: top
        [[0, clip_y_start]],                          // clip spine: bottom
        [[clip_arm_thick, clip_y_start]],             // lower brace: spine edge
        [[back_x, clip_y_start - brace_drop]]         // lower brace: rest wall
    );

    // ── Path 1: Inner cavity (hole) ──────────────────────────────────────
    // Approximates offset(r = -wall_thick) of rest_body_2d()
    // Back wall at inner_back_x, front at contour_x(y) - wall_thick,
    // bottom at inner_bottom_y, top at inner_top_y
    inner_front = [
        for (i = [0:steps])
            let(y = inner_bottom_y + i * (inner_top_y - inner_bottom_y) / steps)
            [inner_contour_x(y), y]
    ];

    inner_cavity = concat(
        [[inner_back_x, inner_bottom_y]],           // back-bottom (36, 6)
        [[inner_back_x, inner_top_y]],               // back-top (36, 110.8)
        [for (i = [steps:-1:0])                      // front: top to bottom (reversed)
            let(y = inner_bottom_y + i * (inner_top_y - inner_bottom_y) / steps)
            [inner_contour_x(y), y]
        ]
    );

    // ── Path 2: Clip gap with integrated chamfers (hole) ─────────────────
    // L-shaped gap: bottom arm to X=30, top arm to X=15
    // Entry chamfers integrated as 45° bevels at arm tips to avoid
    // T-junction non-manifold edges from 3D boolean operations
    gap = [
        [clip_arm_thick, bot_inner_y],                            // (4, 44) spine edge
        [clip_bot_arm - clip_chamfer, bot_inner_y],               // (28, 44) chamfer start
        [clip_bot_arm, bot_inner_y - clip_chamfer],               // (30, 42) chamfer end
        [clip_bot_arm, clip_y_end],                                // (30, 76.8) right edge top
        [clip_top_arm, clip_y_end],                                // (15, 76.8) L-step
        [clip_top_arm, top_inner_y + clip_chamfer],               // (15, 74.8) chamfer start
        [clip_top_arm - clip_chamfer, top_inner_y],               // (13, 72.8) chamfer end
        [clip_arm_thick, top_inner_y]                              // (4, 72.8) spine edge
    ];

    // ── Assemble polygon with three paths ────────────────────────────────
    n_outer = len(outer);
    n_inner = len(inner_cavity);
    n_gap   = len(gap);

    polygon(
        points = concat(outer, inner_cavity, gap),
        paths = [
            [for (i = [0:n_outer-1]) i],
            [for (i = [0:n_inner-1]) n_outer + i],
            [for (i = [0:n_gap-1]) n_outer + n_inner + i]
        ]
    );
}

// ============================================================================
// MODULE: drain_slots — rectangular slots through clip arms
// ============================================================================
module drain_slots() {
    spacing = rest_width / (drain_slot_n + 1);
    slot_x_bot = clip_bot_arm / 2 - drain_slot_w / 2; // centered on bottom arm
    slot_x_top = clip_top_arm / 2 - drain_slot_w / 2; // centered on top arm

    for (i = [1:drain_slot_n]) {
        z = i * spacing - drain_slot_l / 2;
        // Through bottom arm
        translate([slot_x_bot, clip_y_start - 1, z])
            cube([drain_slot_w, clip_arm_thick + 2, drain_slot_l]);
        // Through top arm
        translate([slot_x_top, clip_y_start + clip_arm_thick + clip_gap - 1, z])
            cube([drain_slot_w, clip_arm_thick + 2, drain_slot_l]);
    }
}

// ============================================================================
// MODULE: drain_holes — cylindrical holes through rest body bottom
// ============================================================================
module drain_holes() {
    spacing = rest_width / (drain_hole_n + 1);
    hole_x = back_x + rest_depth / 2; // centered in rest body depth

    for (i = [1:drain_hole_n]) {
        z = i * spacing;
        translate([hole_x, -1, z])
            rotate([-90, 0, 0])
                cylinder(d = drain_hole_d, h = wall_thick + 2);
    }
}

// ============================================================================
// MODULE: friction_ribs — small bumps on clip arm inner surfaces
// Ribs stop before the chamfer zone to avoid T-junction non-manifold edges
// where rib cube vertices would coincide with gap polygon vertices.
// ============================================================================
module friction_ribs() {
    bot_inner_y = clip_y_start + clip_arm_thick;
    top_inner_y = clip_y_start + clip_arm_thick + clip_gap;

    // Bottom arm ribs (protrude upward into gap, facing tile)
    num_bot = floor((clip_bot_arm - clip_arm_thick) / fric_rib_spacing);
    for (i = [1:num_bot]) {
        x = clip_arm_thick + i * fric_rib_spacing;
        if (x + fric_rib_w <= clip_bot_arm - clip_chamfer) {
            translate([x, bot_inner_y, 0])
                cube([fric_rib_w, fric_rib_h, rest_width]);
        }
    }

    // Top arm ribs (protrude downward into gap, facing tile)
    num_top = floor((clip_top_arm - clip_arm_thick) / fric_rib_spacing);
    for (i = [1:num_top]) {
        x = clip_arm_thick + i * fric_rib_spacing;
        if (x + fric_rib_w <= clip_top_arm - clip_chamfer) {
            translate([x, top_inner_y - fric_rib_h, 0])
                cube([fric_rib_w, fric_rib_h, rest_width]);
        }
    }
}

// ============================================================================
// MODULE: internal_ribs — structural ribs across the width
// Uses manually computed inner contour (matches shell_2d inner cavity)
// ============================================================================
module internal_ribs() {
    steps = 80;
    spacing = rest_width / (int_rib_n + 1);
    notch_w = drain_hole_d * 1.5;  // drainage notch width
    notch_h = wall_thick + 4;       // drainage notch height

    // Inner cavity profile (same shape as shell_2d path 1)
    inner_front = [
        for (i = [0:steps])
            let(y = inner_bottom_y + i * (inner_top_y - inner_bottom_y) / steps)
            [inner_contour_x(y), y]
    ];

    for (i = [1:int_rib_n]) {
        z = i * spacing - int_rib_t / 2;
        translate([0, 0, z])
            linear_extrude(int_rib_t)
                difference() {
                    polygon(concat(
                        [[inner_back_x, inner_bottom_y]],
                        inner_front,
                        [[inner_back_x, inner_top_y]]
                    ));
                    // Drainage notch at bottom of rib
                    translate([back_x + rest_depth/2 - notch_w/2, 0])
                        square([notch_w, notch_h]);
                }
    }
}

// ============================================================================
// MODULE: spa_headrest — complete 3D assembly
// Single extrusion of shell_2d (no 2D booleans), then simple 3D subtractions
// for drain features and 3D unions for friction ribs and internal ribs.
// ============================================================================
module spa_headrest() {
    difference() {
        union() {
            // Single extrusion of shell cross-section
            linear_extrude(rest_width)
                shell_2d();
            // Friction ribs on clip arm inner surfaces
            friction_ribs();
        }
        // Drain slots in clip arms
        drain_slots();
        // Drain holes in rest body bottom
        drain_holes();
    }
    // Internal structural ribs
    internal_ribs();
}

// ============================================================================
// RENDER — rotate to print orientation
// After extrude: X=depth, Y=height, Z=width
// Print orientation: rotate so Y->Z (height = vertical up)
//   rotate([90,0,0]): X->X, Y->-Z, Z->Y  ->  then translate Y by +rest_width
// Result: X=depth, Y=width(0..250), Z=height(0..~117), base at Z=0
// ============================================================================
translate([0, rest_width, 0])
    rotate([90, 0, 0])
        spa_headrest();
