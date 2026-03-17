#!/usr/bin/env ~/miniconda3/bin/python3
"""
Spot the Difference S2 — Diff Image Generator
为每个 base 图生成对应的 diff 图 (用 base 作为 img2img 参考)
"""

import os, sys, time, json, ssl, urllib.request, boto3
from PIL import Image
from io import BytesIO

API_URL  = "http://aiservice.wdabuliu.com:8019/genl_image"
USER_ID  = 123456
OUT_DIR  = "src/SpotDiffS2/img/levels"
IMG_W, IMG_H = 780, 554
WAIT_SECS = 78

R2_ENDPOINT = "https://1d45bc02eda6a12a3a35ff83aae31f72.r2.cloudflarestorage.com"
R2_BUCKET   = "aigram"
R2_PUBLIC   = "https://images.aiwaves.tech"

def upload_ref(path: str, key: str) -> str:
    aws_key    = os.environ.get("R2_ACCESS_KEY", "")
    aws_secret = os.environ.get("R2_SECRET_KEY", "")
    if not aws_key:
        raise RuntimeError("Set R2_ACCESS_KEY and R2_SECRET_KEY env vars")
    s3 = boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret,
        region_name="auto",
    )
    with open(path, "rb") as f:
        data = f.read()
    s3.put_object(Bucket=R2_BUCKET, Key=key, Body=data, ContentType="image/png")
    url = f"{R2_PUBLIC}/{key}"
    print(f"  Uploaded ref: {url}")
    return url

def call_api(prompt: str, ref_url: str) -> bytes:
    params = {"prompt": prompt, "user_id": USER_ID, "url": ref_url}
    payload = json.dumps({"query": "", "params": params}).encode()
    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=360, context=ctx) as r:
        resp = json.loads(r.read())
    if resp.get("code") != 200:
        raise RuntimeError(f"API error: {resp}")
    img_url = resp["url"]
    with urllib.request.urlopen(img_url, context=ctx) as r:
        return r.read()

def save_image(data: bytes, path: str):
    img = Image.open(BytesIO(data)).convert("RGB")
    img = img.resize((IMG_W, IMG_H), Image.LANCZOS)
    img.save(path, "PNG")
    print(f"  Saved {path}")

# Diff prompts = base prompt + small specific changes ("instead of")
DIFF_PROMPTS = {
    "cafe": (
        "cozy indie coffee shop interior, warm afternoon light, "
        "vintage espresso machine on wooden counter, artisan pastries under glass dome, "
        "chalkboard menu with handwritten text, small round tables, "
        "PINK potted plant instead of green potted plant on windowsill, "
        "framed indie art on walls, hanging Edison bulbs, "
        "BLUE coffee grinder instead of silver coffee grinder, ceramic mugs stacked, "
        "ORANGE notebook instead of white notebook on table, cozy textured atmosphere, "
        "detailed interior photography, rich colors"
    ),
    "vinyl": (
        "retro vinyl record shop interior, wall-to-wall shelves packed with vinyl records, "
        "vintage turntable on wooden listening station, "
        "RED neon sign instead of PURPLE neon sign, "
        "cassette tapes display rack, band posters and album art on walls, "
        "vintage amplifier and speakers, crate digging bins, "
        "YELLOW jukebox instead of red jukebox in corner, "
        "string lights, music memorabilia, warm moody lighting"
    ),
    "bar": (
        "stylish neon night bar interior, backlit shelves lined with colorful bottles, "
        "cocktail glasses and shakers on bar counter, "
        "BLUE neon sign instead of PINK neon sign, "
        "dimly lit warm atmosphere, leather bar stools, "
        "cocktail ingredients and garnishes, "
        "LIME instead of LEMON as garnish on bar counter, "
        "ROUND ice bucket instead of square ice bucket, "
        "coasters and cocktail menus, vintage photos on walls"
    ),
    "library": (
        "cozy private library reading room, floor-to-ceiling wooden bookshelves, "
        "vintage globe on reading desk, leather armchair with throw blanket, "
        "reading lamp casting warm light, antique wooden desk with open books, "
        "candles in holders, inkwell and quill pen, "
        "RED frame around the certificate instead of gold frame, "
        "vintage maps and prints, "
        "SILVER telescope instead of brass telescope, magnifying glass, "
        "richly detailed interior, warm amber lighting"
    ),
    "kitchen": (
        "bright modern kitchen interior, "
        "ORANGE bowl with fruit instead of white bowl with fruit on marble countertop, "
        "organized spice rack with labeled jars, "
        "PURPLE basil plant instead of green herb plant on windowsill, "
        "sleek coffee machine, ceramic dishes stacked in open shelves, "
        "cutting board with vegetables, cookbook open on stand, "
        "hanging copper pots and pans, refrigerator with magnets, "
        "RED tea towel instead of white tea towel, wooden utensil holder"
    ),
    "rooftop": (
        "rooftop terrace at night, city skyline with glowing skyscraper lights, "
        "fairy string lights draped overhead, "
        "telescope on tripod pointed at DIFFERENT ANGLE, "
        "YELLOW potted flowers instead of pink flowers in terracotta pots, "
        "bistro chairs and table, citronella candles, starry sky above, "
        "hanging lanterns, succulent wall garden, "
        "BLUE string lights instead of warm white string lights overhead"
    ),
}

def main():
    ts = int(time.time())
    scene_ids = list(DIFF_PROMPTS.keys())

    for i, sid in enumerate(scene_ids):
        base_path = f"{OUT_DIR}/{sid}/base.png"
        diff_path = f"{OUT_DIR}/{sid}/diff.png"

        if not os.path.exists(base_path) or os.path.getsize(base_path) < 1000:
            print(f"[{i+1}/6] {sid}: base.png missing, run gen_scenes_s2.py first")
            continue

        if os.path.exists(diff_path) and os.path.getsize(diff_path) > 1000:
            print(f"[{i+1}/6] {sid}: diff already exists, skipping")
            continue

        print(f"[{i+1}/6] Generating diff for {sid}...")
        try:
            # Upload base as reference (with cache-bust timestamp)
            ref_key = f"refs/spot-diff-s2/{sid}_base_{ts}.png"
            ref_url = upload_ref(base_path, ref_key)

            data = call_api(DIFF_PROMPTS[sid], ref_url)
            save_image(data, diff_path)
        except Exception as e:
            print(f"  ERROR: {e}")

        if i < len(scene_ids) - 1:
            print(f"  Waiting {WAIT_SECS}s...")
            time.sleep(WAIT_SECS)

    print("\nAll diffs generated! Run find_diffs_s2.py next to detect difference coordinates.")

if __name__ == "__main__":
    main()
