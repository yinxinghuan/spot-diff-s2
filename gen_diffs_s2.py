#!/usr/bin/env ~/miniconda3/bin/python3
"""
Spot the Difference S2 — Diff Image Generator
为每个 base 图生成对应的 diff 图 (用 base 作为 img2img 参考)
"""

import datetime, hashlib, hmac, json, os, ssl, sys, time, urllib.request, urllib.parse
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
    for attempt in range(3):
        try:
            urllib.request.urlopen(req, timeout=60, context=_SSL)
            break
        except Exception as e:
            if attempt < 2:
                print(f"  ⚠ Upload attempt {attempt+1} failed: {e}, retrying...")
                time.sleep(5)
            else:
                raise
    url = f"{R2_PUBLIC}/{obj_key}"
    print(f"  ↑ Uploaded → {url}")
    return url


def call_api(ref_url: str, prompt: str) -> str:
    payload = json.dumps({"query": "", "params": {"url": ref_url, "prompt": prompt, "user_id": USER_ID}}).encode()
    req = urllib.request.Request(API_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    resp = urllib.request.urlopen(req, timeout=API_TIMEOUT)
    result = json.loads(resp.read())
    print(f"  API response code={result.get('code')} msg={result.get('msg','')}")
    if result.get("code") == 429:
        raise RuntimeError("Rate limited (429)")
    if result.get("code") != 200:
        raise RuntimeError(f"API error: {result}")
    url = result.get("image_url") or result.get("url") or result.get("result", {}).get("image_url", "")
    return url


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


# Diff prompts: base prompt + specific object changes ("instead of")
DIFF_PROMPTS = {
    "cafe": (
        "cozy indie coffee shop interior, warm afternoon light, "
        "vintage espresso machine on wooden counter, artisan pastries under glass dome, "
        "chalkboard menu with handwritten text, small round tables with chairs, "
        "PINK succulent instead of green succulent on windowsill, "
        "framed indie art on walls, hanging Edison bulbs, "
        "BLUE ceramic coffee grinder instead of silver coffee grinder, "
        "colorful mugs stacked, "
        "ORANGE notebook instead of white notebook on table, "
        "wood and tile floor, detailed interior, rich warm colors"
    ),
    "vinyl": (
        "retro vinyl record shop interior, wall-to-wall shelves packed with vinyl records, "
        "vintage turntable on wooden listening station with headphones, "
        "RED neon RECORDS sign instead of PURPLE neon sign, "
        "cassette tapes display rack, band posters and album art covering walls, "
        "vintage amplifier and speakers, crate digging bins filled with records, "
        "GREEN jukebox instead of red jukebox in corner, "
        "string lights, music memorabilia, wooden floor, warm moody lighting"
    ),
    "bar": (
        "stylish neon night bar interior, backlit glass shelves lined with spirit bottles, "
        "cocktail glasses and shaker on bar counter, "
        "BLUE neon OPEN sign instead of pink neon sign, "
        "dimly lit warm atmosphere, bar stools at counter, "
        "LIME instead of LEMON as garnish on bar counter, "
        "TALL cylindrical ice bucket instead of round ice bucket, "
        "cocktail menu cards, pendant lights, "
        "dark wood and brass details, cinematic moody atmosphere"
    ),
    "library": (
        "cozy private library reading room, floor-to-ceiling dark wooden bookshelves "
        "packed with colorful hardcover books, vintage globe on oak reading desk, "
        "leather armchair with plaid throw blanket, reading lamp, "
        "open books and papers on desk, candles in brass holders, "
        "inkwell and quill pen, "
        "BLUE frame around the certificate instead of gold frame, "
        "vintage maps on wall, SILVER telescope instead of brass telescope, "
        "magnifying glass, Persian rug, warm amber light"
    ),
    "kitchen": (
        "bright modern kitchen interior, "
        "PURPLE bowl with grapes instead of colorful fruit bowl on marble countertop, "
        "organized spice rack with labeled jars, "
        "PURPLE basil plant instead of green herb plants on windowsill, "
        "sleek silver espresso machine, white ceramic dishes on open shelves, "
        "cutting board with vegetables, cookbook open on stand, "
        "hanging copper pots and pans, refrigerator with magnets, "
        "RED striped tea towel instead of white tea towel, wooden utensil holder"
    ),
    "rooftop": (
        "rooftop terrace at night, city skyline with glowing lights, "
        "warm fairy string lights overhead, "
        "brass telescope pointing at LOWER ANGLE instead of up, "
        "YELLOW sunflowers instead of pink flowers in terracotta pots, "
        "metal bistro chairs and table, citronella candles, starry sky, "
        "ORANGE paper lanterns instead of white lanterns, "
        "succulent wall garden, wooden deck floor, cozy urban atmosphere"
    ),
}


def main():
    ts = int(time.time() * 1000)
    scene_ids = list(DIFF_PROMPTS.keys())

    for i, sid in enumerate(scene_ids):
        base_path = f"{OUT_DIR}/{sid}/base.png"
        diff_path = f"{OUT_DIR}/{sid}/diff.png"

        if not os.path.exists(base_path) or os.path.getsize(base_path) < 5000:
            print(f"[{i+1}/{len(scene_ids)}] {sid}: base.png missing or placeholder, run gen_scenes_s2.py first")
            continue

        if os.path.exists(diff_path) and os.path.getsize(diff_path) > 5000:
            print(f"[{i+1}/{len(scene_ids)}] {sid}: diff already exists, skipping")
            continue

        print(f"\n[{i+1}/{len(scene_ids)}] Generating diff for {sid}...")
        # Upload base as reference with cache-bust timestamp
        ref_key = f"refs/spot-diff-s2/{sid}_base_{ts}.png"
        ref_url = upload_r2(base_path, ref_key)

        result_url = call_api(ref_url, DIFF_PROMPTS[sid])
        print(f"  ↓ {result_url}")
        download_and_save(result_url, diff_path)

        if i < len(scene_ids) - 1:
            print(f"  Waiting {WAIT_SECS}s (rate limit)...")
            time.sleep(WAIT_SECS)

    print("\n✓ All diffs done! Run find_diffs_s2.py to detect coordinates.")


if __name__ == "__main__":
    main()
