#!/usr/bin/env ~/miniconda3/bin/python3
"""
Spot the Difference S2 — Scene Base Image Generator
生成6个全新场景的 base 图 (780×554)
"""

import os, sys, time, json, ssl, urllib.request, boto3
from PIL import Image
from io import BytesIO

# ── Config ──────────────────────────────────────────────────────────────────
API_URL     = "http://aiservice.wdabuliu.com:8019/genl_image"
USER_ID     = 123456
OUT_DIR     = "src/SpotDiffS2/img/levels"
IMG_W, IMG_H = 780, 554
WAIT_SECS   = 78   # 75s rate limit + buffer

# R2 config (for img2img reference upload)
R2_ENDPOINT = "https://1d45bc02eda6a12a3a35ff83aae31f72.r2.cloudflarestorage.com"
R2_BUCKET   = "aigram"
R2_PUBLIC   = "https://images.aiwaves.tech"

def make_gradient_ref(w: int, h: int) -> bytes:
    """Create a neutral gradient reference image for txt2img mode."""
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            r = int(180 * x / w + 40)
            g = int(160 * y / h + 40)
            b = int(200 * (1 - x / w) * (1 - y / h) + 40)
            px[x, y] = (r, g, b)
    buf = BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()

def upload_ref(data: bytes, key: str) -> str:
    import hashlib, hmac, datetime
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
    s3.put_object(Bucket=R2_BUCKET, Key=key, Body=data, ContentType="image/png")
    return f"{R2_PUBLIC}/{key}"

def call_api(prompt: str, ref_url: str | None = None) -> bytes:
    params = {"prompt": prompt, "user_id": USER_ID}
    if ref_url:
        params["url"] = ref_url
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
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.open(BytesIO(data)).convert("RGB")
    img = img.resize((IMG_W, IMG_H), Image.LANCZOS)
    img.save(path, "PNG")
    print(f"  Saved {path} ({img.size})")

# ── Scene definitions ────────────────────────────────────────────────────────
SCENES = [
    {
        "id": "cafe",
        "prompt": (
            "cozy indie coffee shop interior, warm afternoon light, "
            "vintage espresso machine on wooden counter, artisan pastries under glass dome, "
            "chalkboard menu with handwritten text, small round tables, "
            "potted plants and succulents on windowsill, framed indie art on walls, "
            "hanging Edison bulbs, coffee grinder, ceramic mugs stacked, "
            "notebook and pen on table, cozy textured atmosphere, "
            "detailed interior photography, rich colors, lots of objects"
        ),
    },
    {
        "id": "vinyl",
        "prompt": (
            "retro vinyl record shop interior, wall-to-wall shelves packed with vinyl records, "
            "vintage turntable on wooden listening station, neon 'RECORDS' sign glowing purple, "
            "cassette tapes display rack, band posters and album art on walls, "
            "vintage amplifier and speakers, crate digging bins, "
            "old jukebox in corner, string lights, music memorabilia, "
            "warm moody lighting, lots of details, rich retro atmosphere"
        ),
    },
    {
        "id": "bar",
        "prompt": (
            "stylish neon night bar interior, backlit shelves lined with colorful bottles, "
            "cocktail glasses and shakers on bar counter, neon signs glowing pink and blue, "
            "dimly lit warm atmosphere, leather bar stools, "
            "cocktail ingredients and garnishes, ice bucket, citrus fruits, "
            "coasters and cocktail menus, vintage photos on walls, "
            "pendant lights overhead, bokeh background, cinematic nightlife mood"
        ),
    },
    {
        "id": "library",
        "prompt": (
            "cozy private library reading room, floor-to-ceiling wooden bookshelves "
            "packed with colorful books, vintage globe on reading desk, "
            "leather armchair with throw blanket, reading lamp casting warm light, "
            "antique wooden desk with open books and papers, "
            "candles in holders, inkwell and quill pen, vintage maps and prints, "
            "framed certificates, brass telescope, magnifying glass, "
            "richly detailed interior, warm amber lighting"
        ),
    },
    {
        "id": "kitchen",
        "prompt": (
            "bright modern kitchen interior, colorful fruit bowl on marble countertop, "
            "organized spice rack with labeled jars, herb plants in pots on windowsill, "
            "sleek coffee machine, ceramic dishes stacked in open shelves, "
            "cutting board with vegetables, cookbook open on stand, "
            "hanging copper pots and pans, refrigerator with magnets, "
            "tea towels, wooden utensil holder, natural morning light streaming in, "
            "clean and vibrant kitchen atmosphere, lots of objects and details"
        ),
    },
    {
        "id": "rooftop",
        "prompt": (
            "rooftop terrace at night, city skyline with glowing skyscraper lights, "
            "fairy string lights draped overhead, small telescope on tripod, "
            "potted flowers and plants in terracotta pots, bistro chairs and table, "
            "citronella candles, starry sky above, urban rooftop garden, "
            "hanging lanterns, succulent wall garden, "
            "warm golden ambient lighting, cinematic night atmosphere, "
            "lots of details and objects, beautiful composition"
        ),
    },
]

def main():
    # Upload gradient reference for txt2img
    ts = int(time.time())
    print("Uploading gradient reference image...")
    grad_data = make_gradient_ref(IMG_W, IMG_H)
    ref_key = f"refs/spot-diff-s2/gradient_{ts}.png"
    ref_url = upload_ref(grad_data, ref_key)
    print(f"  Ref URL: {ref_url}")

    for i, scene in enumerate(SCENES):
        sid = scene["id"]
        out_path = f"{OUT_DIR}/{sid}/base.png"

        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            print(f"[{i+1}/6] {sid}: already exists, skipping")
            continue

        print(f"[{i+1}/6] Generating {sid}...")
        try:
            data = call_api(scene["prompt"], ref_url=ref_url)
            save_image(data, out_path)
        except Exception as e:
            print(f"  ERROR: {e}")

        if i < len(SCENES) - 1:
            print(f"  Waiting {WAIT_SECS}s (rate limit)...")
            time.sleep(WAIT_SECS)

    print("\nAll scenes generated! Run gen_diffs_s2.py next.")

if __name__ == "__main__":
    main()
