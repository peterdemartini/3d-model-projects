# 3d-model-projects

Generate 3D models programmatically using AI (Claude / Copilot) and Python, then validate and export them as files compatible with **BambuStudio** for printing on a **Bambu Lab H2D**.

## Quick Start

```bash
# Install Python dependencies
pip install -r scripts/requirements.txt

# Validate a generated model
python scripts/validate.py output/my_model.stl

# Run tests
python -m pytest tests/ -v
```

## Repository Structure

```
3d-model-projects/
├── AGENTS.md              ← AI agent instructions (printer specs, guidelines, validation)
├── models/                ← Source model scripts (.py, .scad)
├── output/                ← Generated STL/3MF files (git-ignored)
├── scripts/
│   ├── validate.py        ← Validation script (watertight, build volume, normals, …)
│   └── requirements.txt   ← Python dependencies
└── tests/
    └── test_validate.py   ← Unit tests
```

## For AI Agents

See **[AGENTS.md](AGENTS.md)** for full instructions including:
- Bambu Lab H2D printer specifications and build volume
- Supported file formats (STL, 3MF, OBJ, STEP)
- Design guidelines (wall thickness, overhangs, tolerances)
- Validation framework and how to run checks
- Workflow from design → generate → validate → slice
