# simulations.md — Spa Headrest Validation Steps

Documents every step of the validation pipeline with the expected outcome for
each iteration. Update the **Actual** column after running each check and note
any deviations from expectation.

---

## Validation Pipeline

```
/openscad  →  /preview-scad  →  /export-stl  →  python scripts/validate.py
```

---

## Step 1: Export STL via `/export-stl` Skill

Run from the repo root:

```bash
.claude/skills/export-stl/scripts/export-stl.sh \
  models/spa_headrest/spa_headrest_001.scad \
  --output models/spa_headrest/output/spa_headrest_001.stl
```

### Expected Geometry Validation (from the skill's built-in checks)

| Check                | Expected v002 | Notes |
|----------------------|---------------|-------|
| Manifold (watertight)| PASSED        | Shell + solid clip, no open edges |
| Self-intersecting    | PASSED        | `union()` used for all joins |
| Degenerate faces     | PASSED        | `$fn = 64` on all cylinders |
| Export file created  | PASSED        | |

**Fix strategy if non-manifold:**
1. Check that `offset(r = -wall_thick)` on `rest_body_2d()` produces a valid
   inner shell (no self-intersections from tight concave regions).
2. Verify drain hole cylinders fully penetrate the wall (add 2 mm overshoot).
3. Ensure internal ribs don't create T-junction edges with the shell.

---

## Step 2: Full Validator — `scripts/validate.py`

```bash
python scripts/validate.py models/spa_headrest/output/spa_headrest_001.stl
```

### Check-by-Check Expected Outcomes

---

#### Check 1: `file_exists`

| Field           | Value |
|-----------------|-------|
| Severity        | FAIL  |
| Expected        | **PASS** |
| Condition       | File must exist after Step 1 export |
| Message pattern | `File found and readable: models/spa_headrest/output/spa_headrest_001.stl` |
| If FAIL         | Re-run the `/export-stl` skill; confirm `--output` path is correct |

---

#### Check 2: `supported_format`

| Field           | Value |
|-----------------|-------|
| Severity        | FAIL  |
| Expected        | **PASS** |
| Condition       | Extension `.stl` is in the supported set |
| Message pattern | `Extension '.stl' is supported by BambuStudio` |
| If FAIL         | Check filename extension |

---

#### Check 3: `loadable`

| Field           | Value |
|-----------------|-------|
| Severity        | FAIL  |
| Expected        | **PASS** |
| Condition       | trimesh can parse the binary STL |
| Message pattern | `Mesh loaded successfully` |
| If FAIL         | STL is corrupt; re-export with `--ascii` flag to inspect |

---

#### Check 4: `non_empty`

| Field           | Value |
|-----------------|-------|
| Severity        | FAIL  |
| Expected        | **PASS** |
| Face count      | Expect ~4,000-7,000 faces (thicker shell + 5 ribs + head ties + drains) |
| Message pattern | `Mesh has N faces and M vertices` |
| If FAIL         | Check for `difference()` that removes all geometry |

---

#### Check 5: `watertight`

| Field           | Value |
|-----------------|-------|
| Severity        | FAIL  |
| Expected        | **PASS** |
| Message pattern | `Mesh is watertight (manifold)` |
| Target          | `open_edge_count` = 0 |

**Notes:** The spa headrest uses simple shell geometry (2D profile extruded,
then hollowed via `offset`). No hinge or articulated parts, so watertight
should pass on first export.

**Fix approach if FAIL:**
- Check that `offset(r = -wall_thick)` doesn't create self-intersecting inner
  profile (especially near the neck bump convex region)
- Ensure drain holes don't create non-manifold edges at tangent intersections
- Verify internal ribs are fully contained within the shell volume

---

#### Check 6: `build_volume`

| Field           | Value |
|-----------------|-------|
| Severity        | FAIL  |
| Expected        | **PASS** |
| Model dims      | ~128 x 250.0 x 197 mm (v002: slightly deeper due to 6mm walls) |
| H2D build volume| 350 x 320 x 325 mm |
| Margins         | X: 225 mm spare; Y: 70 mm spare; Z: 128 mm spare |
| Message pattern | `Model dimensions (124.x x 250.x x 196.x mm) fit within build volume (350 x 320 x 325 mm)` |
| If FAIL on X    | Reduce `rest_depth` parameter |
| If FAIL on Y    | Reduce `rest_width` parameter |
| If FAIL on Z    | Reduce `rest_height` or clip arm thickness |

---

#### Check 7: `positive_volume`

| Field           | Value |
|-----------------|-------|
| Severity        | WARN  |
| Expected        | **PASS** |
| Volume range    | 300,000-800,000 mm³ (hollow shell with 6mm walls + head ties) |
| Message pattern | `Volume = N mm³ (normals look correct)` |
| If WARN (negative) | Normals inverted — run `trimesh.repair.fix_normals(mesh)` |

---

#### Check 8: `no_degenerate_faces`

| Field           | Value |
|-----------------|-------|
| Severity        | WARN  |
| Expected        | **PASS** |
| Condition       | No zero-area triangles |
| Message pattern | `No zero-area (degenerate) faces found` |
| If WARN         | Increase `$fn` on drain hole cylinders; check for zero-thickness geometry at contour extremes |

---

#### Check 9: `wall_thickness`

| Field           | Value |
|-----------------|-------|
| Severity        | WARN  |
| Expected        | **PASS** or SKIP |
| Design wall     | 6 mm throughout (shell walls, clip arms 4 mm) |
| Message pattern | `Minimum sampled wall thickness >= 4.0 mm` |
| Is this blocking? | **No** — WARN does not prevent slicing |
| Escalate if     | Minimum drops below 2 mm — check shell offset geometry |
| Skip option     | `python scripts/validate.py ... --skip-wall-thickness` if rtree not installed |

---

### Overall Result Summary Per Iteration

| Version | `watertight` | `build_volume` | `wall_thickness` | **Overall** | Print-ready? |
|---------|-------------|----------------|------------------|-------------|--------------|
| 001     | **PASS**    | PASS           | SKIP (no rtree)  | **PASS**    | **Yes** (spaghetti at 2/3 height) |
| 002     | **TBD**     | TBD            | TBD              | **TBD**     | TBD          |

Model is considered **print-ready** when:
- No FAIL checks remain
- `watertight` = PASS
- Remaining WARNs are acceptable design choices

**v001 achieved PASS on all critical checks** — the simple extruded shell
design avoids the non-manifold issues common in articulated models. The
`wall_thickness` check was skipped due to missing rtree dependency but the
design uses 4mm walls throughout, well above the 0.8mm advisory threshold.

---

## Step 3: Visual Checks via `/preview-scad`

Render and inspect after every version. Run from the repo root:

```bash
.claude/skills/preview-scad/scripts/render-scad.sh \
  models/spa_headrest/spa_headrest_001.scad \
  --output models/spa_headrest/spa_headrest_001.png \
  --size 1200x900 \
  --render
```

Then read the generated PNG image to verify all items in the checklist below.

### Visual Checklist

| # | Feature            | Expected                                              | Pass Criteria |
|---|--------------------|-------------------------------------------------------|---------------|
| V1 | Overall shape     | Elongated shell with C-clip at top                    | Rest body and clip clearly distinguishable |
| V2 | Clip C-shape      | Three-part clip: spine, top arm (15mm), bottom arm (30mm) | C-shape visible with gap for tile |
| V3 | Contoured front   | Convex neck roll (lower), concave head area (upper)   | Visible curvature change on front face |
| V4 | Shell thickness   | Hollow interior visible from ends                     | 6mm walls visible at top/bottom openings |
| V5 | Internal ribs     | 5 evenly-spaced vertical ribs                         | Ribs visible through shell openings or in cutaway |
| V5b| Head zone ties    | 3 horizontal ribs in head cradle zone                 | Horizontal slabs at Y=90, 120, 150 mm |
| V6 | Drain slots       | 4 rectangular slots in clip arms                      | Slots visible on bottom arm |
| V7 | Drain holes       | 3 circular holes at rest bottom                       | Holes visible on bottom face |
| V8 | Friction ribs     | Small bumps on inner clip surfaces                    | May not be visible at default zoom |
| V9 | Support brace     | 45° triangle connecting back wall to clip spine       | Triangular brace visible between rest body and clip |
| V10 | Print orientation | Back wall (tile-facing) flat on print bed (Z=0)       | Model sits flat with clip at top |

### Recommended Camera Angles

```bash
# Default overview (auto-centered) — start here
# (no --camera flag, relies on --viewall --autocenter)

# Side view (contour profile visible)
--camera 0,125,100,60,125,100,400

# Front view (concave/convex contour)
--camera 200,125,100,60,125,100,400

# Top-down (clip C-shape and drain slots)
--camera 60,125,300,60,125,100,400

# End view (shell cross-section, internal ribs)
--camera 60,0,100,60,125,100,500
```

---

## Step 4: Dimensional Verification

Verify key dimensions match design parameters:

| Dimension          | Expected (mm) | Actual v001 (mm) | v002 Expected (mm) |
|--------------------|---------------|-------------------|--------------------|
| Total width (Y)    | 250.0         | 250.0             | 250.0              |
| Total height (Z)   | 196.8         | 196.8             | ~197               |
| Total depth (X)    | 124.9         | 124.9             | ~128 (6mm walls)   |
| Clip gap           | 28.8          | 28.8              | 28.8               |
| Rest height        | 160.0         | 160.0             | 160.0              |
| Wall thickness     | 4.0           | 4.0 (design)      | 6.0                |

Height breakdown:
- Rest body: 160 mm
- Bottom clip arm: 4 mm
- Clip gap: 28.8 mm
- Top clip arm: 4 mm
- Total clip: 36.8 mm
- **Total: 196.8 mm**

---

## Step 5: Clip Fit Verification

Verify the clip will fit the tile correctly:

| Check               | Formula / Value                          | Result     | Pass? |
|----------------------|------------------------------------------|------------|-------|
| Tile fits in gap     | clip_gap (28.8) < tile_thickness (29.32) | 0.52mm interference | PASS — friction fit |
| Interference per side| (29.32 - 28.8) / 2 = 0.26 mm            | 0.26 mm    | PASS — within PETG flex |
| Top arm reach        | 15 mm onto tile top                      | 15 mm      | PASS — sufficient grip |
| Bottom arm reach     | 30 mm under tile (≤ 40mm overhang)       | 30 mm      | PASS — within overhang |
| Friction ribs        | 0.4mm high, 2mm spacing                 | Present    | PASS — grip enhancement |

---

## CI Workflow Integration

The GitHub Actions `validate-models.yml` workflow detects single-color models
(like spa_headrest) by checking for `RENDER_COLOR` in the SCAD file. Since
spa_headrest does not use `RENDER_COLOR`, the CI pipeline:

1. Exports a plain STL (not multi-color 3MF)
2. Validates the STL with `scripts/validate.py`
3. Uploads the STL as a build artifact

This differs from multi-color models (like toy_laptop) which go through the
white/black export → merge → validate 3MF pipeline.

---

## Iteration Notes

Update this section after each version is validated.

### v001 — Initial export
- Date: 2026-03-06
- Design: C-clip headrest with contoured neck roll and head cradle
- Export: STL, 158 KB, 3,244 triangles
- Validation results:
  - `file_exists`: PASS
  - `supported_format`: PASS
  - `loadable`: PASS
  - `non_empty`: PASS — 3,244 faces
  - `watertight`: PASS — manifold, no open edges
  - `build_volume`: PASS — 124.9 x 250.0 x 196.8 mm (fits 350 x 320 x 325 mm)
  - `positive_volume`: PASS
  - `no_degenerate_faces`: PASS
  - `wall_thickness`: SKIP — rtree not installed (non-blocking)
  - `base_on_bed`: PASS — Z range 0.0 to 196.8 mm
- Visual checks: C-clip, contoured front face, internal ribs, drain features all visible
- Print readiness: **Yes** — all critical checks PASS
- Print result: **FAILED** — spaghetti at ~2/3 height (~131mm Z)
- Failure analysis: Thin 4mm walls in concave head recess + 62.5mm unsupported spans between 3 ribs + PETG slow cooling converged at the head cradle zone

### v002 — Print failure fix
- Date: 2026-03-08
- Changes:
  - `wall_thick`: 4 → 6 mm (thicker shell survives concave offset thinning)
  - `int_rib_n`: 3 → 5 (reduces unsupported span from 62.5mm to ~42mm)
  - Added `head_zone_ties()`: 3 horizontal tie ribs at Y=90, 120, 150mm connecting back wall to contoured front inside the hollow shell
  - Print settings tuned: 0.16mm layers, 235°C nozzle, 150mm/s max, 80mm/s outer walls, 12s min layer time, overhang slowdown enabled
- Next steps: Export STL, validate, re-print with updated settings
