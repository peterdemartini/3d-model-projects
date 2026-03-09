# Spa Neck Rest — Design Specification

## Model Identity

| Field          | Value                                          |
|----------------|------------------------------------------------|
| Name           | Spa Neck Rest                                  |
| Version        | 003                                            |
| Source         | `models/spa_headrest/spa_headrest_001.scad`     |
| Output         | `models/spa_headrest/output/`                   |
| Branch         | `claude/youthful-rhodes`                        |
| Material       | PETG (235 C nozzle, 70 C bed)                  |

## Design Intent

A clip-on neck rest for a custom spa. The tile at the spa edge overhangs into the interior and its sharp edge is uncomfortable to lean against. This rest wraps around the tile — the clip grips the tile in the middle, with the contoured rest surface extending both above and below. The top of the rest is flush with the tile's top surface.

## Tile Parameters

| Parameter         | Value    | Notes                              |
|-------------------|----------|------------------------------------|
| Tile thickness    | 30 mm    | Measured 29.32 mm on one tile      |
| Tile overhang     | 40 mm    | How far tile extends into spa      |
| Tile surface      | Smooth / glazed | Requires friction features  |

## Overall Dimensions (print-pose, post-rotation)

| Axis | Dimension | Description                                        |
|------|-----------|----------------------------------------------------|
| X    | ~125 mm   | Depth — clip spine to rest front                   |
| Y    | 250 mm    | Width — spans along the tile edge                  |
| Z    | ~117 mm   | Height — rest bottom to rest top (40 + 37 + 40)    |

**Print pose**: back surface (tile-facing) flat on bed, clip in the middle height.

## Component Specifications

### Clip (C-shape, wraps around tile, centered vertically)

| Parameter           | Value   | Notes                              |
|---------------------|---------|------------------------------------|
| Clip gap            | 28.8 mm | Interference fit on 29.32 mm tile  |
| Top arm length      | 15 mm   | Sits on top of tile surface        |
| Bottom arm length   | 30 mm   | Extends inward under tile          |
| Arm thickness       | 4 mm    | Both top and bottom arms           |
| Clip Y position     | Y=40 to Y=76.8 | Centered in model height    |
| Friction ribs       | 0.4 mm  | Height, 2 mm spacing, on all inner surfaces |
| Entry chamfer       | 2 mm    | Flared opening to guide tile in    |

### Rest Surface (contoured, neck-only)

| Parameter              | Value    | Notes                           |
|------------------------|----------|---------------------------------|
| Rest below clip        | 40 mm    | Hangs below tile                |
| Rest above clip        | 40 mm    | Flush with tile top surface     |
| Total usable height    | 80 mm    | v003: was 160 mm                |
| Neck roll protrusion   | 15 mm    | Peak of convex bump (centered)  |
| Depth (protrusion)     | 80 mm    | From tile face into spa         |

### Structure

| Parameter           | Value   | Notes                              |
|---------------------|---------|------------------------------------|
| Shell wall thickness| 6 mm    | Throughout                         |
| Internal ribs       | 3       | Vertical ribs, 3 mm thick         |
| Support braces      | 2       | 45 deg triangles above and below clip |
| Back wall           | 6 mm    | Flat, faces tile                   |

### Drainage

| Feature               | Spec                              |
|-----------------------|-----------------------------------|
| Clip drain slots      | 4 rectangular slots, 8 mm × 20 mm |
| Bottom drain holes    | 3 holes, 8 mm diameter            |
| Internal channels     | Ribs don't fully seal compartments |

### Comfort

| Feature              | Value                              |
|----------------------|------------------------------------|
| Edge fillets         | 5-8 mm radius on all outer edges   |
| Surface finish       | Smooth (printed face-up)           |

## Print Settings

| Parameter                | Value       | Notes                                          |
|--------------------------|-------------|-------------------------------------------------|
| Layer height             | 0.16 mm     | Finer layers improve overhang quality           |
| Perimeters               | 3-4 walls   |                                                 |
| Infill                   | 20-25 % gyroid | Gyroid gives omnidirectional support         |
| Material                 | PETG        |                                                 |
| Nozzle temp              | 235 C       | Cooler = faster solidification                  |
| Bed temp                 | 70 C        |                                                 |
| Max print speed          | 150 mm/s    | Reduce from default to lower nozzle-knock risk  |
| Outer wall speed         | 80 mm/s     | Slower outer walls bond better                  |
| Slow down for overhangs  | On          | Bambu Studio auto-slows on detected overhangs   |
| Min layer time           | 12 s        | More cooling time per layer                     |
| Part cooling fan         | 70-80 %     | Aggressive cooling                              |
| Supports                 | None        | Two 45 deg braces designed in; no support needed |

### Pre-Print Checklist

- Dry PETG filament (55 C for 4-6 hours) — wet PETG creates steam bubbles causing clogs
- Use textured PEI plate for PETG adhesion
- Clean bed with IPA before print
- Enable spaghetti detection (Medium or High sensitivity) in Bambu Studio

## Tolerances Summary

| Fit            | Clearance    | Application          |
|----------------|-------------|----------------------|
| Tile clip      | -0.26 mm/side | Interference fit (friction grip) |
| Friction ribs  | +0.4 mm height | Extra grip on glazed tile |

## Iteration Log

| Version | Date       | Changes                      |
|---------|------------|------------------------------|
| 001     | 2026-03-06 | Initial design (clip at top, 160mm rest, neck+head) |
| 002     | 2026-03-08 | Fix print failure: wall 4→6mm, ribs 3→5, head zone ties |
| 003     | 2026-03-08 | Full redesign: wrap-around layout, clip centered, neck-only 80mm, no head cradle |
