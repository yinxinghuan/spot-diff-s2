#!/usr/bin/env ~/miniconda3/bin/python3
"""
Spot the Difference S2 — Difference Coordinate Detector
Detects top-3 difference regions for each scene and outputs
the coordinates ready to paste into scenes.ts
"""

import os
import numpy as np
from PIL import Image
from scipy import ndimage

LEVELS_DIR = "src/SpotDiffS2/img/levels"
SCENES = ["occult", "command", "lounge", "manor", "temple", "gym"]

DELTA_THRESH   = 40
MIN_REGION_PX  = 200
MAX_REGION_PX  = 200_000
N_DIFFS        = 3

def detect_diffs(base_path: str, diff_path: str) -> list[dict]:
    base = np.array(Image.open(base_path).convert("RGB"), dtype=np.float32)
    diff = np.array(Image.open(diff_path).convert("RGB"), dtype=np.float32)

    h, w = base.shape[:2]
    delta = np.sqrt(np.sum((base - diff) ** 2, axis=2))
    mask = delta > DELTA_THRESH

    labeled, n_features = ndimage.label(mask)
    regions = []
    for label_id in range(1, n_features + 1):
        region = labeled == label_id
        size = region.sum()
        if size < MIN_REGION_PX or size > MAX_REGION_PX:
            continue
        ys, xs = np.where(region)
        cx = float(xs.mean() / w)
        cy = float(ys.mean() / h)
        regions.append({"cx": cx, "cy": cy, "size": size})

    # Sort by size descending, take top N
    regions.sort(key=lambda r: r["size"], reverse=True)
    return regions[:N_DIFFS]

def estimate_radius(size_px: int, img_w: int) -> float:
    """Estimate normalized hit radius from region pixel count."""
    r_px = (size_px / np.pi) ** 0.5
    return round(max(0.08, min(0.18, r_px / img_w * 1.4)), 2)

def main():
    print("=== Difference Coordinate Detection ===\n")
    all_results = {}

    for scene_id in SCENES:
        base_path = f"{LEVELS_DIR}/{scene_id}/base.png"
        diff_path = f"{LEVELS_DIR}/{scene_id}/diff.png"

        if not os.path.exists(base_path) or not os.path.exists(diff_path):
            print(f"[{scene_id}] MISSING images, skipping")
            continue
        if os.path.getsize(base_path) < 1000 or os.path.getsize(diff_path) < 1000:
            print(f"[{scene_id}] placeholder images, skipping")
            continue

        regions = detect_diffs(base_path, diff_path)
        base_img = Image.open(base_path)
        img_w = base_img.width

        print(f"[{scene_id}] Found {len(regions)} region(s):")
        diffs = []
        for j, r in enumerate(regions):
            radius = estimate_radius(r["size"], img_w)
            print(f"  [{j+1}] cx={r['cx']:.3f} cy={r['cy']:.3f} r={radius} ({r['size']}px)")
            diffs.append({"cx": round(r["cx"], 3), "cy": round(r["cy"], 3), "r": radius})
        all_results[scene_id] = diffs
        print()

    print("\n=== scenes.ts differences (copy-paste) ===\n")
    for scene_id, diffs in all_results.items():
        print(f"  // {scene_id}")
        prefix_map = {
            "occult": "occult", "command": "cmd", "lounge": "lounge",
            "manor": "manor", "temple": "temple", "gym": "gym"
        }
        p = prefix_map.get(scene_id, scene_id)
        for j, d in enumerate(diffs):
            print(f"  {{ id: '{p}_{j+1}', cx: {d['cx']}, cy: {d['cy']}, r: {d['r']}, label_zh: '???', label_en: '???', emoji: '???' }},")
        print()

if __name__ == "__main__":
    main()
