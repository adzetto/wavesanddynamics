# -*- coding: utf-8 -*-
"""Upload the Studio design assets (portrait, topic icons, arrow, panel glyph)
to the wavesanddata-studio site's Media Manager, folder /design, reusing
tools/wix_import.py's REST helpers (the Wix CLI's account token).

    python tools/studio_media.py        # writes build/studio/media.json

Only the Studio site is ever touched: wix_import._site() refuses anything else."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wix_import as W  # noqa: E402

ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "build", "studio", "assets")
OUT = os.path.join(ROOT, "build", "studio")
MIME = {".svg": "image/svg+xml", ".jpg": "image/jpeg", ".png": "image/png"}

W.S.update(name="studio", id=W.SITES["studio"], out=OUT)


def main():
    media = W._load(os.path.join(OUT, "media.json"), {})
    for name in sorted(os.listdir(ASSETS)):
        path = os.path.join(ASSETS, name)
        blob = W._read(path)
        if media.get(name, {}).get("sha256") == W._sha(blob):
            continue
        f = W.upload_bytes(blob, name, MIME[os.path.splitext(name)[1]], "/design")
        media[name] = W._record(f, blob)
        W._dump(os.path.join(OUT, "media.json"), media)
        print(f"  up   {name} -> {f['id']} {f.get('operationStatus')}")
    bad = W.wait_ready(media)
    print(json.dumps({k: [v["id"], v.get("width"), v.get("height"), v["status"]] for k, v in media.items()}, indent=1))
    if bad:
        print("not ready:", bad)


if __name__ == "__main__":
    main()
