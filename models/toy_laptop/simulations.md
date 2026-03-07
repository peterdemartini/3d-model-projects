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
| Message pattern (FAIL) | contains `open/non-manifold edges detected; open edge count:` |
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
| 001     | **PASS** ✅  | PASS ✅         | PASS ✅           | **PASS** ✅  | **Yes** ✅    |

Model is considered **print-ready** when:
- No FAIL checks remain
- `watertight` = PASS
- Remaining WARNs are only `wall_thickness` (acceptable for keycap geometry)

**v001 achieved full PASS on all 9 checks** — watertight PASS was obtained by using a full-cylinder barrel design (no half-space clipping) which avoids T-junction non-manifold edges. The `wall_thickness` check also PASS (min 5.49mm) since keycaps use `linear_extrude` with taper scaling.

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
| V8 | ~~Bump stops~~   | **Removed in v002** — no domes on lid outer face   | Lid outer face should be smooth; no bumps visible |
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
| Pin fits in bore | bore_d = pin_d + 2 × radial_clearance | 5.0 mm | bore_d ≥ pin_d + 0.8; bore_d ≤ pin_d + 1.6 → 5.0 ✅ |
| Radial clearance | (bore_d − pin_d) / 2 | 0.4–0.8 mm | (5.0 − 4.0) / 2 = 0.5 mm ∈ [0.4, 0.8] ✅ |
| Barrel min wall | wall = (barrel_od − bore_d) / 2 | ≥ 1.2 mm | (12.0 − 5.0) / 2 = 3.5 mm ≥ 1.2 ✅ |
| Knuckle gap | axial clearance between knuckles | ≥ 0.4 mm | 0.5 mm ≥ 0.4 ✅ |
| Hard stop at 135° | Shoulder geometry blocks rotation | 135° max | Preview at `hinge_angle = 135`; lid should contact stop |
| No interference at 0° (closed) | Stop lug clears at closed position | 0° free | Preview at `hinge_angle = 0`; no geometry collision |
| Print gap at 90° | No geometry overlap at print pose | 90° free | Preview at `hinge_angle = 90`; pin/bore gap visible |

---

## Step 5: Closure Simulation (hinge_angle = 0°)

Verify the laptop can **fully close** (lid flat against base) without any geometry
collision. This was added in v002 after bump stops were removed.

### 5a. Visual Verification

Render at `hinge_angle=0` and inspect for overlapping geometry:

```bash
openscad -D 'hinge_angle=0' --render --imgsize 1200,900 \
  -o models/toy_laptop/output/toy_laptop_001_closed.png \
  models/toy_laptop/toy_laptop_001.scad
```

Inspect the resulting PNG. The lid should sit flat on the base with:
- No barrel-on-barrel collision at the hinge
- No keycap protrusion through the lid
- Screen pocket facing down toward the keyboard

### 5b. Mathematical Closure Analysis

When `hinge_angle=0`, the lid folds down flat onto the base. Three clearances must
be verified:

| Clearance Check | Formula | Value | Pass? |
|-----------------|---------|-------|-------|
| **Key-to-pocket (Z)** | screen_pocket_depth − key_protrusion | 2.5 − 1.0 = **1.5 mm** | ✅ Keys fit inside screen pocket |
| **Key-to-pocket (Y)** | screen_pocket_front_y − keyboard_back_edge_y | 165.0 − 161.0 = **4.0 mm** | ✅ Keys don't extend past pocket |
| **Barrel collision** | Base and lid knuckles interleave (never overlap axially) | gap = 0.3 mm | ✅ No barrel overlap |
| **Stop lug at 0°** | Lug is on base barrel; lid barrel rotates to 0° without contact | lug_h = 2.5 mm, only blocks > 135° | ✅ No lug collision at 0° |

**Key-to-pocket (Z) detail:**
- Keyboard bed is recessed 1.5 mm below base top surface
- Keycap protrusion above base top = key_h − bed_depth = 2.5 − 1.5 = **1.0 mm**
- Screen pocket depth = **2.5 mm** (cut into lid inner face)
- Clearance when closed = 2.5 − 1.0 = **1.5 mm** → sufficient

**Key-to-pocket (Y) detail:**
- Keyboard back edge Y = kb_y0 − kb_bed_margin + bed_d_total = base_d − bezel = 180 − 15 = **165 mm**
  - But the actual key back edge is at base_d − bezel = 165 mm (from SCAD: keyboard aligned to bezel)
  - keyboard_back_edge_y_mm in meta.json = **161.0 mm** (last key row back edge)
- Screen pocket starts at bezel = 15 mm from lid edge → when closed, the pocket front edge
  maps to base Y = base_d − bezel = **165 mm**
- Clearance = 165 − 161 = **4.0 mm** → sufficient

### 5c. Angle Sweep — Lid Far-Edge Position

The lid far edge (opposite the hinge) traces an arc as the hinge rotates.
Verify no collision at any angle from 0° (closed) to 135° (max open).

Hinge axis is at `(0, base_d, base_h)` = `(0, 180, 10)`.
Lid depth = `base_d` = 180 mm. Lid far-edge position relative to hinge axis:

```
far_edge_y = base_d − lid_depth × cos(angle) = 180 − 180 × cos(θ)
far_edge_z = base_h + lid_depth × sin(angle) = 10 + 180 × sin(θ)
```

| Angle (°) | far_edge_y (mm) | far_edge_z (mm) | Collision? |
|-----------|-----------------|-----------------|------------|
| 0 (closed)  | 0.0   | 10.0   | No — lid sits on base |
| 15          | 13.3  | 56.6   | No |
| 30          | 24.1  | 100.0  | No |
| 45          | 52.7  | 137.3  | No |
| 60          | 90.0  | 165.9  | No |
| 75          | 133.4 | 183.9  | No |
| 90          | 180.0 | 190.0  | No — lid perpendicular |
| 105         | 226.6 | 183.9  | No |
| 120         | 270.0 | 165.9  | No |
| 135 (max)   | 307.3 | 137.3  | No — hard stop engaged |

At all angles from 0° to 135°, the lid far edge stays within the H2D build volume
(350 × 320 × 325 mm) and does not collide with the base body.

---

## Iteration Notes

Update this section after each version is validated.

### v001 — Initial export
- Date: 2026-03-01
- `watertight` result: **PASS** (all 9 checks PASS — better than expected)
- `open_edge_count`: 0 (no open edges)
- `build_volume` dims: 250.0 × 184.5 × 187.0 mm (fits within 350 × 320 × 325 mm)
- `non_empty`: 6,344 faces / 3,178 vertices
- `positive_volume`: 719,262 mm³
- `wall_thickness`: PASS — min 2.49 mm, mean 17.96 mm
- `no_degenerate_faces`: PASS
- Visual checks: Geometry renders with base plate, keyboard bed, recessed trackpad,
  full-width hinge barrel, lid with screen pocket and bump stops at 90° pose (lid perpendicular to base)
- Key design notes:
  - Print pose: 90° interior hinge angle — lid stands straight up from the base
  - Hinge barrel uses full cylinder (not half-cylinder) unioned with base to avoid non-manifold T-junctions
  - Keycaps use `linear_extrude(height, scale=[...])` to produce clean tapered geometry
  - Bump stops use `hull()` between cylinder disk and raised sphere to avoid tangent-at-face issues
  - Assembly places pin at (0, base_d, base_h) hinge axis; lid rotated -90° (= -(180-90)°) around X
- Next steps: Model is print-ready. Slice in BambuStudio for H2D. Enable 4-color AMS paint
  (body=slot1, keycap tops=slot2, screen bezel=slot3, screen surface=slot4).

### v002 — Increased hinge tolerance, removed bump stops, added closure simulation
- Date: 2026-03-04
- Changes:
  - **Hinge tolerance increase**: bore_d 3.4 → 3.6 mm (0.3 mm radial clearance); knuckle_gap 0.2 → 0.3 mm;
    pin_head_r clearance 0.05 → 0.15 mm; slot cutouts +0.3 mm extra in Y and Z
  - **Bump stops removed**: Deleted stop_d, stop_h_dome, stop_r, stop_inset parameters and hull/sphere dome
    geometry from lid() module. Lid outer face is now smooth.
  - **Closure validation updated**: validate.py check_closure_clearance() now checks screen_pocket_depth
    instead of bump_stop_height. Keys (1.0 mm protrusion) fit inside screen pocket (2.5 mm depth) with
    1.5 mm clearance.
  - **Closure simulation added**: Step 5 documents visual verification at hinge_angle=0, mathematical
    clearance analysis (Z: 1.5 mm, Y: 4.0 mm), and angle sweep from 0°–135° confirming no collision.
  - **meta.json updated**: bore_d_mm=3.6, knuckle_gap_mm=0.3, removed bump_stop_height_mm,
    added screen_pocket_depth_mm=2.5
- Validation results:
  - `file_exists`: PASS
  - `supported_format`: PASS
  - `loadable`: PASS
  - `non_empty`: PASS — 4,108 faces / 2,160 vertices
  - `watertight`: PASS — manifold
  - `build_volume`: PASS — 188.0 × 250.0 × 190.0 mm (fits 350 × 320 × 325 mm)
  - `positive_volume`: PASS — 745,755 mm³
  - `no_degenerate_faces`: WARN — 6 degenerate faces (non-blocking)
  - `wall_thickness`: WARN — skipped (rtree not installed; non-blocking)
  - `expected_dimensions`: PASS — 188 × 250 × 190 mm (within ±5 mm of 189 × 250 × 190)
  - `base_on_bed`: PASS — Z=0 base sits flat
  - `hinge_parameters`: PASS — pin 3.0, bore 3.6, radial clearance 0.30, wall 2.20, stop 135°
  - `closure_clearance`: PASS — Y clearance 4.0 mm, key protrusion 1.0 ≤ pocket depth 2.5
  - `3mf_has_colors`: PASS — 2 color objects, 2 color groups, p:UUID present
- Print readiness: **Yes** — all critical checks PASS, only non-blocking WARNs remain

### v003 — Hinge size increase for reliable FDM print-in-place (red-green-refactor)
- Date: 2026-03-07
- Changes:
  - **Hinge size increase**: pin_d 3.0 → 4.0 mm; bore_d 3.6 → 5.0 mm (0.5 mm radial clearance);
    barrel_od 8.0 → 12.0 mm (3.5 mm barrel wall); knuckle_gap 0.3 → 0.5 mm;
    pin_head_r = bore_r − 0.15 = 2.35 mm
  - **Validator updated**: minimum radial clearance raised from 0.1 to 0.4 mm;
    maximum radial clearance raised from 0.5 to 0.8 mm; knuckle gap minimum of 0.4 mm added
  - **Unit tests added**: test_validate.py now has tests for check_hinge_parameters (8 tests)
    and check_closure_clearance (3 tests) — previously untested
  - **Red-green-refactor pattern**: added to AGENTS.md as a workflow pattern
- Expected validation results:
  - `hinge_parameters`: PASS — pin 4.0, bore 5.0, radial clearance 0.50 mm,
    barrel wall 3.50 mm, knuckle gap 0.50 mm, hard stop 135°
  - All other checks: same as v002 (PASS or non-blocking WARN)
