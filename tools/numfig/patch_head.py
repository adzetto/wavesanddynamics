"""Bring the pages already written up to common.py's current frame rules
without running their models again: the small-frame rules for the pause and
restart buttons (a figure in a table cell or a phone-wide cover). A page that
has them is left alone, so running this twice changes nothing.

Run: python tools/numfig/patch_head.py
"""
import glob
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ANIM = os.path.join(os.path.dirname(os.path.dirname(HERE)), "content", "anim")
ANCHOR = ".ctl button:focus-visible{outline:2px solid #2b5f9e;outline-offset:2px;}\n"
RULE = ("/* small frames */@media (max-width:480px){.ctl{right:3px;bottom:3px;gap:4px;}"
        ".ctl button{width:22px;height:22px;font-size:10px;}}"
        "@media (max-width:300px){#rs{display:none;}.ctl{opacity:.3;}"
        ".ctl button{width:18px;height:18px;font-size:8px;}}\n")


def main():
    done = 0
    for path in sorted(glob.glob(os.path.join(ANIM, "nf-*.html"))):
        with open(path, encoding="utf-8") as fh:
            page = fh.read()
        if "small frames" in page or ANCHOR not in page:
            continue
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(page.replace(ANCHOR, ANCHOR + RULE, 1))
        os.replace(tmp, path)
        done += 1
    print(f"patched {done}")


if __name__ == "__main__":
    main()
