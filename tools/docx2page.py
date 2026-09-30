"""Turn one of Dr. Kaynardag's Word documents into a finished web page.

    python docx2page.py "<file.docx>" out/section-slug

What it does, and why each step is here:

  * pandoc carries the Word file over to HTML, pulling the figures out of the
    file as it goes and turning Word equations into real mathematics;
  * the Word "Contents" field is dropped, because the page builds its own
    table of contents from the headings, and that one is always in step;
  * every figure is paired with the italic caption Word left underneath it,
    numbered, and given an anchor, so a sentence that says "Figure 6 (d)"
    becomes a link to the figure it is talking about;
  * the result is written as one page with the fixed left menu the site uses.

The author keeps writing in Word. Nothing here asks him to change that.
"""

import html
import os
import re
import subprocess
import sys

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "page.html")


def run_pandoc(docx: str, out: str) -> str:
    os.makedirs(out, exist_ok=True)
    body = os.path.join(out, "_body.html")
    subprocess.run(
        [
            "pandoc",
            docx,
            "-t",
            "html5",
            "--extract-media=.",
            "--katex",
            "--wrap=none",
            "-o",
            "_body.html",
        ],
        cwd=out,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    text = open(body, encoding="utf-8").read()
    os.remove(body)
    return text


IMG = re.compile(r'<img src="\./media/(?P<file>[^"]+)"[^>]*/?>')
CAPTION = re.compile(r"<p><em>(?P<cap>Figure\s+(?P<num>\d+)\.\s*.*?)</em></p>", re.S)


def figures(doc: str):
    """Pair every image with the caption paragraph that follows it."""
    out, pos, seen = [], 0, {}
    for m in IMG.finditer(doc):
        out.append(doc[pos : m.start()])
        rest = doc[m.end() :]
        cap = CAPTION.match(rest.lstrip("\n"))
        file = m.group("file")
        if cap:
            num = cap.group("num")
            seen[num] = file
            out.append(
                f'<figure id="fig-{num}">\n'
                f'  <img src="media/{file}" alt="{html.escape(strip(cap.group("cap")))}" loading="lazy">\n'
                f"  <figcaption>{cap.group('cap')}</figcaption>\n"
                f"</figure>"
            )
            skip = rest.index(cap.group(0)) + len(cap.group(0))
            pos = m.end() + skip
        else:
            out.append(
                f'<figure class="plain"><img src="media/{file}" alt="" loading="lazy"></figure>'
            )
            pos = m.end()
    out.append(doc[pos:])
    return "".join(out), seen


def strip(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


REF = re.compile(r"(?<![>\w])Figure\s+(\d+)(\s*\(([a-g])\))?")


def crossref(doc: str, known: dict) -> str:
    """Turn a mention of a figure into a link, but never inside a caption."""
    parts = re.split(r"(<figcaption>.*?</figcaption>)", doc, flags=re.S)
    for i, part in enumerate(parts):
        if part.startswith("<figcaption>"):
            continue
        parts[i] = REF.sub(
            lambda m: (
                f'<a class="xref" href="#fig-{m.group(1)}">{m.group(0)}</a>'
                if m.group(1) in known
                else m.group(0)
            ),
            part,
        )
    return "".join(parts)


def drop_word_toc(doc: str) -> str:
    """Remove the Contents heading and the page-number list Word wrote under it."""
    m = re.search(
        r"<h[1-3][^>]*>\s*(<strong>)?\s*Contents\s*(</strong>)?\s*</h[1-3]>", doc, re.I
    )
    if not m:
        return doc
    tail = doc[m.end() :]
    stop = re.search(r"<h[1-3]", tail)
    return doc[: m.start()] + (tail[stop.start() :] if stop else "")


def unbold_headings(doc: str) -> str:
    return re.sub(
        r"(<h[1-6][^>]*>)\s*<strong>(.*?)</strong>\s*(</h[1-6]>)",
        lambda m: m.group(1) + m.group(2) + m.group(3),
        doc,
        flags=re.S,
    )


def headings(doc: str):
    out, n = [], 0

    def tag(m):
        nonlocal n
        n += 1
        slug = (
            re.sub(r"[^a-z0-9]+", "-", strip(m.group(2)).lower()).strip("-")[:60]
            or f"s{n}"
        )
        out.append((int(m.group(1)), slug, strip(m.group(2))))
        return f'<h{m.group(1)} id="{slug}">{m.group(2)}</h{m.group(1)}>'

    doc = re.sub(r"<h([12])[^>]*>(.*?)</h\1>", tag, doc, flags=re.S)
    return doc, out


def lead(doc: str):
    """The first paragraphs of these documents are set bold in Word; that is a lead, not emphasis."""

    def once(m):
        return f'<p class="lead">{m.group(1)}</p>'

    return re.sub(r"<p><strong>(.*?)</strong></p>", once, doc, count=6, flags=re.S)


def build(docx: str, out: str, title: str | None = None):
    doc = run_pandoc(docx, out)
    doc = drop_word_toc(unbold_headings(doc))
    doc, seen = figures(doc)
    doc = crossref(doc, seen)
    doc, heads = headings(doc)
    doc = lead(doc)

    if title is None:
        m = re.search(r"<p><strong>(.*?)</strong></p>", doc, re.S)
        title = strip(m.group(1)) if m else os.path.basename(docx)
    toc = "\n".join(
        f'      <li class="lv{lv}"><a href="#{slug}">{html.escape(text)}</a></li>'
        for lv, slug, text in heads
    )
    page = open(TEMPLATE, encoding="utf-8").read()
    page = (
        page.replace("{{title}}", html.escape(title))
        .replace("{{toc}}", toc)
        .replace("{{body}}", doc)
        .replace("{{figures}}", str(len(seen)))
    )
    open(os.path.join(out, "index.html"), "w", encoding="utf-8", newline="\n").write(
        page
    )
    print(
        f"{out}/index.html  {len(heads)} headings, {len(seen)} figures, "
        f"{len(strip(doc).split())} words"
    )


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
