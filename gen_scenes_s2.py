#!/usr/bin/env ~/miniconda3/bin/python3
"""
Spot the Difference S2 — Scene Base Image Generator
生成6个场景的 base 图 (780×554)
"""

import datetime, hashlib, hmac, json, os, ssl, sys, time, urllib.request, urllib.parse
import numpy as np
from PIL import Image
from io import BytesIO

API_URL       = "http://aiservice.wdabuliu.com:8019/genl_image"
API_TIMEOUT   = 360
USER_ID       = 123456
R2_ACCOUNT_ID = "bdccd2c68ff0d2e622994d24dbb1bae3"
R2_ACCESS_KEY = "b203adb7561b4f8800cbc1fa02424467"
R2_SECRET_KEY = "e7926e4175b7a0914496b9c999afd914cd1e4af7db8f83e0cf2bfad9773fa2b0"
R2_BUCKET     = "aigram"
R2_PUBLIC     = "https://images.aiwaves.tech"
OUT_DIR       = "src/SpotDiffS2/img/levels"
TARGET_W, TARGET_H = 780, 554
WAIT_SECS     = 78

_SSL = ssl.create_default_context()
_SSL.check_hostname = False
_SSL.verify_mode = ssl.CERT_NONE


def _sign(key, msg):
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def upload_r2(local_path: str, obj_key: str) -> str:
    with open(local_path, "rb") as f:
        data = f.read()
    host = f"{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    now = datetime.datetime.now(datetime.timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    region, service, method = "auto", "s3", "PUT"
    content_type = "image/png"
    canon_uri = "/" + R2_BUCKET + "/" + urllib.parse.quote(obj_key, safe="/")
    canon_headers = f"content-type:{content_type}\nhost:{host}\nx-amz-content-sha256:UNSIGNED-PAYLOAD\nx-amz-date:{amz_date}\n"
    signed_headers = "content-type;host;x-amz-content-sha256;x-amz-date"
    canon_req = f"{method}\n{canon_uri}\n\n{canon_headers}\n{signed_headers}\nUNSIGNED-PAYLOAD"
    scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string2sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{scope}\n{hashlib.sha256(canon_req.encode()).hexdigest()}"
    k = _sign(_sign(_sign(_sign(("AWS4" + R2_SECRET_KEY).encode(), date_stamp), region), service), "aws4_request")
    sig = hmac.new(k, string2sign.encode(), hashlib.sha256).hexdigest()
    auth = f"AWS4-HMAC-SHA256 Credential={R2_ACCESS_KEY}/{scope}, SignedHeaders={signed_headers}, Signature={sig}"
    req = urllib.request.Request(
        f"https://{host}/{R2_BUCKET}/{urllib.parse.quote(obj_key, safe='/')}",
        data=data, method="PUT",
        headers={"Content-Type": content_type, "x-amz-content-sha256": "UNSIGNED-PAYLOAD",
                 "x-amz-date": amz_date, "Authorization": auth},
    )
    urllib.request.urlopen(req, timeout=60, context=_SSL)
    url = f"{R2_PUBLIC}/{obj_key}"
    print(f"  ↑ Uploaded → {url}")
    return url


def create_gradient_ref(w: int, h: int, tmp_path: str) -> str:
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            arr[y, x] = [40 + x * 80 // w, 30 + y * 60 // h, 50]
    Image.fromarray(arr).save(tmp_path, "PNG")
    return tmp_path


def call_api(ref_url: str, prompt: str) -> str:
    payload = json.dumps({"query": "", "params": {"url": ref_url, "prompt": prompt, "user_id": USER_ID}}).encode()
    req = urllib.request.Request(API_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    resp = urllib.request.urlopen(req, timeout=API_TIMEOUT)
    result = json.loads(resp.read())
    return result.get("image_url") or result.get("url") or result.get("result", {}).get("image_url", "")


def download_and_save(url: str, out_path: str):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=60, context=_SSL).read()
            img = Image.open(BytesIO(data)).convert("RGB")
            img = img.resize((TARGET_W, TARGET_H), Image.LANCZOS)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            img.save(out_path, "PNG")
            print(f"  ✓ Saved {out_path}")
            return
        except Exception as e:
            print(f"  ⚠ Attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(5)
    raise RuntimeError(f"Failed to download {url}")


SCENES = [
    {
        "id": "cafe",
        "prompt": (
            "cozy indie coffee shop interior, warm afternoon light, "
            "vintage espresso machine on wooden counter, artisan pastries under glass dome, "
            "chalkboard menu with handwritten text, small round tables with chairs, "
            "potted succulents on windowsill, framed indie art on walls, "
            "hanging Edison bulbs, ceramic coffee grinder, colorful mugs stacked, "
            "open notebook and pen on table, wood and tile floor, "
            "detailed interior, rich warm colors, many objects visible"
        ),
    },
    {
        "id": "vinyl",
        "prompt": (
            "retro vinyl record shop interior, wall-to-wall shelves packed with vinyl records, "
            "vintage turntable on wooden listening station with headphones, "
            "neon RECORDS sign glowing purple on wall, cassette tapes display rack, "
            "band posters and album art covering walls, vintage amplifier and speakers, "
            "crate digging bins filled with records, old jukebox in corner, "
            "string lights, music memorabilia and stickers, wooden floor, "
            "warm moody lighting, many objects, rich retro atmosphere"
        ),
    },
    {
        "id": "bar",
        "prompt": (
            "stylish neon night bar interior, backlit glass shelves lined with spirit bottles, "
            "cocktail glasses and shaker on bar counter, pink neon OPEN sign, "
            "dimly lit warm atmosphere, bar stools at counter, "
            "citrus fruits and cocktail garnishes, ice bucket, cocktail menu cards, "
            "pendant lights, blurred bokeh background lights, "
            "vintage black and white photos on walls, dark wood and brass details, "
            "cinematic moody nightlife atmosphere, many bar objects"
        ),
    },
    {
        "id": "library",
        "prompt": (
            "cozy private library reading room, floor-to-ceiling dark wooden bookshelves "
            "packed with colorful hardcover books, vintage globe on oak reading desk, "
            "leather armchair with plaid throw blanket beside window, "
            "reading lamp casting warm golden light, open books and papers on desk, "
            "candles in brass holders, inkwell and quill pen, "
            "framed certificates and vintage maps on wall, brass telescope, magnifying glass, "
            "Persian rug on floor, warm amber fireplace glow, rich detailed interior"
        ),
    },
    {
        "id": "kitchen",
        "prompt": (
            "bright modern kitchen interior, colorful fruit bowl with apples and oranges "
            "on white marble countertop, organized spice rack with labeled jars, "
            "fresh herb plants in terracotta pots on sunny windowsill, "
            "sleek silver espresso machine, white ceramic dishes on open shelves, "
            "cutting board with vegetables, cookbook open on wooden stand, "
            "hanging copper pots and pans, refrigerator with magnets and notes, "
            "striped tea towels, wooden utensil holder, natural morning light, "
            "many kitchen objects, clean fresh atmosphere"
        ),
    },
    {
        "id": "rooftop",
        "prompt": (
            "rooftop terrace at night, city skyline with glowing skyscraper lights behind, "
            "warm fairy string lights draped overhead in zigzag pattern, "
            "brass telescope on tripod aimed at stars, "
            "pink and white flowers in terracotta pots, metal bistro chairs and table, "
            "citronella candles in glass holders, clear starry night sky, "
            "succulent wall garden on brick wall, hanging paper lanterns, "
            "wooden deck floor, cozy urban garden atmosphere, many decorative objects"
        ),
    },
]


def main():
    ts = int(time.time() * 1000)
    tmp_ref = f"/tmp/s2_gradient_ref_{ts}.png"
    create_gradient_ref(TARGET_W, TARGET_H, tmp_ref)
    ref_key = f"refs/spot-diff-s2/gradient_{ts}.png"
    print("Uploading gradient reference...")
    ref_url = upload_r2(tmp_ref, ref_key)
    os.remove(tmp_ref)

    for i, scene in enumerate(SCENES):
        sid = scene["id"]
        out_path = f"{OUT_DIR}/{sid}/base.png"

        if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
            print(f"[{i+1}/{len(SCENES)}] {sid}: already exists, skipping")
            continue

        print(f"\n[{i+1}/{len(SCENES)}] Generating {sid}...")
        result_url = call_api(ref_url, scene["prompt"])
        print(f"  ↓ {result_url}")
        download_and_save(result_url, out_path)

        if i < len(SCENES) - 1:
            print(f"  Waiting {WAIT_SECS}s (rate limit)...")
            time.sleep(WAIT_SECS)

    print("\n✓ All scenes done! Run gen_diffs_s2.py next.")


if __name__ == "__main__":
    main()
