#!/usr/bin/env python3
"""
Generate diff images by using base images as reference via online img2img API.
The API will produce a similar but subtly different version of each scene.

Usage:
  ~/miniconda3/bin/python3 generate_diffs_online.py          # all 6
  ~/miniconda3/bin/python3 generate_diffs_online.py --only 1  # level 1 only

After generation, use find_diffs.py to detect actual difference regions
and update coordinates in levels/index.ts.
"""

import argparse
import datetime
import hashlib
import hmac
import json
import os
import ssl
import subprocess
import sys
import time
import urllib.request
import urllib.error
import urllib.parse

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

API_URL = "http://aiservice.wdabuliu.com:8019/genl_image"
API_TIMEOUT = 360
RATE_LIMIT_S = 78
USER_ID = 123456

R2_ACCOUNT_ID = "bdccd2c68ff0d2e622994d24dbb1bae3"
R2_ACCESS_KEY = "b203adb7561b4f8800cbc1fa02424467"
R2_SECRET_KEY = "e7926e4175b7a0914496b9c999afd914cd1e4af7db8f83e0cf2bfad9773fa2b0"
R2_BUCKET = "aigram"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(SCRIPT_DIR, "src", "SpotDiff", "img", "levels")

# Each scene: use same theme prompt but ask for small variations
SCENES = [
    {
        "id": "algram",
        "prompt": (
            "anime illustration of a cozy music studio room interior, "
            "blue electric guitar leaning on wall, guitar amplifier with red glowing knobs, "
            "CD player instead of vinyl record player, sheet music on stand with different notes, "
            "guitar pedals on floor with green LED lights, warm ambient lighting, "
            "different posters on wall, wooden floor, cables and red headphones, "
            "detailed anime background art style, no people, no characters"
        ),
    },
    {
        "id": "jenny",
        "prompt": (
            "anime illustration of a programmer desk workspace interior, "
            "dual monitor setup with different code on screens, mechanical keyboard with blue RGB lighting, "
            "tea cup instead of coffee mug, different colored sticky notes on monitor, "
            "small cactus instead of potted plant, red desk lamp, different stack of books, "
            "white cat sleeping on desk corner, USB cables, different figurines, "
            "cozy night atmosphere, detailed anime background art style, no people, no characters"
        ),
    },
    {
        "id": "jmf",
        "prompt": (
            "anime illustration of a dark hacker room interior, "
            "multiple monitors showing red terminal text and code instead of green, "
            "server rack with blue blinking LED lights, dim purple and red ambient light, "
            "cola cans instead of energy drinks, tangled ethernet cables, white keyboard and mouse, "
            "dark curtains, pink neon accent lights, cyberpunk atmosphere, "
            "detailed anime background art style, no people, no characters"
        ),
    },
    {
        "id": "ghostpixel",
        "prompt": (
            "anime illustration of a spooky haunted cottage interior, "
            "floating books and objects in mid-air, glowing candles with green flames instead of blue, "
            "old wooden furniture, cobwebs, mysterious red portal glow instead of purple, "
            "round mirror on wall instead of antique, ghostly mist, orange and green lighting, "
            "cracked window with moonlight, different ornate rug pattern on floor, "
            "detailed anime background art style, no people, no characters"
        ),
    },
    {
        "id": "isaya",
        "prompt": (
            "anime illustration of an artist bedroom studio interior, "
            "easel with different painting showing a landscape, art supplies and paint tubes scattered, "
            "orange cat instead of black cat sitting on windowsill, red headphones on desk, "
            "sketchbooks stacked, different colored fairy lights on wall, cozy bed with different plushies, "
            "warm sunset light through window, paint palette with different colors, brush cups, "
            "detailed anime background art style, no people, no characters"
        ),
    },
    {
        "id": "isabel",
        "prompt": (
            "anime illustration of an elegant floral vanity room interior, "
            "ornate mirror with silver frame instead of gold, flower vases with tulips and sunflowers, "
            "open jewelry box with bracelets and rings, blue perfume bottles, "
            "different makeup brushes and cosmetics, lace curtains, soft purple lighting instead of pink, "
            "dried lavender bouquets, ribbon and different hairpins, vintage decor, "
            "detailed anime background art style, no people, no characters"
        ),
    },
]


def _sign(key, msg):
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def upload_to_r2(path):
    """Upload image to Cloudflare R2 → public CDN URL."""
    print(f"  ↑ Uploading {os.path.basename(path)} to R2…")
    with open(path, "rb") as f:
        data = f.read()

    obj_key = "refs/spot-diff/" + os.path.basename(os.path.dirname(path)) + "_" + os.path.basename(path)
    host = f"{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    now = datetime.datetime.now(datetime.UTC)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    region = "auto"
    service = "s3"

    content_type = "image/png"
    content_hash = hashlib.sha256(data).hexdigest()
    canon_uri = "/" + R2_BUCKET + "/" + urllib.parse.quote(obj_key, safe="/")

    canon_headers = (
        f"content-type:{content_type}\n"
        f"host:{host}\n"
        f"x-amz-content-sha256:{content_hash}\n"
        f"x-amz-date:{amz_date}\n"
    )
    signed_headers = "content-type;host;x-amz-content-sha256;x-amz-date"

    canon_req = "\n".join([
        "PUT", canon_uri, "",
        canon_headers, signed_headers, content_hash,
    ])

    cred_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    str_to_sign = "\n".join([
        "AWS4-HMAC-SHA256", amz_date, cred_scope,
        hashlib.sha256(canon_req.encode()).hexdigest(),
    ])

    k_date = _sign(("AWS4" + R2_SECRET_KEY).encode(), date_stamp)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, service)
    k_signing = _sign(k_service, "aws4_request")
    signature = hmac.new(k_signing, str_to_sign.encode(), hashlib.sha256).hexdigest()

    auth = (
        f"AWS4-HMAC-SHA256 Credential={R2_ACCESS_KEY}/{cred_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    url = f"https://{host}/{R2_BUCKET}/{urllib.parse.quote(obj_key, safe='/')}"
    req = urllib.request.Request(url, data=data, method="PUT", headers={
        "Content-Type": content_type,
        "Host": host,
        "x-amz-content-sha256": content_hash,
        "x-amz-date": amz_date,
        "Authorization": auth,
    })

    with urllib.request.urlopen(req, timeout=60, context=_SSL_CTX) as resp:
        resp.read()

    public_url = f"https://images.aiwaves.tech/{obj_key}"
    print(f"  ✓ Uploaded → {public_url}")
    return public_url


def call_api(ref_url, prompt):
    payload = json.dumps({
        "query": "",
        "params": {
            "url": ref_url,
            "prompt": prompt,
            "user_id": USER_ID,
        },
    }).encode()

    req = urllib.request.Request(
        API_URL, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            result = json.loads(body)
        except Exception:
            sys.exit(f"ERROR: HTTP {e.code} — {body}")

    code = result.get("code")
    if code == 200:
        return result["url"]
    if code == 429:
        raise RuntimeError("rate_limit")
    print(f"  ✗ API returned code={code}")
    return None


def download_image(url, out_path):
    print(f"  ↓ Downloading result…")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    src_ext = os.path.splitext(url.split("?")[0])[1].lower()
    dst_ext = os.path.splitext(out_path)[1].lower()
    tmp_path = out_path if src_ext == dst_ext else out_path + src_ext

    # Retry up to 3 times with delay
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60, context=_SSL_CTX) as resp:
                data = resp.read()
            break
        except urllib.error.HTTPError as e:
            if attempt < 2:
                print(f"  ⚠ Download failed ({e.code}), retrying in 5s…")
                time.sleep(5)
            else:
                raise

    with open(tmp_path, "wb") as f:
        f.write(data)

    if src_ext != dst_ext and dst_ext in (".png", ".jpg", ".jpeg"):
        fmt = "png" if dst_ext == ".png" else "jpeg"
        subprocess.run(["sips", "-s", "format", fmt, tmp_path, "--out", out_path],
                       check=True, capture_output=True)
        os.remove(tmp_path)
        print(f"  ✓ Converted {src_ext} → {dst_ext}")
    elif tmp_path != out_path:
        os.rename(tmp_path, out_path)

    size_kb = os.path.getsize(out_path) // 1024
    print(f"  ✓ Saved → {out_path}  ({size_kb} KB)")


def resize_to_match(diff_path, base_path):
    """Resize diff image to match base image dimensions exactly."""
    from PIL import Image
    base = Image.open(base_path)
    diff = Image.open(diff_path)
    if diff.size != base.size:
        print(f"  ✂ Resizing diff {diff.size} → {base.size}")
        diff = diff.resize(base.size, Image.LANCZOS)
        diff.save(diff_path, "PNG", optimize=True)


def generate_diff(scene):
    base_path = os.path.join(IMG_DIR, scene["id"], "base.png")
    diff_path = os.path.join(IMG_DIR, scene["id"], "diff.png")

    if not os.path.exists(base_path):
        print(f"\n  ⏭ Skipping {scene['id']} — no base.png")
        return False

    print(f"\n{'='*60}")
    print(f"Generating diff for: {scene['id']}")
    print(f"  Using base.png as reference image")
    print(f"{'='*60}")

    # Upload base image as reference
    ref_url = upload_to_r2(base_path)

    # Call API with base as ref
    while True:
        try:
            result_url = call_api(ref_url, scene["prompt"])
        except RuntimeError as e:
            if str(e) == "rate_limit":
                print(f"  ⏳ Rate limited — waiting {RATE_LIMIT_S}s…")
                time.sleep(RATE_LIMIT_S)
                continue
            raise
        break

    if not result_url:
        print(f"  ✗ Failed to generate diff for {scene['id']}")
        return False

    download_image(result_url, diff_path)

    # Ensure same dimensions as base
    try:
        resize_to_match(diff_path, base_path)
    except ImportError:
        print("  ⚠ PIL not available, skipping resize check")

    return True


def main():
    parser = argparse.ArgumentParser(description="Generate diff images via img2img API")
    parser.add_argument("--only", type=int, help="Generate only level N (1-6)")
    args = parser.parse_args()

    scenes = SCENES
    if args.only:
        idx = args.only - 1
        if idx < 0 or idx >= len(SCENES):
            sys.exit(f"ERROR: --only must be 1-{len(SCENES)}")
        scenes = [SCENES[idx]]

    success = 0
    for i, scene in enumerate(scenes):
        ok = generate_diff(scene)
        if ok:
            success += 1
        if i < len(scenes) - 1:
            print(f"\n  ⏳ Waiting {RATE_LIMIT_S}s for rate limit…")
            time.sleep(RATE_LIMIT_S)

    print(f"\n{'='*60}")
    print(f"Done: {success}/{len(scenes)} diff images generated")
    print(f"\nNext: run find_diffs.py to detect difference regions")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
