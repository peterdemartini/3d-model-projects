# toy_laptop — Output Directory

Generated 3D model files for the `toy_laptop` project live here.

## Committed Files

`toy_laptop_001.3mf` is **committed to git** (force-added despite `.gitignore`)
as the deliverable for PR `feat/toy-laptop-model`. This is the print-ready file.

## Regenerating Files

```bash
# Export 3MF directly from OpenSCAD source
/opt/homebrew/bin/openscad \
  --export-format 3mf \
  -o models/toy_laptop/output/toy_laptop_001.3mf \
  models/toy_laptop/toy_laptop_001.scad

# Run full H2D validation suite
python scripts/validate.py models/toy_laptop/output/toy_laptop_001.3mf
```

See `models/toy_laptop/simulations.md` for expected validation outcomes.

## v001 Validation Summary

All 9 checks **PASS**:
- watertight: PASS (manifold mesh, 0 open edges)
- build_volume: PASS (250×241.6×178.9 mm — fits H2D 350×320×325 mm)
- wall_thickness: PASS (min 5.49 mm)
- no_degenerate_faces: PASS
- file_exists / supported_format / loadable / non_empty / positive_volume: all PASS
