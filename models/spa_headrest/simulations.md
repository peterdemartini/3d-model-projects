# Spa Headrest — Validation Simulations

Documents every step of the validation pipeline with the expected outcome for
each iteration. Update the **Actual** column after running each check and note
any deviations from expectation.

---

## Validation Pipeline

```
/openscad  ->  /preview-scad  ->  /export-stl  ->  python scripts/validate.py
```

---

## v002 — Solid Body Redesign

---

### Step 1: Export STL via `/export-stl` Skill

Run from the repo root:

```bash
.claude/skills/export-stl/scripts/export-stl.sh \
  models/spa_headrest/spa_headrest_002.scad \
  --output models/spa_headrest/output/spa_headrest_002.stl
```

#### Expected Geometry Validation (from the skill's built-in checks)

| Check                | Expected  | Notes |
|----------------------|-----------|-------|
| Manifold (watertight)| PASSED    | Solid body, no open edges |
| Self-intersecting    | PASSED    | `union()` used for all joins |
| Degenerate faces     | PASSED    | High `$fa` on curved slot cylinder |
| Export file created  | PASSED    | |

Expected: manifold geometry, no self-intersections, no degenerate faces.

---

### Step 2: Full Validator Checks

```bash
python3 scripts/validate.py models/spa_headrest/output/spa_headrest_002.stl --skip-wall-thickness
```

#### Check-by-Check Expected Outcomes

| #  | Check              | Expected  | Notes |
|----|--------------------|-----------|-------|
| 1  | file_exists        | PASS      | `output/spa_headrest_002.stl` |
| 2  | supported_format   | PASS      | `.stl` format |
| 3  | loadable           | PASS      | Standard STL mesh |
| 4  | non_empty          | PASS      | Solid body mesh |
| 5  | watertight         | PASS      | Manifold, no open edges |
| 6  | build_volume       | PASS      | ~95 x 200 x 150 mm fits 350x320x325 |
| 7  | positive_volume    | PASS      | Correct normals |
| 8  | no_degenerate_faces| PASS      | Clean geometry |
| 9  | wall_thickness     | SKIP      | Skipped; solid body with 55 mm depth |
| 10 | base_on_bed        | PASS      | Z=0 at base |

#### Spa-Headrest Specific Checks

| #  | Check              | Expected  | Notes |
|----|--------------------|-----------|-------|
| 11 | slot_curvature     | PASS      | Sagitta ~4.7 mm matches R=1066.8 mm |
| 12 | max_profile_depth  | PASS      | Depth <= 57 mm (55 mm + 2 mm tolerance) |
| 13 | no_trapped_volumes | PASS      | Single watertight body |
| 14 | max_overhang_angle | PASS      | <5% faces exceed 45 degrees |

---

### Step 3: Visual Checks via `/preview-scad`

Render and inspect after every version. Run from the repo root:

```bash
.claude/skills/preview-scad/scripts/render-scad.sh \
  models/spa_headrest/spa_headrest_002.scad \
  --output models/spa_headrest/output/spa_headrest_002_preview.png \
  --size 1200x900 \
  --render
```

Then read the generated PNG image to verify all items in the checklist below.

#### Visual Checklist

- [ ] Overall shape matches design (compact, no hollow interior visible)
- [ ] Slot curvature visible in top-down view
- [ ] Contoured front face (head bulge, neck dip)
- [ ] Drain holes visible at bottom
- [ ] Friction ribs on slot inner surfaces
- [ ] Triangular gussets connecting slot to pad body
- [ ] Rounded top corners (30 mm radius)
- [ ] Square bottom corners (for bed adhesion)

---

### Step 4: Curvature Verification (Mathematical)

Verify the curved slot geometry matches the 7' diameter spa wall:

| Check | Formula | Value | Pass? |
|-------|---------|-------|-------|
| Sagitta | R - sqrt(R^2 - (W/2)^2) | 1066.8 - sqrt(1066.8^2 - 100^2) = ~4.7 mm | Matches design |
| Interference fit | tile_thickness - slot_gap | 29.32 - 29.0 = 0.32 mm total = 0.16 mm compression per side | Within PETG flex |

---

### Physical Test Plan

- [ ] Print with PETG (240C / 70C)
- [ ] Verify tile fit (29.0 mm gap on 29.32 mm tile)
- [ ] Check friction rib grip
- [ ] Test head/neck comfort
- [ ] Verify structural integrity
- [ ] Check drainage function
- [ ] Verify flush fit against curved tile
