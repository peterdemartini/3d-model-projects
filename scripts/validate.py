#!/usr/bin/env python3
"""
validate.py - Validate 3D model files for Bambu Lab H2D / BambuStudio compatibility.

Usage:
    python scripts/validate.py output/model.stl
    python scripts/validate.py output/              # validate all files in directory
"""

import sys
import json
import argparse
from pathlib import Path

import numpy as np
import trimesh

# ── Bambu Lab H2D build volume (mm) ─────────────────────────────────────────
BUILD_VOLUME_MM = (350.0, 320.0, 325.0)  # X, Y, Z

# Supported extensions
SUPPORTED_EXTENSIONS = {".stl", ".3mf", ".obj", ".step", ".stp"}

# Minimum wall thickness (mm) – 2 × 0.4 mm nozzle diameter
MIN_WALL_THICKNESS_MM = 0.8

# ── Hinge validation thresholds ──────────────────────────────────────────────
RADIAL_CLEARANCE_MIN_MM = 0.4
RADIAL_CLEARANCE_MAX_MM = 0.8
KNUCKLE_GAP_MIN_MM = 0.4
HARD_STOP_MAX_DEG = 135
LID_SLOT_CLEARANCE_MIN_MM = 0.4
PIN_HEAD_CLEARANCE_MIN_MM = 0.20

# ── Hinge sweep validation thresholds ─────────────────────────────────────────
SWEEP_ANGLE_STEP_DEG = 1.0
SWEEP_MIN_CLEARANCE_MM = 0.3

# ── Closure validation thresholds ────────────────────────────────────────────
MIN_CLOSURE_CLEARANCE_MM = 2.0


# ── Result helpers ────────────────────────────────────────────────────────────

class ValidationResult:
    """Holds the outcome of a single validation check."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"

    def __init__(self, status: str, check: str, message: str):
        self.status = status
        self.check = check
        self.message = message

    def __repr__(self) -> str:
        return f"[{self.status}] {self.check}: {self.message}"


def _pass(check: str, message: str) -> ValidationResult:
    return ValidationResult(ValidationResult.PASS, check, message)


def _warn(check: str, message: str) -> ValidationResult:
    return ValidationResult(ValidationResult.WARN, check, message)


def _fail(check: str, message: str) -> ValidationResult:
    return ValidationResult(ValidationResult.FAIL, check, message)


# ── Individual checks ─────────────────────────────────────────────────────────

def check_file_exists(path: Path) -> ValidationResult:
    """Check that the file exists, is a regular file, and is readable."""
    if not path.exists() or not path.is_file():
        return _fail("file_exists", f"File not found: {path}")
    try:
        path.open("rb").close()
    except OSError as exc:
        return _fail("file_exists", f"File is not readable: {path} ({exc})")
    return _pass("file_exists", f"File found and readable: {path}")


def check_supported_format(path: Path) -> ValidationResult:
    ext = path.suffix.lower()
    if ext in SUPPORTED_EXTENSIONS:
        return _pass("supported_format", f"Extension '{ext}' is supported by BambuStudio")
    return _fail(
        "supported_format",
        f"Extension '{ext}' is not supported. Use one of: {sorted(SUPPORTED_EXTENSIONS)}",
    )


def load_mesh(path: Path) -> tuple[trimesh.Trimesh | None, str | None]:
    """Load a mesh and return (mesh, error_string). error_string is None on success."""
    try:
        mesh = trimesh.load(str(path), force="mesh")
        if mesh is None:
            return None, "trimesh returned None"
        # If it loaded as a Scene (e.g. multi-body 3MF), merge into one mesh
        if isinstance(mesh, trimesh.Scene):
            if len(mesh.geometry) == 0:
                return None, "Scene contains no geometry"
            mesh = trimesh.util.concatenate(list(mesh.geometry.values()))
        return mesh, None
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def check_loadable(path: Path) -> tuple[ValidationResult, trimesh.Trimesh | None]:
    """Attempt to load the mesh and return a result alongside the mesh (or None on failure)."""
    mesh, err = load_mesh(path)
    if err:
        return _fail("loadable", f"Failed to load mesh: {err}"), None
    return _pass("loadable", "Mesh loaded successfully"), mesh


def check_non_empty(mesh: trimesh.Trimesh) -> ValidationResult:
    """Check that the mesh contains at least one face and one vertex."""
    if len(mesh.faces) == 0 or len(mesh.vertices) == 0:
        return _fail("non_empty", "Mesh has no faces or vertices")
    return _pass(
        "non_empty",
        f"Mesh has {len(mesh.faces):,} faces and {len(mesh.vertices):,} vertices",
    )


def check_watertight(mesh: trimesh.Trimesh) -> ValidationResult:
    if mesh.is_watertight:
        return _pass("watertight", "Mesh is watertight (manifold)")
    # For multi-body meshes (e.g. print-in-place hinge with disconnected
    # base and lid), check each body individually. If all bodies are
    # individually watertight, the combined mesh is valid for slicing.
    try:
        bodies = mesh.split()
        if len(bodies) > 1:
            non_wt = [i for i, b in enumerate(bodies) if not b.is_watertight]
            if not non_wt:
                return _pass(
                    "watertight",
                    f"Mesh has {len(bodies)} separate bodies, each individually watertight",
                )
            return _fail(
                "watertight",
                f"Mesh has {len(bodies)} separate bodies; "
                f"body(ies) {non_wt} are NOT watertight. "
                "Non-watertight models may cause slicing failures in BambuStudio.",
            )
    except Exception:  # noqa: BLE001
        pass

    # Single body that isn't watertight — count open edges
    try:
        edges = mesh.edges_sorted.reshape(-1, 2)
        _, counts = np.unique(edges, axis=0, return_counts=True)
        open_edge_count = int(np.sum(counts == 1))
        detail = f"open edge count: {open_edge_count}"
    except Exception:  # noqa: BLE001
        detail = "open edge count: unknown"
    return _fail(
        "watertight",
        f"Mesh is NOT watertight (open/non-manifold edges detected; {detail}). "
        "Non-watertight models may cause slicing failures in BambuStudio.",
    )


def check_build_volume(mesh) -> ValidationResult:
    bounds = mesh.bounds  # shape (2, 3): [[xmin,ymin,zmin],[xmax,ymax,zmax]]
    size = bounds[1] - bounds[0]  # [dx, dy, dz]
    bx, by, bz = BUILD_VOLUME_MM
    sx, sy, sz = size

    fits_x = sx <= bx
    fits_y = sy <= by
    fits_z = sz <= bz

    dims = f"{sx:.1f} × {sy:.1f} × {sz:.1f} mm"
    limit = f"{bx:.0f} × {by:.0f} × {bz:.0f} mm"

    if fits_x and fits_y and fits_z:
        return _pass("build_volume", f"Model dimensions ({dims}) fit within build volume ({limit})")

    violations = []
    if not fits_x:
        violations.append(f"X={sx:.1f} > {bx:.0f}")
    if not fits_y:
        violations.append(f"Y={sy:.1f} > {by:.0f}")
    if not fits_z:
        violations.append(f"Z={sz:.1f} > {bz:.0f}")

    return _fail(
        "build_volume",
        f"Model ({dims}) exceeds Bambu H2D build volume ({limit}): {', '.join(violations)}",
    )


def check_positive_volume(mesh) -> ValidationResult:
    try:
        vol = mesh.volume
    except Exception as exc:  # noqa: BLE001
        return _warn("positive_volume", f"Could not compute volume: {exc}")
    if vol > 0:
        return _pass("positive_volume", f"Volume = {vol:.2f} mm³ (normals look correct)")
    if vol < 0:
        return _warn(
            "positive_volume",
            f"Volume = {vol:.2f} mm³ (negative — face normals may be inverted). "
            "Run trimesh.repair.fix_normals(mesh) to fix.",
        )
    return _warn("positive_volume", "Volume = 0 (mesh may be a surface / open shell)")


def check_no_degenerate_faces(mesh) -> ValidationResult:
    areas = mesh.area_faces
    degenerate = int(np.sum(areas < 1e-10))
    if degenerate == 0:
        return _pass("no_degenerate_faces", "No zero-area (degenerate) faces found")
    return _warn(
        "no_degenerate_faces",
        f"{degenerate} degenerate face(s) with near-zero area. These may cause slicing artefacts.",
    )


def check_expected_dimensions(
    mesh, expected: tuple[float, float, float], tolerance_mm: float = 5.0
) -> ValidationResult:
    """
    Check that the bounding-box dimensions match the expected print-pose values.

    *expected* is a (W, D, H) tuple in mm.  Each axis is allowed ±tolerance_mm.
    This is a pose-validation proxy: a wrong hinge angle or rotated base would
    produce very different bounding-box dimensions.
    """
    bounds = mesh.bounds
    size = bounds[1] - bounds[0]
    sx, sy, sz = float(size[0]), float(size[1]), float(size[2])
    ex, ey, ez = expected

    ok_x = abs(sx - ex) <= tolerance_mm
    ok_y = abs(sy - ey) <= tolerance_mm
    ok_z = abs(sz - ez) <= tolerance_mm

    actual = f"{sx:.1f} × {sy:.1f} × {sz:.1f} mm"
    exp_str = f"{ex:.0f} × {ey:.0f} × {ez:.0f} mm"

    if ok_x and ok_y and ok_z:
        return _pass(
            "expected_dimensions",
            f"Model dimensions ({actual}) match expected ({exp_str}, ±{tolerance_mm:.0f} mm)",
        )

    violations = []
    if not ok_x:
        violations.append(f"X={sx:.1f} (expected {ex:.0f} ±{tolerance_mm:.0f})")
    if not ok_y:
        violations.append(f"Y={sy:.1f} (expected {ey:.0f} ±{tolerance_mm:.0f})")
    if not ok_z:
        violations.append(f"Z={sz:.1f} (expected {ez:.0f} ±{tolerance_mm:.0f})")

    return _fail(
        "expected_dimensions",
        f"Model dimensions ({actual}) do NOT match expected ({exp_str}, ±{tolerance_mm:.0f} mm): "
        + ", ".join(violations)
        + ". Check hinge_angle and print pose in the .scad file.",
    )


def check_base_on_bed(mesh, z_tolerance_mm: float = 0.5) -> ValidationResult:
    """
    Check that the model has geometry at Z ≈ 0, confirming the base (bottom face)
    sits flat on the print bed.

    For assembled print-in-place models (e.g. a laptop with the lid opened upward
    from the hinge), other parts may extend below Z=0.  We therefore look for
    vertex clusters *near* Z=0 from above — specifically, we check whether the
    minimum Z among vertices with Z ≥ -z_tolerance_mm is within tolerance of 0.
    This is equivalent to asking: "does the model have a flat surface at Z=0?"
    """
    verts_z = mesh.vertices[:, 2]
    # Find the lowest Z that is at or above -(tolerance), i.e. near the bed plane
    near_bed = verts_z[verts_z >= -z_tolerance_mm]
    if len(near_bed) == 0:
        return _fail(
            "base_on_bed",
            f"No vertices found at Z ≥ {-z_tolerance_mm:.1f} mm. "
            "The model may not have a flat base on the print bed.",
        )
    lowest_near_bed = float(near_bed.min())
    if abs(lowest_near_bed) <= z_tolerance_mm:
        return _pass(
            "base_on_bed",
            f"Model has geometry at Z = {lowest_near_bed:.2f} mm "
            f"(base sits flat on the print bed; overall Z range "
            f"{float(mesh.bounds[0][2]):.1f} to {float(mesh.bounds[1][2]):.1f} mm)",
        )
    return _fail(
        "base_on_bed",
        f"Lowest base vertex at Z = {lowest_near_bed:.2f} mm "
        f"(expected ≈ 0 mm, tolerance ±{z_tolerance_mm} mm). "
        "The model may be floating above the bed or oriented incorrectly.",
    )


def check_hinge_parameters(meta: dict) -> ValidationResult:
    """
    Verify print-in-place hinge geometry from sidecar metadata.

    Checks:
    - bore_d > pin_d (pin fits in bore)
    - radial clearance (bore_d - pin_d)/2 in [RADIAL_CLEARANCE_MIN_MM, RADIAL_CLEARANCE_MAX_MM]
    - barrel wall (barrel_od - bore_d)/2 ≥ min_wall_mm
    - hard_stop_angle ≤ HARD_STOP_MAX_DEG
    - knuckle_gap ≥ KNUCKLE_GAP_MIN_MM (axial clearance for FDM print-in-place)
    - lid_slot_clearance ≥ LID_SLOT_CLEARANCE_MIN_MM (lid must not obstruct base barrels)
    - pin_head_clearance ≥ PIN_HEAD_CLEARANCE_MIN_MM (pin head must not fuse with bore)
    """
    h = meta["hinge"]
    pin_d      = float(h["pin_d_mm"])
    bore_d     = float(h["bore_d_mm"])
    barrel_od  = float(h["barrel_od_mm"])
    min_wall   = float(h["min_wall_mm"])
    hard_stop  = float(h["hard_stop_angle_deg"])

    radial_clearance   = (bore_d - pin_d) / 2
    barrel_wall        = (barrel_od - bore_d) / 2
    knuckle_gap        = float(h.get("knuckle_gap_mm", 0))
    lid_slot_clearance = float(h.get("lid_slot_clearance_mm", 0))
    pin_head_clearance = float(h.get("pin_head_clearance_mm", 0))

    issues = []
    if bore_d <= pin_d:
        issues.append(f"bore_d ({bore_d}) ≤ pin_d ({pin_d}): pin cannot fit in bore")
    if not (RADIAL_CLEARANCE_MIN_MM <= radial_clearance <= RADIAL_CLEARANCE_MAX_MM):
        issues.append(
            f"radial clearance {radial_clearance:.2f} mm outside "
            f"[{RADIAL_CLEARANCE_MIN_MM:.2f}, {RADIAL_CLEARANCE_MAX_MM:.2f}] mm "
            f"(too tight → fused; too loose → sloppy)"
        )
    if barrel_wall < min_wall:
        issues.append(
            f"barrel wall {barrel_wall:.2f} mm < minimum {min_wall} mm "
            f"(risk of fracture during deflashing)"
        )
    if hard_stop > HARD_STOP_MAX_DEG:
        issues.append(f"hard_stop_angle {hard_stop}° > {HARD_STOP_MAX_DEG}° physical maximum")
    if knuckle_gap < KNUCKLE_GAP_MIN_MM:
        issues.append(
            f"knuckle_gap {knuckle_gap:.2f} mm < {KNUCKLE_GAP_MIN_MM:.2f} mm minimum "
            f"(axial clearance too tight for FDM print-in-place)"
        )
    if lid_slot_clearance < LID_SLOT_CLEARANCE_MIN_MM:
        issues.append(
            f"lid_slot_clearance {lid_slot_clearance:.2f} mm < {LID_SLOT_CLEARANCE_MIN_MM:.2f} mm minimum "
            f"(lid body obstructs base barrel knuckles — hinge will not rotate)"
        )
    if pin_head_clearance < PIN_HEAD_CLEARANCE_MIN_MM:
        issues.append(
            f"pin_head_clearance {pin_head_clearance:.2f} mm < {PIN_HEAD_CLEARANCE_MIN_MM:.2f} mm minimum "
            f"(pin head may fuse with bore wall during FDM printing)"
        )

    if not issues:
        return _pass(
            "hinge_parameters",
            f"Pin {pin_d} mm ∅, bore {bore_d} mm ∅, radial clearance "
            f"{radial_clearance:.2f} mm, barrel wall {barrel_wall:.2f} mm, "
            f"knuckle gap {knuckle_gap:.2f} mm, lid slot clearance {lid_slot_clearance:.2f} mm, "
            f"pin head clearance {pin_head_clearance:.2f} mm, hard stop {hard_stop:.0f}°",
        )
    return _fail("hinge_parameters", "; ".join(issues))


# ── Hinge sweep clearance helpers ────────────────────────────────────────────

def _rotate_point_around_x(y: float, z: float, angle_deg: float) -> tuple[float, float]:
    """Rotate point (y, z) around the X-axis by angle_deg degrees. Returns (y', z')."""
    rad = np.radians(angle_deg)
    c, s = np.cos(rad), np.sin(rad)
    return float(y * c - z * s), float(y * s + z * c)


def _point_to_box_clearance(
    py: float, pz: float,
    box_y_min: float, box_y_max: float,
    box_z_min: float, box_z_max: float,
) -> float:
    """Signed distance from point (py, pz) to axis-aligned box in YZ plane.

    Returns negative if inside, positive if outside, zero on boundary.
    """
    # Distance to each face (positive = outside that face)
    dy_min = box_y_min - py  # positive if point is below y_min
    dy_max = py - box_y_max  # positive if point is above y_max
    dz_min = box_z_min - pz
    dz_max = pz - box_z_max

    # If all are negative, point is inside — return negative of min penetration
    if dy_min <= 0 and dy_max <= 0 and dz_min <= 0 and dz_max <= 0:
        return max(dy_min, dy_max, dz_min, dz_max)  # negative, closest to 0

    # Point is outside — return distance to nearest face (positive)
    outside_y = max(dy_min, dy_max, 0.0)
    outside_z = max(dz_min, dz_max, 0.0)
    return float(np.sqrt(outside_y**2 + outside_z**2))


def compute_hinge_sweep_clearances(
    barrel_r: float,
    slot_clearance: float,
    slot_y_extra: float,
    slot_z_extra: float,
    base_d: float,
    base_h: float,
    lid_h: float,
    hard_stop_angle: float,
    stop_lug_h: float,
    stop_lug_w: float,
    shoulder_y_offset_factor: float,
    shoulder_z_offset: float,
    angle_step: float = SWEEP_ANGLE_STEP_DEG,
) -> dict:
    """Compute clearance between moving lid geometry and stationary base geometry
    at each angle from 0 to hard_stop_angle.

    The hinge axis is at assembly (Y=base_d, Z=base_h). The lid rotates by
    (180 - angle) degrees around X. In lid-local coords, the hinge axis is
    at (Y=0, Z=0).

    Returns dict with:
      - min_clearance_mm: overall minimum clearance across all angles
      - min_clearance_angle_deg: angle at minimum clearance
      - min_clearance_pair: geometry pair name at minimum
      - collision_detected: True if any clearance < 0
      - clearance_by_angle: list of {angle, clearances: {pair: value}}
    """
    # Base body region (the solid part, excluding the slot cutout)
    # The base body is a box from (Y=0, Z=0) to (Y=base_d, Z=base_h).
    # At lid-knuckle X positions, a slot is cut:
    slot_y_start = base_d - barrel_r - slot_clearance - slot_y_extra
    slot_y_end = base_d  # slot goes to rear edge
    slot_z_start = base_h - barrel_r - slot_clearance
    slot_z_end = slot_z_start + 2 * barrel_r + 2 * slot_clearance + slot_z_extra

    # Base hard-stop shoulder (assembly coords)
    shoulder_y_min = base_d + barrel_r * shoulder_y_offset_factor
    shoulder_y_max = shoulder_y_min + stop_lug_h
    shoulder_z_min = base_h + barrel_r + shoulder_z_offset
    shoulder_z_max = shoulder_z_min + stop_lug_w

    # Lid geometry points in lid-local coords (Y=0 is hinge axis, Z=0 is inner face)
    # Critical points on the lid plate near the hinge:
    # The lid plate extends from Y=0 to Y=base_d, Z=0 (inner) to Z=-lid_h (outer).
    # Near the hinge, the most critical points are at small Y values.
    lid_plate_points = []
    for y_l in [0.0, 0.5, 1.0, 2.0, 5.0]:
        for z_l in [0.0, -lid_h / 2, -lid_h]:
            lid_plate_points.append((y_l, z_l))

    # Barrel boundary points (circle at hinge axis, r=barrel_r)
    barrel_points = []
    for angle_sample in range(0, 360, 15):
        rad = np.radians(angle_sample)
        barrel_points.append((barrel_r * np.cos(rad), barrel_r * np.sin(rad)))

    # Stop lug corners in lid-local coords
    # The stop lug is at (Y=-stop_lug_h, Z=0) to (Y=0, Z=stop_lug_w)
    lug_corners = [
        (-stop_lug_h, 0.0),
        (-stop_lug_h, stop_lug_w),
        (0.0, 0.0),
        (0.0, stop_lug_w),
    ]

    clearance_by_angle = []
    global_min = float("inf")
    global_min_angle = 0.0
    global_min_pair = ""
    collision = False

    angles = np.arange(0, hard_stop_angle + angle_step / 2, angle_step)

    for theta in angles:
        rotation = 180.0 - theta
        angle_clearances = {}

        # --- Check 1: lid plate points vs base body (excluding slot) ---
        min_plate_clearance = float("inf")
        for y_l, z_l in lid_plate_points:
            y_rot, z_rot = _rotate_point_around_x(y_l, z_l, rotation)
            y_asm = base_d + y_rot
            z_asm = base_h + z_rot

            # Check if point is inside the base body (Y in [0, base_d], Z in [0, base_h])
            # but NOT inside the slot cutout
            in_base_y = 0 <= y_asm <= base_d
            in_base_z = 0 <= z_asm <= base_h
            in_slot_y = slot_y_start <= y_asm <= slot_y_end
            in_slot_z = slot_z_start <= z_asm <= slot_z_end

            if in_base_y and in_base_z and not (in_slot_y and in_slot_z):
                # Point is inside base body (collision!)
                # Compute penetration depth as negative clearance
                pen_y = min(y_asm, base_d - y_asm)
                pen_z = min(z_asm, base_h - z_asm)
                clearance = -min(pen_y, pen_z)
                min_plate_clearance = min(min_plate_clearance, clearance)
            elif in_slot_y and in_slot_z:
                # Point is in the slot — compute distance to slot walls
                dist_to_slot_y = y_asm - slot_y_start  # distance from front wall of slot
                dist_to_slot_z_lo = z_asm - slot_z_start
                dist_to_slot_z_hi = slot_z_end - z_asm
                slot_cl = min(dist_to_slot_y, dist_to_slot_z_lo, dist_to_slot_z_hi)
                min_plate_clearance = min(min_plate_clearance, slot_cl)
            else:
                # Point is outside base body — Euclidean distance in YZ
                dist_y = max(0 - y_asm, y_asm - base_d, 0.0)
                dist_z = max(0 - z_asm, z_asm - base_h, 0.0)
                clearance = float(np.hypot(dist_y, dist_z))
                min_plate_clearance = min(min_plate_clearance, clearance)

        angle_clearances["lid_plate_vs_base"] = min_plate_clearance

        # --- Check 2: barrel vs slot (sanity — should be constant) ---
        min_barrel_clearance = float("inf")
        for by, bz in barrel_points:
            # Barrel points are in hinge-axis coords, already in assembly:
            y_asm = base_d + by
            z_asm = base_h + bz

            in_base_y = 0 <= y_asm <= base_d
            in_base_z = 0 <= z_asm <= base_h
            in_slot_y = slot_y_start <= y_asm <= slot_y_end
            in_slot_z = slot_z_start <= z_asm <= slot_z_end

            if in_base_y and in_base_z and not (in_slot_y and in_slot_z):
                # Barrel point is inside base body but outside slot — collision
                pen_y = min(y_asm, base_d - y_asm)
                pen_z = min(z_asm, base_h - z_asm)
                min_barrel_clearance = min(min_barrel_clearance, -min(pen_y, pen_z))
            elif in_slot_y and in_slot_z:
                # Point is in the slot — compute distance to slot walls
                dist_y = y_asm - slot_y_start
                dist_z_lo = z_asm - slot_z_start
                dist_z_hi = slot_z_end - z_asm
                min_barrel_clearance = min(min_barrel_clearance, dist_y, dist_z_lo, dist_z_hi)
            else:
                # Point is outside base body — Euclidean distance
                dist_y = max(0 - y_asm, y_asm - base_d, 0.0)
                dist_z = max(0 - z_asm, z_asm - base_h, 0.0)
                min_barrel_clearance = min(min_barrel_clearance, float(np.hypot(dist_y, dist_z)))

        angle_clearances["barrel_vs_slot"] = min_barrel_clearance

        # --- Check 3: stop lug vs base shoulder ---
        min_lug_clearance = float("inf")
        for y_l, z_l in lug_corners:
            y_rot, z_rot = _rotate_point_around_x(y_l, z_l, rotation)
            y_asm = base_d + y_rot
            z_asm = base_h + z_rot

            lug_cl = _point_to_box_clearance(
                y_asm, z_asm,
                shoulder_y_min, shoulder_y_max,
                shoulder_z_min, shoulder_z_max,
            )
            min_lug_clearance = min(min_lug_clearance, lug_cl)

        angle_clearances["stop_lug_vs_shoulder"] = min_lug_clearance

        # --- Track overall minimum ---
        for pair_name, cl in angle_clearances.items():
            if cl < global_min:
                global_min = cl
                global_min_angle = float(theta)
                global_min_pair = pair_name
            if cl < 0:
                collision = True

        clearance_by_angle.append({
            "angle": float(theta),
            "clearances": angle_clearances,
        })

    return {
        "min_clearance_mm": float(global_min),
        "min_clearance_angle_deg": global_min_angle,
        "min_clearance_pair": global_min_pair,
        "collision_detected": collision,
        "clearance_by_angle": clearance_by_angle,
    }


def check_hinge_sweep(meta: dict) -> ValidationResult:
    """Validate hinge rotation clearance across the full angle range.

    Uses geometry parameters from meta["hinge"] to numerically estimate
    clearance between the moving lid geometry and stationary base geometry
    by sampling at fixed angle increments (e.g., 1 degree) from 0 to
    hard_stop_angle rather than performing a continuous analytic proof.
    """
    h = meta["hinge"]
    barrel_r = float(h["barrel_od_mm"]) / 2

    result = compute_hinge_sweep_clearances(
        barrel_r=barrel_r,
        slot_clearance=float(h.get("lid_slot_clearance_mm", 0.5)),
        slot_y_extra=float(h["slot_y_extra_mm"]),
        slot_z_extra=float(h["slot_z_extra_mm"]),
        base_d=float(h["base_d_mm"]),
        base_h=float(h["base_h_mm"]),
        lid_h=float(h["lid_h_mm"]),
        hard_stop_angle=float(h["hard_stop_angle_deg"]),
        stop_lug_h=float(h["stop_lug_h_mm"]),
        stop_lug_w=float(h["stop_lug_w_mm"]),
        shoulder_y_offset_factor=float(h["stop_shoulder_y_offset_factor"]),
        shoulder_z_offset=float(h["stop_shoulder_z_offset_mm"]),
    )

    min_cl = result["min_clearance_mm"]
    min_angle = result["min_clearance_angle_deg"]
    min_pair = result["min_clearance_pair"]

    if result["collision_detected"] or min_cl < SWEEP_MIN_CLEARANCE_MM:
        return _fail(
            "hinge_sweep",
            f"Sweep clearance insufficient: min clearance {min_cl:.2f} mm "
            f"at {min_angle:.0f}° ({min_pair}), "
            f"required ≥ {SWEEP_MIN_CLEARANCE_MM} mm",
        )

    return _pass(
        "hinge_sweep",
        f"Sweep clearance OK: min clearance {min_cl:.2f} mm "
        f"at {min_angle:.0f}° ({min_pair}), "
        f"checked 0°–{float(h['hard_stop_angle_deg']):.0f}° "
        f"in {SWEEP_ANGLE_STEP_DEG}° steps",
    )


def check_closure_clearance(meta: dict) -> ValidationResult:
    """
    Verify that the laptop lid can close fully without interference.

    Checks (using world-Y coordinates measured from the base front edge):
    - keyboard back edge Y < screen pocket front edge Y when closed (≥ 2 mm gap)
    - key protrusion above base top ≤ screen pocket depth (keys fit inside pocket)
    """
    c = meta["closure"]
    kb_back  = float(c["keyboard_back_edge_y_mm"])
    sc_front = float(c["screen_pocket_front_y_when_closed_mm"])
    key_prot = float(c["key_protrusion_above_base_mm"])
    sc_depth = float(c.get("screen_pocket_depth_mm", 2.5))

    issues = []

    clearance = sc_front - kb_back
    if clearance <= 0:
        issues.append(
            f"Keys (back edge Y={kb_back:.1f} mm) overlap screen pocket "
            f"(front edge Y={sc_front:.1f} mm when closed) — lid CANNOT close"
        )
    elif clearance < MIN_CLOSURE_CLEARANCE_MM:
        issues.append(
            f"Closure clearance {clearance:.1f} mm < {MIN_CLOSURE_CLEARANCE_MM} mm minimum "
            f"(keyboard back Y={kb_back:.1f}, screen pocket front Y={sc_front:.1f})"
        )

    if key_prot > sc_depth:
        issues.append(
            f"Key protrusion {key_prot:.2f} mm > screen pocket depth {sc_depth:.2f} mm — "
            f"keys would collide with lid inner face when closed"
        )

    if not issues:
        return _pass(
            "closure_clearance",
            f"Keyboard back edge Y={kb_back:.1f} mm, screen pocket front Y={sc_front:.1f} mm "
            f"(clearance {clearance:.1f} mm); key protrusion {key_prot:.2f} mm ≤ "
            f"screen pocket depth {sc_depth:.2f} mm",
        )
    return _fail("closure_clearance", "; ".join(issues))


def check_3mf_has_colors(path: Path) -> ValidationResult:
    """
    Check that a 3MF file contains multi-object color data for Bambu AMS printing.

    A Bambu-compatible multi-color 3MF must have:
      - At least 2 <object> elements (one per color/filament)
      - At least 1 <m:colorgroup> element (Bambu's format, one group per object)
        OR at least 1 <m:basematerials> group (generic 3MF spec fallback)
      - p:UUID attributes on objects (Production Extension, required by Bambu)

    OpenSCAD's color() is preview-only and is NOT exported to 3MF.
    Use scripts/colorize_3mf.py to produce a properly structured multi-color 3MF.
    """
    if path.suffix.lower() != ".3mf":
        return _pass("3mf_has_colors", "Not a 3MF file — color check skipped")

    import zipfile as _zipfile
    from xml.etree import ElementTree as _ET

    CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
    MAT_NS  = "http://schemas.microsoft.com/3dmanufacturing/material/2015/02"
    PROD_NS = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"

    try:
        with _zipfile.ZipFile(path) as zf:
            raw = zf.read("3D/3dmodel.model")
        root = _ET.fromstring(raw)
        objects     = root.findall(f".//{{{CORE_NS}}}object")
        colorgroups = root.findall(f".//{{{MAT_NS}}}colorgroup")
        basemats    = root.findall(f".//{{{MAT_NS}}}basematerials")
        # Check for Production Extension p:UUID (Bambu requirement)
        prod_uuid_attr = f"{{{PROD_NS}}}UUID"
        has_prod_uuid = any(obj.get(prod_uuid_attr) for obj in objects)

        color_groups_total = len(colorgroups) + len(basemats)
        format_note = (
            "Bambu colorgroup" if colorgroups
            else "basematerials" if basemats
            else "none"
        )

        if len(objects) >= 2 and color_groups_total >= 1 and has_prod_uuid:
            return _pass(
                "3mf_has_colors",
                f"{len(objects)} color object(s), {color_groups_total} color group(s) "
                f"({format_note}), p:UUID present — "
                "ready for Bambu AMS multi-filament printing",
            )
        issues = []
        if len(objects) < 2:
            issues.append(f"only {len(objects)} object(s) (need ≥ 2)")
        if color_groups_total < 1:
            issues.append("no color groups found")
        if not has_prod_uuid:
            issues.append("missing p:UUID on objects (Production Extension required by Bambu)")
        return _warn(
            "3mf_has_colors",
            f"Multi-color AMS data incomplete ({'; '.join(issues)}) — "
            "will import as monochrome in Bambu Studio. "
            "Run: python scripts/colorize_3mf.py --white <w.3mf> --black <b.3mf> --output <out.3mf>",
        )
    except Exception as exc:  # noqa: BLE001
        return _warn("3mf_has_colors", f"Could not inspect 3MF color data: {exc}")


def load_meta(path: Path) -> dict | None:
    """Load sidecar metadata JSON if it exists (e.g. model.meta.json for model.3mf)."""
    meta_path = path.parent / (path.stem + ".meta.json")
    if not meta_path.exists():
        return None
    try:
        with meta_path.open() as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return None


def check_wall_thickness(mesh) -> ValidationResult:
    """
    Advisory check: sample ray-based wall thickness at a small number of points.
    This is an approximation; a full analysis requires a dedicated tool.
    """
    try:
        sample_count = 200
        points, face_idx = trimesh.sample.sample_surface(mesh, sample_count)
        normals = mesh.face_normals[face_idx]

        # Cast inward rays and measure distance to opposite wall
        # Use 1e-2 offset (0.01 mm) to avoid self-intersection from floating-point imprecision
        tiny_offset = normals * 1e-2
        origins = points - tiny_offset
        directions = -normals

        locations, index_ray, _ = mesh.ray.intersects_location(
            ray_origins=origins, ray_directions=directions, multiple_hits=False
        )
        if len(locations) == 0:
            return _warn("wall_thickness", "Could not sample wall thickness (no ray hits)")

        distances = np.linalg.norm(locations - origins[index_ray], axis=1)
        min_thickness = float(np.min(distances))
        mean_thickness = float(np.mean(distances))

        if min_thickness < MIN_WALL_THICKNESS_MM:
            return _warn(
                "wall_thickness",
                f"Minimum sampled wall thickness ≈ {min_thickness:.2f} mm "
                f"(recommended ≥ {MIN_WALL_THICKNESS_MM} mm for 0.4 mm nozzle). "
                f"Mean ≈ {mean_thickness:.2f} mm.",
            )
        return _pass(
            "wall_thickness",
            f"Minimum sampled wall thickness ≈ {min_thickness:.2f} mm (mean ≈ {mean_thickness:.2f} mm)",
        )
    except Exception as exc:  # noqa: BLE001
        return _warn("wall_thickness", f"Wall thickness check skipped: {exc}")


# ── Spa-headrest checks ──────────────────────────────────────────────────────

def check_max_profile_depth(mesh, meta: dict) -> ValidationResult:
    """Check that the smallest bounding-box dimension does not exceed max_depth_mm + 2 mm tolerance."""
    max_depth = float(meta["dimensions"]["max_depth_mm"])
    tolerance = 2.0
    bounds = mesh.bounds
    size = bounds[1] - bounds[0]
    smallest = float(np.min(size))

    if smallest <= max_depth + tolerance:
        return _pass(
            "max_profile_depth",
            f"Smallest bounding-box dimension {smallest:.1f} mm "
            f"≤ max depth {max_depth:.0f} mm (+{tolerance:.0f} mm tolerance)",
        )
    return _fail(
        "max_profile_depth",
        f"Smallest bounding-box dimension {smallest:.1f} mm "
        f"> max depth {max_depth:.0f} mm (+{tolerance:.0f} mm tolerance). "
        "Profile may be too thick for the spa headrest slot.",
    )


def check_no_interior_trapped_volumes(mesh) -> ValidationResult:
    """Check that all connected bodies are individually watertight with positive volume."""
    bodies = mesh.split()
    failed = []
    for i, body in enumerate(bodies):
        if not body.is_watertight:
            failed.append(f"body {i} not watertight")
        elif body.volume <= 0:
            failed.append(f"body {i} has non-positive volume ({body.volume:.2f})")

    if failed:
        return _fail(
            "no_interior_trapped_volumes",
            f"Interior trapped volumes detected: {'; '.join(failed)}",
        )
    return _pass(
        "no_interior_trapped_volumes",
        f"All {len(bodies)} body(ies) are watertight with positive volume",
    )


def check_max_overhang_angle(mesh, max_angle_deg: float = 45.0, max_pct: float = 5.0) -> ValidationResult:
    """Check that downward-facing faces do not exceed the overhang angle threshold.

    Args:
        max_pct: Maximum percentage of faces exceeding the angle before FAIL.
                 Default 5%. Configurable via meta["overhang"]["max_pct"].
    """
    z_component = mesh.face_normals[:, 2]
    # Downward-facing faces have z_component < 0
    downward = z_component < 0
    overhang_threshold = np.cos(np.radians(max_angle_deg))
    problematic = downward & (np.abs(z_component) < overhang_threshold)
    n_total = len(z_component)
    n_problematic = int(np.sum(problematic))
    pct = n_problematic / n_total * 100 if n_total > 0 else 0.0

    if pct > max_pct:
        return _fail(
            "max_overhang_angle",
            f"{pct:.1f}% of faces ({n_problematic}/{n_total}) exceed "
            f"{max_angle_deg:.0f}° overhang threshold (>{max_pct:.0f}% limit)",
        )
    if pct > 0:
        return _warn(
            "max_overhang_angle",
            f"{pct:.1f}% of faces ({n_problematic}/{n_total}) exceed "
            f"{max_angle_deg:.0f}° overhang threshold (within 1-5% warning range)",
        )
    return _pass(
        "max_overhang_angle",
        f"No faces exceed {max_angle_deg:.0f}° overhang threshold",
    )


def check_slot_curvature(mesh, meta: dict) -> ValidationResult:
    """Check that the slot back-face curvature (sagitta) matches expected arc geometry."""
    arc_radius = float(meta["slot"]["arc_radius_mm"])
    slot_width = float(meta["slot"]["width_mm"])
    tolerance = 2.0

    # Expected sagitta: R - sqrt(R^2 - (W/2)^2)
    half_w = slot_width / 2.0
    if arc_radius < half_w:
        return _fail(
            "slot_curvature",
            f"Arc radius {arc_radius:.1f} mm < half slot width {half_w:.1f} mm — invalid geometry",
        )
    expected_sagitta = arc_radius - np.sqrt(arc_radius**2 - half_w**2)

    # Find back-face vertices (those near minimum X)
    verts = mesh.vertices
    min_x = float(np.min(verts[:, 0]))
    back_mask = verts[:, 0] <= min_x + 2.0
    back_verts = verts[back_mask]

    if len(back_verts) < 2:
        return _fail(
            "slot_curvature",
            "Could not find enough back-face vertices to measure sagitta",
        )

    # Actual sagitta: range in X among back-face vertices
    actual_sagitta = float(np.max(back_verts[:, 0]) - np.min(back_verts[:, 0]))

    if abs(actual_sagitta - expected_sagitta) <= tolerance:
        return _pass(
            "slot_curvature",
            f"Slot sagitta {actual_sagitta:.2f} mm ≈ expected {expected_sagitta:.2f} mm "
            f"(±{tolerance:.0f} mm tolerance)",
        )
    return _fail(
        "slot_curvature",
        f"Slot sagitta {actual_sagitta:.2f} mm ≠ expected {expected_sagitta:.2f} mm "
        f"(±{tolerance:.0f} mm tolerance). Check arc_radius and slot width.",
    )


# ── Main validation pipeline ──────────────────────────────────────────────────

def validate_file(
    path: Path,
    *,
    skip_wall_thickness: bool = False,
    expected_dims: tuple[float, float, float] | None = None,
) -> list[ValidationResult]:
    """Run all validation checks on *path* and return a list of ValidationResult."""
    results: list[ValidationResult] = []

    # 1. File existence
    r = check_file_exists(path)
    results.append(r)
    if r.status == ValidationResult.FAIL:
        return results

    # 2. Supported format
    r = check_supported_format(path)
    results.append(r)
    if r.status == ValidationResult.FAIL:
        return results

    # 3. Load
    r, mesh = check_loadable(path)
    results.append(r)
    if r.status == ValidationResult.FAIL or mesh is None:
        return results

    # 4. Non-empty
    r = check_non_empty(mesh)
    results.append(r)
    if r.status == ValidationResult.FAIL:
        return results

    # 5. Watertight / manifold
    results.append(check_watertight(mesh))

    # 6. Build volume
    results.append(check_build_volume(mesh))

    # 7. Positive volume / normals
    results.append(check_positive_volume(mesh))

    # 8. Degenerate faces
    results.append(check_no_degenerate_faces(mesh))

    # 9. Wall thickness (advisory, slow for large meshes)
    if not skip_wall_thickness:
        results.append(check_wall_thickness(mesh))

    # 10. Expected dimensions — pose / orientation proxy (only when --expected-dims supplied)
    if expected_dims is not None:
        results.append(check_expected_dimensions(mesh, expected_dims))

    # 11. Base on bed — Z_min ≈ 0 (base flat on print bed)
    results.append(check_base_on_bed(mesh))

    # 12 & 13. Hinge parameters + closure clearance (from sidecar .meta.json if present)
    meta = load_meta(path)
    if meta is not None:
        if "hinge" in meta:
            results.append(check_hinge_parameters(meta))
            if "base_d_mm" in meta["hinge"]:
                try:
                    results.append(check_hinge_sweep(meta))
                except KeyError as exc:
                    results.append(_warn(
                        "hinge_sweep",
                        f"Skipped: missing hinge metadata key {exc}",
                    ))
        if "closure" in meta:
            results.append(check_closure_clearance(meta))

    # 14. Spa-headrest meta checks (from sidecar .meta.json if present)
    if meta is not None:
        if "slot" in meta:
            results.append(check_slot_curvature(mesh, meta))
        if "dimensions" in meta:
            results.append(check_max_profile_depth(mesh, meta))

    # 15. Spa-headrest general geometry checks
    if meta is not None and ("slot" in meta or "dimensions" in meta):
        results.append(check_no_interior_trapped_volumes(mesh))
        # Read overhang config from meta if present
        oh_angle = 45.0
        oh_pct = 5.0
        if "overhang" in meta:
            oh_angle = float(meta["overhang"].get("max_angle_deg", 45.0))
            oh_pct = float(meta["overhang"].get("max_pct", 5.0))
        results.append(check_max_overhang_angle(mesh, oh_angle, oh_pct))

    # 16. Multi-color / Bambu AMS check — WARN if 3MF is monochrome
    results.append(check_3mf_has_colors(path))

    return results


def print_results(path: Path, results: list[ValidationResult]) -> bool:
    """Print results and return True if overall validation passed (no FAILs)."""
    print(f"\n{'='*60}")
    print(f"Validating: {path}")
    print("=" * 60)

    overall = ValidationResult.PASS
    for r in results:
        symbol = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}.get(r.status, "?")
        print(f"  {symbol} [{r.status}] {r.check}: {r.message}")
        if r.status == ValidationResult.FAIL:
            overall = ValidationResult.FAIL
        elif r.status == ValidationResult.WARN and overall == ValidationResult.PASS:
            overall = ValidationResult.WARN

    print("-" * 60)
    final_symbol = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}.get(overall, "?")
    print(f"  {final_symbol} Overall: {overall}")
    return overall != ValidationResult.FAIL


def collect_files(target: Path) -> list[Path]:
    """Return a list of model files to validate from a file or directory path."""
    if target.is_file():
        return [target]
    if target.is_dir():
        files = [
            p for p in sorted(target.iterdir())
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        if not files:
            print(f"No supported model files found in {target}")
        return files
    return []


def parse_expected_dims(value: str) -> tuple[float, float, float]:
    """Parse a 'WxDxH' string (e.g. '250x185x187') into a (W, D, H) float tuple."""
    parts = value.lower().replace(",", "x").split("x")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(
            f"Expected dimensions must be in 'WxDxH' format (e.g. '250x185x187'), got: {value!r}"
        )
    try:
        return tuple(float(p) for p in parts)  # type: ignore[return-value]
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Could not parse dimensions from {value!r} — ensure all values are numbers."
        )


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate 3D model files for Bambu Lab H2D / BambuStudio compatibility."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default="output",
        help="Path to an STL/3MF file or a directory of files (default: output/)",
    )
    parser.add_argument(
        "--skip-wall-thickness",
        action="store_true",
        help="Skip the (slow) wall-thickness advisory check",
    )
    parser.add_argument(
        "--expected-dims",
        metavar="WxDxH",
        type=parse_expected_dims,
        default=None,
        help=(
            "Expected bounding-box dimensions in mm, e.g. '250x185x187'. "
            "When supplied, adds a pose-validation check (±5 mm tolerance on each axis) "
            "that detects wrong hinge angles or incorrect print orientation."
        ),
    )
    args = parser.parse_args(argv)

    target = Path(args.target)
    files = collect_files(target)
    if not files:
        print(f"No files to validate at: {target}")
        return 1

    all_passed = True
    for f in files:
        results = validate_file(
            f,
            skip_wall_thickness=args.skip_wall_thickness,
            expected_dims=args.expected_dims,
        )
        passed = print_results(f, results)
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("✅  All models passed validation.")
        return 0
    else:
        print("❌  One or more models FAILED validation. Fix the issues above before slicing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
