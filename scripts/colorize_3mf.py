#!/usr/bin/env python3
"""
colorize_3mf.py — Merge two single-color 3MF bodies into one Bambu-compatible
multi-object 3MF file with <m:basematerials> material assignments.

Usage:
    python scripts/colorize_3mf.py \
        --white  models/toy_laptop/output/toy_laptop_001_white.3mf \
        --black  models/toy_laptop/output/toy_laptop_001_black.3mf \
        --output models/toy_laptop/output/toy_laptop_001.3mf

Why separate objects (not face colors)?
    Bambu Studio assigns AMS filaments at the *object* level, not per face.
    The p:colorgroup / p:colorid per-triangle XML is visual-only and does NOT
    drive AMS slot selection.  Each <object> in the output 3MF maps to one
    entry in Bambu Studio's Objects panel, where users assign a filament slot.

Output 3MF structure:
    <m:basematerials id="1">
        <m:base name="White PLA" displaycolor="#FFFFFF" />   ← pindex 0
        <m:base name="Black PLA" displaycolor="#000000" />   ← pindex 1
    </m:basematerials>
    <object id="2" name="white_parts" pid="1" pindex="0"> ... </object>
    <object id="3" name="black_parts" pid="1" pindex="1"> ... </object>
"""

import argparse
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

# ── 3MF namespace constants ───────────────────────────────────────────────────
CORE_NS = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
MAT_NS  = "http://schemas.microsoft.com/3dmanufacturing/material/2015/02"
PROD_NS = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"

# Register namespaces so ElementTree doesn't invent ns0/ns1 prefixes
ET.register_namespace("",  CORE_NS)
ET.register_namespace("m", MAT_NS)
ET.register_namespace("p", PROD_NS)

_NS = {"c": CORE_NS, "m": MAT_NS, "p": PROD_NS}


# ── Content-type and relationship templates ───────────────────────────────────

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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _read_model_xml(path: Path) -> ET.Element:
    """Open a 3MF (ZIP) and return the parsed root Element of 3D/3dmodel.model."""
    with zipfile.ZipFile(path) as zf:
        raw = zf.read("3D/3dmodel.model")
    return ET.fromstring(raw)


def _extract_mesh(root: ET.Element) -> ET.Element:
    """
    Extract the <mesh> element from the first <object> in a 3MF model.
    Raises ValueError if not found.
    """
    # The object may live directly under <resources> or nested; search broadly.
    obj = root.find(f".//{{{CORE_NS}}}object")
    if obj is None:
        raise ValueError("No <object> element found in 3MF")
    mesh = obj.find(f"{{{CORE_NS}}}mesh")
    if mesh is None:
        raise ValueError("No <mesh> element found inside <object>")
    return mesh


def _q(tag: str, ns: str = CORE_NS) -> str:
    """Return a Clark-notation qualified name, e.g. '{namespace}tag'."""
    return f"{{{ns}}}{tag}"


# ── Main merge function ───────────────────────────────────────────────────────

def merge_to_multicolor(
    white_path: Path,
    black_path: Path,
    output_path: Path,
) -> None:
    """
    Read white and black 3MF files and write a single multi-object Bambu 3MF.

    The output contains:
      - <m:basematerials id="1"> with two <m:base> entries (white, black)
      - <object id="2" name="white_parts" pid="1" pindex="0"> with white mesh
      - <object id="3" name="black_parts" pid="1" pindex="1"> with black mesh
      - <build> items for both objects
    """
    print(f"Reading white body from: {white_path}")
    white_root = _read_model_xml(white_path)
    white_mesh = _extract_mesh(white_root)

    print(f"Reading black body from: {black_path}")
    black_root = _read_model_xml(black_path)
    black_mesh = _extract_mesh(black_root)

    # ── Build the merged model XML ────────────────────────────────────────────
    # Note: namespace declarations are emitted automatically by ElementTree via
    # ET.register_namespace() calls at module level — do NOT set xmlns:* as
    # attributes or they will be duplicated in the output.
    model = ET.Element(_q("model"))
    model.set("unit", "millimeter")
    model.set("xml:lang", "en-US")

    resources = ET.SubElement(model, _q("resources"))

    # Material group — index 0 = white, index 1 = black
    mat_grp = ET.SubElement(resources, _q("basematerials", MAT_NS))
    mat_grp.set("id", "1")

    white_mat = ET.SubElement(mat_grp, _q("base", MAT_NS))
    white_mat.set("name", "White PLA")
    white_mat.set("displaycolor", "#FFFFFF")

    black_mat = ET.SubElement(mat_grp, _q("base", MAT_NS))
    black_mat.set("name", "Black PLA")
    black_mat.set("displaycolor", "#000000")

    # White object (pindex=0 → white material)
    white_obj = ET.SubElement(resources, _q("object"))
    white_obj.set("id", "2")
    white_obj.set("name", "white_parts")
    white_obj.set("type", "model")
    white_obj.set("pid", "1")
    white_obj.set("pindex", "0")
    white_obj.append(white_mesh)

    # Black object (pindex=1 → black material)
    black_obj = ET.SubElement(resources, _q("object"))
    black_obj.set("id", "3")
    black_obj.set("name", "black_parts")
    black_obj.set("type", "model")
    black_obj.set("pid", "1")
    black_obj.set("pindex", "1")
    black_obj.append(black_mesh)

    # Build items
    build = ET.SubElement(model, _q("build"))
    item_w = ET.SubElement(build, _q("item"))
    item_w.set("objectid", "2")
    item_b = ET.SubElement(build, _q("item"))
    item_b.set("objectid", "3")

    # ── Serialise to bytes ────────────────────────────────────────────────────
    ET.indent(model, space="\t")  # pretty-print (Python 3.9+)
    model_bytes = ET.tostring(model, encoding="utf-8", xml_declaration=True)

    # ── Write output 3MF (ZIP) ────────────────────────────────────────────────
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", CONTENT_TYPES_XML.strip())
        zf.writestr("_rels/.rels",         RELS_XML.strip())
        zf.writestr("3D/3dmodel.model",    model_bytes)

    # Quick size report
    white_faces = len(white_mesh.findall(f".//{{{CORE_NS}}}triangle"))
    black_faces = len(black_mesh.findall(f".//{{{CORE_NS}}}triangle"))
    total_faces = white_faces + black_faces
    size_kb = output_path.stat().st_size / 1024

    print(f"\nOutput written: {output_path}")
    print(f"  white_parts : {white_faces:,} triangles")
    print(f"  black_parts : {black_faces:,} triangles")
    print(f"  total       : {total_faces:,} triangles")
    print(f"  file size   : {size_kb:.1f} KB")
    print()
    print("In Bambu Studio:")
    print("  File → Import → select the output .3mf")
    print("  Objects panel will show 'white_parts' and 'black_parts'")
    print("  Right-click each object → assign AMS filament slot")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Merge two single-color 3MF bodies into one Bambu-compatible "
            "multi-object 3MF with <m:basematerials> AMS material assignments."
        )
    )
    parser.add_argument("--white",  required=True, type=Path,
                        help="3MF file containing the white parts (base, lid, pin)")
    parser.add_argument("--black",  required=True, type=Path,
                        help="3MF file containing the black parts (keycaps, trackpad, screen)")
    parser.add_argument("--output", required=True, type=Path,
                        help="Output path for the merged multi-color 3MF")
    args = parser.parse_args(argv)

    for p, name in [(args.white, "--white"), (args.black, "--black")]:
        if not p.exists():
            print(f"ERROR: {name} file not found: {p}", file=sys.stderr)
            return 1

    try:
        merge_to_multicolor(args.white, args.black, args.output)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
