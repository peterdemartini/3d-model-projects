# Spa Head & Neck Rest — Design Specification

## Model Identity

| Field          | Value                                          |
|----------------|------------------------------------------------|
| Name           | Spa Head & Neck Rest                           |
| Version        | 001                                            |
| Source         | `models/spa_headrest/spa_headrest_001.scad`     |
| Output         | `models/spa_headrest/output/`                   |
| Branch         | `claude/youthful-rhodes`                        |
| Material       | PETG (240 C nozzle, 70 C bed)                  |

## Design Intent

A clip-on head and neck rest for a custom spa. The tile at the spa edge overhangs into the interior and its sharp edge is uncomfortable to lean against. This rest clips onto the tile overhang and provides a contoured surface with a neck roll and head cradle.

## Tile Parameters

| Parameter         | Value    | Notes                              |
|-------------------|----------|------------------------------------|
| Tile thickness    | 30 mm    | Measured 29.32 mm on one tile      |
| Tile overhang     | 40 mm    | How far tile extends into spa      |
| Tile surface      | Smooth / glazed | Requires friction features  |

## Overall Dimensions

| Axis | Dimension | Description                                   |
|------|-----------|-----------------------------------------------|
| X    | 250 mm    | Width — spans along the tile edge             |
| Y    | ~140 mm   | Depth — 30 mm clip inward + 30 mm tile + 80 mm rest |
| Z    | ~195 mm   | Height — clip top arm + 30 mm tile + 160 mm rest |

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
| Shell wall thickness| 4 mm    | Throughout                         |
| Internal ribs       | 3       | Vertical ribs, 3 mm thick         |
| Back wall           | 4 mm    | Flat, faces tile                   |

### Drainage

| Feature               | Spec                              |
|-----------------------|-----------------------------------|
| Clip drain slots      | 4 oval slots, 8 mm x 20 mm       |
| Bottom drain holes    | 3 holes, 8 mm diameter            |
| Internal channels     | Ribs don't fully seal compartments |

### Comfort

| Feature              | Value                              |
|----------------------|------------------------------------|
| Edge fillets         | 5-8 mm radius on all outer edges   |
| Surface finish       | Smooth (printed face-up)           |

## Print Settings

| Parameter         | Value       |
|-------------------|-------------|
| Layer height      | 0.2 mm      |
| Perimeters        | 3-4 walls   |
| Infill            | 15-20 %     |
| Material          | PETG        |
| Nozzle temp       | 240 C       |
| Bed temp          | 70 C        |
| Supports          | None (designed to avoid >45 deg overhangs) |

## Tolerances Summary

| Fit            | Clearance    | Application          |
|----------------|-------------|----------------------|
| Tile clip      | -0.25 mm/side | Interference fit (friction grip) |
| Friction ribs  | +0.4 mm height | Extra grip on glazed tile |

## Iteration Log

| Version | Date       | Changes                      |
|---------|------------|------------------------------|
| 001     | 2026-03-06 | Initial design               |
