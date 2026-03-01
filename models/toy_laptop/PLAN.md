# PLAN.md — Toy Laptop 3D Model

Persistent specification document. **Update this file with every iteration** that
changes dimensions, tolerances, or design decisions. Keep the iteration log current.

---

## Model Identity

| Field           | Value                                           |
|-----------------|-------------------------------------------------|
| Model name      | `toy_laptop`                                    |
| Current version | `001`                                           |
| Source file     | `models/toy_laptop/toy_laptop_001.scad`         |
| Output dir      | `models/toy_laptop/output/`                     |
| Branch          | `feat/toy-laptop-v1`                            |

---

## Design Intent

A single-piece, print-in-place toy laptop. Both the base and lid are printed
together in the same orientation with a captive friction hinge that allows the
lid to open and close after printing. Designed for AMS multi-color printing on
the Bambu Lab H2D with no supports required.

---

## Overall Dimensions

| Part              | X (width) | Y (depth) | Z (height/thickness) |
|-------------------|-----------|-----------|----------------------|
| Base              | 250 mm    | 180 mm    | 10 mm                |
| Lid               | 250 mm    | 180 mm    | 8 mm                 |
| Print pose (open) | 250 mm    | 180 mm    | ~187 mm              |

**Print orientation:** 110° open — base flat on bed, lid rises at 70° from
horizontal. This provides full AMS color-change access to the screen pocket and
requires no supports on the H2D.

> Z envelope at 110° ≈ base (10 mm) + hinge barrel radius (~8 mm) + lid vertical
> rise (sin(70°) × 180 mm ≈ 169 mm) ≈ 187 mm. Well within the H2D Z limit of 325 mm.

---

## Hinge

| Parameter             | Value                           |
|-----------------------|---------------------------------|
| Type                  | Captive pin, friction           |
| Style                 | Full-width barrel (spans 250 mm)|
| Print pose            | 110° open                       |
| Hard stop             | 135° (cannot open further)      |
| Pin diameter          | 3.0 mm                          |
| Bore inner diameter   | 3.4 mm                          |
| Bore radial clearance | 0.2 mm per side                 |
| Total bore clearance  | 0.4 mm                          |
| Hinge axis            | Full X width (250 mm)           |
| Min barrel wall       | ≥ 1.2 mm (structural minimum)   |

The hinge is a single continuous barrel spanning the full X width. The pin is
a captive feature printed in-place inside the barrel. The 0.2 mm radial
clearance matches the "slip fit" spec from AGENTS.md. This should free with
gentle flexing after printing.

The 135° hard stop is implemented as a geometric shoulder on the base-side
barrel collar that contacts a lug on the lid when fully open. The stop geometry
is designed so it does not interfere when the lid is fully closed.

---

## Keyboard

| Parameter           | Value                                  |
|---------------------|----------------------------------------|
| Location            | Recessed bed in base, near hinge end   |
| Layout              | ANSI-ish simplified (US layout)        |
| Key style           | Raised keycaps from recessed bed       |
| Keycap nominal size | ~15 × 15 mm (smaller for function row) |
| Keycap height       | 2–3 mm above key bed surface           |
| Keycap sidewall     | ~0.8 mm (WARN from validator expected) |
| Bed recess depth    | 1.5 mm below base top surface          |

Rows (back to front, near hinge to front):
1. Function row (Esc + F1–F12)
2. Number row (` 1–0 - = Backspace)
3. Tab row (Tab Q–P [ ] \)
4. Caps row (Caps A–L ; ' Enter)
5. Shift row (LShift Z–M , . / RShift)
6. Bottom row (Ctrl, Win, Alt, Space, Alt, Fn, Ctrl)

---

## Trackpad

| Parameter        | Value                               |
|------------------|-------------------------------------|
| Location         | Centered in base, front of keyboard |
| Style            | Recessed rectangular pocket         |
| Size             | 80 × 55 mm                          |
| Recess depth     | 0.5 mm                              |

---

## Screen

| Parameter         | Value                                   |
|-------------------|-----------------------------------------|
| Location          | Recessed pocket on inner face of lid    |
| Bezel width       | 15 mm all sides                         |
| Pocket width      | 220 mm (250 − 2 × 15)                  |
| Pocket height     | 150 mm (180 − 2 × 15)                  |
| Pocket depth      | 2.5 mm                                 |
| Remaining lid wall| 5.5 mm (8 mm lid − 2.5 mm pocket)      |

The screen is not a separate part — it is a recessed region in the lid with a
clear color boundary for AMS painting in BambuStudio.

---

## Bump Stops

Two small dome features on the inner face of the lid, at the top-left and
top-right corners of the screen bezel band. They contact the keyboard area
when the lid closes, giving a satisfying click and preventing the screen
surface from resting directly on the keys.

| Parameter | Value                                            |
|-----------|--------------------------------------------------|
| Count     | 2                                                |
| Location  | Top-left and top-right of screen bezel, lid face |
| Shape     | Dome (hemisphere)                                |
| Diameter  | 3.0 mm                                           |
| Height    | 1.0 mm                                           |

---

## Multi-Color Strategy

| Region          | AMS Slot | Suggested Color         |
|-----------------|----------|-------------------------|
| Body shell      | 1        | Space gray / dark gray  |
| Keycap tops     | 2        | Light gray              |
| Screen bezel    | 3        | Black                   |
| Screen surface  | 4        | Dark gray / charcoal    |

Color boundaries are achieved via BambuStudio paint-in (single-body STL) or
by splitting the 3MF by geometry region. The recessed screen pocket and raised
keycap geometry provide natural color selection targets.

---

## Print Settings

Inherit defaults from AGENTS.md with the following overrides:

| Parameter     | Value    | Reason                                   |
|---------------|----------|------------------------------------------|
| Perimeters    | 4        | Extra strength for hinge barrel walls    |
| Infill        | 20 %     | Slightly heavier for toy durability      |
| Layer height  | 0.15 mm  | Better keycap and bezel definition       |
| Support       | None     | Model designed support-free at 110° pose |

---

## Tolerances Summary

| Feature                | Clearance     | Fit type                       |
|------------------------|---------------|--------------------------------|
| Hinge pin / bore       | 0.2 mm radial | Slip fit (AGENTS.md spec)      |
| Keycap ledge to bed    | 0.1 mm        | Press fit (solid, no movement) |
| Bump stop height       | 1.0 mm        | Clearance gap when open        |

---

## Iteration Log

| Version | Date       | Changes                                             |
|---------|------------|-----------------------------------------------------|
| 001     | 2026-03-01 | Initial scaffolding — spec established, no .scad yet |

---

## Known Issues / Watch Items

- `watertight` check will **FAIL** on early exports if hinge gap geometry creates
  open mesh edges at the pin/bore interface. Expected on v001. Fix with tighter
  `difference()` depth or `trimesh.repair.fill_holes()`.
- `wall_thickness` **WARN** is expected and acceptable for keycap sidewalls
  (~0.8 mm). This is a deliberate design choice — the slicer will handle it.
- Hard stop geometry must be visually verified with `/preview-scad` at
  `hinge_angle = 135` before exporting a final version.
- If minimum wall drops below 0.4 mm anywhere, the slicer will skip those
  features; redesign keycap geometry if that occurs.
