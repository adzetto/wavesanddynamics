"""Which image belongs to which blog post, in the order the post shows them.

    python tools/blog_map.py            print the map
    python tools/blog_map.py --copy     also copy the images into content/blog/<slug>/

The posts were written in Word and pasted into Wix as screenshots, so the text
lives inside these pictures. This gives each post its own folder of pages, in
reading order, ready to be read back out.
"""

import glob
import json
import os
import re
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(HERE, "reference", "wix-site")
MEDIA = os.path.join(HERE, "reference", "wix-media")
OUT = os.path.join(HERE, "content", "blog")
MEDIA_RE = re.compile(r"[0-9a-f]{6}_[0-9a-f]{20,}~mv2\.(?:jpg|png|jpeg)")


def title_of(html: str, slug: str) -> str:
    m = re.search(r'<meta property="og:title" content="([^"]+)"', html)
    if m:
        return m.group(1).strip()
    return slug.replace("-", " ").title()


def posts():
    for path in sorted(glob.glob(os.path.join(SITE, "p_post_*.html"))):
        slug = os.path.basename(path)[7:-5]
        html = open(path, encoding="utf-8", errors="replace").read()
        body = re.search(r'<div[^>]+id="content-wrapper".*', html, re.S)
        scope = body.group(0) if body else html
        seen, order = set(), []
        for m in MEDIA_RE.finditer(scope):  # first appearance wins: reading order
            if m.group(0) not in seen:
                seen.add(m.group(0))
                order.append(m.group(0))
        date = re.search(r'"datePublished":"([0-9-]{10})', html)
        yield {
            "slug": slug,
            "title": title_of(html, slug),
            "date": date.group(1) if date else "",
            "images": order,
        }


def main(copy: bool):
    data = list(posts())
    for p in data:
        have = [
            i
            for i in p["images"]
            if os.path.exists(os.path.join(MEDIA, i.replace("~", "_")))
        ]
        print(
            f"{p['date'] or '?':10s} {p['slug'][:46]:46s} {len(have)}/{len(p['images'])} images"
        )
        if copy:
            d = os.path.join(OUT, p["slug"])
            os.makedirs(d, exist_ok=True)
            for n, i in enumerate(have, 1):
                src = os.path.join(MEDIA, i.replace("~", "_"))
                shutil.copy(
                    src, os.path.join(d, f"page-{n:02d}{os.path.splitext(src)[1]}")
                )
    if copy:
        os.makedirs(OUT, exist_ok=True)
        with open(
            os.path.join(OUT, "posts.json"), "w", encoding="utf-8", newline="\n"
        ) as fh:
            json.dump(data, fh, ensure_ascii=False, indent=1)
        print(f"\ncopied into {OUT}")


if __name__ == "__main__":
    main("--copy" in sys.argv)
