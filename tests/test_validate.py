"""
tests/test_validate.py — Unit tests for scripts/validate.py
"""

import numpy as np
import pytest
import trimesh

# sys.path is configured in conftest.py
from validate import (
    BUILD_VOLUME_MM,
    ValidationResult,
    check_build_volume,
    check_closure_clearance,
    check_file_exists,
    check_hinge_parameters,
    check_no_degenerate_faces,
    check_non_empty,
    check_positive_volume,
    check_supported_format,
    check_watertight,
    collect_files,
    validate_file,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_box_mesh(size=(10, 10, 10)) -> trimesh.Trimesh:
    """Return a simple watertight box mesh."""
    return trimesh.creation.box(extents=size)


def make_open_mesh() -> trimesh.Trimesh:
    """Return a non-watertight mesh (one face removed from a box)."""
    mesh = trimesh.creation.box()
    mesh = trimesh.Trimesh(
        vertices=mesh.vertices,
        faces=mesh.faces[:-2],  # remove last two faces to open it up
        process=False,
    )
    return mesh


# ── check_file_exists ─────────────────────────────────────────────────────────

def test_file_exists_pass(tmp_path):
    f = tmp_path / "model.stl"
    f.write_bytes(b"solid test\nendsolid test\n")
    result = check_file_exists(f)
    assert result.status == ValidationResult.PASS


def test_file_exists_fail(tmp_path):
    result = check_file_exists(tmp_path / "missing.stl")
    assert result.status == ValidationResult.FAIL


# ── check_supported_format ────────────────────────────────────────────────────

@pytest.mark.parametrize("ext", [".stl", ".3mf", ".obj", ".step", ".stp"])
def test_supported_format_pass(tmp_path, ext):
    f = tmp_path / f"model{ext}"
    f.touch()
    result = check_supported_format(f)
    assert result.status == ValidationResult.PASS


def test_unsupported_format_fail(tmp_path):
    f = tmp_path / "model.gcode"
    f.touch()
    result = check_supported_format(f)
    assert result.status == ValidationResult.FAIL


# ── check_non_empty ───────────────────────────────────────────────────────────

def test_non_empty_pass():
    mesh = make_box_mesh()
    result = check_non_empty(mesh)
    assert result.status == ValidationResult.PASS
    assert "faces" in result.message


def test_non_empty_fail_no_faces():
    mesh = trimesh.Trimesh(
        vertices=np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]]),
        faces=np.empty((0, 3), dtype=int),
    )
    result = check_non_empty(mesh)
    assert result.status == ValidationResult.FAIL


# ── check_watertight ─────────────────────────────────────────────────────────

def test_watertight_pass():
    mesh = make_box_mesh()
    assert mesh.is_watertight, "test fixture must be watertight"
    result = check_watertight(mesh)
    assert result.status == ValidationResult.PASS


def test_watertight_fail():
    mesh = make_open_mesh()
    assert not mesh.is_watertight, "test fixture must be non-watertight"
    result = check_watertight(mesh)
    assert result.status == ValidationResult.FAIL


# ── check_build_volume ────────────────────────────────────────────────────────

def test_build_volume_pass():
    bx, by, bz = BUILD_VOLUME_MM
    mesh = make_box_mesh(size=(bx - 10, by - 10, bz - 10))
    result = check_build_volume(mesh)
    assert result.status == ValidationResult.PASS


def test_build_volume_fail_x():
    bx, by, bz = BUILD_VOLUME_MM
    mesh = make_box_mesh(size=(bx + 10, by - 10, bz - 10))
    result = check_build_volume(mesh)
    assert result.status == ValidationResult.FAIL
    assert "X=" in result.message


def test_build_volume_fail_y():
    bx, by, bz = BUILD_VOLUME_MM
    mesh = make_box_mesh(size=(bx - 10, by + 10, bz - 10))
    result = check_build_volume(mesh)
    assert result.status == ValidationResult.FAIL
    assert "Y=" in result.message


def test_build_volume_fail_z():
    bx, by, bz = BUILD_VOLUME_MM
    mesh = make_box_mesh(size=(bx - 10, by - 10, bz + 10))
    result = check_build_volume(mesh)
    assert result.status == ValidationResult.FAIL
    assert "Z=" in result.message


# ── check_positive_volume ─────────────────────────────────────────────────────

def test_positive_volume_pass():
    mesh = make_box_mesh()
    result = check_positive_volume(mesh)
    assert result.status == ValidationResult.PASS
    assert float(mesh.volume) > 0


def test_positive_volume_warn_inverted():
    mesh = make_box_mesh()
    # Invert all face normals by flipping winding order
    mesh.faces = mesh.faces[:, ::-1]
    result = check_positive_volume(mesh)
    # trimesh may return negative volume for inverted normals
    assert result.status in (ValidationResult.WARN, ValidationResult.PASS)


# ── check_no_degenerate_faces ─────────────────────────────────────────────────

def test_no_degenerate_faces_pass():
    mesh = make_box_mesh()
    result = check_no_degenerate_faces(mesh)
    assert result.status == ValidationResult.PASS


def test_no_degenerate_faces_warn():
    mesh = make_box_mesh()
    # Add a degenerate face (all three vertices identical)
    verts = np.vstack([mesh.vertices, [[5, 5, 5], [5, 5, 5], [5, 5, 5]]])
    n = len(mesh.vertices)
    degen_face = np.array([[n, n + 1, n + 2]])
    faces = np.vstack([mesh.faces, degen_face])
    bad_mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    result = check_no_degenerate_faces(bad_mesh)
    assert result.status == ValidationResult.WARN
    assert "degenerate" in result.message


# ── collect_files ─────────────────────────────────────────────────────────────

def test_collect_files_single_file(tmp_path):
    f = tmp_path / "model.stl"
    f.write_bytes(b"")
    files = collect_files(f)
    assert files == [f]


def test_collect_files_directory(tmp_path):
    (tmp_path / "a.stl").write_bytes(b"")
    (tmp_path / "b.3mf").write_bytes(b"")
    (tmp_path / "c.gcode").write_bytes(b"")  # should be ignored
    files = collect_files(tmp_path)
    names = {f.name for f in files}
    assert "a.stl" in names
    assert "b.3mf" in names
    assert "c.gcode" not in names


def test_collect_files_empty_directory(tmp_path):
    files = collect_files(tmp_path)
    assert files == []


# ── validate_file integration ─────────────────────────────────────────────────

def test_validate_good_stl(tmp_path):
    """A watertight box within build volume should produce no FAIL results."""
    mesh = make_box_mesh(size=(50, 50, 50))
    # Translate so base sits at Z=0 (trimesh boxes are centered at origin)
    mesh.apply_translation([0, 0, 25])
    path = tmp_path / "good.stl"
    mesh.export(str(path))
    results = validate_file(path, skip_wall_thickness=True)
    statuses = [r.status for r in results]
    assert ValidationResult.FAIL not in statuses


def test_validate_missing_file(tmp_path):
    results = validate_file(tmp_path / "missing.stl", skip_wall_thickness=True)
    assert results[0].status == ValidationResult.FAIL
    assert results[0].check == "file_exists"


def test_validate_oversized_stl(tmp_path):
    bx, by, bz = BUILD_VOLUME_MM
    mesh = make_box_mesh(size=(bx + 50, by + 50, bz + 50))
    path = tmp_path / "oversized.stl"
    mesh.export(str(path))
    results = validate_file(path, skip_wall_thickness=True)
    statuses_by_check = {r.check: r.status for r in results}
    assert statuses_by_check["build_volume"] == ValidationResult.FAIL


# ── check_hinge_parameters ──────────────────────────────────────────────────

def _make_hinge_meta(
    pin_d=4.0,
    bore_d=5.0,
    barrel_od=12.0,
    hard_stop=135,
    min_wall=1.2,
    n_knuckles=7,
    knuckle_gap=0.5,
):
    """Return a meta dict with hinge section for testing."""
    return {
        "hinge": {
            "pin_d_mm": pin_d,
            "bore_d_mm": bore_d,
            "barrel_od_mm": barrel_od,
            "hard_stop_angle_deg": hard_stop,
            "min_wall_mm": min_wall,
            "type": "interleaved_knuckle",
            "n_knuckles": n_knuckles,
            "knuckle_gap_mm": knuckle_gap,
        }
    }


def test_hinge_parameters_pass():
    """Hinge with 0.5 mm radial clearance and 0.5 mm knuckle gap passes."""
    meta = _make_hinge_meta(pin_d=4.0, bore_d=5.0, barrel_od=12.0, knuckle_gap=0.5)
    result = check_hinge_parameters(meta)
    assert result.status == ValidationResult.PASS


def test_hinge_parameters_fail_radial_clearance_too_tight():
    """Radial clearance below 0.4 mm must fail (old v002 values)."""
    # bore_d=3.6, pin_d=3.0 => clearance = 0.3 mm < 0.4
    meta = _make_hinge_meta(pin_d=3.0, bore_d=3.6, barrel_od=8.0, knuckle_gap=0.5)
    result = check_hinge_parameters(meta)
    assert result.status == ValidationResult.FAIL
    assert "radial clearance" in result.message


def test_hinge_parameters_fail_radial_clearance_too_loose():
    """Radial clearance above 0.8 mm must fail."""
    # bore_d=5.0, pin_d=3.0 => clearance = 1.0 mm > 0.8
    meta = _make_hinge_meta(pin_d=3.0, bore_d=5.0, knuckle_gap=0.5)
    result = check_hinge_parameters(meta)
    assert result.status == ValidationResult.FAIL
    assert "radial clearance" in result.message


def test_hinge_parameters_fail_bore_le_pin():
    """bore_d <= pin_d must fail."""
    meta = _make_hinge_meta(pin_d=5.0, bore_d=5.0)
    result = check_hinge_parameters(meta)
    assert result.status == ValidationResult.FAIL
    assert "bore_d" in result.message


def test_hinge_parameters_fail_barrel_wall_too_thin():
    """Barrel wall below min_wall must fail."""
    # barrel_od=5.5, bore_d=5.0 => wall = 0.25 mm < 1.2
    meta = _make_hinge_meta(bore_d=5.0, barrel_od=5.5, knuckle_gap=0.5)
    result = check_hinge_parameters(meta)
    assert result.status == ValidationResult.FAIL
    assert "barrel wall" in result.message


def test_hinge_parameters_fail_hard_stop_too_large():
    """hard_stop > 135 must fail."""
    meta = _make_hinge_meta(hard_stop=140)
    result = check_hinge_parameters(meta)
    assert result.status == ValidationResult.FAIL
    assert "hard_stop" in result.message


def test_hinge_parameters_fail_knuckle_gap_too_small():
    """Knuckle gap below 0.4 mm must fail (old v002 value)."""
    meta = _make_hinge_meta(knuckle_gap=0.3)
    result = check_hinge_parameters(meta)
    assert result.status == ValidationResult.FAIL
    assert "knuckle_gap" in result.message


def test_hinge_parameters_boundary_radial_clearance():
    """Radial clearance just above 0.4 mm should pass."""
    # pin=4.0, bore=4.82 => clearance = 0.41
    meta = _make_hinge_meta(pin_d=4.0, bore_d=4.82, knuckle_gap=0.5)
    result = check_hinge_parameters(meta)
    assert result.status == ValidationResult.PASS


def test_hinge_parameters_boundary_radial_clearance_upper_limit():
    """Radial clearance at the upper limit 0.80 mm should pass."""
    # pin=4.0, bore=5.6 => clearance = (5.6 - 4.0) / 2 = 0.80
    meta = _make_hinge_meta(pin_d=4.0, bore_d=5.6, knuckle_gap=0.5)
    result = check_hinge_parameters(meta)
    assert result.status == ValidationResult.PASS


def test_hinge_parameters_fail_radial_clearance_just_over_upper():
    """Radial clearance just above 0.80 mm should fail."""
    # pin=4.0, bore=5.62 => clearance = (5.62 - 4.0) / 2 = 0.81
    meta = _make_hinge_meta(pin_d=4.0, bore_d=5.62, knuckle_gap=0.5)
    result = check_hinge_parameters(meta)
    assert result.status == ValidationResult.FAIL


# ── check_closure_clearance ──────────────────────────────────────────────────

def _make_closure_meta(
    keyboard_back_edge_y=161.0,
    screen_pocket_front_y=165.0,
    key_protrusion=1.0,
    screen_pocket_depth=2.5,
):
    """Return a meta dict with closure section for testing."""
    return {
        "closure": {
            "base_d_mm": 180,
            "bezel_mm": 15,
            "key_protrusion_above_base_mm": key_protrusion,
            "screen_pocket_depth_mm": screen_pocket_depth,
            "keyboard_back_edge_y_mm": keyboard_back_edge_y,
            "screen_pocket_front_y_when_closed_mm": screen_pocket_front_y,
        }
    }


def test_closure_clearance_pass():
    """Default closure values (4mm gap, key 1mm < pocket 2.5mm) pass."""
    meta = _make_closure_meta()
    result = check_closure_clearance(meta)
    assert result.status == ValidationResult.PASS


def test_closure_clearance_fail_overlap():
    """Keys extending past screen pocket front edge must fail."""
    meta = _make_closure_meta(keyboard_back_edge_y=170.0, screen_pocket_front_y=165.0)
    result = check_closure_clearance(meta)
    assert result.status == ValidationResult.FAIL


def test_closure_clearance_fail_key_protrusion():
    """Key protrusion exceeding screen pocket depth must fail."""
    meta = _make_closure_meta(key_protrusion=3.0, screen_pocket_depth=2.5)
    result = check_closure_clearance(meta)
    assert result.status == ValidationResult.FAIL


def test_closure_clearance_fail_too_tight():
    """Clearance between 0 and 2.0 mm must fail (too tight)."""
    # 165.0 - 164.0 = 1.0 mm clearance, below MIN_CLEARANCE_MM=2.0
    meta = _make_closure_meta(keyboard_back_edge_y=164.0, screen_pocket_front_y=165.0)
    result = check_closure_clearance(meta)
    assert result.status == ValidationResult.FAIL
    assert "clearance" in result.message.lower()
