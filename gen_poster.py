#!/usr/bin/env python3
"""
Generate poster for Spot the Difference Season 2.
"""
import datetime
import hashlib
import hmac
import json
import os
import shutil
import ssl
import sys
import time
import urllib.request
import urllib.parse
from PIL import Image
import numpy as np

API_URL = "http://aiservice.wdabuliu.com:8019/genl_image"
API_TIMEOUT = 360
USER_ID = 123456

R2_ACCOUNT_ID = "bdccd2c68ff0d2e622994d24dbb1bae3"
R2_ACCESS_KEY = "b203adb7561b4f8800cbc1fa02424467"
R2_SECRET_KEY = "e7926e4175b7a0914496b9c999afd914cd1e4af7db8f83e0cf2bfad9773fa2b0"
R2_BUCKET = "aigram"

_SSL = ssl.create_default_context()
_SSL.check_hostname = False
_SSL.verify_mode = ssl.CERT_NONE

TARGET_W, TARGET_H = 600, 600

PROMPT = (
    "vintage detective noir game poster, 'SPOT DIFF II' title in gold pixel font, "
    "dark sepia background, magnifying glass with golden rim, multiple small vignette "
    "windows showing: cozy cafe interior, vinyl record shop with neon lights, neon bar, "
    "cozy library with books, bright kitchen, rooftop terrace at night, arranged in a "
    "grid layout, detective case file aesthetic, warm gold and brown tones, retro game art style"
)

OUTPUT_MAIN = "/Users/yin/claude code/games-template/spot-diff-s2/src/SpotDiffS2/img/poster.png"
OUTPUT_GAMES = "/Users/yin/claude code/games-template/games/posters/spot-diff-s2.png"


def _sign(key, msg):
    return hmac.new(key, msg.encode(), hashlib.sha256).digest()


def upload_r2(local_path):
    with open(local_path, "rb") as f:
        data = f.read()

    ts = int(time.time() * 1000)
    name = os.path.basename(local_path)
    obj_key = f"refs/spot-diff-s2/poster_{ts}_{name}"
    host = f"{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

    now = datetime.datetime.now(datetime.timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    region = "auto"
    service = "s3"
    method = "PUT"
    content_type = "image/png"
    canon_uri = "/" + R2_BUCKET + "/" + urllib.parse.quote(obj_key, safe="/")
    canon_qs = ""
    canon_headers = (
        f"content-type:{content_type}\nhost:{host}\nx-amz-content-sha256:UNSIGNED-PAYLOAD\nx-amz-date:{amz_date}\n"
    )
    signed_headers = "content-type;host;x-amz-content-sha256;x-amz-date"
    canon_req = f"{method}\n{canon_uri}\n{canon_qs}\n{canon_headers}\n{signed_headers}\nUNSIGNED-PAYLOAD"
    scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string2sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{scope}\n{hashlib.sha256(canon_req.encode()).hexdigest()}"
    k = _sign(_sign(_sign(_sign(("AWS4" + R2_SECRET_KEY).encode(), date_stamp), region), service), "aws4_request")
    sig = hmac.new(k, string2sign.encode(), hashlib.sha256).hexdigest()
    auth = f"AWS4-HMAC-SHA256 Credential={R2_ACCESS_KEY}/{scope}, SignedHeaders={signed_headers}, Signature={sig}"

    req = urllib.request.Request(
        f"https://{host}/{R2_BUCKET}/{urllib.parse.quote(obj_key, safe='/')}",
        data=data, method="PUT",
        headers={
            "Content-Type": content_type,
            "x-amz-content-sha256": "UNSIGNED-PAYLOAD",
            "x-amz-date": amz_date,
            "Authorization": auth,
        },
    )
    urllib.request.urlopen(req, timeout=60, context=_SSL)
    url = f"https://images.aiwaves.tech/{obj_key}"
    print(f"  Uploaded -> {url}")
    return url


def call_api(ref_url, prompt):
    payload = json.dumps({
        "query": "",
        "params": {"url": ref_url, "prompt": prompt, "user_id": USER_ID},
    }).encode()
    req = urllib.request.Request(API_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    resp = urllib.request.urlopen(req, timeout=API_TIMEOUT)
    result = json.loads(resp.read())
    return result.get("image_url") or result.get("url") or result.get("result", {}).get("image_url", "")


def download(url, dst):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            resp = urllib.request.urlopen(req, timeout=60, context=_SSL)
            data = resp.read()
            with open(dst, "wb") as f:
                f.write(data)
            if dst.endswith(".png"):
                img = Image.open(dst)
                if img.format == "WEBP":
                    img.save(dst, "PNG")
                    print("  Converted webp -> png")
            return True
        except Exception as e:
            print(f"  Download failed ({e}), retrying in 5s...")
            time.sleep(5)
    return False


def create_ref(w, h):
    """Create a warm sepia-toned gradient reference at target aspect ratio."""
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            # Warm sepia gradient: dark brown to gold
            arr[y, x] = [
                int(30 + x * 60 // w + y * 30 // h),  # R
                int(20 + x * 40 // w + y * 20 // h),  # G
                int(10 + x * 10 // w),                  # B
            ]
    img = Image.fromarray(arr)
    tmp = "/tmp/spot_diff_s2_poster_ref.png"
    img.save(tmp, "PNG")
    print(f"  Created gradient ref: {w}x{h}")
    return tmp


def main():
    print("=== Spot the Difference S2 Poster Generator ===")
    print(f"Target size: {TARGET_W}x{TARGET_H}")
    print(f"Prompt: {PROMPT[:80]}...")

    # Create gradient ref
    ref_path = create_ref(TARGET_W, TARGET_H)

    # Upload ref to R2
    print("Uploading reference image...")
    ref_url = upload_r2(ref_path)

    # Call API
    print("Calling API (may take up to 90s)...")
    result_url = call_api(ref_url, PROMPT)
    if not result_url:
        print("ERROR: No image URL returned from API")
        sys.exit(1)
    print(f"  Result URL: {result_url}")

    # Download result
    print("Downloading result...")
    tmp = "/tmp/spot_diff_s2_poster_result.png"
    if not download(result_url, tmp):
        print("ERROR: Download failed")
        sys.exit(1)

    # Resize and save
    img = Image.open(tmp).convert("RGB")
    img = img.resize((TARGET_W, TARGET_H), Image.LANCZOS)

    # Save to main location
    os.makedirs(os.path.dirname(OUTPUT_MAIN), exist_ok=True)
    img.save(OUTPUT_MAIN, "PNG")
    print(f"  Saved: {OUTPUT_MAIN}")

    # Copy to games posters
    os.makedirs(os.path.dirname(OUTPUT_GAMES), exist_ok=True)
    shutil.copy2(OUTPUT_MAIN, OUTPUT_GAMES)
    print(f"  Copied: {OUTPUT_GAMES}")

    os.remove(tmp)
    print("Done!")


if __name__ == "__main__":
    main()
