// ============================================================================
// Spa Headrest — v002
// Solid-body redesign with curved tile slot
// Material: PETG  |  Printer: Bambu Lab H2D
// ============================================================================
//
// Coordinate system (2D profile in XY, extruded along Z):
//   X = depth (0 at slot spine, positive toward person/spa interior)
//   Y = height (0 at pad bottom, positive upward)
//   Z = width (0 to pad_width, along tile edge)
//
// v002 changes from v001:
//   - Solid body (no inner cavity, no internal ribs)
//   - Curved slot following tile's 7' diameter arc (R=1066.8 mm)
//   - Reduced pad dimensions: 200×150×55 (was 250×200×80)
//   - Slot gap widened to 29.0 mm (was 28.8)
//   - Drain holes penetrate full solid depth
//
// After extrusion, rotate so Y->Z for print orientation (bottom on bed).
// ============================================================================

$fn = 64;

// ── Tile parameters ─────────────────────────────────────────────────────────
tile_thickness    = 29.32;   // measured tile thickness (mm)
tile_overhang     = 40;      // tile overhang into spa (mm)

// ── Slot parameters ─────────────────────────────────────────────────────────
slot_gap          = 29.0;    // clearance gap for tile (mm) — was 28.8
slot_depth        = 40;      // slot arm length from spine (mm)
slot_arm_thick    = 5;       // arm thickness (mm)
slot_fillet       = 5;       // fillet radius on slot entry edges (mm) — generous rounding
spine_thick       = 2;       // spine wall thickness connecting arms (mm) — minimum printable
fric_rib_h        = 0.4;     // friction rib height (mm)
fric_rib_spacing  = 2;       // friction rib center-to-center (mm)
fric_rib_w        = 1.0;     // friction rib width (mm)

// ── Curvature ───────────────────────────────────────────────────────────────
slot_arc_radius   = 1066.8;  // 7' diameter / 2 (mm)

// ── Pad parameters (reduced from v001) ──────────────────────────────────────
pad_width         = 200;     // width along tile edge — Z axis (mm) — was 250
pad_height        = 75;      // total pad height — Y axis (mm) — tight around slot, 18mm above/below
pad_depth         = 55;      // depth from back wall to front baseline — X axis (mm) — was 80
corner_radius     = 10;      // outer profile corner radius (mm) — proportional to 75mm height

// ── Contour parameters ─────────────────────────────────────────────────────
head_bulge        = 10;      // head region convex bump (mm)
neck_dip          = 10;      // neck region concave dip (mm) — was 12
head_center_frac  = 0.35;    // head bump center — tuned for 75mm pad
neck_center_frac  = 0.75;    // neck dip center — tuned for 75mm pad
head_sigma_frac   = 0.30;    // head Gaussian spread — wide for compact pad
neck_sigma_frac   = 0.25;    // neck Gaussian spread — wide for compact pad

// ── Drainage ────────────────────────────────────────────────────────────────
drain_hole_d      = 8;       // bottom drain hole diameter (mm)
drain_hole_n      = 3;       // number of bottom drain holes

// ── Derived ─────────────────────────────────────────────────────────────────
slot_total_h      = 2 * slot_arm_thick + slot_gap;  // total slot height
pad_below         = pad_height / 2;                  // pad below slot center
pad_above         = pad_height / 2;                  // pad above slot center
slot_y_start      = pad_below - slot_total_h / 2;    // Y where slot bottom arm begins
slot_y_end        = slot_y_start + slot_total_h;      // Y where slot top arm ends
bot_inner_y       = slot_y_start + slot_arm_thick;    // tile bottom surface Y
top_inner_y       = bot_inner_y + slot_gap;           // tile top surface Y

// Contour derived
head_center_y     = head_center_frac * pad_height;
neck_center_y     = neck_center_frac * pad_height;
head_sigma        = head_sigma_frac * pad_height;
neck_sigma        = neck_sigma_frac * pad_height;

// Sagitta: max arc deviation from flat at center of width
sagitta = slot_arc_radius - sqrt(slot_arc_radius * slot_arc_radius
          - (pad_width / 2) * (pad_width / 2));

// Function: X offset to follow tile arc at a given Z position
// Returns 0 at center, -sagitta at edges
function arc_dx(z) =
    let(dz = z - pad_width / 2)
    -slot_arc_radius + sqrt(slot_arc_radius * slot_arc_radius - dz * dz);

// ── Assertions ──────────────────────────────────────────────────────────────
assert(slot_depth <= tile_overhang, "Slot depth exceeds tile overhang");
assert(slot_y_start > 0, "Slot extends below pad bottom");
assert(slot_y_end < pad_height, "Slot extends above pad top");
assert(pad_width / 2 < slot_arc_radius, "Pad width exceeds arc diameter");
assert(slot_gap > 0, "Slot gap must be positive");
assert(corner_radius < pad_height / 2, "Corner radius too large for pad height");
assert(corner_radius < (pad_depth + head_bulge) / 2, "Corner radius too large for pad depth");

// ============================================================================
// FUNCTION: contour_x — front surface X position at a given Y height
// Two-Gaussian model: head bulge (convex) + neck dip (concave)
// ============================================================================
function contour_x(y) =
    slot_depth + pad_depth
    + head_bulge * exp(-pow((y - head_center_y) / head_sigma, 2))
    - neck_dip   * exp(-pow((y - neck_center_y) / neck_sigma, 2));

// ============================================================================
// MODULE: pad_profile_2d — solid outer 2D profile of the pad body
// Extends from X=0 (spine) to contoured front, includes slot arm area
// Back wall at X=0 (same as slot spine), contoured front, Y from 0 to pad_height
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

    // Top-right rounded corner: arc from 0deg to 90deg
    tr_cx = contour_x(contour_top_y) - corner_radius;
    tr_cy = contour_top_y;
    top_right_arc = [
        for (i = [0:corner_steps])
            let(a = 90 * i / corner_steps)
            [tr_cx + corner_radius * cos(a), tr_cy + corner_radius * sin(a)]
    ];

    // Top-left rounded corner: arc from 90deg to 180deg
    // Back edge is at X=0 (spine), so corner center at X=corner_radius
    tl_cx = corner_radius;
    tl_cy = pad_height - corner_radius;
    top_left_arc = [
        for (i = [0:corner_steps])
            let(a = 90 + 90 * i / corner_steps)
            [tl_cx + corner_radius * cos(a), tl_cy + corner_radius * sin(a)]
    ];

    // Back edge at X=0, bottom corners square
    polygon(concat(
        [[0, 0]],                                   // bottom-left (back at spine)
        [[contour_x(0), 0]],                        // bottom-right (front)
        front_pts,                                   // contour from bottom to top
        [[contour_x(contour_top_y), contour_top_y]], // explicit endpoint at arc join
        top_right_arc,                               // top-right rounded corner
        top_left_arc                                 // top-left rounded corner
    ));
}

// ============================================================================
// MODULE: slot_gap_2d — the gap where the tile inserts (subtracted from body)
// Rectangle representing the open channel between the arms
// ============================================================================
module slot_gap_2d() {
    // The gap between the two arms, open to the right (toward person)
    // Extends from spine (X = spine_thick) to beyond slot_depth
    translate([spine_thick, bot_inner_y])
        square([slot_depth - spine_thick + 1, slot_gap]);
}

// ============================================================================
// MODULE: slot_fillets_2d — rounded entry fillets on slot mouth
// Quarter-circle arcs replace the old triangular chamfers
// ============================================================================
module slot_fillets_2d() {
    r = slot_fillet;
    fillet_steps = 8;

    // Bottom arm entry fillet (concave quarter-circle into gap)
    translate([slot_depth, bot_inner_y])
        polygon(concat(
            [for (i = [0:fillet_steps])
                let(a = 90 * i / fillet_steps)
                [-r + r * cos(a), -r * sin(a)]
            ],
            [[-r, 0]]
        ));

    // Top arm entry fillet (mirrored)
    translate([slot_depth, top_inner_y])
        polygon(concat(
            [for (i = [0:fillet_steps])
                let(a = 90 * i / fillet_steps)
                [-r + r * cos(a), r * sin(a)]
            ],
            [[-r, 0]]
        ));
}

// ============================================================================
// MODULE: drain_holes — cylindrical holes through solid pad bottom
// Full penetration through solid body
// ============================================================================
module drain_holes() {
    spacing = pad_width / (drain_hole_n + 1);
    hole_x = slot_depth + pad_depth / 2;  // centered in pad body depth

    for (i = [1:drain_hole_n]) {
        z = i * spacing;
        translate([hole_x, -1, z])
            rotate([-90, 0, 0])
                cylinder(d = drain_hole_d, h = pad_depth + 2);
    }
}

// ============================================================================
// MODULE: friction_ribs — small bumps on slot arm inner surfaces
// Ribs stop before the chamfer zone to avoid non-manifold edges
// ============================================================================
module friction_ribs() {
    // Bottom arm ribs (protrude upward into gap, facing tile)
    num_bot = floor((slot_depth - slot_arm_thick) / fric_rib_spacing);
    for (i = [1:num_bot]) {
        x = slot_arm_thick + i * fric_rib_spacing;
        if (x + fric_rib_w <= slot_depth - slot_fillet) {
            translate([x, bot_inner_y, 0])
                cube([fric_rib_w, fric_rib_h, pad_width]);
        }
    }

    // Top arm ribs (protrude downward into gap, facing tile)
    num_top = floor((slot_depth - slot_arm_thick) / fric_rib_spacing);
    for (i = [1:num_top]) {
        x = slot_arm_thick + i * fric_rib_spacing;
        if (x + fric_rib_w <= slot_depth - slot_fillet) {
            translate([x, top_inner_y - fric_rib_h, 0])
                cube([fric_rib_w, fric_rib_h, pad_width]);
        }
    }
}

// ============================================================================
// MODULE: curved_gap_3d — the slot gap carved out, following tile arc
// Built from hull-connected slices of the gap profile, shifted by arc_dx(z)
// ============================================================================
curve_slices = 20;  // number of slices for arc approximation

module curved_gap_3d() {
    for (i = [0:curve_slices-1]) {
        z0 = i * pad_width / curve_slices;
        z1 = (i + 1) * pad_width / curve_slices;
        hull() {
            translate([arc_dx(z0), 0, z0])
                linear_extrude(0.01)
                    union() { slot_gap_2d(); slot_fillets_2d(); }
            translate([arc_dx(z1), 0, z1])
                linear_extrude(0.01)
                    union() { slot_gap_2d(); slot_fillets_2d(); }
        }
    }
}

// ============================================================================
// MODULE: slot_external_fillets — round the exterior corners where slot
// arms meet the pad body. Subtracts quarter-cylinder notches from the
// outside of the slot opening, creating visible rounded transitions.
// ============================================================================
module slot_external_fillets() {
    r = slot_fillet;

    // Bottom arm — exterior bottom edge (where bottom arm meets pad below)
    translate([slot_depth, slot_y_start, -1])
        linear_extrude(pad_width + 2)
            difference() {
                square([r, r]);
                translate([0, r]) circle(r = r, $fn = 32);
            }

    // Top arm — exterior top edge (where top arm meets pad above)
    translate([slot_depth, slot_y_end - r, -1])
        linear_extrude(pad_width + 2)
            difference() {
                square([r, r]);
                translate([0, 0]) circle(r = r, $fn = 32);
            }
}

// ============================================================================
// MODULE: spa_headrest — complete 3D assembly
// Solid pad body with curved slot, gussets, and friction ribs
// No inner cavity — body is completely solid for clean printing
// ============================================================================
module spa_headrest() {
    difference() {
        union() {
            // Solid body: pad profile extends from X=0 (spine) to contoured front
            // This single extrusion includes the slot arms and pad body as one piece
            linear_extrude(pad_width)
                pad_profile_2d();
            // Friction ribs on slot inner surfaces
            friction_ribs();
        }
        // Subtract the slot gap (curved to follow tile arc)
        curved_gap_3d();
        // Subtract external fillets at slot-to-body junction
        slot_external_fillets();
        // Subtract drain holes
        drain_holes();
    }
}

// ============================================================================
// RENDER — rotate to print orientation
// After extrude: X=depth, Y=height, Z=width
// Print orientation: rotate so Y->Z (height = vertical up)
//   rotate([90,0,0]): X->X, Y->-Z, Z->Y  ->  then translate Y by +pad_width
// Result: X=depth, Y=width(0..200), Z=height(0..~150), base at Z=0
// ============================================================================
translate([slot_depth, pad_width, 0])
    rotate([90, 0, 0])
        spa_headrest();
