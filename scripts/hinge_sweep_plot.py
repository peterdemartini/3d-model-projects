#!/usr/bin/env python3
"""
hinge_sweep_plot.py — Generate hinge sweep clearance analysis and visualization.

Usage:
    python scripts/hinge_sweep_plot.py models/toy_laptop/output/toy_laptop_001.meta.json

Outputs:
    <model>_hinge_sweep.json   — clearance data at every angle
    <model>_hinge_sweep.png    — clearance vs angle plot
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

# Allow import from scripts/
sys.path.insert(0, str(Path(__file__).parent))
from validate import SWEEP_MIN_CLEARANCE_MM, compute_hinge_sweep_clearances


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/hinge_sweep_plot.py <meta.json>")
        sys.exit(1)

    meta_path = Path(sys.argv[1])
    with open(meta_path) as f:
        meta = json.load(f)

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

    # Save JSON
    output_dir = meta_path.parent
    stem = meta_path.stem.replace(".meta", "")
    json_path = output_dir / f"{stem}_hinge_sweep.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Saved clearance data to {json_path}")

    # Generate plot
    angles = [e["angle"] for e in result["clearance_by_angle"]]
    pairs = list(result["clearance_by_angle"][0]["clearances"].keys())

    fig, ax = plt.subplots(figsize=(12, 6))

    for pair in pairs:
        values = [e["clearances"][pair] for e in result["clearance_by_angle"]]
        ax.plot(angles, values, label=pair, linewidth=1.5)

    # Danger zone
    ax.axhline(y=SWEEP_MIN_CLEARANCE_MM, color="red", linestyle="--",
               linewidth=1, label=f"Min threshold ({SWEEP_MIN_CLEARANCE_MM} mm)")
    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)

    # Mark minimum point
    ax.plot(result["min_clearance_angle_deg"], result["min_clearance_mm"],
            "rv", markersize=10,
            label=f"Min: {result['min_clearance_mm']:.2f} mm @ {result['min_clearance_angle_deg']:.0f}°")

    ax.set_xlabel("Hinge Angle (degrees)", fontsize=12)
    ax.set_ylabel("Clearance (mm)", fontsize=12)
    ax.set_title("Hinge Sweep Clearance Analysis — Operation Free Hinge", fontsize=14)
    ax.legend(loc="upper left", fontsize=9)
    ax.set_xlim(0, float(h["hard_stop_angle_deg"]))
    ax.grid(True, alpha=0.3)

    # Fill danger zone
    ax.fill_between(angles, 0, SWEEP_MIN_CLEARANCE_MM, alpha=0.1, color="red")

    plt.tight_layout()
    png_path = output_dir / f"{stem}_hinge_sweep.png"
    plt.savefig(png_path, dpi=150)
    print(f"Saved clearance plot to {png_path}")

    # Print summary
    print(f"\n{'='*50}")
    print(f"Min clearance: {result['min_clearance_mm']:.3f} mm")
    print(f"At angle:      {result['min_clearance_angle_deg']:.0f}°")
    print(f"Pair:          {result['min_clearance_pair']}")
    print(f"Collision:     {result['collision_detected']}")
    print(f"Status:        {'PASS' if result['min_clearance_mm'] >= SWEEP_MIN_CLEARANCE_MM else 'FAIL'}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
