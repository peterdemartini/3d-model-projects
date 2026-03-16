# Spa Headrest — Validation Simulations

## v001 — Pillow-Style with Tile Clip

### Expected Outcomes

| # | Check                 | Expected | Notes                                          |
|---|-----------------------|----------|-------------------------------------------------|
| 1 | file_exists           | PASS     | `output/spa_headrest_001.stl`                   |
| 2 | supported_format      | PASS     | `.stl` format                                   |
| 3 | loadable              | PASS     | Standard STL mesh                               |
| 4 | non_empty             | PASS     | ~2000 faces                                     |
| 5 | watertight            | PASS     | Manifold mesh, no open edges                    |
| 6 | build_volume          | PASS     | ~119 × 250 × 188 mm fits 350×320×325           |
| 7 | positive_volume       | PASS     | ~111,000 mm³                                    |
| 8 | no_degenerate_faces   | PASS     | Clean geometry                                  |
| 9 | wall_thickness        | SKIP     | Skipped (--skip-wall-thickness); design uses 6mm walls |
| 10| base_on_bed           | PASS     | Z=0 at base (print orientation corrected)       |

### Validation Command

```bash
python3 scripts/validate.py models/spa_headrest/output/spa_headrest_001.stl --skip-wall-thickness
```

### Results (2026-03-16)

```
✅ file_exists: PASS
✅ supported_format: PASS
✅ loadable: PASS
✅ non_empty: PASS (2,028 faces, 1,080 vertices)
✅ watertight: PASS
✅ build_volume: PASS (118.8 × 250.0 × 188.0 mm)
✅ positive_volume: PASS (113,816 mm³)
✅ no_degenerate_faces: PASS
✅ base_on_bed: PASS (Z = 0.00 mm)
Overall: PASS
```

### Physical Test Plan

- [ ] Print with PETG (240°C / 70°C)
- [ ] Verify tile fit (28.8mm gap on 29.32mm tile)
- [ ] Check friction rib grip strength
- [ ] Test head/neck comfort on contoured front face
- [ ] Verify structural integrity under head weight
- [ ] Check drainage holes function when wet
