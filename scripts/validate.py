#!/usr/bin/env python3
"""
validate.py - Validate 3D model files for Bambu Lab H2D / BambuStudio compatibility.

Usage:
    python scripts/validate.py output/model.stl
    python scripts/validate.py output/              # validate all files in directory
"""

import sys
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
    # Count open (boundary) edges: edges referenced by only one face
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


# ── Main validation pipeline ──────────────────────────────────────────────────

def validate_file(path: Path, *, skip_wall_thickness: bool = False) -> list[ValidationResult]:
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
    args = parser.parse_args(argv)

    target = Path(args.target)
    files = collect_files(target)
    if not files:
        print(f"No files to validate at: {target}")
        return 1

    all_passed = True
    for f in files:
        results = validate_file(f, skip_wall_thickness=args.skip_wall_thickness)
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
