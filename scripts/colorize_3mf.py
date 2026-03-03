#!/usr/bin/env python3
"""
colorize_3mf.py — Merge two single-color 3MF bodies into one Bambu-compatible
multi-object 3MF file with per-object <m:colorgroup> and Production Extension
p:UUID attributes required by Bambu Studio for AMS filament assignment.

Usage:
    python scripts/colorize_3mf.py \\
        --white  models/toy_laptop/output/toy_laptop_001_white.3mf \\
        --black  models/toy_laptop/output/toy_laptop_001_black.3mf \\
        --output models/toy_laptop/output/toy_laptop_001.3mf

Why separate objects (not face colors)?
    Bambu Studio assigns AMS filaments at the *object* level, not per face.
    Each <object> in the output 3MF maps to one entry in Bambu Studio's
    Objects panel, where users assign a filament slot.

Why <m:colorgroup>, not <m:basematerials>?
    Bambu Studio uses <m:colorgroup> (one group per object, each with a single
    <m:color color="#RRGGBBAA">) for AMS color assignment.  <m:basematerials>
    is the 3MF spec's generic material group and is ignored by Bambu Studio's
    AMS slot selector.

Why p:UUID?
    Bambu Studio checks for the 3MF Production Extension namespace
    (xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06")
    and requires p:UUID attributes on <object>, <build>, and <item> elements.
    Without them, Bambu Studio shows "The 3mf is not from Bambu Lab, load
    geometry data only" and merges all objects into one body.

Output 3MF structure (matches flowrate-test-pass1.3mf from BambuStudio.app):
    <m:colorgroup id="2">
        <m:color color="#FFFFFFFF"/>   ← white with alpha
    </m:colorgroup>
    <m:colorgroup id="4">
        <m:color color="#000000FF"/>   ← black with alpha
    </m:colorgroup>
    <object id="1" name="white_parts" p:UUID="…" pid="2" pindex="0"> … </object>
    <object id="3" name="black_parts" p:UUID="…" pid="4" pindex="0"> … </object>
    <build p:UUID="…">
        <item objectid="1" p:UUID="…"/>
        <item objectid="3" p:UUID="…"/>
    </build>
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

# Register namespaces so ElementTree emits them on the root element with the
# correct prefixes (e.g. xmlns:m, xmlns:p) rather than inventing ns0/ns1.
ET.register_namespace("",   CORE_NS)
ET.register_namespace("m",  MAT_NS)
ET.register_namespace("p",  PROD_NS)
ET.register_namespace("b",  BEAM_NS)
ET.register_namespace("s",  SLIC_NS)
ET.register_namespace("sc", SECU_NS)

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


def _new_uuid() -> str:
    """Return a fresh random UUID4 string."""
    return str(_uuid.uuid4())


# ── Main merge function ───────────────────────────────────────────────────────

def merge_to_multicolor(
    white_path: Path,
    black_path: Path,
    output_path: Path,
) -> None:
    """
    Read white and black 3MF files and write a single multi-object Bambu 3MF.

    The output matches the structure used by Bambu Studio's own calibration
    files (e.g. flowrate-test-pass1.3mf bundled with the app):

      - One <m:colorgroup> per object, each with a single <m:color> entry
        using 8-character RGBA hex (e.g. "#FFFFFFFF")
      - Each <object> carries a p:UUID attribute (Production Extension)
        and references its own colorgroup via pid; pindex is always "0"
      - <build> and each <item> also carry p:UUID attributes
      - All Bambu namespace declarations are emitted on the root <model>

    ID layout:
      colorgroup id="2"  ←→  object id="1"  (white_parts)
      colorgroup id="4"  ←→  object id="3"  (black_parts)
    """
    print(f"Reading white body from: {white_path}")
    white_root = _read_model_xml(white_path)
    white_mesh = _extract_mesh(white_root)

    print(f"Reading black body from: {black_path}")
    black_root = _read_model_xml(black_path)
    black_mesh = _extract_mesh(black_root)

    # ── Build the merged model XML ────────────────────────────────────────────
    # Namespace declarations are emitted automatically on the root element by
    # ElementTree via ET.register_namespace() calls at module level.
    model = ET.Element(_q("model"))
    model.set("unit", "millimeter")
    model.set("xml:lang", "en-US")

    resources = ET.SubElement(model, _q("resources"))

    # ── Color groups — one per object, RGBA 8-char hex ────────────────────────
    # id="2" → white (referenced by object id="1")
    cg_white = ET.SubElement(resources, _q("colorgroup", MAT_NS))
    cg_white.set("id", "2")
    ET.SubElement(cg_white, _q("color", MAT_NS)).set("color", "#FFFFFFFF")

    # id="4" → black (referenced by object id="3")
    cg_black = ET.SubElement(resources, _q("colorgroup", MAT_NS))
    cg_black.set("id", "4")
    ET.SubElement(cg_black, _q("color", MAT_NS)).set("color", "#000000FF")

    # ── White object ──────────────────────────────────────────────────────────
    # id="1", pid="2" (white colorgroup), pindex="0" (first/only color in group)
    white_obj = ET.SubElement(resources, _q("object"))
    white_obj.set("id", "1")
    white_obj.set("name", "white_parts")
    white_obj.set("type", "model")
    white_obj.set(_q("UUID", PROD_NS), _new_uuid())
    white_obj.set("pid", "2")
    white_obj.set("pindex", "0")
    white_obj.append(white_mesh)

    # ── Black object ──────────────────────────────────────────────────────────
    # id="3", pid="4" (black colorgroup), pindex="0"
    black_obj = ET.SubElement(resources, _q("object"))
    black_obj.set("id", "3")
    black_obj.set("name", "black_parts")
    black_obj.set("type", "model")
    black_obj.set(_q("UUID", PROD_NS), _new_uuid())
    black_obj.set("pid", "4")
    black_obj.set("pindex", "0")
    black_obj.append(black_mesh)

    # ── Build — p:UUID on element and each item ───────────────────────────────
    build = ET.SubElement(model, _q("build"))
    build.set(_q("UUID", PROD_NS), _new_uuid())

    item_w = ET.SubElement(build, _q("item"))
    item_w.set("objectid", "1")
    item_w.set(_q("UUID", PROD_NS), _new_uuid())

    item_b = ET.SubElement(build, _q("item"))
    item_b.set("objectid", "3")
    item_b.set(_q("UUID", PROD_NS), _new_uuid())

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
            "multi-object 3MF with per-object <m:colorgroup> and p:UUID "
            "Production Extension attributes for AMS filament assignment."
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
