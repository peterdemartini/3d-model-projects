// ============================================================================
// Spa Head & Neck Rest — v002
// Clips onto overhanging spa tile, provides contoured neck + head support
// Material: PETG  |  Printer: Bambu Lab H2D
// ============================================================================
//
// Coordinate system (2D profile in XY, extruded along Z):
//   X = depth (0 at clip spine, positive toward person/spa interior)
//   Y = height (0 at rest bottom, positive upward)
//   Z = width (0 to rest_width, along tile edge)
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
rest_height       = 160;     // vertical height — Y axis (mm)
rest_depth        = 80;      // depth from back wall to front baseline — X axis (mm)
wall_thick        = 6;       // shell wall thickness (mm) — v002: was 4, thicker for print reliability

// ── Contour parameters ──────────────────────────────────────────────────────
neck_zone_h       = 55;      // neck roll zone height (mm)
neck_bump         = 15;      // peak of neck roll convex bump (mm)
head_zone_h       = 105;     // head cradle zone height (mm)
head_recess       = 8;       // depth of head concave recess (mm)

// ── Drainage ────────────────────────────────────────────────────────────────
drain_slot_w      = 8;       // clip drain slot width in X (mm)
drain_slot_l      = 20;      // clip drain slot length in Z (mm)
drain_slot_n      = 4;       // number of clip drain slots
drain_hole_d      = 8;       // bottom drain hole diameter (mm)
drain_hole_n      = 3;       // number of bottom drain holes

// ── Internal ribs ───────────────────────────────────────────────────────────
int_rib_n         = 5;       // number of internal structural ribs — v002: was 3, closer spacing for stability
int_rib_t         = 3;       // internal rib thickness in Z (mm)

// ── Derived ─────────────────────────────────────────────────────────────────
back_x            = clip_bot_arm;              // rest body back wall X position
front_x           = clip_bot_arm + rest_depth; // rest body front baseline X
clip_total_h      = 2 * clip_arm_thick + clip_gap; // total clip height
model_height      = rest_height + clip_total_h;     // total model height (Y)

assert(clip_bot_arm <= tile_overhang, "Bottom arm exceeds tile overhang");

// ── Contour centers ─────────────────────────────────────────────────────────
neck_center_y     = neck_zone_h * 0.5;                    // 27.5 mm
head_center_y     = neck_zone_h + head_zone_h * 0.5;      // 107.5 mm
neck_sigma        = neck_zone_h * 0.35;                    // 19.25 mm
head_sigma        = head_zone_h * 0.35;                    // 36.75 mm

// ============================================================================
// FUNCTION: contour X position at a given Y height
// ============================================================================
function contour_x(y) =
    front_x
    + neck_bump * exp(-pow((y - neck_center_y) / neck_sigma, 2))
    - head_recess * exp(-pow((y - head_center_y) / head_sigma, 2));

// ============================================================================
// MODULE: rest_body_2d — solid 2D profile of rest body
// Back wall at X=back_x, contoured front, Y from 0 to rest_height
// ============================================================================
module rest_body_2d() {
    steps = 80;
    front_pts = [
        for (i = [0:steps])
            let(y = i * rest_height / steps)
            [contour_x(y), y]
    ];
    // Polygon: back-bottom → front-bottom → contour up → front-top → back-top
    polygon(concat(
        [[back_x, 0]],                    // back-bottom
        front_pts,                         // contour from bottom to top
        [[back_x, rest_height]]            // back-top
    ));
}

// ============================================================================
// MODULE: clip_2d — C-shaped clip (union of 3 rectangles)
// Spine at X=0, arms extend rightward, gap opens to the right
// ============================================================================
module clip_2d() {
    bot_arm_y = rest_height;
    top_arm_y = rest_height + clip_arm_thick + clip_gap;

    // Bottom arm
    translate([0, bot_arm_y])
        square([clip_bot_arm, clip_arm_thick]);

    // Top arm
    translate([0, top_arm_y])
        square([clip_top_arm, clip_arm_thick]);

    // Spine (vertical connector at X=0)
    translate([0, bot_arm_y])
        square([clip_arm_thick, clip_total_h]);
}

// ============================================================================
// MODULE: support_brace_2d — 45° brace for printability
// Connects rest body back wall to clip spine so bottom arm prints without support
// ============================================================================
module support_brace_2d() {
    brace_drop = clip_bot_arm - clip_arm_thick; // 26mm below rest_height
    polygon([
        [back_x, rest_height],                  // back wall at top of rest
        [clip_arm_thick, rest_height],           // spine right edge
        [back_x, rest_height - brace_drop]       // back wall, 26mm below top
    ]);
}

// ============================================================================
// MODULE: full_solid_2d — union of rest body + clip + brace
// ============================================================================
module full_solid_2d() {
    union() {
        rest_body_2d();
        clip_2d();
        support_brace_2d();
    }
}

// ============================================================================
// MODULE: entry_chamfers_2d — chamfer cuts at clip gap opening
// ============================================================================
module entry_chamfers_2d() {
    bot_inner_y = rest_height + clip_arm_thick;
    top_inner_y = rest_height + clip_arm_thick + clip_gap;

    // Bottom arm chamfer (top-right corner of bottom arm)
    translate([clip_bot_arm - clip_chamfer, bot_inner_y - clip_chamfer])
        polygon([
            [0, 0],
            [clip_chamfer, 0],
            [clip_chamfer, clip_chamfer]
        ]);

    // Top arm chamfer (bottom-right corner of top arm)
    translate([clip_top_arm - clip_chamfer, top_inner_y])
        polygon([
            [0, clip_chamfer],
            [clip_chamfer, 0],
            [clip_chamfer, clip_chamfer]
        ]);
}

// ============================================================================
// MODULE: shell_2d — hollowed rest body + solid clip
// ============================================================================
module shell_2d() {
    difference() {
        full_solid_2d();
        // Hollow out rest body only (clip stays solid)
        offset(r = -wall_thick)
            rest_body_2d();
        // Chamfer the gap entrance
        entry_chamfers_2d();
    }
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
        translate([slot_x_bot, rest_height - 1, z])
            cube([drain_slot_w, clip_arm_thick + 2, drain_slot_l]);
        // Through top arm
        translate([slot_x_top, rest_height + clip_arm_thick + clip_gap - 1, z])
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
// ============================================================================
module friction_ribs() {
    bot_inner_y = rest_height + clip_arm_thick;
    top_inner_y = rest_height + clip_arm_thick + clip_gap;

    // Bottom arm ribs (protrude upward into gap, facing tile)
    num_bot = floor((clip_bot_arm - 4) / fric_rib_spacing);
    for (i = [1:num_bot]) {
        x = clip_arm_thick + i * fric_rib_spacing;
        if (x + fric_rib_w <= clip_bot_arm) {
            translate([x, bot_inner_y, 0])
                cube([fric_rib_w, fric_rib_h, rest_width]);
        }
    }

    // Top arm ribs (protrude downward into gap, facing tile)
    num_top = floor((clip_top_arm - 4) / fric_rib_spacing);
    for (i = [1:num_top]) {
        x = clip_arm_thick + i * fric_rib_spacing;
        if (x + fric_rib_w <= clip_top_arm) {
            translate([x, top_inner_y - fric_rib_h, 0])
                cube([fric_rib_w, fric_rib_h, rest_width]);
        }
    }
}

// ============================================================================
// MODULE: internal_ribs — structural ribs across the width
// ============================================================================
module internal_ribs() {
    spacing = rest_width / (int_rib_n + 1);
    notch_w = drain_hole_d * 1.5;  // drainage notch width
    notch_h = wall_thick + 4;       // drainage notch height

    for (i = [1:int_rib_n]) {
        z = i * spacing - int_rib_t / 2;
        translate([0, 0, z])
            linear_extrude(int_rib_t)
                difference() {
                    offset(r = -wall_thick)
                        rest_body_2d();
                    // Drainage notch at bottom of rib
                    translate([back_x + rest_depth/2 - notch_w/2, 0])
                        square([notch_w, notch_h]);
                }
    }
}

// ============================================================================
// MODULE: head_zone_ties — horizontal tie ribs in the head cradle zone
// Connects back wall to contoured front at critical heights to prevent
// spaghetti failure from unsupported thin walls in the concave recess.
// ============================================================================
module head_zone_ties() {
    tie_ys = [90, 120, 150];   // Y positions spanning head cradle zone

    for (ty = tie_ys) {
        translate([0, 0, 0])
            linear_extrude(rest_width)
                intersection() {
                    offset(r = -wall_thick)
                        rest_body_2d();
                    // Horizontal slab at this Y height
                    translate([back_x, ty])
                        square([rest_depth, int_rib_t]);
                }
    }
}

// ============================================================================
// MODULE: spa_headrest — complete 3D assembly
// ============================================================================
module spa_headrest() {
    // Main shell + clip
    difference() {
        union() {
            // Extruded shell
            linear_extrude(rest_width)
                shell_2d();
            // Friction ribs
            friction_ribs();
        }
        // Drain slots in clip arms
        drain_slots();
        // Drain holes in rest body bottom
        drain_holes();
    }
    // Internal structural ribs
    internal_ribs();
    // Horizontal tie ribs in head cradle zone (v002 — anti-spaghetti)
    head_zone_ties();
}

// ============================================================================
// RENDER — rotate to print orientation
// After extrude: X=depth, Y=height, Z=width
// Print orientation: rotate so Y→Z (height = vertical up)
//   rotate([90,0,0]): X→X, Y→-Z, Z→Y  →  then translate Y by +rest_width
// Result: X=depth, Y=width(0..250), Z=height(0..~197), base at Z=0
// ============================================================================
translate([0, rest_width, 0])
    rotate([90, 0, 0])
        spa_headrest();
