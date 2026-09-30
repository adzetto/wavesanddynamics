"""Upload the sanitized Word files (build/wordpub/<slug>.docx: his Gmail replaced
by the IYTE address, Word comments removed) to the Media Manager of the site on
wavesanddata.com, and write content/word-urls.json {slug: {"url", "bytes",
"name"}} for build.py to link. A file whose bytes were already uploaded is not
sent again.

    python tools/wix_word.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import wix_import as W  # noqa: E402

MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
OUT = os.path.join(ROOT, "content", "word-urls.json")


def main():
    W.S.update(name="public", id=W.SITES["public"])
    src = os.path.join(ROOT, "build", "wordpub")
    done = json.load(open(OUT, encoding="utf-8")) if os.path.isfile(OUT) else {}
    names = W.site_build.SRC_DOCX
    for f in sorted(os.listdir(src)):
        slug = f[:-5]
        blob = open(os.path.join(src, f), "rb").read()
        sha = W._sha(blob)
        if done.get(slug, {}).get("sha256") == sha:
            print(f"  {slug}: already there")
            continue
        send = W.upload_resumable if len(blob) > 10_000_000 else W.upload_bytes
        name = names.get(slug, "WT Literature - Final Summary.docx")
        got = send(blob, name, MIME, "/documents")
        done[slug] = {"url": got.get("url"), "bytes": len(blob), "name": name,
                      "sha256": sha, "id": got.get("id")}
        print(f"  {slug}: {got.get('url')}")
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(done, fh, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
