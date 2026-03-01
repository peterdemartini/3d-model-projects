# toy_laptop — Output Directory

Generated 3D model files for the `toy_laptop` project live here.
**These files are not committed to git** (see `.gitignore`).

## Regenerating Files

```bash
# Export from OpenSCAD source
.claude/skills/export-stl/scripts/export-stl.sh \
  models/toy_laptop/toy_laptop_001.scad \
  --output models/toy_laptop/output/toy_laptop_001.stl

# Run full H2D validation suite
python scripts/validate.py models/toy_laptop/output/toy_laptop_001.stl
```

See `models/toy_laptop/simulations.md` for expected validation outcomes.
