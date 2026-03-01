# AGENTS.md — Instructions for AI Coding Agents

This file contains instructions for AI coding agents (Claude, GitHub Copilot, etc.) working in this repository.
Read this file in full before writing any code or generating any models.

---

## Project Goal

Generate 3D models programmatically using Python (or OpenSCAD), then validate and export them as files compatible with **BambuStudio** for printing on a **Bambu Lab H2D** printer.

---

## Printer: Bambu Lab H2D

### Build Volume
| Axis | Max (mm) |
|------|----------|
| X    | 350      |
| Y    | 320      |
| Z    | 325      |

Every model **must** fit within this envelope.

### Extruder & Nozzle
- **Type**: Dual extrusion (two independent toolheads)
- **Default nozzle diameter**: 0.4 mm
- **Available nozzle diameters**: 0.2 mm, 0.4 mm, 0.6 mm, 0.8 mm
- **Filament diameter**: 1.75 mm

### Print Settings (defaults for new models)
| Parameter         | Default     | Range           |
|-------------------|-------------|-----------------|
| Layer height      | 0.2 mm      | 0.05 – 0.35 mm  |
| Line width        | 0.42 mm     | 0.3 – 0.6 mm    |
| Print speed       | 200 mm/s    | 20 – 600 mm/s   |
| Travel speed      | 400 mm/s    | —               |
| Perimeters        | 3 walls     | —               |
| Top/bottom layers | 4           | —               |
| Infill            | 15 %        | 0 – 100 %       |

### Supported Materials
| Material | Nozzle Temp | Bed Temp | Notes                  |
|----------|-------------|----------|------------------------|
| PLA      | 220 °C      | 55 °C    | Default, easy to print |
| PETG     | 240 °C      | 70 °C    | Flexible, food-safe    |
| ABS      | 245 °C      | 90 °C    | Requires enclosure     |
| ASA      | 255 °C      | 90 °C    | UV-resistant           |
| TPU 95A  | 220 °C      | 40 °C    | Flexible               |
| PA (Nylon)| 260 °C     | 80 °C    | Tough, hygroscopic     |
| PC       | 280 °C      | 100 °C   | High-temp, strong      |
| PA-CF    | 280 °C      | 90 °C    | Carbon-fiber reinforced|
| PETG-CF  | 260 °C      | 75 °C    | Carbon-fiber reinforced|

### Multi-Color / Multi-Material (AMS)
- Up to **4 materials** per print via the AMS (Automatic Material System).
- When creating multi-color models, use separate mesh bodies/components per color in the source and tag them in the `.3mf` file, or rely on BambuStudio's "split by color" feature.
- For dual-extrusion soluble supports, designate one extruder for PVA or HIPS.

---

## File Format Requirements

### BambuStudio-Compatible Formats
| Format | Extension | Notes                                      |
|--------|-----------|--------------------------------------------|
| 3MF    | `.3mf`    | **Preferred.** Preserves colors, settings. |
| STL    | `.stl`    | Most common; single body/color only.       |
| OBJ    | `.obj`    | Supported; rarely needed.                  |
| STEP   | `.step`, `.stp` | Good for engineering parts.          |

### Output Location
Generated model files go in one of two places:

- **Root `output/`** — for standalone or one-off models.
- **`models/<model-name>/output/`** — for models that have a project folder under `models/`. **Prefer this.** It keeps all project artifacts (source, spec, validation results) co-located.

Neither location is committed to git (see `.gitignore`).

### Naming Convention
```
{project-name}_v{version}.stl
{project-name}_v{version}.3mf
```
Examples: `phone-stand_v1.stl`, `cable-clip_v2.3mf`

---

## Modeling Tools

### Python — build123d (recommended)
[build123d](https://build123d.readthedocs.io) is a Python CAD library well-suited to AI-generated code.

```bash
# Install all dependencies
pip install -r scripts/requirements.txt
```

Minimal example:
```python
from build123d import *

with BuildPart() as part:
    Box(50, 30, 20)
    fillet(part.edges(), radius=2)

export_stl(part.part, "output/box_v1.stl")
```

### OpenSCAD (alternative)
For simple parametric models, OpenSCAD `.scad` files are also acceptable.

```bash
openscad -o output/model_v1.stl models/model.scad
```

**Prefer using the built-in OpenSCAD skills (see below) over calling OpenSCAD directly.** They handle versioning, preview rendering, and geometry validation automatically.

### Python — trimesh (mesh manipulation / repair)
`trimesh` is available for mesh repair, analysis, and format conversion.

```python
import trimesh
mesh = trimesh.load("output/model.stl")
trimesh.repair.fill_holes(mesh)
mesh.export("output/model_fixed.stl")
```

---

## Design Guidelines

### Wall Thickness
| Rule               | Value        |
|--------------------|--------------|
| Absolute minimum   | 0.4 mm (1 nozzle width) — slicer will ignore thinner |
| Recommended minimum| 0.8 mm (2 nozzle widths) |
| Structural minimum | 1.2 mm       |
| Strong walls       | 2.0 mm+      |

### Overhangs
| Angle from vertical | Support needed? |
|---------------------|-----------------|
| ≤ 45°               | No              |
| 45° – 70°           | Recommended     |
| > 70°               | Required        |

Maximum unsupported bridge length: **~50 mm** (shorter is better).

### Tolerances & Fit
| Fit type     | Clearance per side |
|--------------|--------------------|
| Press fit    | 0.1 mm             |
| Slip fit     | 0.2 mm             |
| Clearance fit| 0.3 mm             |
| Loose fit    | 0.5 mm+            |

### Minimum Feature Sizes
| Feature                | Minimum  |
|------------------------|----------|
| Positive (raised) detail| 0.4 mm  |
| Hole diameter (functional)| 1.0 mm |
| Embossed text height   | 0.6 mm   |
| Embossed text line width| 0.8 mm  |

### Layer Height vs. Detail
| Use case           | Layer height |
|--------------------|--------------|
| Detailed / fine    | 0.05 – 0.10 mm |
| Standard           | 0.15 – 0.20 mm |
| Draft / fast       | 0.25 – 0.35 mm |

---

## Validation Framework

**All models MUST pass validation before being considered complete.**

### Quick Start
```bash
# Validate a single file
python scripts/validate.py output/model_v1.stl

# Validate every file in output/
python scripts/validate.py output/

# Skip the wall-thickness check (faster)
python scripts/validate.py output/model.stl --skip-wall-thickness
```

### Checks Performed

| # | Check                  | Severity | Description |
|---|------------------------|----------|-------------|
| 1 | `file_exists`          | FAIL     | File must exist and be readable |
| 2 | `supported_format`     | FAIL     | Extension must be in `.stl .3mf .obj .step .stp` |
| 3 | `loadable`             | FAIL     | File must be parseable by trimesh |
| 4 | `non_empty`            | FAIL     | Mesh must have at least one face and vertex |
| 5 | `watertight`           | FAIL     | Mesh must be manifold (no open/non-manifold edges) |
| 6 | `build_volume`         | FAIL     | Model must fit within 350 × 320 × 325 mm |
| 7 | `positive_volume`      | WARN     | Volume should be positive (correct normals) |
| 8 | `no_degenerate_faces`  | WARN     | No zero-area triangles |
| 9 | `wall_thickness`       | WARN     | Minimum sampled wall ≥ 0.8 mm (advisory) |

### Result Levels
| Level | Meaning |
|-------|---------|
| ✅ PASS | Check passed — no action needed |
| ⚠️  WARN | Advisory issue — model may still print but review recommended |
| ❌ FAIL | Critical issue — **must be fixed** before slicing |

### Interpreting Output
```
============================================================
Validating: output/model_v1.stl
============================================================
  ✅ [PASS] file_exists: File found: output/model_v1.stl
  ✅ [PASS] supported_format: Extension '.stl' is supported by BambuStudio
  ✅ [PASS] loadable: Mesh loaded successfully
  ✅ [PASS] non_empty: Mesh has 1,200 faces and 602 vertices
  ❌ [FAIL] watertight: Mesh is NOT watertight (open edge count: 6). ...
  ✅ [PASS] build_volume: Model dimensions (50.0 × 30.0 × 20.0 mm) fit within build volume (350 × 320 × 325 mm)
  ✅ [PASS] positive_volume: Volume = 28543.21 mm³ (normals look correct)
  ✅ [PASS] no_degenerate_faces: No zero-area (degenerate) faces found
  ⚠️  [WARN] wall_thickness: Minimum sampled wall thickness ≈ 0.62 mm ...
------------------------------------------------------------
  ❌ Overall: FAIL
```

---

## Common Fixes

### Model Not Watertight
```python
import trimesh
mesh = trimesh.load("output/model.stl")
trimesh.repair.fill_holes(mesh)
trimesh.repair.fix_winding(mesh)
mesh.export("output/model_fixed.stl")
```

### Inverted Face Normals
```python
import trimesh
mesh = trimesh.load("output/model.stl")
trimesh.repair.fix_normals(mesh)
mesh.export("output/model_fixed.stl")
```

### Model Exceeds Build Volume — Scale Down
```python
import trimesh
import numpy as np
mesh = trimesh.load("output/model.stl")
# Scale uniformly so the largest dimension fits within 300 mm
scale = 300.0 / max(mesh.extents)
mesh.apply_scale(scale)
mesh.export("output/model_scaled.stl")
```

### Remove Degenerate Faces
```python
import trimesh
mesh = trimesh.load("output/model.stl")
mesh.remove_degenerate_faces()
mesh.export("output/model_fixed.stl")
```

---

## Workflow

```
1. Design  →  Write model code in models/
2. Generate →  Run the script → output/model_v1.stl
3. Validate →  python scripts/validate.py output/model_v1.stl
4. Fix      →  Address any FAIL/WARN results → re-run step 2-3
5. Slice    →  Import into BambuStudio → review supports, infill, etc.
6. Export   →  Save as .3mf or send .gcode/.bgcode to printer
```

---

## Repository Structure

```
3d-model-projects/
├── AGENTS.md              ← This file
├── README.md              ← Human-readable overview
├── pytest.ini             ← pytest configuration
├── .gitignore
├── .claude/
│   └── skills/
│       ├── openscad/      ← /openscad skill (versioned design + preview)
│       ├── preview-scad/  ← /preview-scad skill (render to PNG)
│       └── export-stl/    ← /export-stl skill (export + geometry validation)
├── models/                ← Source model scripts (.scad, .py)
│   ├── <model-name>/      ← one folder per project (preferred structure)
│   │   ├── PLAN.md        ← persistent spec (dimensions, tolerances, decisions)
│   │   ├── simulations.md ← validation steps with expected outcomes per iteration
│   │   ├── <name>_001.scad← versioned OpenSCAD source (or .py for build123d)
│   │   └── output/        ← project-scoped generated files (git-ignored)
│   └── examples/          ← Example models (reference)
├── output/                ← Generated STL/3MF files for standalone models (git-ignored)
│   └── README.md          ← Explains the directory
├── scripts/
│   ├── validate.py        ← Model validation script (H2D-specific checks)
│   └── requirements.txt   ← Python dependencies
└── tests/
    └── test_validate.py   ← Unit tests for validate.py
```

---

## Running Tests

```bash
# Install dependencies first (once)
pip install -r scripts/requirements.txt

# Run all tests
python -m pytest tests/ -v

# Run a specific test
python -m pytest tests/test_validate.py::test_validate_good_stl -v
```

All tests must pass before committing new code.

---

## Style & Code Conventions

- **Python version**: 3.10+
- **Formatting**: follow PEP 8; keep lines ≤ 100 chars
- **Type hints**: use them for all function signatures
- **Docstrings**: one-line docstring for every public function
- **No external 3D CAD files committed**: source code only; generated files go in `output/`
- **Version models**: increment `_v1`, `_v2`, … when making incompatible shape changes

---

## OpenSCAD Skills

This repository includes Claude Code skills from [openscad-agent](https://github.com/iancanderson/openscad-agent) for an AI-driven OpenSCAD workflow. They are located in `.claude/skills/`.

### Prerequisites

Install OpenSCAD from [openscad.org](https://openscad.org/) (macOS: `/Applications/OpenSCAD.app` or `brew install --cask openscad`).

### Available Skills

| Skill | Invoke | Description |
|-------|--------|-------------|
| `openscad` | `/openscad` | Create versioned `.scad` files, render previews, and compare iterations |
| `preview-scad` | `/preview-scad` | Render a `.scad` file to a PNG image for visual verification |
| `export-stl` | `/export-stl` | Export a `.scad` file to STL with geometry validation |

### Full Pipeline

```
/openscad → /preview-scad → /export-stl → python scripts/validate.py
```

1. **`/openscad`** — Design and iterate. Automatically manages versioned filenames (`model_001.scad`, `model_002.scad`, …), renders each version to a matching PNG, and lets you compare iterations visually.
2. **`/preview-scad`** — Re-render any `.scad` file to PNG for a quick visual check without creating a new version.
3. **`/export-stl`** — Convert the final `.scad` to STL with basic geometry validation (non-manifold, self-intersections, degenerate faces).
4. **`python scripts/validate.py`** — Run the full H2D-specific validation suite (build volume, watertightness, wall thickness, etc.) on the exported STL.

### File Naming Convention

OpenSCAD skill files use underscores and zero-padded three-digit version numbers:

```
models/<model-name>/<model-name>_001.scad  →  models/<model-name>/<model-name>_001.png
models/<model-name>/<model-name>_002.scad  →  models/<model-name>/<model-name>_002.png
models/<model-name>/output/<model-name>_002.stl  ← final export
```

When using `version-scad.sh`, run it from inside the model's folder:

```bash
cd models/<model-name>
../../../.claude/skills/openscad/scripts/version-scad.sh <model-name>
```

### Example Session

```bash
# 1. Start a new model (creates models/stand/stand_001.scad and renders models/stand/stand_001.png)
/openscad design a phone stand with a 15-degree viewing angle

# 2. Re-render after manual edits without incrementing version
/preview-scad models/stand/stand_001.scad

# 3. Export the approved version to STL into the project output folder
/export-stl models/stand/stand_001.scad --output models/stand/output/stand_001.stl

# 4. Run the full H2D validation suite
python scripts/validate.py models/stand/output/stand_001.stl
```

### OpenSCAD Design Tips

- Use `$fn` to control curve smoothness (higher = smoother but slower to render)
- Use `module` for reusable components
- Use `difference()` to subtract shapes, `union()` to combine
- Use `hull()` for organic shapes and smooth transitions
- Use `union()` when combining overlapping shapes to avoid self-intersection

---

## Quick-Reference Cheat Sheet

```
Build volume : 350 × 320 × 325 mm
Min wall     : 0.8 mm (functional), 1.2 mm (structural)
Min hole     : 1.0 mm diameter
Overhangs    : support if > 45°
Bridging     : up to ~50 mm without support
Press fit    : ±0.1 mm clearance
OpenSCAD     : /openscad → /preview-scad → /export-stl
Validate     : python scripts/validate.py output/<file>.stl  # or models/<name>/output/<file>.stl
Test         : python -m pytest tests/ -v
```
