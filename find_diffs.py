#!/usr/bin/env python3
"""
Compare base.png and diff.png to find the top N difference regions.
Outputs normalized coordinates for levels/index.ts.

Usage: ~/miniconda3/bin/python3 find_diffs.py [--level algram] [--top 5] [--visual]
"""

import argparse
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFilter
    import numpy as np
except ImportError:
    sys.exit("Need PIL + numpy. Use: ~/miniconda3/bin/python3 find_diffs.py")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(SCRIPT_DIR, "src", "SpotDiff", "img", "levels")
LEVELS = ["algram", "jenny", "jmf", "ghostpixel", "isaya", "isabel"]


def find_diff_regions(base_path, diff_path, top_n=5, min_distance=0.2):
    """
    Find top N difference regions between two images.
    Returns list of (cx, cy, r) in normalized coordinates.
    """
    base = Image.open(base_path).convert("RGB")
    diff = Image.open(diff_path).convert("RGB")

    # Ensure same size
    if diff.size != base.size:
        diff = diff.resize(base.size, Image.LANCZOS)

    w, h = base.size
    base_arr = np.array(base, dtype=np.float32)
    diff_arr = np.array(diff, dtype=np.float32)

    # Per-pixel difference magnitude
    delta = np.sqrt(np.sum((base_arr - diff_arr) ** 2, axis=2))

    # Blur to find regions rather than individual pixels
    # Convert to PIL for gaussian blur, then back
    delta_img = Image.fromarray(delta.astype(np.uint8))
    delta_blurred = delta_img.filter(ImageFilter.GaussianBlur(radius=15))
    delta_map = np.array(delta_blurred, dtype=np.float32)

    # Find top N peaks with minimum distance constraint
    regions = []
    used_mask = np.zeros_like(delta_map, dtype=bool)
    min_dist_px = min_distance * max(w, h)

    for _ in range(top_n * 3):  # search more candidates
        if len(regions) >= top_n:
            break

        # Find max in unused area
        masked = delta_map.copy()
        masked[used_mask] = 0

        if masked.max() < 5:  # threshold: minimum difference
            break

        peak_y, peak_x = np.unravel_index(masked.argmax(), masked.shape)

        # Check distance from existing regions
        too_close = False
        for rx, ry, _ in regions:
            dist = np.sqrt((peak_x - rx * w) ** 2 + (peak_y - ry * h) ** 2)
            if dist < min_dist_px:
                too_close = True
                break

        if too_close:
            y_lo = max(0, peak_y - int(min_dist_px // 2))
            y_hi = min(h, peak_y + int(min_dist_px // 2))
            x_lo = max(0, peak_x - int(min_dist_px // 2))
            x_hi = min(w, peak_x + int(min_dist_px // 2))
            used_mask[y_lo:y_hi, x_lo:x_hi] = True
            continue

        # Skip edge regions (within 5% of border)
        margin = 0.05
        norm_x, norm_y = peak_x / w, peak_y / h
        if norm_x < margin or norm_x > 1 - margin or norm_y < margin or norm_y > 1 - margin:
            y_lo = max(0, peak_y - int(min_dist_px // 2))
            y_hi = min(h, peak_y + int(min_dist_px // 2))
            x_lo = max(0, peak_x - int(min_dist_px // 2))
            x_hi = min(w, peak_x + int(min_dist_px // 2))
            used_mask[y_lo:y_hi, x_lo:x_hi] = True
            continue

        # Calculate region radius based on difference spread
        threshold = masked.max() * 0.3
        region_pixels = masked[
            max(0, peak_y - 50):min(h, peak_y + 50),
            max(0, peak_x - 50):min(w, peak_x + 50),
        ] > threshold
        radius_px = max(20, np.sqrt(region_pixels.sum()) * 1.5)

        # Normalize
        cx = peak_x / w
        cy = peak_y / h
        r = radius_px / max(w, h)
        r = max(0.04, min(0.08, r))  # clamp radius to reasonable game range

        regions.append((cx, cy, r))

        # Mask out this region
        y_lo = max(0, peak_y - int(min_dist_px))
        y_hi = min(h, peak_y + int(min_dist_px))
        x_lo = max(0, peak_x - int(min_dist_px))
        x_hi = min(w, peak_x + int(min_dist_px))
        used_mask[y_lo:y_hi, x_lo:x_hi] = True

    return regions


def visualize(base_path, diff_path, regions, out_path):
    """Draw detected regions on a side-by-side comparison image."""
    base = Image.open(base_path).convert("RGB")
    diff = Image.open(diff_path).convert("RGB")
    if diff.size != base.size:
        diff = diff.resize(base.size, Image.LANCZOS)

    w, h = base.size
    canvas = Image.new("RGB", (w * 2 + 10, h), (30, 30, 30))
    canvas.paste(base, (0, 0))
    canvas.paste(diff, (w + 10, 0))

    draw = ImageDraw.Draw(canvas)
    colors = [(255, 80, 80), (80, 255, 80), (80, 80, 255), (255, 255, 80), (255, 80, 255)]

    for i, (cx, cy, r) in enumerate(regions):
        color = colors[i % len(colors)]
        px, py = int(cx * w), int(cy * h)
        pr = int(r * max(w, h))

        # Draw on both images
        for offset_x in [0, w + 10]:
            draw.ellipse(
                [offset_x + px - pr, py - pr, offset_x + px + pr, py + pr],
                outline=color, width=3,
            )
            draw.text((offset_x + px - 5, py - 8), str(i + 1), fill=color)

    canvas.save(out_path, "PNG")
    print(f"  ✓ Visual saved: {out_path}")


def process_level(level_id, top_n=5, visual=False):
    base_path = os.path.join(IMG_DIR, level_id, "base.png")
    diff_path = os.path.join(IMG_DIR, level_id, "diff.png")

    if not os.path.exists(base_path) or not os.path.exists(diff_path):
        print(f"  ⏭ Skipping {level_id} — missing base.png or diff.png")
        return None

    print(f"\n  Analyzing {level_id}…")
    regions = find_diff_regions(base_path, diff_path, top_n=top_n)

    if not regions:
        print(f"  ⚠ No significant differences found for {level_id}")
        return None

    print(f"  Found {len(regions)} difference regions:")
    for i, (cx, cy, r) in enumerate(regions):
        print(f"    [{i+1}] cx={cx:.3f}, cy={cy:.3f}, r={r:.3f}")

    if visual:
        vis_path = os.path.join(IMG_DIR, level_id, "comparison.png")
        visualize(base_path, diff_path, regions, vis_path)

    return regions


def main():
    parser = argparse.ArgumentParser(description="Find differences between base and diff images")
    parser.add_argument("--level", help="Process only this level (e.g. algram)")
    parser.add_argument("--top", type=int, default=5, help="Number of top differences to find")
    parser.add_argument("--visual", action="store_true", help="Generate visual comparison image")
    args = parser.parse_args()

    levels = [args.level] if args.level else LEVELS
    all_results = {}

    for level_id in levels:
        result = process_level(level_id, top_n=args.top, visual=args.visual)
        if result:
            all_results[level_id] = result

    # Output TypeScript code
    if all_results:
        print(f"\n{'='*60}")
        print("TypeScript for levels/index.ts:")
        print(f"{'='*60}")

        id_prefix = {'algram': 'a', 'jenny': 'j', 'jmf': 'm',
                      'ghostpixel': 'g', 'isaya': 'i', 'isabel': 'b'}

        for level_id, regions in all_results.items():
            prefix = id_prefix.get(level_id, level_id[0])
            print(f"\n// {level_id}")
            print("differences: [")
            for i, (cx, cy, r) in enumerate(regions):
                print(f"  {{ id: '{prefix}{i+1}', cx: {cx:.3f}, cy: {cy:.3f}, "
                      f"r: {r:.3f}, label_zh: '差异{i+1}', label_en: 'Diff {i+1}' }},")
            print("],")


if __name__ == "__main__":
    main()
