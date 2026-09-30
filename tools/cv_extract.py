# -*- coding: utf-8 -*-
"""Read the professor's CV out of his Word file into content/cv/cv.json.

    python tools/cv_extract.py [--docx PATH] [--out PATH] [--check]

The CV page (site/parts/cv.py), the research areas on About and the profile
links on About and Contact all read that JSON. The Word file itself is never
published (ROUND4_SPEC.md sections 6 and 8).

Sanitised on the way: his CV's contact line carries a personal Gmail address
and a personal phone number, and neither is copied. The email is his IYTE
address, the location is the first part of that line ("Izmir, Turkiye"), and
the "Personal webpage" link (this site) is dropped. A last check refuses to
write a file that still holds a Gmail address, any other email address, or
anything shaped like a phone number.

Every other entry is kept word for word: his words, in his order, with his
spelling ("Bogazici", "Turkey", "patent no:"). Three things change, and none
of them is a word:
  - whitespace: runs of spaces, tabs and no-break spaces become one space;
  - capitals: a heading or an organisation he typed in capitals is set in
    title case ("THE UNIVERSITY OF TEXAS AT AUSTIN" becomes "The University
    of Texas at Austin", as the same name reads elsewhere in his CV);
  - separators: a dash, a " | " or a tab between two facts (a grant and its
    amount, a start and an end date, an award and who gave it) splits them
    into two fields, so the page sets them apart by position, never with an
    em dash. The quotation marks around a title go the same way.
Each entry is checked as it is read: its fields hold exactly the words and
figures of his line, in his order. The schema is in site/parts/cv.md.

Standard library only: zipfile and ElementTree.
"""

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCX = os.path.join(ROOT, "content", "source", "Korkut_Kaynardag_Resume.docx")
OUT = os.path.join(ROOT, "content", "cv", "cv.json")

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

EMAIL = "korkutkaynardag@iyte.edu.tr"

# A profile link's kind, by its label in his CV. A label missing here stops
# the run: a new link is published only once someone has chosen its kind.
KINDS = {"google scholar": "scholar", "linkedin": "linkedin",
         "researchgate": "researchgate", "github": "github", "youtube": "youtube"}
DROPPED = {"personal webpage"}          # this site
# The profile addresses as the user gave them (ROUND4_SPEC.md section 12). His
# CV's LinkedIn link ends in a slash; the published one does not. A link of
# his that differs from these by more than that slash is kept as he wrote it.
EXACT = {"scholar": "https://scholar.google.com/citations?user=v_eQpwUAAAAJ&hl=en",
         "linkedin": "https://www.linkedin.com/in/korkutkaynardag",
         "researchgate": "https://www.researchgate.net/profile/Korkut-Kaynardag"}
OURS = "wavesanddata.com"

# Short, stable anchors for his section headings; another heading gets a slug.
IDS = {
    "Education": "education",
    "Research Interests and Areas of Expertise": "research-interests",
    "Experience": "experience",
    "Grants, Funding, and Proposals": "grants",
    "Journal Publications": "journal-publications",
    "Conference Proceedings": "conference-proceedings",
    "Conference Presentations": "conference-presentations",
    "Invited Talks": "invited-talks",
    "Patents": "patents",
    "Awards and Honors": "awards",
    "Peer Review Activities": "peer-review",
    "International Workshops and Memberships": "workshops-and-memberships",
    "Certification and Additional Machine Learning Projects": "certifications",
}

SMALL = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the", "to"}
DATE = r"(?:\d{2}/\d{4}|\d{4})"
RANGE = re.compile(rf"^(?P<start>{DATE})\s*[-\u2013\u2014]\s*(?P<end>{DATE}|present)$", re.I)
ONE = re.compile(rf"^{DATE}$")
TAIL_DATE = re.compile(r"^(?P<body>.+?),\s*(?P<date>\d{2}/\d{4})$")
DASH = re.compile(r"\s+[\u2013\u2014]\s+")
# authors, then the title in his curly quotes, then where it appeared, then the year
CITE = re.compile(r"^(?P<authors>[^\u201c]*?)[\s.,]*\u201c(?P<title>[^\u201d]+)\u201d[\s,]*"
                  r"(?P<venue>.*?)[\s,]*(?P<year>(?:19|20)\d{2})\.?$")

# What must never reach the site: his personal contact details.
PRIVATE = (
    (re.compile(r"gmail", re.I), "a Gmail address"),
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "an email address"),
    (re.compile(r"\+\s*\d"), "a phone prefix"),
    (re.compile(r"\(\d{3}\)\s*\d{3}"), "a phone number"),
    (re.compile(r"(?<!\d)\d{3}[-.\s]\d{4}(?!\d)"), "a phone number"),
)


class CVError(ValueError):
    """The CV has a line this reader does not know how to file."""


# ------------------------------------------------------------ reading Word

class Para:
    """A paragraph as its text, its runs' emphasis, its list and its link."""

    def __init__(self, el, rels, lists):
        self.runs = []                      # (text, bold, italic, caps)
        for r in el.iter(W + "r"):
            rpr = r.find(W + "rPr")
            text = "".join(c.text or "" if c.tag == W + "t" else "\t" if c.tag == W + "tab"
                           else "\n" if c.tag in (W + "br", W + "cr") else "" for c in r)
            if text:
                self.runs.append((text, _on(rpr, "b"), _on(rpr, "i"), _on(rpr, "caps")))
        self.text = "".join(t for t, *_ in self.runs).replace("\xa0", " ")
        num = el.find(f"{W}pPr/{W}numPr/{W}numId")
        self.list = lists.get(num.get(W + "val")) if num is not None else None
        link = el.find(W + "hyperlink")
        self.href = rels.get(link.get(R + "id")) if link is not None else None

    def shows(self, flag):
        """True when every run with visible text carries the flag (1 bold, 2 italic, 3 caps)."""
        seen = [r for r in self.runs if r[0].strip()]
        return bool(seen) and all(r[flag] for r in seen)


def _on(rpr, tag):
    el = rpr.find(W + tag) if rpr is not None else None
    return el is not None and el.get(W + "val") not in ("0", "false", "none")


def read(path):
    """The body's blocks in order: ("p", Para) or ("tbl", [[[cell text, ...], ...], ...])."""
    with zipfile.ZipFile(path) as z:
        doc = ET.fromstring(z.read("word/document.xml"))
        rels = {r.get("Id"): r.get("Target")
                for r in ET.fromstring(z.read("word/_rels/document.xml.rels"))}
        lists = {}
        if "word/numbering.xml" in z.namelist():
            num = ET.fromstring(z.read("word/numbering.xml"))
            fmt = {}
            for a in num.findall(W + "abstractNum"):
                lvl = a.find(f"{W}lvl/{W}numFmt")
                fmt[a.get(W + "abstractNumId")] = lvl.get(W + "val") if lvl is not None else ""
            for n in num.findall(W + "num"):
                ref = n.find(W + "abstractNumId")
                kind = fmt.get(ref.get(W + "val"), "") if ref is not None else ""
                lists[n.get(W + "numId")] = kind
    blocks = []
    for el in doc.find(W + "body"):
        if el.tag == W + "p":
            blocks.append(("p", Para(el, rels, lists)))
        elif el.tag == W + "tbl":
            rows = [[[" ".join(Para(p, rels, lists).text.split()) for p in tc.iter(W + "p")]
                     for tc in tr.findall(W + "tc")] for tr in el.findall(W + "tr")]
            blocks.append(("tbl", rows))
    return blocks


# ------------------------------------------------------------ small helpers

def clean(s):
    """One space for every run of whitespace, none at the ends."""
    return " ".join(s.replace("\xa0", " ").split())


def title_case(s):
    """His capitals as a title: small words lower, the rest capitalised.
    A word that is not all capitals ("Ph.D.") is left as he typed it."""
    out = []
    for k, w in enumerate(s.split()):
        if not w.isupper():
            out.append(w)
            continue
        low = w.lower()
        out.append(low if k and low.strip(",.;:") in SMALL else low[:1].upper() + low[1:])
    return " ".join(out)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def when(s):
    """A date or a range as fields: {"date"} or {"start", "end"}."""
    s = clean(s)
    m = RANGE.match(s)
    if m:
        return {"start": m.group("start"), "end": m.group("end")}
    if ONE.match(s):
        return {"date": s}
    raise CVError(f"not a date or a range: {s!r}")


def tokens(s):
    """The words and figures of a string, the unit "word for word" is held to."""
    return re.findall(r"[^\W_]+|[*$&%#+]", s.lower())


def same_words(line, *fields):
    """Stop unless the fields hold exactly the words of his line, in order."""
    got = tokens(" ".join(f for f in fields if f))
    if got != tokens(line):
        raise CVError(f"fields do not hold his line word for word:\n  line:   {clean(line)!r}\n"
                      f"  fields: {' | '.join(f for f in fields if f)!r}")


# ------------------------------------------------------------ one line each

def position(head, tail):
    """ORGANISATION <tab> place, then role <tab> dates."""
    org, _, place = head.text.partition("\t")
    role, _, dates = tail.text.partition("\t")
    if not place.strip() or not dates.strip():
        raise CVError(f"a position without its place or its dates: {head.text!r} / {tail.text!r}")
    org = clean(org)
    entry = {"type": "position", "org": title_case(org) if org.isupper() else org,
             "place": clean(place), "role": clean(role)}
    entry.update(when(dates))
    same_words(head.text + " " + tail.text, entry["org"], entry["place"], entry["role"],
               *[entry.get(k) for k in ("date", "start", "end")])
    return entry


def grant(text):
    """Title - amount <tab> years, then a line, then "Role: ..." (his label)."""
    lines = [ln for ln in text.split("\n") if ln.strip()]
    head, _, dates = lines[0].partition("\t")
    parts = DASH.split(clean(head), maxsplit=1)
    entry = {"type": "grant", "title": parts[0]}
    if len(parts) > 1:
        entry["amount"] = parts[1]
    if dates.strip():
        entry.update(when(dates))
    rest = [clean(ln) for ln in lines[1:]]
    roles = [ln for ln in rest if ln.lower().startswith("role:")]
    others = [ln for ln in rest if ln not in roles]
    if len(roles) > 1 or len(others) > 1:
        raise CVError(f"a grant with more lines than a title, a line and a role: {text!r}")
    if others:
        entry["line"] = others[0]
    if roles:
        entry["role"] = roles[0].split(":", 1)[1].strip()
    same_words(text, entry["title"], entry.get("amount"), entry.get("date"), entry.get("start"),
               entry.get("end"), entry.get("line"), "Role" if roles else "", entry.get("role"))
    return entry


def citation(text):
    """Authors "Title", where it appeared, year."""
    line = clean(text)
    m = CITE.match(line)
    if not m:
        return None
    authors = [a.strip() for a in m.group("authors").split(",") if a.strip()]
    entry = {"type": "citation", "authors": authors, "title": m.group("title").strip(),
             "venue": m.group("venue").strip(), "year": m.group("year")}
    same_words(line, *authors, entry["title"], entry["venue"], entry["year"])
    return entry


def item(text):
    """Title | detail <tab> date, or a line ending in its month; or just a line."""
    body, _, date = text.rpartition("\t") if "\t" in text else (text, "", "")
    body, date = clean(body), clean(date)
    if not date:
        m = TAIL_DATE.match(body)
        if m:
            body, date = m.group("body"), m.group("date")
    title, _, detail = body.partition(" | ")
    if not detail:
        m = re.match(r"^(.+?), (patent no:.*)$", body, re.I)
        if m:
            title, detail = m.groups()
    entry = {"type": "item", "title": clean(title)}
    if detail:
        entry["detail"] = clean(detail)
    if date:
        entry.update(when(date))
    same_words(text, entry["title"], entry.get("detail"), entry.get("date"),
               entry.get("start"), entry.get("end"))
    return entry


def list_entry(p):
    if "\n" in p.text:
        return grant(p.text)
    if "\u201c" in p.text and "\u201d" in p.text:
        return citation(p.text) or item(p.text)
    return item(p.text)


def subheading(p):
    """"Published (* stands for equal contribution)": a group and its note."""
    m = re.match(r"^(?P<title>[^(]+?)\s*(?:\((?P<note>[^)]*)\))?$", clean(p.text))
    group = {"type": "group", "title": m.group("title")}
    if m.group("note"):
        group["note"] = m.group("note").strip()
    return group


# ------------------------------------------------------------ the CV

def extract(path=DOCX):
    """His CV as the site's data (the schema is in site/parts/cv.md)."""
    blocks = [(kind, b) for kind, b in read(path) if kind == "tbl" or b.text.strip()]
    cv = {"name": "", "location": "", "email": EMAIL, "links": [], "areas": [], "sections": []}
    k = 0
    # the head: his name, the contact line, the profile links
    while k < len(blocks) and not _heading(blocks[k]):
        kind, p = blocks[k]
        k += 1
        if kind != "p":
            raise CVError("a table above the first section")
        if not cv["name"]:
            cv["name"] = title_case(clean(p.text))
        elif p.href:
            label = clean(re.split(r"\s*\|", p.text, maxsplit=1)[0])
            if label.lower() in DROPPED or OURS in p.href:
                continue
            if label.lower() not in KINDS:
                raise CVError(f"a profile link with no kind yet: {label!r}; add it to KINDS")
            kind = KINDS[label.lower()]
            href = EXACT[kind] if p.href.rstrip("/") == EXACT.get(kind) else p.href
            cv["links"].append({"label": label, "href": href, "kind": kind})
        elif not cv["location"] and ("\u2022" in p.text or "@" in p.text):
            place = clean(p.text.split("\u2022")[0])
            if "@" in place or re.search(r"\d", place):
                raise CVError(f"the contact line does not open with a place: {place!r}")
            cv["location"] = place
        else:
            raise CVError(f"a line above the first section with nowhere to go: {p.text!r}")
    # the sections
    section = group = None
    while k < len(blocks):
        kind, b = blocks[k]
        k += 1
        if _heading((kind, b)):
            title = title_case(clean(b.text))
            section = {"id": IDS.get(title, slug(title)), "title": title, "entries": []}
            cv["sections"].append(section)
            group = None
        elif kind == "tbl":
            # his table reads down its columns: the first column is the monitoring,
            # the second the dynamics and the data, the third the modelling
            cols = max(len(r) for r in b)
            areas = [t for c in range(cols) for r in b if c < len(r) for t in r[c] if t]
            section["entries"] += [{"type": "area", "text": a} for a in areas]
            cv["areas"] += areas
        elif b.list is not None:
            into = group if group is not None else section
            into["entries"].append(list_entry(b))
            if b.list == "decimal":
                into["numbered"] = True
        elif b.shows(1) and "\t" in b.text:
            if k >= len(blocks) or blocks[k][0] != "p" or "\t" not in blocks[k][1].text:
                raise CVError(f"an organisation line with no role line under it: {b.text!r}")
            section["entries"].append(position(b, blocks[k][1]))
            k += 1
        elif b.shows(1) and b.shows(2):
            group = subheading(b)
            group["entries"] = []
            section["entries"].append(group)
        else:
            raise CVError(f"a line this reader cannot file: {b.text!r}")
    for key in ("name", "location"):
        if not cv[key]:
            raise CVError(f"no {key} found at the top of the CV")
    cv["sections"] = [_tidy(s) for s in cv["sections"]]
    found = leaks(cv)
    if found:
        raise CVError("private contact details would be published: " + "; ".join(found))
    return cv


def _tidy(box):
    """A section or a group with "numbered" ahead of its entries, for the reader of the JSON."""
    head = {k: v for k, v in box.items() if k not in ("numbered", "entries")}
    if box.get("numbered"):
        head["numbered"] = True
    head["entries"] = [_tidy(e) if e.get("type") == "group" else e for e in box["entries"]]
    return head


def _heading(block):
    kind, p = block
    return kind == "p" and p.list is None and "\t" not in p.text and p.shows(1) and (
        p.shows(3) or clean(p.text).isupper())


def leaks(obj):
    """Every private contact detail in `obj` (anything JSON can hold)."""
    text = json.dumps(obj, ensure_ascii=False)
    found = []
    for pattern, what in PRIVATE:
        found += [f"{what} {m.group(0)!r}" for m in pattern.finditer(text)
                  if not (what == "an email address" and m.group(0) == EMAIL)]
    return found


def dump(cv):
    return json.dumps(cv, ensure_ascii=False, indent=1) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Read his CV (Word) into content/cv/cv.json.")
    ap.add_argument("--docx", default=DOCX, help="the CV (default: content/source/...)")
    ap.add_argument("--out", default=OUT, help="the JSON to write (default: content/cv/cv.json)")
    ap.add_argument("--check", action="store_true",
                    help="write nothing; fail if the JSON on disk differs from the CV")
    args = ap.parse_args(argv)
    try:
        cv = extract(args.docx)
    except CVError as e:
        sys.exit(f"cv_extract: {e}")
    text = dump(cv)
    if args.check:
        try:
            with open(args.out, encoding="utf-8") as fh:
                same = fh.read() == text
        except OSError:
            same = False
        state = "current" if same else "STALE: run tools/cv_extract.py"
        print(f"cv_extract: {args.out} is {state}")
        return 0 if same else 1
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    count = sum(len(g["entries"]) if g.get("type") == "group" else 1
                for s in cv["sections"] for g in s["entries"])
    print(f"cv_extract: {len(cv['sections'])} sections, {count} entries, {len(cv['links'])} links, "
          f"{len(cv['areas'])} areas -> {os.path.relpath(args.out, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
