# Spa Headrest — Design Specification

## Model Identity

| Field          | Value                                          |
|----------------|------------------------------------------------|
| Name           | Spa Headrest — Pillow-Style with Tile Clip     |
| Version        | 001                                            |
| Source         | `models/spa_headrest/spa_headrest_001.scad`     |
| Output         | `models/spa_headrest/output/`                   |
| Branch         | `claude/trusting-lalande`                       |
| Material       | PETG (240°C nozzle, 70°C bed)                  |

## Design Intent

A pillow-shaped headrest that clips onto a spa tile overhang via a friction-fit slot. The front face has a smooth, flowing ergonomic contour (convex at head height, concave at neck) for comfortable head and neck support. Triangular gussets above and below the slot transfer head load into the tile and prevent rotation.

## Tile Parameters

| Parameter         | Value    | Notes                              |
|-------------------|----------|------------------------------------|
| Tile thickness    | 29.32 mm | Measured                           |
| Tile overhang     | 40 mm    | How far tile extends into spa      |
| Tile surface      | Smooth / glazed | Requires friction features  |

## Overall Dimensions

| Axis | Dimension | Description                                   |
|------|-----------|-----------------------------------------------|
| X    | ~119 mm   | Depth — pad + slot depth                      |
| Y    | 250 mm    | Width — along tile edge                       |
| Z    | ~188 mm   | Height — pad height (print orientation)       |

**Print pose**: back surface flat on bed, slot/supports facing up.

## Component Specifications

### Pad (main body)

| Parameter              | Value   | Notes                           |
|------------------------|---------|---------------------------------|
| Width                  | 250 mm  | Along tile edge (Z axis)        |
| Height                 | 200 mm  | Vertical coverage               |
| Depth (max)            | 80 mm   | Back to contour peak            |
| Wall thickness         | 6 mm    | Hollow shell                    |
| Top corner radius      | 40 mm   | Rounded top corners             |
| Bottom corners         | Square  | Flat base for printing          |

### Front Face Contour (Ergonomic)

| Parameter              | Value   | Notes                           |
|------------------------|---------|---------------------------------|
| Head bulge             | +10 mm  | Convex at upper zone            |
| Neck dip               | -12 mm  | Concave at mid zone (the dent)  |
| Head center            | 70%     | From bottom (140mm up)          |
| Neck center            | 40%     | From bottom (80mm up)           |
| Profile                | Gaussian| Smooth flowing, no hard zones   |

### Tile Slot

| Parameter           | Value   | Notes                              |
|---------------------|---------|------------------------------------|
| Slot gap            | 28.8 mm | Interference fit on 29.32mm tile   |
| Slot depth          | 40 mm   | How far tile inserts               |
| Arm thickness       | 5 mm    | Top and bottom arms                |
| Entry chamfer       | 2 mm    | Flare at slot opening              |
| Friction ribs       | 0.4 mm  | Height, 2mm spacing, 1mm width    |

### Triangle Supports

| Feature              | Description                               |
|----------------------|-------------------------------------------|
| Top gusset           | Pad top to slot top, full width           |
| Bottom gusset        | Slot bottom to pad bottom, full width     |
| Purpose              | Transfer load, prevent rotation           |

### Drainage

| Feature               | Spec                              |
|-----------------------|-----------------------------------|
| Bottom drain holes    | 3 holes, 8mm diameter             |
| Internal rib notches  | Drainage cutouts at bottom        |

### Structure

| Parameter           | Value   | Notes                              |
|---------------------|---------|------------------------------------|
| Internal ribs       | 3       | Structural ribs, 3mm thick         |
| Shell construction   | Hollow | 6mm walls with offset cavity       |

## Iteration Log

| Version | Date       | Changes                                    |
|---------|------------|--------------------------------------------|
| 001     | 2026-03-16 | Initial pillow-style design with tile slot  |
