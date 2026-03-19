# Spa Headrest — Session Context

Current spec and state for the spa headrest 3D model. Read this before making
any changes.

## Project

- **Repo:** `peterdemartini/3d-model-projects`
- **Model dir:** `models/spa_headrest/`
- **Source:** `spa_headrest_002.scad` (OpenSCAD)
- **Output:** `models/spa_headrest/output/` (STL is gitignored, meta.json and PNG are committed)
- **Printer:** Bambu Lab H2D (build volume 350 x 320 x 325 mm)
- **Material:** PETG (240C nozzle, 70C bed)

## What This Is

A solid-body headrest that clips onto a spa wall tile via a friction-fit slot.
The front face has an ergonomic Gaussian contour (convex at head, concave at
neck). The slot follows the tile wall's 7-foot diameter curvature.

## Current Dimensions (v002, as-built)

### Pad Body

| Parameter | Value | Notes |
|-----------|-------|-------|
| pad_width | 200 mm | Along tile edge (Z axis) |
| pad_height | 95 mm | Vertical (Y axis) |
| pad_depth | 55 mm | Front baseline depth (X axis) |
| corner_radius | 15 mm | Top corners rounded, bottom square |
| Body style | Solid | No interior cavity; slicer handles infill |

### Slot (Tile Clip)

| Parameter | Value | Notes |
|-----------|-------|-------|
| slot_gap | 29.0 mm | For 29.32 mm tile (0.32 mm interference) |
| slot_depth | 40 mm | Arm length from back |
| slot_arm_thick | 5 mm | Each arm |
| slot_fillet | 3 mm | Quarter-circle entry fillets |
| spine_thick | 3 mm | **Param exists but spine is fully removed** — gap cuts through to X=-1 |
| Slot curvature | R = 1066.8 mm | 7' diameter / 2, ~4.7 mm sagitta over 200 mm width |
| Friction ribs | 0.4 mm h, 2 mm spacing, 1.0 mm w | On both arm inner surfaces |

### Slot Placement (derived, centered vertically)

| Value | mm |
|-------|-----|
| slot_total_h | 39 (5 + 29 + 5) |
| slot_y_start | 28.0 |
| slot_y_end | 67.0 |
| bot_inner_y | 33.0 |
| top_inner_y | 62.0 |
| Material above slot | 28 mm |
| Material below slot | 28 mm |

### Contour (Ergonomic Front Face)

| Parameter | Value |
|-----------|-------|
| head_bulge | +10 mm |
| neck_dip | -10 mm |
| head_center_frac | 0.30 |
| neck_center_frac | 0.70 |
| head_sigma_frac | 0.22 |
| neck_sigma_frac | 0.18 |

### Drainage

3 x 8 mm holes at pad bottom, centered in pad body depth.

### Print Orientation

`rotate([90, 0, 0])` then translate — pad bottom on bed, slot extending
backward. Bounding box in print pose: ~105 x 200 x 95 mm.

## Architecture of the .scad File

The model uses a **subtraction approach**: a single solid pad body (linear
extrusion of `pad_profile_2d()`) with the slot gap carved out.

### Key Modules

| Module | Purpose |
|--------|---------|
| `contour_x(y)` | Two-Gaussian function for front surface X at height Y |
| `pad_profile_2d()` | Solid 2D profile from X=0 to contoured front, with manual corner arcs |
| `slot_gap_2d()` | Rectangle from X=-1 to X=slot_depth+1 at gap height — **no spine wall** |
| `slot_fillets_2d()` | Quarter-circle arcs at slot entry (replaces old triangular chamfers) |
| `friction_ribs()` | Small cubes on arm inner surfaces, stop before fillet zone |
| `curved_gap_3d()` | Hull-connected slices of gap profile shifted by `arc_dx(z)` for tile curvature |
| `drain_holes()` | Cylinders through pad bottom |
| `spa_headrest()` | Top-level: pad body + friction ribs, minus curved gap, minus drain holes |

### Curvature Implementation

The tile curvature is achieved by the `arc_dx(z)` function which returns an X
offset at each Z position along the width. The `curved_gap_3d()` module builds
the gap from 20 hull-connected slices, each translated by this offset. This
shifts the entire slot gap profile to follow the 7' diameter arc. The pad body
itself is a straight extrusion (flat back face); only the subtracted gap curves.

## Validation

Run with:
```bash
python3 scripts/validate.py models/spa_headrest/output/spa_headrest_002.stl --skip-wall-thickness
```

All standard checks pass. The spa-headrest-specific checks (in `.meta.json`)
validate profile depth, trapped volumes, and overhang angle. The overhang check
uses a 10% FAIL threshold (configurable in meta) because rounded corners
produce ~6-9% overhanging faces.

Export pipeline:
```
/openscad → /preview-scad → /export-stl → python scripts/validate.py
```

After export, always copy STL to `~/Downloads/`.

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| 001 | 2026-03-16 | Initial hollow-shell design. Issues: spaghetti filament from interior cavity, flat slot (no curvature), oversized (250x200x80 mm). Branch: `claude/trusting-lalande`. |
| 002 | 2026-03-17 | Full redesign: solid body, curved slot (R=1066.8 mm), reduced to 200x95x55 mm, slot gap widened to 29.0 mm, spine wall removed, 3 mm entry fillets, contour retuned. |

## Known Issues

- `spine_thick` parameter still exists in code (set to 3) but is unused — gap starts at X=-1
- PLAN.md is out of date (still shows v002 initial dimensions before defect fixes — pad_height=150, corner_radius=30)
- The `.scad` header comment still says "Reduced pad dimensions: 200x150x55" — should be 200x95x55
- Overhang WARN (6-9% faces) is expected from rounded corners — not a defect
- Slot curvature is in the subtracted gap, not measurable from external mesh vertices
- 2 degenerate faces occasionally appear in export (from hull slice boundaries) — harmless

## What Needs Doing Next

- Update PLAN.md to match actual current dimensions
- Update .scad header comment (150→95)
- Clean up unused `spine_thick` parameter
- Print and test-fit on actual spa tile
- Iterate based on physical test results
