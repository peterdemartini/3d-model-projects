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
slot_chamfer      = 2;       // entry flare on gap opening (mm)
fric_rib_h        = 0.4;     // friction rib height (mm)
fric_rib_spacing  = 2;       // friction rib center-to-center (mm)
fric_rib_w        = 1.0;     // friction rib width (mm)

// ── Curvature ───────────────────────────────────────────────────────────────
slot_arc_radius   = 1066.8;  // 7' diameter / 2 (mm)

// ── Pad parameters (reduced from v001) ──────────────────────────────────────
pad_width         = 200;     // width along tile edge — Z axis (mm) — was 250
pad_height        = 150;     // total pad height — Y axis (mm) — was 200
pad_depth         = 55;      // depth from back wall to front baseline — X axis (mm) — was 80
corner_radius     = 30;      // outer profile corner radius (mm) — was 40

// ── Contour parameters ─────────────────────────────────────────────────────
head_bulge        = 10;      // head region convex bump (mm)
neck_dip          = 10;      // neck region concave dip (mm) — was 12
head_center_frac  = 0.30;    // head bump center as fraction of pad_height
neck_center_frac  = 0.60;    // neck dip center as fraction of pad_height
head_sigma_frac   = 0.18;    // head Gaussian spread fraction
neck_sigma_frac   = 0.15;    // neck Gaussian spread fraction

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

// Sagitta for curvature positioning
sagitta = slot_arc_radius - sqrt(slot_arc_radius * slot_arc_radius
          - (pad_width / 2) * (pad_width / 2));

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
// Rounded rectangle with contoured front surface
// Back wall at X = slot_depth, contoured front, Y from 0 to pad_height
// ============================================================================
module pad_profile_2d() {
    steps = 80;
    eps = 0.1;

    // Front contour points
    front_pts = [
        for (i = [0:steps])
            let(y = i * pad_height / steps)
            [contour_x(y), y]
    ];

    // Build profile with rounded corners using offset
    offset(r = corner_radius)
    offset(delta = -corner_radius)
    polygon(concat(
        [[slot_depth, 0]],
        front_pts,
        [[slot_depth, pad_height]]
    ));
}

// ============================================================================
// MODULE: slot_2d — C-shape slot cross-section
// Bottom arm extends to slot_depth, top arm extends to slot_depth
// ============================================================================
module slot_2d() {
    eps = 0.1;

    // Spine + two arms forming C-shape
    polygon([
        [0, slot_y_start - eps],                     // spine bottom (with eps overlap)
        [slot_depth, slot_y_start - eps],             // bottom arm outer
        [slot_depth, slot_y_end + eps],               // top arm outer
        [0, slot_y_end + eps],                        // spine top (with eps overlap)
        [0, top_inner_y],                             // spine at gap top
        [slot_depth, top_inner_y],                    // top arm inner tip
        [slot_depth, bot_inner_y],                    // bottom arm inner tip
        [0, bot_inner_y]                              // spine at gap bottom
    ]);
}

// ============================================================================
// MODULE: slot_chamfers_2d — entry chamfers subtracted from slot_2d
// 45-degree bevels at arm tips for easy tile insertion
// ============================================================================
module slot_chamfers_2d() {
    // Bottom arm chamfer (at tip, bottom-inner corner)
    polygon([
        [slot_depth, bot_inner_y],
        [slot_depth, bot_inner_y - slot_chamfer],
        [slot_depth - slot_chamfer, bot_inner_y]
    ]);

    // Top arm chamfer (at tip, top-inner corner)
    polygon([
        [slot_depth, top_inner_y],
        [slot_depth, top_inner_y + slot_chamfer],
        [slot_depth - slot_chamfer, top_inner_y]
    ]);
}

// ============================================================================
// MODULE: triangle_top_2d — triangular gusset above slot, connecting to pad
// ============================================================================
module triangle_top_2d() {
    eps = 0.1;
    polygon([
        [slot_depth - eps, slot_y_end - eps],         // slot arm outer top
        [slot_depth - eps, slot_y_end + (pad_height - slot_y_end) / 2],  // pad body
        [slot_arm_thick, slot_y_end - eps]            // near spine
    ]);
}

// ============================================================================
// MODULE: triangle_bot_2d — triangular gusset below slot, connecting to pad
// ============================================================================
module triangle_bot_2d() {
    eps = 0.1;
    polygon([
        [slot_depth - eps, slot_y_start + eps],       // slot arm outer bottom
        [slot_depth - eps, slot_y_start - slot_y_start / 2],  // pad body
        [slot_arm_thick, slot_y_start + eps]          // near spine
    ]);
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
        if (x + fric_rib_w <= slot_depth - slot_chamfer) {
            translate([x, bot_inner_y, 0])
                cube([fric_rib_w, fric_rib_h, pad_width]);
        }
    }

    // Top arm ribs (protrude downward into gap, facing tile)
    num_top = floor((slot_depth - slot_arm_thick) / fric_rib_spacing);
    for (i = [1:num_top]) {
        x = slot_arm_thick + i * fric_rib_spacing;
        if (x + fric_rib_w <= slot_depth - slot_chamfer) {
            translate([x, top_inner_y - fric_rib_h, 0])
                cube([fric_rib_w, fric_rib_h, pad_width]);
        }
    }
}

// ============================================================================
// MODULE: curvature_cylinder — the large cylinder representing tile curvature
// Shared geometry used by curved_slot_3d, curved_gussets_3d, curved_friction_ribs
// Cylinder axis along Y (height), positioned so surface is tangent to slot
// back face at Z = pad_width/2
// ============================================================================
module curvature_cylinder() {
    translate([-slot_depth + slot_arc_radius - sagitta, 0, pad_width / 2])
        rotate([90, 0, 0])
            translate([0, 0, -(pad_height + 50)])
                cylinder(r = slot_arc_radius, h = pad_height + 100, $fa = 0.5);
}

// ============================================================================
// MODULE: curved_slot_3d — slot trimmed to follow tile arc curvature
// Intersects straight slot extrusion with curvature cylinder
// ============================================================================
module curved_slot_3d() {
    intersection() {
        // Straight extrusion of slot profile (with chamfers removed)
        translate([0, 0, -1])
            linear_extrude(pad_width + 2)
                difference() {
                    slot_2d();
                    slot_chamfers_2d();
                }

        // Curvature cylinder
        curvature_cylinder();
    }
}

// ============================================================================
// MODULE: curved_gussets_3d — triangular gussets trimmed to follow tile arc
// ============================================================================
module curved_gussets_3d() {
    intersection() {
        translate([0, 0, -1])
            linear_extrude(pad_width + 2) {
                triangle_top_2d();
                triangle_bot_2d();
            }

        // Same curvature cylinder
        curvature_cylinder();
    }
}

// ============================================================================
// MODULE: curved_friction_ribs — friction ribs trimmed to follow tile arc
// ============================================================================
module curved_friction_ribs() {
    intersection() {
        friction_ribs();

        // Same curvature cylinder
        curvature_cylinder();
    }
}

// ============================================================================
// MODULE: spa_headrest — complete 3D assembly
// Solid pad body with curved slot, gussets, and friction ribs
// No inner cavity — body is completely solid for clean printing
// ============================================================================
module spa_headrest() {
    union() {
        // Solid pad body with drain holes only
        difference() {
            linear_extrude(pad_width)
                pad_profile_2d();
            // Drain holes through full solid depth
            drain_holes();
        }
        // Curved slot with chamfers
        curved_slot_3d();
        // Curved triangular gussets
        curved_gussets_3d();
        // Curved friction ribs
        curved_friction_ribs();
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
