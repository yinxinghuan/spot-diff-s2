#!/usr/bin/env ~/miniconda3/bin/python3
"""
Spot the Difference S2 — Character Art Generator
Generates per character:
  1. 立绘 (portrait illustration, transparent bg) → img/characters/{id}.png
  2. 侦探卡片 (detective-style card portrait, 512×512) → img/cards/{id}.png
"""

import datetime, hashlib, hmac, json, os, ssl, time, urllib.request, urllib.parse
from PIL import Image, ImageFilter, ImageEnhance
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
CHAR_DIR      = "src/SpotDiffS2/img/characters"
CARD_DIR      = "src/SpotDiffS2/img/cards"
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
            img = Image.open(BytesIO(data)).convert("RGBA")
            img.save(out_path, "PNG")
            return
        except Exception as e:
            print(f"  ⚠ Download retry {attempt+1}: {e}")
            if attempt < 2:
                time.sleep(5)
    raise RuntimeError(f"Failed to download {url}")


def remove_green(img_path: str, threshold=50, feather=30):
    img = Image.open(img_path).convert("RGBA")
    data = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = data[x, y]
            greenness = g - max(r, b)
            if greenness > threshold:
                alpha = 1.0 - min(1.0, (greenness - threshold) / feather)
                data[x, y] = (r, g, b, int(a * alpha))
    img.save(img_path, "PNG")


def apply_detective_style(img: Image.Image) -> Image.Image:
    """Apply warm sepia tint + slight vignette for detective card aesthetic."""
    rgb = img.convert("RGB")
    # Warm sepia tint
    r, g, b = rgb.split()
    r = r.point(lambda p: min(255, int(p * 1.08 + 20)))
    g = g.point(lambda p: min(255, int(p * 0.95 + 10)))
    b = b.point(lambda p: min(255, int(p * 0.75)))
    sepia = Image.merge("RGB", (r, g, b))
    # Slight contrast boost
    sepia = ImageEnhance.Contrast(sepia).enhance(1.2)
    return sepia


CHARACTERS = [
    {
        "id": "occult",
        "name": "Goat McFisty",
        "portrait_prompt": (
            "anime character illustration half body portrait, "
            "dark fantasy demon goat man, grey skin, long curved black ram horns, "
            "intense glowing blue eyes, sinister grin with sharp teeth, "
            "wearing a dark crimson robe with hood down, silver skull amulet, "
            "dramatic underlighting, high quality anime illustration, "
            "solid flat bright green background #00FF00, green screen"
        ),
        "card_prompt": (
            "detective noir portrait illustration, dark fantasy demon goat character, "
            "grey skin, black curved horns, piercing blue eyes, "
            "wearing crimson robe, head and shoulders close-up, "
            "vintage detective case file style, warm sepia amber tones, "
            "dramatic chiaroscuro lighting, aged parchment vignette border, "
            "high quality illustration, square format"
        ),
    },
    {
        "id": "command",
        "name": "Capitan",
        "portrait_prompt": (
            "anime character illustration half body portrait, "
            "military commander, silver white spiky hair, strong face with grey stubble, "
            "dark green military coat with gold epaulettes and medals, "
            "crossed arms, battle-worn confident expression, "
            "high quality anime illustration, "
            "solid flat bright green background #00FF00, green screen"
        ),
        "card_prompt": (
            "detective noir portrait illustration, anime military commander character, "
            "silver white hair, stern scarred face, dark military uniform with epaulettes, "
            "head and shoulders close-up, "
            "vintage detective case file style, warm sepia amber tones, "
            "dramatic military lighting, aged parchment vignette border, "
            "high quality illustration, square format"
        ),
    },
    {
        "id": "lounge",
        "name": "Chill guy",
        "portrait_prompt": (
            "anime character illustration half body portrait, "
            "anthropomorphic brown bear, fluffy fur, wavy brown hair, "
            "light blue denim jacket over white t-shirt, "
            "completely relaxed pose, gentle smile, chill expression, "
            "high quality anime illustration, "
            "solid flat bright green background #00FF00, green screen"
        ),
        "card_prompt": (
            "detective noir portrait illustration, anthropomorphic brown bear character, "
            "fluffy brown fur, wearing casual denim jacket, "
            "head and shoulders close-up, relaxed bear face, "
            "vintage detective case file style, warm amber tones, "
            "soft noir lighting, aged parchment vignette border, "
            "high quality illustration, square format"
        ),
    },
    {
        "id": "manor",
        "name": "Last Best",
        "portrait_prompt": (
            "anime character illustration half body portrait, "
            "distinguished elderly gentleman, silver white hair, grey beard and mustache, "
            "immaculate black tuxedo with bow tie, gold cufflinks, "
            "dignified warm smile, aristocratic posture, "
            "high quality anime illustration, "
            "solid flat bright green background #00FF00, green screen"
        ),
        "card_prompt": (
            "detective noir portrait illustration, elegant elderly gentleman character, "
            "silver hair, neat beard, formal black tuxedo, "
            "head and shoulders close-up, distinguished expression, "
            "vintage detective case file style, warm sepia golden tones, "
            "candlelit noir lighting, aged parchment vignette border, "
            "high quality illustration, square format"
        ),
    },
    {
        "id": "temple",
        "name": "KI_Bo",
        "portrait_prompt": (
            "anime character illustration half body portrait, "
            "ancient mystical sage, dark brown skin, bald head, "
            "golden glowing third eye mark on forehead, long white beard, "
            "ethereal teal lightning energy crackling around shoulders, "
            "white robes with gold trim, hands in prayer gesture, "
            "serene powerful expression, "
            "high quality anime illustration, "
            "solid flat bright green background #00FF00, green screen"
        ),
        "card_prompt": (
            "detective noir portrait illustration, ancient mystical sage character, "
            "dark skin, bald head with glowing golden mark, white beard, "
            "ethereal energy aura, simple white robes, "
            "head and shoulders close-up, knowing wise expression, "
            "vintage detective case file style, warm amber mystical tones, "
            "divine dramatic lighting, aged parchment vignette border, "
            "high quality illustration, square format"
        ),
    },
    {
        "id": "gym",
        "name": "Bonjour",
        "portrait_prompt": (
            "anime character illustration half body portrait, "
            "powerfully built anime boxer, platinum white buzz cut hair, "
            "chiseled muscular physique, bare upper torso, "
            "white boxing hand wraps, fighting stance, fierce confident eyes, "
            "gym spotlight lighting, "
            "high quality anime illustration, "
            "solid flat bright green background #00FF00, green screen"
        ),
        "card_prompt": (
            "detective noir portrait illustration, muscular anime boxer character, "
            "completely bald shaved head NO HAIR, strong jawline, athletic build, "
            "boxing wraps visible, confident fierce expression, "
            "head and shoulders close-up, "
            "vintage detective case file style, warm amber dramatic tones, "
            "spotlight noir lighting, aged parchment vignette border, "
            "high quality illustration, square format"
        ),
    },
]


def gen_portrait(char: dict, ts: int) -> bool:
    """Generate 立绘 (transparent bg portrait)."""
    sid = char["id"]
    out_path = f"{CHAR_DIR}/{sid}.png"
    if os.path.exists(out_path) and os.path.getsize(out_path) > 50000:
        print(f"  立绘: already exists, skipping")
        return False

    # Prepare portrait-ratio ref (2:3)
    avatar_path = f"{AVATAR_DIR}/{sid}_avatar.png"
    avatar = Image.open(avatar_path).convert("RGB").resize((512, 512), Image.LANCZOS)
    canvas = Image.new("RGB", (512, 768), (80, 80, 80))
    canvas.paste(avatar, (0, 0))
    tmp_ref = f"/tmp/s2_pref_{sid}_{ts}.png"
    canvas.save(tmp_ref, "PNG")
    ref_url = upload_r2(tmp_ref, f"refs/spot-diff-s2/pref_{sid}_{ts}.png")
    os.remove(tmp_ref)

    result_url = call_api(ref_url, char["portrait_prompt"])
    print(f"  ↓ {result_url}")
    tmp_out = f"/tmp/s2_portrait_{sid}_{ts}.png"
    download_as_png(result_url, tmp_out)

    print(f"  Removing green screen...")
    remove_green(tmp_out)

    img = Image.open(tmp_out).convert("RGBA")
    h = 600
    w = int(img.width * h / img.height)
    img = img.resize((w, h), Image.LANCZOS)
    img.save(out_path, "PNG")
    os.remove(tmp_out)
    print(f"  ✓ 立绘 saved: {out_path} ({w}×{h})")
    return True


def gen_card(char: dict, ts: int) -> bool:
    """Generate detective-style card portrait (512×512)."""
    sid = char["id"]
    out_path = f"{CARD_DIR}/{sid}.png"
    if os.path.exists(out_path) and os.path.getsize(out_path) > 50000:
        print(f"  卡片: already exists, skipping")
        return False

    # Use avatar directly as ref (512×512 = 1:1, matches card output)
    avatar_path = f"{AVATAR_DIR}/{sid}_avatar.png"
    ref_url = upload_r2(avatar_path, f"refs/spot-diff-s2/cref_{sid}_{ts}.png")

    result_url = call_api(ref_url, char["card_prompt"])
    print(f"  ↓ {result_url}")
    tmp_out = f"/tmp/s2_card_{sid}_{ts}.png"
    download_as_png(result_url, tmp_out)

    img = Image.open(tmp_out).convert("RGB")
    img = apply_detective_style(img)
    img = img.resize((512, 512), Image.LANCZOS)
    img.save(out_path, "PNG")
    os.remove(tmp_out)
    print(f"  ✓ 卡片 saved: {out_path} (512×512)")
    return True


def main():
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    # mode: "portrait" | "card" | "all"

    os.makedirs(CHAR_DIR, exist_ok=True)
    os.makedirs(CARD_DIR, exist_ok=True)
    ts = int(time.time() * 1000)

    for i, char in enumerate(CHARACTERS):
        print(f"\n[{i+1}/{len(CHARACTERS)}] {char['name']} ({char['id']})")

        if mode in ("portrait", "all"):
            used = gen_portrait(char, ts)
            if used and mode == "all":
                print(f"  Waiting {WAIT_SECS}s...")
                time.sleep(WAIT_SECS)

        if mode in ("card", "all"):
            used = gen_card(char, ts)
            if used and i < len(CHARACTERS) - 1:
                print(f"  Waiting {WAIT_SECS}s...")
                time.sleep(WAIT_SECS)

    print("\n✓ Done!")


if __name__ == "__main__":
    main()
