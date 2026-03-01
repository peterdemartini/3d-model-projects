"""
tests/test_validate.py — Unit tests for scripts/validate.py
"""

import sys
import os
from pathlib import Path

import numpy as np
import pytest
import trimesh

# Make the scripts directory importable
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from validate import (  # noqa: E402
    BUILD_VOLUME_MM,
    MIN_WALL_THICKNESS_MM,
    SUPPORTED_EXTENSIONS,
    ValidationResult,
    check_build_volume,
    check_file_exists,
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
