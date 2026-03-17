#!/usr/bin/env ~/miniconda3/bin/python3
"""
Spot the Difference S2 — Poster Generator
侦探风格海报，加入6个角色形象
"""

import datetime, hashlib, hmac, json, os, ssl, time, urllib.request, urllib.parse
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from io import BytesIO

API_URL       = "http://aiservice.wdabuliu.com:8019/genl_image"
API_TIMEOUT   = 360
USER_ID       = 123456
R2_ACCOUNT_ID = "bdccd2c68ff0d2e622994d24dbb1bae3"
R2_ACCESS_KEY = "b203adb7561b4f8800cbc1fa02424467"
R2_SECRET_KEY = "e7926e4175b7a0914496b9c999afd914cd1e4af7db8f83e0cf2bfad9773fa2b0"
R2_BUCKET     = "aigram"
R2_PUBLIC     = "https://images.aiwaves.tech"
AVATAR_DIR    = "src/SpotDiffS2/img/avatars"
OUT_PATH      = "src/SpotDiffS2/img/poster.png"
SIZE          = 1024

_SSL = ssl.create_default_context()
_SSL.check_hostname = False
_SSL.verify_mode = ssl.CERT_NONE

SCENE_IDS = ["occult", "command", "lounge", "manor", "temple", "gym"]


def _sign(key, msg):
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def upload_r2(local_path: str, obj_key: str) -> str:
    with open(local_path, "rb") as f:
        data = f.read()
    host = f"{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    now = datetime.datetime.now(datetime.timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    region, service = "auto", "s3"
    content_type = "image/png"
    canon_uri = "/" + R2_BUCKET + "/" + urllib.parse.quote(obj_key, safe="/")
    canon_headers = f"content-type:{content_type}\nhost:{host}\nx-amz-content-sha256:UNSIGNED-PAYLOAD\nx-amz-date:{amz_date}\n"
    signed_headers = "content-type;host;x-amz-content-sha256;x-amz-date"
    canon_req = f"PUT\n{canon_uri}\n\n{canon_headers}\n{signed_headers}\nUNSIGNED-PAYLOAD"
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
                print(f"  ⚠ Upload retry {attempt+1}: {e}")
                time.sleep(5)
            else:
                raise
    url = f"{R2_PUBLIC}/{obj_key}"
    print(f"  ↑ {url}")
    return url


def call_api(ref_url: str, prompt: str) -> str:
    payload = json.dumps({"query": "", "params": {"url": ref_url, "prompt": prompt, "user_id": USER_ID}}).encode()
    req = urllib.request.Request(API_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    resp = urllib.request.urlopen(req, timeout=API_TIMEOUT)
    result = json.loads(resp.read())
    print(f"  API code={result.get('code')}")
    if result.get("code") == 429:
        raise RuntimeError("Rate limited (429)")
    return result.get("image_url") or result.get("url") or result.get("result", {}).get("image_url", "")


def download_as_png(url: str, out_path: str):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=60, context=_SSL).read()
            img = Image.open(BytesIO(data)).convert("RGB")
            img.save(out_path, "PNG")
            return
        except Exception as e:
            print(f"  ⚠ Download retry {attempt+1}: {e}")
            if attempt < 2:
                time.sleep(5)
    raise RuntimeError(f"Failed to download {url}")


def build_ref_collage() -> str:
    """
    Build a 1024×1024 reference collage:
    - Dark warm brown background
    - 6 character avatar circles arranged in 2 rows × 3 cols at bottom
    - Top area left for title + magnifying glass (dark)
    """
    canvas = Image.new("RGB", (SIZE, SIZE), (26, 18, 10))  # very dark brown

    # Avatar circle size and positions (2 rows × 3 cols, bottom 60% of canvas)
    AVATAR_SIZE = 230
    COLS, ROWS = 3, 2
    start_y = 420
    margin_x = (SIZE - COLS * AVATAR_SIZE) // (COLS + 1)
    margin_y = (SIZE - start_y - ROWS * AVATAR_SIZE) // (ROWS + 1)

    for idx, sid in enumerate(SCENE_IDS):
        row = idx // COLS
        col = idx % COLS
        x = margin_x + col * (AVATAR_SIZE + margin_x)
        y = start_y + margin_y + row * (AVATAR_SIZE + margin_y)

        avatar_path = f"{AVATAR_DIR}/{sid}_avatar.png"
        if not os.path.exists(avatar_path):
            continue

        av = Image.open(avatar_path).convert("RGB").resize((AVATAR_SIZE, AVATAR_SIZE), Image.LANCZOS)

        # Create circular mask
        mask = Image.new("L", (AVATAR_SIZE, AVATAR_SIZE), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, AVATAR_SIZE - 1, AVATAR_SIZE - 1), fill=255)

        # Slight sepia tint on avatars
        r, g, b = av.split()
        r = r.point(lambda p: min(255, int(p * 1.05 + 15)))
        g = g.point(lambda p: min(255, int(p * 0.95)))
        b = b.point(lambda p: min(255, int(p * 0.80)))
        av = Image.merge("RGB", (r, g, b))

        # Gold ring border
        ring = Image.new("RGBA", (AVATAR_SIZE + 8, AVATAR_SIZE + 8), (0, 0, 0, 0))
        ring_draw = ImageDraw.Draw(ring)
        ring_draw.ellipse((0, 0, AVATAR_SIZE + 7, AVATAR_SIZE + 7), outline=(200, 164, 80), width=4)
        canvas.paste(ring.convert("RGB"), (x - 4, y - 4), ring.split()[3])

        av_rgba = av.convert("RGBA")
        av_rgba.putalpha(mask)
        canvas.paste(av.convert("RGB"), (x, y), mask)

    tmp_path = "/tmp/s2_poster_ref.png"
    canvas.save(tmp_path, "PNG")
    print(f"  Reference collage saved: {tmp_path}")
    return tmp_path


POSTER_PROMPT = (
    "vintage detective game poster illustration, 'SPOT DIFF II' large pixel art retro title at top, "
    "giant golden magnifying glass with ornate handle in upper center, "
    "six circular character portrait frames arranged in two rows at bottom, "
    "each frame shows a unique character: demon goat in red robe, military commander, brown bear in denim, "
    "elderly gentleman in tuxedo, glowing sage, muscular boxer, "
    "dark warm brown background with aged parchment texture, "
    "sepia amber gold color palette, dramatic detective noir lighting, "
    "ornate vintage borders and decorative elements, "
    "retro pixel font text, magnifying glass motif, "
    "SEASON II badge, detective case file aesthetic, "
    "high quality game poster art, square format"
)


def main():
    ts = int(time.time() * 1000)

    print("Building reference collage...")
    ref_path = build_ref_collage()

    print("Uploading reference...")
    ref_url = upload_r2(ref_path, f"refs/spot-diff-s2/poster_ref_{ts}.png")

    print("Generating poster...")
    result_url = call_api(ref_url, POSTER_PROMPT)
    print(f"  ↓ {result_url}")

    tmp_out = f"/tmp/s2_poster_raw_{ts}.png"
    download_as_png(result_url, tmp_out)

    # Resize to 1024×1024
    img = Image.open(tmp_out).convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
    img.save(OUT_PATH, "PNG")
    os.remove(tmp_out)
    print(f"✓ Poster saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
