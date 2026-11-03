#!/usr/bin/env python3
"""Build the ROOM-1 walkthrough page: embed the Wakefit product photos and swatch tiles (docs/wakefit-pages, read
from wakefit.co on 03.11.2026) into docs/walkthrough/room-1.src.html as data URLs.

Usage: python3 tools/build_walkthrough.py <out.html>     (the built page is published as an artifact, not committed)
"""
import base64
import io
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
WP = ROOT / "docs/wakefit-pages"
PHOTOS = ["centaur/frosty-white", "centaur/wyoming-maple", "tinker/columbian-walnut", "twill/columbia-walnut", "twill/dark-brown",
          "cabrera/urban-teak-and-white", "cabrera/pumic-grey"]
SWATCHES = {"centaur/frosty-white": (14, 14, 242, 242),      # crop off the tile's border
            "centaur/wyoming-maple": None, "twill/columbia-walnut": None, "twill/dark-brown": None,
            "cabrera/pumic-grey": (10, 50, 246, 206)}           # crop off the white bands above and below the grey


def data_url(im, width, quality):
    im = im.convert("RGB")
    im.thumbnail((width, width))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


assets = {"photo": {k: data_url(Image.open(WP / f"{k}.jpg"), 480, 78) for k in PHOTOS}, "sw": {}}
for k, crop in SWATCHES.items():
    im = Image.open(WP / f"{k}-swatch.jpg")
    assets["sw"][k] = data_url(im.crop(crop) if crop else im, 256, 88)
src = (ROOT / "docs/walkthrough/room-1.src.html").read_text()
assert src.count("/*__ASSETS__*/{}") == 1
out = Path(sys.argv[1])
out.write_text(src.replace("/*__ASSETS__*/{}", json.dumps(assets, separators=(",", ":"))))
print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB)")
