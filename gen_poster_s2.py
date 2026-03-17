#!/usr/bin/env ~/miniconda3/bin/python3
"""
Spot the Difference S2 — Poster Generator
occult 主角居中前景大图，其余5张扇形背景排布
"""

import datetime, hashlib, hmac, json, math, os, ssl, time, urllib.request, urllib.parse
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from io import BytesIO

API_URL       = "http://aiservice.wdabuliu.com:8019/genl_image"
API_TIMEOUT   = 360
USER_ID       = 123456
R2_ACCOUNT_ID = "bdccd2c68ff0d2e622994d24dbb1bae3"
R2_ACCESS_KEY = "b203adb7561b4f8800cbc1fa02424467"
R2_SECRET_KEY = "e7926e4175b7a0914496b9c999afd914cd1e4af7db8f83e0cf2bfad9773fa2b0"
R2_BUCKET     = "aigram"
R2_PUBLIC     = "https://images.aiwaves.tech"
CARD_DIR      = "src/SpotDiffS2/img/cards"
OUT_PATH      = "src/SpotDiffS2/img/poster.png"

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


def paste_card(canvas: Image.Image, card_path: str, size: int, cx: int, cy: int, angle: float = 0):
    """Load, resize, rotate and paste a card centered at (cx, cy)."""
    card = Image.open(card_path).convert("RGBA")
    card = card.resize((size, size), Image.LANCZOS)
    if angle != 0:
        card = card.rotate(-angle, expand=True, resample=Image.BICUBIC)
    px = cx - card.width // 2
    py = cy - card.height // 2
    canvas.alpha_composite(card, (max(0, px), max(0, py)))


def build_ref_collage() -> str:
    """
    Layout:
      - Dark background
      - Top ~22%: title area (dark, left for API to fill)
      - Middle zone: 5 supporting cards fanned in a semicircle arc
      - Bottom center: occult (main) card, larger, no rotation, on top of fan
    """
    W, H = 1024, 1024
    canvas = Image.new("RGBA", (W, H), (18, 12, 6, 255))
    draw = ImageDraw.Draw(canvas)
    gold = (180, 140, 60)

    # Decorative rules
    draw.rectangle([30, 224, W - 30, 228], fill=gold)
    draw.rectangle([30, H - 60, W - 30, H - 56], fill=gold)
    # Corner dots
    for cx, cy in [(30, 224), (W-30, 224), (30, H-60), (W-30, H-60)]:
        draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=gold)

    # ── Fan of 5 supporting cards ──
    # Pivot far below canvas; cards arc across the middle zone
    PIVOT_X = W // 2
    PIVOT_Y = H + 120          # pivot below canvas bottom
    R        = 540             # pivot → card center distance
    SUPPORT  = 240             # card size (px)

    support = [
        ("lounge",  -60),
        ("command", -30),
        ("manor",     0),
        ("temple",  +30),
        ("gym",     +60),
    ]

    for sid, angle_deg in support:
        angle_rad = math.radians(angle_deg)
        cx = int(PIVOT_X + R * math.sin(angle_rad))
        cy = int(PIVOT_Y - R * math.cos(angle_rad))
        paste_card(canvas, f"{CARD_DIR}/{sid}.png", SUPPORT, cx, cy, angle_deg)

    # ── Occult: main character, front-center, no rotation, larger ──
    MAIN = 330
    occult_cx = W // 2
    occult_cy = H - MAIN // 2 - 55   # vertically centered in lower half, above bottom rule
    paste_card(canvas, f"{CARD_DIR}/occult.png", MAIN, occult_cx, occult_cy, 0)

    # Save
    result = canvas.convert("RGB")
    tmp_path = "/tmp/s2_poster_ref.png"
    result.save(tmp_path, "PNG")
    print(f"  Reference collage saved: {tmp_path}")
    return tmp_path


POSTER_PROMPT = (
    "vintage detective game poster illustration, square 1:1 format, "
    "large bold retro pixel title 'SPOT THE DIFFERENCE II' at top with golden magnifying glass emblem, "
    "SEASON II gold badge below title, "
    "center-bottom: large prominent portrait of a dark fantasy demon goat man with black curved horns and glowing blue eyes in crimson robe, "
    "this is the main character shown large in front, "
    "behind him: five smaller detective case file portraits fanned out in a semicircle arc — "
    "military commander with medals, relaxed brown bear in denim jacket, "
    "distinguished elderly gentleman in tuxedo, bald mystical sage with lightning energy, bald muscular boxer, "
    "all portraits in aged parchment frames with gold borders, rotated at slight angles like a hand of cards, "
    "dark walnut brown background with fog and shadow atmosphere, "
    "warm sepia amber gold palette, dramatic chiaroscuro detective noir lighting, "
    "ornate vintage decorative border frame around entire poster, "
    "high quality atmospheric game key art"
)


def main():
    ts = int(time.time() * 1000)

    print("Building reference collage (fan layout)...")
    ref_path = build_ref_collage()

    print("Uploading reference...")
    ref_url = upload_r2(ref_path, f"refs/spot-diff-s2/poster_ref_{ts}.png")

    print("Generating poster...")
    result_url = call_api(ref_url, POSTER_PROMPT)
    print(f"  ↓ {result_url}")

    tmp_out = f"/tmp/s2_poster_raw_{ts}.png"
    download_as_png(result_url, tmp_out)

    img = Image.open(tmp_out).convert("RGB").resize((1024, 1024), Image.LANCZOS)
    img.save(OUT_PATH, "PNG")
    os.remove(tmp_out)
    print(f"✓ Poster saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
