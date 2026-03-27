#!/usr/bin/env python3
"""
assemble_3mf.py — Combine separately-exported base and lid 3MF bodies into one
Bambu-compatible multi-object 3MF with per-object color assignments.

WHY SEPARATE EXPORTS?
    OpenSCAD's CGAL kernel implicitly unions all top-level geometry. When the
    base plate and lid plate share the hinge axis edge, CGAL merges them into
    ONE connected body — destroying the print-in-place gap. By exporting base
    and lid separately and combining them as separate <object> elements in the
    3MF, the slicer sees independent bodies with physical separation.

OBJECT LAYOUT (4 objects, 2 color groups):
    colorgroup id="2"  →  #FFFFFFFF (white)
    colorgroup id="4"  →  #000000FF (black)

    object id="1"  name="base_white"  pid="2"  ← base plate + barrels + shoulders
    object id="3"  name="lid_white"   pid="2"  ← lid plate + barrels + pin
    object id="5"  name="base_black"  pid="4"  ← keycaps + trackpad
    object id="7"  name="lid_black"   pid="4"  ← screen plate

Usage:
    python scripts/assemble_3mf.py \\
        --white-base  output/toy_laptop_001_white_base.3mf \\
        --white-lid   output/toy_laptop_001_white_lid.3mf \\
        --black-base  output/toy_laptop_001_black_base.3mf \\
        --black-lid   output/toy_laptop_001_black_lid.3mf \\
        --output      output/toy_laptop_001.3mf
"""

import argparse
import sys
import uuid as _uuid
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

# ── 3MF namespace constants ───────────────────────────────────────────────────
CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
MAT_NS  = "http://schemas.microsoft.com/3dmanufacturing/material/2015/02"
PROD_NS = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
BEAM_NS = "http://schemas.microsoft.com/3dmanufacturing/beamlattice/2017/02"
SLIC_NS = "http://schemas.microsoft.com/3dmanufacturing/slice/2015/07"
SECU_NS = "http://schemas.microsoft.com/3dmanufacturing/securecontent/2019/04"

ET.register_namespace("",   CORE_NS)
ET.register_namespace("m",  MAT_NS)
ET.register_namespace("p",  PROD_NS)
ET.register_namespace("b",  BEAM_NS)
ET.register_namespace("s",  SLIC_NS)
ET.register_namespace("sc", SECU_NS)


CONTENT_TYPES_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml" />
  <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml" />
</Types>
"""

RELS_XML = """\
<?xml version="1.0" encoding="utf-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
                Target="/3D/3dmodel.model"
                Id="rel0" />
</Relationships>
"""


def _q(tag: str, ns: str = CORE_NS) -> str:
    return f"{{{ns}}}{tag}"


def _new_uuid() -> str:
    return str(_uuid.uuid4())


def _read_mesh(path: Path) -> ET.Element:
    """Extract the <mesh> element from a single-object 3MF file."""
    with zipfile.ZipFile(path) as zf:
        raw = zf.read("3D/3dmodel.model")
    root = ET.fromstring(raw)
    obj = root.find(f".//{{{CORE_NS}}}object")
    if obj is None:
        raise ValueError(f"No <object> in {path}")
    mesh = obj.find(f"{{{CORE_NS}}}mesh")
    if mesh is None:
        raise ValueError(f"No <mesh> in {path}")
    return mesh


def _count_faces(mesh: ET.Element) -> int:
    return len(mesh.findall(f".//{{{CORE_NS}}}triangle"))


def assemble(
    white_base_path: Path,
    white_lid_path: Path,
    black_base_path: Path,
    black_lid_path: Path,
    output_path: Path,
) -> None:
    """Read 4 single-body 3MFs and write one multi-object Bambu 3MF."""

    # ── Read all meshes ────────────────────────────────────────────────────
    parts = [
        ("base_white", white_base_path, "2"),  # pid → white colorgroup
        ("lid_white",  white_lid_path,  "2"),
        ("base_black", black_base_path, "4"),  # pid → black colorgroup
        ("lid_black",  black_lid_path,  "4"),
    ]

    meshes = {}
    for name, path, _ in parts:
        print(f"Reading {name} from: {path}")
        meshes[name] = _read_mesh(path)

    # ── Build model XML ────────────────────────────────────────────────────
    model = ET.Element(_q("model"))
    model.set("unit", "millimeter")
    model.set("xml:lang", "en-US")

    resources = ET.SubElement(model, _q("resources"))

    # Color groups (shared across objects of same color)
    cg_white = ET.SubElement(resources, _q("colorgroup", MAT_NS))
    cg_white.set("id", "2")
    ET.SubElement(cg_white, _q("color", MAT_NS)).set("color", "#FFFFFFFF")

    cg_black = ET.SubElement(resources, _q("colorgroup", MAT_NS))
    cg_black.set("id", "4")
    ET.SubElement(cg_black, _q("color", MAT_NS)).set("color", "#000000FF")

    # Objects — each gets an odd id so colorgroup ids (even) don't collide
    build = ET.SubElement(model, _q("build"))
    build.set(_q("UUID", PROD_NS), _new_uuid())

    obj_id = 1
    for name, _, pid in parts:
        obj = ET.SubElement(resources, _q("object"))
        obj.set("id", str(obj_id))
        obj.set("name", name)
        obj.set("type", "model")
        obj.set(_q("UUID", PROD_NS), _new_uuid())
        obj.set("pid", pid)
        obj.set("pindex", "0")
        obj.append(meshes[name])

        item = ET.SubElement(build, _q("item"))
        item.set("objectid", str(obj_id))
        item.set(_q("UUID", PROD_NS), _new_uuid())

        obj_id += 2  # keep odd: 1, 3, 5, 7

    # ── Write output ───────────────────────────────────────────────────────
    ET.indent(model, space="\t")
    model_bytes = ET.tostring(model, encoding="utf-8", xml_declaration=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES_XML.strip())
        zf.writestr("_rels/.rels",         RELS_XML.strip())
        zf.writestr("3D/3dmodel.model",    model_bytes)

    # Report
    total = 0
    for name, _, _ in parts:
        n = _count_faces(meshes[name])
        total += n
        print(f"  {name:15s}: {n:,} triangles")
    print(f"  {'total':15s}: {total:,} triangles")
    print(f"  file size    : {output_path.stat().st_size / 1024:.1f} KB")
    print(f"\nOutput: {output_path}")
    print("\nIn Bambu Studio:")
    print("  Objects panel will show: base_white, lid_white, base_black, lid_black")
    print("  base_white + lid_white  → assign white filament slot")
    print("  base_black + lid_black  → assign black filament slot")
    print("  base_white and lid_white are SEPARATE bodies → hinge gap preserved")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Assemble 4 separate 3MF bodies into one multi-object Bambu 3MF"
    )
    parser.add_argument("--white-base", required=True, type=Path)
    parser.add_argument("--white-lid",  required=True, type=Path)
    parser.add_argument("--black-base", required=True, type=Path)
    parser.add_argument("--black-lid",  required=True, type=Path)
    parser.add_argument("--output",     required=True, type=Path)
    args = parser.parse_args(argv)

    for p, name in [
        (args.white_base, "--white-base"),
        (args.white_lid,  "--white-lid"),
        (args.black_base, "--black-base"),
        (args.black_lid,  "--black-lid"),
    ]:
        if not p.exists():
            print(f"ERROR: {name} file not found: {p}", file=sys.stderr)
            return 1

    try:
        assemble(args.white_base, args.white_lid,
                 args.black_base, args.black_lid, args.output)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
