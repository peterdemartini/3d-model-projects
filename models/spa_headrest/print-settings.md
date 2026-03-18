# Spa Headrest v002 — Print Settings

Recommended BambuStudio settings for Bambu Lab H2D.

## Material

| Parameter | Value |
|-----------|-------|
| Filament | PETG |
| Nozzle temp | 240°C |
| Bed temp | 70°C |
| Nozzle diameter | 0.4mm |

## Print Settings

| Parameter | Value | Reason |
|-----------|-------|--------|
| Layer height | 0.20mm | Standard quality for large part |
| Perimeters (walls) | 3 | Structural for spa use |
| Top layers | 4 | Solid top for head contact comfort |
| Bottom layers | 4 | Solid base for bed adhesion |
| Infill density | 15% | Solid body — infill replaces v1 hollow shell |
| Infill pattern | Gyroid | Uniform strength, good water drainage |
| Print speed | 150 mm/s | Slower than default for PETG adhesion |
| Supports | None | All overhangs < 45° (rounded corners are gradual) |
| Bed adhesion | Brim, 5mm | Large footprint, PETG can warp |

## Orientation

Print with **pad bottom on bed** (default from STL export). The slot extends
backward from the base. The contoured front face prints as a gradual vertical
curve — no support needed.

## Estimates

| Metric | Value |
|--------|-------|
| Bounding box | ~105 × 200 × 150 mm |
| Volume | ~2,547 cm³ |
| Est. filament | ~150–200g PETG |
| Est. print time | ~6–8 hours |

## Notes

- No supports required — design is overhang-safe
- Gyroid infill recommended for water drainage through the solid body
- Consider printing with textured PEI plate for better PETG release
- The slot gap (29.0mm) provides 0.32mm interference on a 29.32mm tile
