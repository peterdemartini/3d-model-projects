# PLAN.md — Spa Headrest 3D Model

Persistent specification document. **Update this file with every iteration** that
changes dimensions, tolerances, or design decisions. Keep the iteration log current.

---

## Model Identity

| Field           | Value                                           |
|-----------------|-------------------------------------------------|
| Model name      | `spa_headrest`                                  |
| Current version | `002`                                           |
| Source file     | `models/spa_headrest/spa_headrest_002.scad`     |
| Output dir      | `models/spa_headrest/output/`                   |

---

## Design Intent

Solid-body spa headrest with curved tile slot for 7' diameter spa wall, printed
flat in PETG. v2 redesign addressing v1 spaghetti (hollow interior), flat slot,
and oversized profile.

---

## Overall Dimensions

| Parameter              | Value   |
|------------------------|---------|
| Pad width (Z axis)     | 200 mm  |
| Pad height (Y axis)    | 150 mm  |
| Pad depth (X axis)     | 55 mm   |
| Corner radius          | 30 mm   |

---

## Slot Parameters

| Parameter              | Value                                        |
|------------------------|----------------------------------------------|
| Slot gap               | 29.0 mm (0.32 mm interference on 29.32 mm tile) |
| Slot depth             | 40 mm                                        |
| Slot arm thickness     | 5 mm                                         |
| Slot curvature radius  | 1066.8 mm (7' diameter / 2)                  |
| Sagitta over 200 mm width | ~4.7 mm                                   |
| Slot chamfer           | 2 mm                                         |
| Friction rib height    | 0.4 mm                                       |
| Friction rib spacing   | 2 mm center-to-center                        |
| Friction rib width     | 1.0 mm                                       |

---

## Contour Parameters

| Parameter              | Value                |
|------------------------|----------------------|
| Head bulge             | +10 mm               |
| Neck dip               | -10 mm               |
| Head center fraction   | 0.30 (from top)      |
| Neck center fraction   | 0.60 (from top)      |
| Head sigma fraction    | 0.18                 |
| Neck sigma fraction    | 0.15                 |

---

## Body Style

Solid (no interior cavity; slicer handles infill at 15% gyroid). This eliminates
the v1 spaghetti problem caused by the hollow shell.

---

## Drainage

3 x 8 mm holes at bottom of pad body.

---

## Material

PETG (240C nozzle, 70C bed)

---

## Print Orientation

`rotate([90, 0, 0])` -- pad bottom on bed, slot extending backward. All
overhangs <45 degrees.

---

## Iteration Log

| Version | Date       | Changes                                             |
|---------|------------|-----------------------------------------------------|
| 001     | 2026-03-06 | Initial design (branch `claude/trusting-lalande`). Issues: spaghetti from hollow interior, flat slot doesn't match curved tile, 80 mm depth too thick. |
| 002     | 2026-03-17 | Redesign -- solid body, curved slot (R=1066.8 mm), reduced dimensions (200x150x55 mm), looser slot fit (29.0 mm gap). Validated: 1580 faces, 790 vertices, 2,547 cm³, watertight, 104.8 × 200.0 × 150.0 mm. |

---

## Known Issues / Watch Items

- Rounded top corners produce 8.7% overhanging faces (WARN, below 10% threshold)
- Slot curvature is in subtracted gap — not validatable from external mesh
- Curvature approximated with 20 hull-connected slices (smooth enough for 4.7mm sagitta)
- Print time estimate: ~6-8h at 15% gyroid infill
