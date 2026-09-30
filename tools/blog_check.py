"""How much of each blog post is real text, and how much is a screenshot?

    python tools/blog_check.py

The author said he pasted screenshots of Word pages into the blog. This counts,
for every saved post, the words that are actually in the HTML and the images the
post carries, so we know which posts have to be read out of pictures.
"""

import glob
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = sorted(glob.glob(os.path.join(HERE, "reference", "wix-site", "p_post_*.html")))

print(f"{'post':58s} {'words':>6s} {'images':>7s}")
for p in POSTS:
    s = open(p, encoding="utf-8", errors="replace").read()
    body = re.search(r'<div[^>]+id="content-wrapper".*', s, re.S)
    s = body.group(0) if body else s
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    words = len(re.sub(r"\s+", " ", text).split())
    imgs = len(set(re.findall(r"[0-9a-f]{6}_[0-9a-f]{20,}~mv2\.(?:jpg|png|jpeg)", s)))
    name = os.path.basename(p)[7:-5]
    print(f"{name[:58]:58s} {words:6d} {imgs:7d}")
