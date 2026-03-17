#!/usr/bin/env ~/miniconda3/bin/python3
"""
Spot the Difference S2 — Scene Base Image Generator
生成6个场景的 base 图 (780×554)
Characters: Goat McFisty / Capitan / Chill guy / Last Best / KI_Bo / Bonjour
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
    urllib.request.urlopen(req, timeout=60, context=_SSL)
    url = f"{R2_PUBLIC}/{obj_key}"
    print(f"  ↑ Uploaded → {url}")
    return url


def prepare_avatar_ref(avatar_path: str, tmp_path: str) -> str:
    """Resize avatar to target 780×554 ratio (img2img output matches ref aspect ratio)."""
    img = Image.open(avatar_path).convert("RGB")
    img = img.resize((TARGET_W, TARGET_H), Image.LANCZOS)
    img.save(tmp_path, "PNG")
    return tmp_path


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


AVATAR_DIR = "src/SpotDiffS2/img/avatars"

SCENES = [
    {
        # Goat McFisty — dark demon goat, chaotic & mysterious
        "id": "occult",
        "avatar": f"{AVATAR_DIR}/occult_avatar.png",
        "prompt": (
            "dark fantasy occult den interior, dimly lit stone chamber, "
            "tall black candles in silver candelabra casting dramatic shadows, "
            "mystical books and grimoires stacked on a worn wooden shelf, "
            "glass potions and bottles glowing green and purple on a stone table, "
            "animal skull and ram horns displayed on a pedestal, "
            "tarot cards spread on a velvet cloth, "
            "ritual circle carved in the floor with glowing runes, "
            "hanging dried herbs and black feathers, "
            "ancient leather-bound spellbook open showing arcane symbols, "
            "red curtains with gold fringe, crystal ball on ornate stand, "
            "chains and iron rings on stone wall, detailed dark atmospheric interior"
        ),
    },
    {
        # Capitan — anime military commander, stern and disciplined
        "id": "command",
        "avatar": f"{AVATAR_DIR}/command_avatar.png",
        "prompt": (
            "military command center interior, large tactical war table with spread map "
            "marked with red and blue pins and arrows, "
            "glass display case with medals and military decorations, "
            "national flag and unit banner on stands, "
            "radio equipment and communication devices on wooden desk, "
            "framed battle portraits and military certificates on wall, "
            "brass telescope on tripod, leather-bound strategy books, "
            "wooden chess pieces and battle strategy figurines on table, "
            "oil lamp and vintage typewriter, stack of sealed dispatches, "
            "detailed military aesthetic, warm candlelight and window light, "
            "no people, no characters, no humans, no figures, empty room"
        ),
    },
    {
        # Chill guy — bear in denim jacket, relaxed and laid-back
        "id": "lounge",
        "avatar": f"{AVATAR_DIR}/lounge_avatar.png",
        "prompt": (
            "cozy relaxed living room interior, large overstuffed sofa with colorful throw pillows, "
            "flat screen TV on wooden stand with console controllers scattered around, "
            "coffee table with half-eaten snacks, chips bag, and open soda cans, "
            "potted succulent and fiddle-leaf fig plant in corners, "
            "fuzzy rug on hardwood floor, beanbag chair, "
            "string lights on wall, framed posters of movies and games, "
            "hoodies and jacket tossed on armchair, "
            "bookshelf with graphic novels and manga, "
            "pizza box on side table, TV remote between cushions, "
            "warm casual atmosphere, soft afternoon light"
        ),
    },
    {
        # Last Best — elegant elderly gentleman in tuxedo
        "id": "manor",
        "avatar": f"{AVATAR_DIR}/manor_avatar.png",
        "prompt": (
            "grand manor hall interior, marble fireplace with roaring fire, "
            "ornate gold-framed oil paintings of aristocrats on paneled walls, "
            "crystal chandelier with warm candlelight above a formal dining table, "
            "crystal wine glasses and silver candelabra on white tablecloth, "
            "tall bookshelves with leather-bound classic volumes, "
            "antique grandfather clock in corner, "
            "silver tray with tea service on side table, "
            "detailed carved wooden wainscoting, "
            "Persian rug on polished herringbone wood floor, "
            "hunting trophy above mantelpiece, fresh flower arrangement, "
            "opulent Edwardian atmosphere, rich warm lighting"
        ),
    },
    {
        # KI_Bo — mystical glowing sage / shaman
        "id": "temple",
        "avatar": f"{AVATAR_DIR}/temple_avatar.png",
        "prompt": (
            "mystical ancient temple meditation chamber, stone walls with carved mandala patterns, "
            "ornate brass incense burner emitting curling smoke wisps, "
            "glowing crystal orb on a stone altar pedestal, "
            "ancient scroll partially unrolled revealing golden text symbols, "
            "rows of burning oil lamps in brass holders, "
            "meditation mat and cushion on polished stone floor, "
            "hanging silk tapestries with sacred geometry, "
            "wooden shelves with herbs, minerals, and ritual objects, "
            "small golden Buddha statue, singing bowl and wooden mallet, "
            "stone water feature trickling softly, "
            "ethereal warm glow, incense smoke and mystical atmosphere"
        ),
    },
    {
        # Bonjour — muscular anime boxer, energetic and competitive
        "id": "gym",
        "avatar": f"{AVATAR_DIR}/gym_avatar.png",
        "prompt": (
            "professional boxing gym interior, heavy punching bags hanging from ceiling chains, "
            "boxing ring with red and white ropes in background, "
            "weight rack with dumbbells and barbells lined up neatly, "
            "championship belt displayed on wooden trophy stand, "
            "boxing gloves hanging on hook by locker, "
            "round gym clock on brick wall, "
            "speed bag platform with leather speed bag, "
            "jump ropes and resistance bands hanging on hooks, "
            "motivational posters and fight photos on walls, "
            "water bottle and white towel on bench, "
            "dramatic spotlight lighting, sweat and champion atmosphere, "
            "no people, no characters, no humans, no figures, empty room"
        ),
    },
]


def main():
    ts = int(time.time() * 1000)

    for i, scene in enumerate(SCENES):
        sid = scene["id"]
        out_path = f"{OUT_DIR}/{sid}/base.png"

        if os.path.exists(out_path) and os.path.getsize(out_path) > 500000:
            print(f"[{i+1}/{len(SCENES)}] {sid}: already exists, skipping")
            continue

        # Prepare avatar as reference (resized to target aspect ratio)
        tmp_ref = f"/tmp/s2_avatar_ref_{sid}_{ts}.png"
        prepare_avatar_ref(scene["avatar"], tmp_ref)
        ref_key = f"refs/spot-diff-s2/{sid}_avatar_{ts}.png"
        print(f"\n[{i+1}/{len(SCENES)}] Uploading avatar ref for {sid}...")
        ref_url = upload_r2(tmp_ref, ref_key)
        os.remove(tmp_ref)

        print(f"  Generating scene...")
        result_url = call_api(ref_url, scene["prompt"])
        print(f"  ↓ {result_url}")
        download_and_save(result_url, out_path)

        if i < len(SCENES) - 1:
            print(f"  Waiting {WAIT_SECS}s (rate limit)...")
            time.sleep(WAIT_SECS)

    print("\n✓ All scenes done! Run gen_diffs_s2.py next.")


if __name__ == "__main__":
    main()
