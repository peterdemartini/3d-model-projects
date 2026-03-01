# simulations.md — Toy Laptop Validation Steps

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
  models/toy_laptop/toy_laptop_001.scad \
  --output models/toy_laptop/output/toy_laptop_001.stl
```

### Expected Geometry Validation (from the skill's built-in checks)

| Check                | Expected v001     | Expected final | Notes |
|----------------------|-------------------|----------------|-------|
| Manifold (watertight)| **WARNING**       | PASSED         | Hinge gap geometry creates open edges on first attempt |
| Self-intersecting    | PASSED            | PASSED         | `union()` used for all barrel/base joins |
| Degenerate faces     | PASSED            | PASSED         | Use `$fn ≥ 60` on all cylinders |
| Export file created  | PASSED            | PASSED         | |

If the skill reports `STATUS: PASSED` on first attempt, skip directly to Step 2.
If manifold warnings appear, see Fix Strategy below before proceeding.

**Fix strategy for non-manifold on v001:**
1. Ensure hinge bore `difference()` cuts fully through both mating bodies (add 1 mm
   overshoot on each side of the bore along the pin axis).
2. Use `hull()` transitions at barrel ends where the barrel joins the base/lid body.
3. Re-export and re-check. If still failing, run:
   ```python
   import trimesh
   mesh = trimesh.load("models/toy_laptop/output/toy_laptop_001.stl")
   trimesh.repair.fill_holes(mesh)
   trimesh.repair.fix_winding(mesh)
   mesh.export("models/toy_laptop/output/toy_laptop_001_fixed.stl")
   ```
   Then validate the `_fixed.stl` file.

---

## Step 2: Full Validator — `scripts/validate.py`

```bash
python scripts/validate.py models/toy_laptop/output/toy_laptop_001.stl
```

### Check-by-Check Expected Outcomes

---

#### Check 1: `file_exists`

| Field           | Value |
|-----------------|-------|
| Severity        | FAIL  |
| Expected        | **PASS** |
| Condition       | File must exist after Step 1 export |
| Message pattern | `File found and readable: models/toy_laptop/output/toy_laptop_001.stl` |
| If FAIL         | Re-run the `/export-stl` skill; confirm `--output` path is correct |

---

#### Check 2: `supported_format`

| Field           | Value |
|-----------------|-------|
| Severity        | FAIL  |
| Expected        | **PASS** |
| Condition       | Extension `.stl` is in the supported set |
| Message pattern | `Extension '.stl' is supported by BambuStudio` |
| If FAIL         | Impossible for a correctly named `.stl` — check filename |

---

#### Check 3: `loadable`

| Field           | Value |
|-----------------|-------|
| Severity        | FAIL  |
| Expected        | **PASS** |
| Condition       | trimesh can parse the binary STL |
| Message pattern | `Mesh loaded successfully` |
| If FAIL         | STL is corrupt; re-export from OpenSCAD with `--ascii` flag to inspect |

---

#### Check 4: `non_empty`

| Field           | Value |
|-----------------|-------|
| Severity        | FAIL  |
| Expected        | **PASS** |
| Face count      | Expect > 10,000 faces for the full model |
| Message pattern | `Mesh has N faces and M vertices` |
| If FAIL         | OpenSCAD produced empty geometry — check for subtraction errors where `difference()` removes all geometry; inspect with OpenSCAD GUI |

---

#### Check 5: `watertight`

| Field           | Value |
|-----------------|-------|
| Severity        | FAIL  |
| Expected v001   | **FAIL** (expected, see notes) |
| Expected final  | **PASS** |
| Message pattern (FAIL) | `Mesh is NOT watertight (open edge count: N)` |
| Target          | `open_edge_count` must reach 0 before the model is print-ready |
| Acceptable trend| open_edge_count should decrease monotonically each version |

**Notes:** The hinge clearance gap between pin and bore creates open mesh edges
on first export. This is the primary geometry gate — do not submit to the slicer
until this is PASS.

**Fix approach:**
- Ensure bore `difference()` depth fully penetrates the barrel on both sides
- Use `hull()` at the barrel-to-body junctions
- Check that the pin head caps fully close the pin ends inside the barrel
- If open_edge_count is small (< 10), run `trimesh.repair.fill_holes()`

---

#### Check 6: `build_volume`

| Field           | Value |
|-----------------|-------|
| Severity        | FAIL  |
| Expected        | **PASS** |
| Model dims (110° pose) | ~250 × 180 × 187 mm |
| H2D build volume| 350 × 320 × 325 mm |
| Margins         | X: 100 mm spare; Y: 140 mm spare; Z: 138 mm spare |
| Message pattern | `Model dimensions (250.x × 180.x × 187.x mm) fit within build volume (350 × 320 × 325 mm)` |
| If FAIL on X    | Model is wider than 350 mm — check base width parameter |
| If FAIL on Y    | Model depth exceeds 320 mm — reduce keyboard depth or hinge barrel radius |
| If FAIL on Z    | Lid rise at 110° exceeds 325 mm — reduce lid depth or print pose angle |

---

#### Check 7: `positive_volume`

| Field           | Value |
|-----------------|-------|
| Severity        | WARN  |
| Expected        | **PASS** |
| Volume range    | 50,000–300,000 mm³ (rough estimate for toy laptop at 20% infill) |
| Message pattern | `Volume = N mm³ (normals look correct)` |
| If WARN (negative) | Normals inverted — run `trimesh.repair.fix_normals(mesh)` then re-export |
| If WARN (zero)  | Mesh is an open surface — check that all OpenSCAD bodies are solids, not 2D extruded incorrectly |

---

#### Check 8: `no_degenerate_faces`

| Field           | Value |
|-----------------|-------|
| Severity        | WARN  |
| Expected        | **PASS** |
| Condition       | No zero-area triangles |
| Message pattern | `No zero-area (degenerate) faces found` |
| If WARN         | Increase `$fn` on all `cylinder()` and `sphere()` calls to ≥ 60; check for zero-thickness `difference()` planes that create coincident faces |

---

#### Check 9: `wall_thickness`

| Field           | Value |
|-----------------|-------|
| Severity        | WARN  |
| Expected        | **WARN** (acceptable — deliberate design choice) |
| Reason          | Keycap sidewalls are ~0.8 mm, at the advisory threshold |
| Message pattern | `Minimum sampled wall thickness ≈ 0.6–0.8 mm (recommended ≥ 0.8 mm for 0.4 mm nozzle). Mean ≈ N mm` |
| Is this blocking?| **No** — WARN does not prevent slicing |
| Escalate if     | Minimum drops below 0.4 mm (slicer will skip features) — redesign keycap geometry |
| Skip option     | `python scripts/validate.py ... --skip-wall-thickness` for fast iteration |

---

### Overall Result Summary Per Iteration

| Version | `watertight` | `build_volume` | `wall_thickness` | **Overall** | Print-ready? |
|---------|-------------|----------------|------------------|-------------|--------------|
| 001     | FAIL        | PASS           | WARN             | **FAIL**    | No           |
| 002+    | PASS        | PASS           | WARN             | **WARN**    | Yes          |

Model is considered **print-ready** when:
- No FAIL checks remain
- `watertight` = PASS
- Remaining WARNs are only `wall_thickness` (acceptable for keycap geometry)

---

## Step 3: Visual Checks via `/preview-scad`

Render and inspect after every version. Run from the repo root:

```bash
.claude/skills/preview-scad/scripts/render-scad.sh \
  models/toy_laptop/toy_laptop_001.scad \
  --output models/toy_laptop/toy_laptop_001.png \
  --size 1200x900 \
  --render
```

Then read the generated PNG image to verify all items in the checklist below.

### Visual Checklist

| # | Feature           | Expected                                           | Pass Criteria |
|---|-------------------|----------------------------------------------------|---------------|
| V1 | Overall shape    | Laptop form factor                                 | Base and lid clearly distinguishable; hinge at rear |
| V2 | Hinge barrel     | Full-width cylinder at rear edge                   | Barrel spans full X (250 mm); no gaps or discontinuities |
| V3 | Hinge pin        | Visible inside barrel                              | Pin is concentric; does not visually contact bore walls at this scale |
| V4 | Hard stop        | Shoulder geometry on base side of barrel collar    | Stop lug present; does not overlap with lid in closed position |
| V5 | Keyboard         | Grid of raised keycaps in recessed bed             | Keys visible as raised bumps; near-hinge position confirmed |
| V6 | Trackpad         | Recessed rectangle centered in front of keyboard   | Visible as a flat inset; clearly separated from keyboard area |
| V7 | Screen pocket    | Deep recess on inner (hinge-side) face of lid      | Recess is visible; bezel margin clearly present on all 4 sides |
| V8 | Bump stops       | Two small domes on screen border (top corners)     | One dome at top-left, one at top-right of screen bezel |
| V9 | Print pose       | ~110° open angle                                   | Base flat; lid angled upward at roughly 110° from base plane |
| V10 | No islands      | All geometry connected                             | No floating or disconnected mesh islands visible |

### Recommended Camera Angles

```bash
# Default overview (auto-centered) — start here
# (no --camera flag, relies on --viewall --autocenter)

# Front-facing (keyboard and trackpad visible)
--camera 0,-300,80,0,0,50,500

# Lid interior (screen pocket and bump stops)
--camera 0,300,150,0,0,80,500

# Hinge close-up (pin, barrel, hard stop)
--camera 0,-20,30,0,0,50,200

# Top-down (overall footprint and layout)
--camera 0,0,600,0,0,90,600
```

---

## Step 4: Hinge Function Simulation (Mathematical)

Before committing a version as final, verify these constraints mathematically
using the parameter values in PLAN.md:

| Check | Formula | Target | Pass Criteria |
|-------|---------|--------|---------------|
| Pin fits in bore | bore_d = pin_d + 2 × radial_clearance | 3.4 mm | bore_d ≥ pin_d + 0.4; bore_d ≤ pin_d + 0.6 |
| Barrel min wall | wall = (barrel_od − bore_d) / 2 | ≥ 1.2 mm | (barrel_od − 3.4) / 2 ≥ 1.2 → barrel_od ≥ 5.8 mm |
| Hard stop at 135° | Shoulder geometry blocks rotation | 135° max | Preview at `hinge_angle = 135`; lid should contact stop |
| No interference at 0° (closed) | Stop lug clears at closed position | 0° free | Preview at `hinge_angle = 0`; no geometry collision |
| Print gap at 110° | No geometry overlap at print pose | 110° free | Preview at `hinge_angle = 110`; pin/bore gap visible |

---

## Iteration Notes

Update this section after each version is validated.

### v001 — Initial export
- Date: (to be filled)
- `watertight` result: (to be filled)
- `open_edge_count`: (to be filled)
- `build_volume` dims: (to be filled)
- Visual checks passed: (to be filled)
- Next steps: (to be filled)
