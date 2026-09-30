"""His CV, read out of his Word file into content/cv/cv.json (tools/cv_extract.py).

What these hold: the JSON on disk is the CV as it reads today; every section
and every entry of the CV is in it, word for word; the facts his CV joins with
a dash or a bar are separate fields; and his personal Gmail address and phone
number never get in, while his IYTE address and his profile links do.

The Word file is read a second time here, independently and more crudely
(every run's text, every heading by its capitals), so a word the extractor
drops or bends shows up as a difference between the two readings.
"""

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

import pytest

from tools import cv_extract
from tools.cv_extract import EMAIL, CVError, extract, leaks

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCX = os.path.join(ROOT, "content", "source", "Korkut_Kaynardag_Resume.docx")
JSON = os.path.join(ROOT, "content", "cv", "cv.json")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


@pytest.fixture(scope="module")
def cv():
    with open(JSON, encoding="utf-8") as fh:
        return json.load(fh)


def words(s):
    return re.findall(r"[^\W_]+|[*$&%#+]", s.lower())


# ------------------------------------------------------- the crude second reading

def docx_blocks(path=DOCX):
    """[(kind, text, is_caps_heading, is_list)] in body order; a table's text is its
    cells, row by row, one per line."""
    with zipfile.ZipFile(path) as z:
        body = ET.fromstring(z.read("word/document.xml")).find(W + "body")
    out = []
    for el in body:
        if el.tag == W + "p":
            text = "".join("\t" if c.tag == W + "tab" else "\n" if c.tag == W + "br" else
                           (c.text or "") if c.tag == W + "t" else ""
                           for r in el.iter(W + "r") for c in r)
            caps = el.find(f".//{W}caps") is not None
            is_list = el.find(f"{W}pPr/{W}numPr") is not None
            if text.strip():
                out.append(("p", text, caps, is_list))
        elif el.tag == W + "tbl":
            cells = ["".join(t.text or "" for t in p.iter(W + "t"))
                     for tr in el.iter(W + "tr") for tc in tr.findall(W + "tc")
                     for p in tc.iter(W + "p")]
            out.append(("tbl", "\n".join(c for c in cells if c.strip()), False, False))
    return out


def docx_sections():
    """{heading text: [blocks under it]}, headings found by their capitals alone."""
    secs, cur = {}, None
    for block in docx_blocks():
        if block[2]:
            cur = " ".join(block[1].split())
            secs[cur] = []
        elif cur is not None:
            secs[cur].append(block)
    return secs


def json_words(entries):
    """The words of a section's entries, fields in the order the JSON keeps them.
    A grant's role is printed under his own label "Role", so the label is counted."""
    out = []
    for e in entries:
        for key, value in e.items():
            if key in ("type", "numbered"):
                continue
            if key == "entries":
                out += json_words(value)
            elif key == "role" and e["type"] == "grant":
                out += ["role"] + words(value)
            elif isinstance(value, list):
                out += [w for v in value for w in words(v)]
            else:
                out += words(value)
    return out


# ------------------------------------------------------------------ the tests

def test_the_json_on_disk_is_his_cv_as_it_reads_today(cv):
    assert extract(DOCX) == cv
    assert cv_extract.main(["--check"]) == 0


def test_check_mode_fails_on_a_stale_file(tmp_path):
    stale = tmp_path / "cv.json"
    stale.write_text("{}\n", encoding="utf-8")
    assert cv_extract.main(["--check", "--out", str(stale)]) == 1


def test_the_schema_the_site_reads(cv):
    assert list(cv) == ["name", "location", "email", "links", "areas", "sections"]
    assert cv["name"] == "Korkut Kaynardag, Ph.D."
    for link in cv["links"]:
        assert set(link) == {"label", "href", "kind"}
    for s in cv["sections"]:
        assert {"id", "title", "entries"} <= set(s)
        assert re.fullmatch(r"[a-z0-9-]+", s["id"])
    assert len({s["id"] for s in cv["sections"]}) == len(cv["sections"])


def test_no_personal_email_or_phone_anywhere(cv):
    with open(JSON, encoding="utf-8") as fh:
        raw = fh.read()
    for private in ("gmail", "korkut.kaynardag@", "300-4065", "(512)", "512", "+1"):
        assert private not in raw.lower()
    assert cv["email"] == "korkutkaynardag@iyte.edu.tr"
    assert cv["location"] == "Izmir, Turkiye"
    assert re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", raw) == [EMAIL]
    assert leaks(cv) == []


def test_the_guard_catches_every_shape_of_private_detail():
    assert leaks({"a": "korkut.kaynardag@gmail.com"})
    assert leaks({"a": "someone@example.org"})
    assert leaks({"a": "+1 (512) 300-4065"})
    assert leaks({"a": "call 300-4065"})
    assert leaks({"a": "(512) 300 4065"})
    assert leaks({"email": EMAIL}) == []
    # page ranges, patent numbers and a YouTube handle are not phone numbers
    assert leaks({"a": "15 (8), 3227-3243 and 37(4):230-245, US20200271543A1",
                  "b": "https://www.youtube.com/@korkutkaynardag9147"}) == []


def rewrite(tmp_path, old, new):
    """A copy of his CV with one string of document.xml replaced."""
    dst = tmp_path / "cv.docx"
    with zipfile.ZipFile(DOCX) as src, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as out:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename == "word/document.xml":
                text = data.decode("utf-8")
                assert old in text
                data = text.replace(old, new, 1).encode("utf-8")
            out.writestr(info, data)
    return str(dst)


def test_a_cv_that_would_publish_his_gmail_is_refused(tmp_path):
    path = rewrite(tmp_path, "<w:t>Sensors</w:t>", "<w:t>Sensors korkut.kaynardag@gmail.com</w:t>")
    with pytest.raises(CVError, match="Gmail"):
        extract(path)


def test_a_new_profile_link_waits_for_a_kind(tmp_path):
    path = rewrite(tmp_path, "<w:t>YouTube</w:t>", "<w:t>ORCID</w:t>")
    with pytest.raises(CVError, match="ORCID"):
        extract(path)


def test_a_line_the_reader_cannot_file_stops_it(tmp_path):
    # a plain paragraph under a heading: no list, no emphasis, no tab
    path = rewrite(tmp_path, "<w:t>PATENTS</w:t></w:r></w:p>",
                   "<w:t>PATENTS</w:t></w:r></w:p><w:p><w:r><w:t>A stray line</w:t></w:r></w:p>")
    with pytest.raises(CVError, match="A stray line"):
        extract(path)


def test_links_are_his_profiles_and_not_this_site(cv):
    with zipfile.ZipFile(DOCX) as z:
        rels = ET.fromstring(z.read("word/_rels/document.xml.rels"))
    external = [r.get("Target") for r in rels if r.get("TargetMode") == "External"]
    assert any("wavesanddata.com" in h for h in external)       # his CV has it
    assert sorted(link["href"].rstrip("/") for link in cv["links"]) == sorted(
        h.rstrip("/") for h in external if "wavesanddata.com" not in h)
    # the three the user gave exactly (ROUND4_SPEC.md section 12): no trailing slash
    assert {link["kind"]: link["href"] for link in cv["links"][:3]} == {
        "scholar": "https://scholar.google.com/citations?user=v_eQpwUAAAAJ&hl=en",
        "linkedin": "https://www.linkedin.com/in/korkutkaynardag",
        "researchgate": "https://www.researchgate.net/profile/Korkut-Kaynardag"}
    assert [link["label"] for link in cv["links"]] == [
        "Google Scholar", "LinkedIn", "ResearchGate", "GitHub", "YouTube"]
    assert [link["kind"] for link in cv["links"]] == [
        "scholar", "linkedin", "researchgate", "github", "youtube"]
    assert "personal webpage" not in json.dumps(cv).lower()
    assert "wavesanddata" not in json.dumps(cv).lower()


def test_every_section_in_his_order(cv):
    headings = list(docx_sections())
    assert len(headings) == 13
    assert [s["title"].lower() for s in cv["sections"]] == [h.lower() for h in headings]


def test_every_entry_word_for_word(cv):
    secs = docx_sections()
    for s, (heading, blocks) in zip(cv["sections"], secs.items()):
        his = [w for _, text, _, _ in blocks for w in words(text)]
        ours = json_words(s["entries"])
        if any(kind == "tbl" for kind, *_ in blocks):
            his, ours = sorted(his), sorted(ours)      # his table reads across; we read down
        assert ours == his, heading


def test_every_list_entry_and_position_is_there(cv):
    secs = docx_sections()

    def flat(entries):
        for e in entries:
            yield from flat(e["entries"]) if e["type"] == "group" else [e]

    for s, blocks in zip(cv["sections"], secs.values()):
        entries = list(flat(s["entries"]))
        listed = [b for b in blocks if b[3]]
        assert len([e for e in entries if e["type"] not in ("position", "area")]) == len(listed)
        # a position is two lines of his: organisation <tab> place, role <tab> dates
        unlisted = [b for b in blocks if b[0] == "p" and not b[3] and "\t" in b[1]]
        assert len([e for e in entries if e["type"] == "position"]) * 2 == len(unlisted)
    counts = {s["id"]: len(list(flat(s["entries"]))) for s in cv["sections"]}
    assert counts == {
        "education": 3, "research-interests": 15, "experience": 5, "grants": 4,
        "journal-publications": 12, "conference-proceedings": 6,
        "conference-presentations": 5, "invited-talks": 1, "patents": 2, "awards": 8,
        "peer-review": 4, "workshops-and-memberships": 7, "certifications": 7}


def test_the_research_areas_read_down_his_columns(cv):
    with zipfile.ZipFile(DOCX) as z:
        body = ET.fromstring(z.read("word/document.xml")).find(W + "body")
    table = body.find(W + "tbl")
    rows = [[[" ".join("".join(t.text or "" for t in p.iter(W + "t")).split())
              for p in tc.iter(W + "p")] for tc in tr.findall(W + "tc")]
            for tr in table.findall(W + "tr")]
    down = [t for c in range(3) for r in rows for t in r[c] if t]
    assert cv["areas"] == down
    assert cv["areas"][:2] == ["Structural Health Monitoring", "Non-Destructive Testing"]
    section = next(s for s in cv["sections"] if s["id"] == "research-interests")
    assert [e["text"] for e in section["entries"]] == cv["areas"]


def test_a_dash_between_two_facts_is_two_fields(cv):
    raw = json.dumps(cv, ensure_ascii=False)
    assert "\u2014" not in raw                      # no em dash survives
    grants = next(s for s in cv["sections"] if s["id"] == "grants")["entries"]
    assert [g.get("amount") for g in grants] == ["$600K", "$20,000", "$5,000", None]
    assert grants[0]["title"] == "Federal Railroad Administration (FRA), Phase I & II"
    assert (grants[0]["start"], grants[0]["end"]) == ("2017", "2019")
    assert grants[0]["role"] == "Proposal co-author; led technical methodology development"
    assert grants[2]["role"] == "Co-PI"
    exp = next(s for s in cv["sections"] if s["id"] == "experience")["entries"]
    assert (exp[0]["start"], exp[0]["end"]) == ("08/2026", "present")
    awards = next(s for s in cv["sections"] if s["id"] == "awards")["entries"]
    assert awards[0] == {"type": "item", "title": "Second Place",
                         "detail": "Michael Sutton International Paper Competition, "
                                   "2023 SEM Annual Conference", "date": "07/2023"}
    for s in cv["sections"]:
        for e in s["entries"]:
            for key in ("date", "start", "end"):
                if key in e:
                    assert re.fullmatch(r"\d{2}/\d{4}|\d{4}|present", e[key]), e


def test_a_citation_keeps_his_authors_title_venue_and_year(cv):
    pubs = next(s for s in cv["sections"] if s["id"] == "journal-publications")["entries"]
    group = pubs[0]
    assert (group["title"], group["note"]) == ("Published", "* stands for equal contribution")
    assert group["numbered"] is True
    first = group["entries"][0]
    assert first["authors"] == ["B Uluutku*", "K Kaynardag*", "D Oshima", "J Cotter", "FN Catbas"]
    assert first["title"].startswith("Machine Learning-Based Road Surface Defect Detection")
    assert (first["venue"], first["year"]) == ("Infrastructures, 11(6):200", "2026")
    # every citation names him once
    for s in cv["sections"]:
        for e in s["entries"]:
            for c in (e["entries"] if e["type"] == "group" else [e]):
                if c["type"] == "citation" and c["authors"]:
                    assert sum(bool(re.match(r"K\.? ?Kaynardag\*?$", a)) for a in c["authors"]) == 1
    talk = next(s for s in cv["sections"] if s["id"] == "invited-talks")
    assert talk["entries"][0]["authors"] == [] and "numbered" not in talk


def test_title_case_is_only_for_his_capitals():
    tc = cv_extract.title_case
    assert tc("THE UNIVERSITY OF TEXAS AT AUSTIN") == "The University of Texas at Austin"
    assert tc("KORKUT KAYNARDAG, Ph.D.") == "Korkut Kaynardag, Ph.D."
    assert tc("GRANTS, FUNDING, AND PROPOSALS") == "Grants, Funding, and Proposals"
    assert tc("Bogazici University") == "Bogazici University"


# ------------------------------------------------------------------ the page

@pytest.fixture(scope="module")
def page(cv):
    sys.path.insert(0, os.path.join(ROOT, "site"))
    from parts import cv as cvpage
    return cvpage, cvpage.render(cv)


def test_the_page_is_the_sites_own_wrap(page):
    # build.py's page() recognises a part's wrapper by this pattern and would
    # otherwise wrap the page a second time
    assert re.match(r'\s*<div class="wrap\b[^"]*">', page[1])
    assert page[1].count('class="wrap') == 1


def test_every_section_has_its_anchor_in_both_contents_lists(cv, page):
    body = page[1]
    for s in cv["sections"]:
        assert f'id="{s["id"]}"' in body
        assert body.count(f'href="#{s["id"]}"') == 2          # the fold and the rail


def test_every_word_of_the_json_reaches_the_page(cv, page):
    body = page[1]
    cvpage = page[0]
    missing = [w for w in cvpage.his(cv) if w not in body]
    assert missing == []


def test_his_name_is_bold_in_every_author_list(page):
    for li in re.findall(r'<li class="cv-e cv-cite">.*?</li>', page[1]):
        if 'class="cv-by"' in li:
            assert len(re.findall(r'<b class="cv-me">K Kaynardag\*?</b>', li)) == 1, li


def test_amounts_roles_and_dates_are_fields_not_dashes(page):
    body = page[1]
    assert "\u2014" not in body and "&mdash;" not in body
    assert '<p class="cv-amt">$600K</p>' in body
    assert '<span class="cv-lbl">Role</span>Co-PI' in body
    assert ('<time datetime="2016-09">09/2016</time><span class="cv-to">&#8211;</span>'
            '<time datetime="2023-08">08/2023</time>') in body
    assert ('<time datetime="2026-08">08/2026</time><span class="cv-to">&#8211;</span>'
            'present') in body


def test_no_private_detail_on_the_page(page):
    body = page[1].lower()
    assert "gmail" not in body and "300-4065" not in body and "(512)" not in body
    assert 'href="mailto:korkutkaynardag@iyte.edu.tr"' in body


def test_the_print_sheet_makes_a_clean_cv(page):
    css = page[0].CSS
    assert "@page cv{" in css and ".cv{page:cv;" in css
    for gone in (".skip", ".foot", ".bar", ".side", ".fold", ".cv-pdf", ".cv-rail", ".cv-toc-nav"):
        assert gone in css[css.index("@media print"):]
    assert "content:attr(href)" in css                       # link addresses printed
    assert "break-inside:avoid" in css
