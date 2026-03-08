# Spa Head & Neck Rest — Design Specification

## Model Identity

| Field          | Value                                          |
|----------------|------------------------------------------------|
| Name           | Spa Head & Neck Rest                           |
| Version        | 002                                            |
| Source         | `models/spa_headrest/spa_headrest_001.scad`     |
| Output         | `models/spa_headrest/output/`                   |
| Branch         | `claude/youthful-rhodes`                        |
| Material       | PETG (235 C nozzle, 70 C bed)                  |

## Design Intent

A clip-on head and neck rest for a custom spa. The tile at the spa edge overhangs into the interior and its sharp edge is uncomfortable to lean against. This rest clips onto the tile overhang and provides a contoured surface with a neck roll and head cradle.

## Tile Parameters

| Parameter         | Value    | Notes                              |
|-------------------|----------|------------------------------------|
| Tile thickness    | 30 mm    | Measured 29.32 mm on one tile      |
| Tile overhang     | 40 mm    | How far tile extends into spa      |
| Tile surface      | Smooth / glazed | Requires friction features  |

## Overall Dimensions (print-pose, post-rotation)

| Axis | Dimension | Description                                        |
|------|-----------|----------------------------------------------------|
| X    | ~140 mm   | Depth — clip spine to rest front                   |
| Y    | 250 mm    | Width — spans along the tile edge                  |
| Z    | ~197 mm   | Height — rest bottom to clip top (160 + 4 + 29 + 4)|

**Print pose**: back surface (tile-facing) flat on bed, clip arms facing up.

## Component Specifications

### Clip (C-shape, wraps around tile)

| Parameter           | Value   | Notes                              |
|---------------------|---------|------------------------------------|
| Clip gap            | 28.8 mm | Interference fit on 29.32 mm tile  |
| Top arm length      | 15 mm   | Sits on top of tile surface        |
| Bottom arm length   | 30 mm   | Extends inward under tile          |
| Arm thickness       | 4 mm    | Both top and bottom arms           |
| Friction ribs       | 0.4 mm  | Height, 2 mm spacing, on all inner surfaces |
| Entry chamfer       | 2 mm    | Flared opening to guide tile in    |

### Rest Surface (contoured, two-zone)

| Parameter              | Value   | Notes                           |
|------------------------|---------|---------------------------------|
| Total height           | 160 mm  | Vertical, hanging from tile     |
| Neck roll zone         | 55 mm   | Lower portion, convex bump      |
| Neck roll protrusion   | 15 mm   | Peak of convex bump             |
| Neck roll radius       | ~40 mm  | Radius of convex curve          |
| Head area zone         | 105 mm  | Upper portion, concave cradle   |
| Head area depth        | 8 mm    | Depth of concave recess         |
| Head area radius       | ~120 mm | Radius of concave curve         |
| Depth (protrusion)     | 80 mm   | From tile face into spa         |

### Structure

| Parameter           | Value   | Notes                              |
|---------------------|---------|------------------------------------|
| Shell wall thickness| 6 mm    | Throughout (v002: was 4 mm)        |
| Internal ribs       | 5       | Vertical ribs, 3 mm thick (v002: was 3) |
| Head zone tie ribs  | 3       | Horizontal ribs at Y=90,120,150 mm |
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
| Layer height             | 0.16 mm     | v002: was 0.2; finer layers improve overhang quality |
| Perimeters               | 3-4 walls   |                                                 |
| Infill                   | 20-25 % gyroid | v002: was 15-20%; gyroid gives omnidirectional support |
| Material                 | PETG        |                                                 |
| Nozzle temp              | 235 C       | v002: was 240; cooler = faster solidification   |
| Bed temp                 | 70 C        |                                                 |
| Max print speed          | 150 mm/s    | v002: reduce from default to lower nozzle-knock risk |
| Outer wall speed         | 80 mm/s     | Slower outer walls bond better on concave surfaces |
| Slow down for overhangs  | On          | Bambu Studio auto-slows on detected overhangs   |
| Min layer time           | 12 s        | v002: was 8; more cooling time per layer         |
| Part cooling fan         | 70-80 %     | Aggressive cooling in upper zones                |
| Supports                 | None        | Designed to avoid >45 deg overhangs              |

### Pre-Print Checklist

- Dry PETG filament (55 C for 4-6 hours) — wet PETG creates steam bubbles causing clogs
- Use textured PEI plate for PETG adhesion
- Clean bed with IPA before print
- Enable spaghetti detection (Medium or High sensitivity) in Bambu Studio

## Tolerances Summary

| Fit            | Clearance    | Application          |
|----------------|-------------|----------------------|
| Tile clip      | -0.25 mm/side | Interference fit (friction grip) |
| Friction ribs  | +0.4 mm height | Extra grip on glazed tile |

## Iteration Log

| Version | Date       | Changes                      |
|---------|------------|------------------------------|
| 001     | 2026-03-06 | Initial design               |
| 002     | 2026-03-08 | Fix print failure: wall 4→6mm, ribs 3→5, add head zone ties, tune print settings |
