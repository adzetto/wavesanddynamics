"""Put the site's content into a Wix site through the REST API: the seven
converted documents, the three topic sections, the photo gallery and the blog.

    python tools/wix_import.py --site dup|studio COMMAND

    plan         build every CMS item locally, no network, print its size
    collections  create the CMS collections the site is missing (SCHEMAS)
    media        upload the document figures and the audited Word files
    gallery      strip camera metadata from the gallery photos, check the bytes,
                 upload the photos and the film, check the stored copies
    probe        ask the live Ricos validator about each new node shape
    validate     validate every CMS rich-content body with the live validator
    save         save the CMS items (Documents, Topics, GallerySets, Photos)
    blog         upload the blog pictures and attachment, validate, then create
                 and publish the eight posts (a slug already there is skipped)
    counts       read back what the site holds: items, media, posts
    report       write build/wix/<site>/REPORT.md from the site and the state

Local state per site in build/wix/<site>/ (gitignored): media.json (uploaded
file ids, so nothing is uploaded twice and the two sites' ids never mix),
validate/*.json (the validator's full answers), items/*.json (exactly what was
saved), gallery/ (the photo bytes that were uploaded), blog.json, counts.json.

SAFETY. A request can reach only a site named in SITES, chosen with --site;
the live site's id is written here only so that _site() can refuse it. Each
request carries wix-site-id and a token minted for that one site, exchanged
from the Wix CLI login in ~/.wix/auth/account.json the way @wix/mcp does it
(account-auth-strategy.js). The token is never printed or stored. Nothing here
publishes a site or touches a domain.

WHAT IS CHANGED IN A DOCUMENT, AND WHY. The body is the converter's Ricos
(build/ricos/<slug>/part-01.json) with these changes, all but the last taken
from the static site's own reading of the file (site/preview.py, build.py):
  1. the cover (opening picture, title, subtitle, byline, their rules) leaves
     the body and becomes fields, so the page has one H1, bound to `title`;
  2. Word's heading levels shift down one, his Heading 1 becomes h2 under it;
  3. a bold line the static site reads as a heading becomes a HEADING node;
  4. in the guide whose "Table of Contents" field Word filled in (the converter
     cannot carry a field), a list of its chapter headings follows that line,
     each linked to its heading inside the document;
  5. his personal Gmail, which closes three guides' disclaimers, becomes his
     institutional address, linked, as on the static site; any other address
     stops the tool (the site carries one address);
  6. table column shares become whole percentages: the live validator parses
     colsWidthRatio as int32 and fails on the converter's fractions;
  7. Word's justified paragraphs set left (JUSTIFY -> AUTO), as the static page
     sets them (preview._para keeps only CENTER and RIGHT), and a table column
     he centred keeps its centring only where its values are short, the rule of
     preview._column_align;
  8. a document long enough to lose your place in (four h2 chapters and 2,000
     words or more, build.page_doc's rule) that has no "Table of Contents" line
     of his gets a "Contents" line and the list of its chapters at the top of
     the body, each linked to its heading, as the static page's list does.
  9. a table's gaps from Word's merged cells go, as preview._table drops them:
     rows with nothing in them, and columns empty in every row but those whose
     only content is their first cell (_gapless);
 10. a picture no caption describes gets the static page's alt text (build.ALT).
Words are never edited otherwise. Image ids are rewritten to the site's own
Media Manager ids: bare ids in Ricos, wix:image:// URLs in CMS image fields.
"""

import argparse
import base64
import copy
import hashlib
import io
import json
import os
import re
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# tools/inspect.py would shadow the standard library's inspect, which build.py imports
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != _HERE]
sys.path.insert(0, os.path.join(ROOT, "site"))
import build as site_build  # noqa: E402  the static site's document table
import preview  # noqa: E402  the static site's reading of each document

SITES = {
    "dup": "c810e33e-579e-45f2-96a2-02d6922a0fce",  # classic Editor duplicate, stage 1
    "studio": "e4242161-3b8c-4fd2-9763-7c93b4063a15",  # wavesanddata-studio
    "public": "329f83ff-0d8f-4188-8f9f-e842991e9d2a",  # the static site on wavesanddata.com
}
LIVE = "36a33e18-0863-4d42-8bbd-70c189d86351"  # wavesanddata.com: refused, always
OWNER = (
    "ce0a40ea-9fb2-430e-a0dd-91830c938523"  # the account owner, a member of each site
)
API = "https://www.wixapis.com"
AUTH = os.path.expanduser("~/.wix/auth/account.json")
CLI_CLIENT = "f234ac48-6cab-4ef2-9ea0-03d56a376da4"  # @wix/cli public client id
BUILD = os.path.join(ROOT, "build", "ricos")
SRC = os.path.join(ROOT, "content", "source")
GALLERY_DIR = os.path.join(ROOT, "content", "gallery")
BLOG_DIR = os.path.join(ROOT, "content", "blog")
LIMIT = 500_000
MAIL = site_build.CONTACT["email"]  # korkutkaynardag@iyte.edu.tr, the one address
GMAIL = re.compile(r"korkut\.kaynardag@gmail\.com", re.I)
ADDRESS = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

# Stage 1 handover (docs/superpowers/specs/2026-09-22-asama-1-devir.md, section 4);
# the blog adds the two plugins its posts use (a YouTube film, a Word attachment).
PLUGINS = [
    "IMAGE",
    "TABLE",
    "LINK",
    "HEADING",
    "TEXT_COLOR",
    "DIVIDER",
    "CODE_BLOCK",
    "INDENT",
    "LINE_SPACING",
    "TEXT_HIGHLIGHT",
    "FONT_FAMILY",
    "COLLAPSIBLE_LIST",
]
BLOG_PLUGINS = PLUGINS + ["VIDEO", "FILE"]

# Converter slug -> CMS slug. Only the guide changes: "_5" is his file's version
# number, and a page address must survive "_6".
CMS_SLUG = {
    "machine-learning-the-complete-picture-and-guide-5": "machine-learning-the-complete-picture-and-guide"
}
WORD_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

S = {}  # the chosen site: name, id, out


# ------------------------------------------------------------------ the wire


class WixError(Exception):
    pass


def _site():
    """The id of the site chosen with --site, after refusing anything else."""
    sid = S.get("id")
    if not sid or sid == LIVE or sid not in SITES.values():
        raise SystemExit(f"refusing site {sid}: allowed are {sorted(SITES)}")
    return sid


def _http(method, url, body=None, headers=None, raw=None, tries=4):
    data = (
        raw
        if raw is not None
        else (
            json.dumps(body, ensure_ascii=False).encode("utf-8")
            if body is not None
            else None
        )
    )
    for k in range(tries):
        req = urllib.request.Request(
            url, data=data, method=method, headers=headers or {}
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                text = r.read().decode("utf-8")
                return json.loads(text) if text.strip() else {}
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")
            if (e.code == 429 or e.code >= 500) and k + 1 < tries:
                time.sleep(15 * (k + 1))  # WDE0014 / quota: wait and retry
                continue
            raise WixError(f"HTTP {e.code} {method} {url.split('?')[0]}: {text[:1500]}")
        except urllib.error.URLError as e:
            if k + 1 < tries:
                time.sleep(5 * (k + 1))
                continue
            raise WixError(f"{method} {url.split('?')[0]}: {e}")
    raise WixError("unreachable")


_TOKENS = {}


def _token():
    sid = _site()
    got = _TOKENS.get(sid)
    if got and got["exp"] > time.time():
        return got["t"]
    with open(AUTH, encoding="utf-8") as fh:
        refresh = json.load(fh)["refreshToken"]
    got = _http(
        "POST",
        API + "/oauth2/token",
        {
            "clientId": CLI_CLIENT,
            "grantType": "refresh_token",
            "refreshToken": refresh,
            "siteId": sid,
        },
        {"Content-Type": "application/json"},
    )
    _TOKENS[sid] = {
        "t": got["access_token"],
        "exp": time.time() + min(int(got.get("expires_in") or 600), 3600) - 120,
    }
    return _TOKENS[sid]["t"]


def call(method, path, body=None):
    return _http(
        method,
        API + path,
        body,
        {
            "Authorization": _token(),
            "wix-site-id": _site(),
            "Content-Type": "application/json",
        },
    )


def nbytes(obj):
    """What a field costs against the item limit: UTF-8 of the unescaped JSON."""
    return len(json.dumps(obj, ensure_ascii=False).encode("utf-8"))


def out(*parts):
    return os.path.join(S["out"], *parts)


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return default


def _dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _read(path):
    with open(path, "rb") as fh:
        return fh.read()


# ------------------------------------------------------------------ collections

_READ_ANYONE = {
    "insert": "ADMIN",
    "update": "ADMIN",
    "remove": "ADMIN",
    "read": "ANYONE",
}
_BY_ORDER = [
    {
        "type": "CMS",
        "cmsOptions": {
            "siteSort": {"sort": [{"fieldKey": "order", "direction": "ASC"}]}
        },
    }
]


def _f(key, name, kind, desc, required=False, ref=None):
    field = {"key": key, "displayName": name, "type": kind, "description": desc}
    if required:
        field["required"] = True
    if ref:
        field["typeMetadata"] = {"reference": {"referencedCollectionId": ref}}
    return field


# The schemas the duplicate got in stage 1 (created there through the MCP with
# these bodies), plus Photos: one item per photo, which the professor can add to.
SCHEMAS = {
    "Documents": {
        "displayName": "Documents",
        "fields": [
            _f(
                "title",
                "Title",
                "TEXT",
                "His title, from the cover of the Word file. Shown as the page heading.",
                True,
            ),
            _f(
                "slug",
                "URL slug",
                "TEXT",
                "Last part of this document's page address. Lowercase words joined by hyphens.",
                True,
            ),
            _f(
                "order",
                "Order",
                "NUMBER",
                "Position in the Documents list and in the left menu, 1 first.",
            ),
            _f(
                "subtitle",
                "Subtitle",
                "TEXT",
                "The italic line under the title on his cover.",
            ),
            _f("byline", "Byline", "TEXT", "The author line on his cover."),
            _f(
                "summary", "Summary", "TEXT", "One line shown under the title in lists."
            ),
            _f("navLabel", "Menu label", "TEXT", "Short name used in the left menu."),
            _f(
                "coverImage",
                "Cover image",
                "IMAGE",
                "The picture at the top of his cover, when the document has one.",
            ),
            _f(
                "body",
                "Body",
                "RICH_CONTENT",
                "The document itself: text, figures and tables.",
            ),
            _f(
                "wordFile",
                "Word file",
                "DOCUMENT",
                "The Word original visitors can download. Leave empty to hide the download link.",
            ),
            _f(
                "seoTitle",
                "SEO title",
                "TEXT",
                "Title for the browser tab and search results.",
            ),
            _f(
                "sourceFile",
                "Source file",
                "TEXT",
                "The Word file this item was imported from.",
            ),
        ],
    },
    "Topics": {
        "displayName": "Topics",
        "fields": [
            _f(
                "title",
                "Title",
                "TEXT",
                "Name of the educational section. Shown as the page heading.",
                True,
            ),
            _f(
                "slug",
                "URL slug",
                "TEXT",
                "Last part of this section's page address. Lowercase words joined by hyphens.",
                True,
            ),
            _f(
                "order",
                "Order",
                "NUMBER",
                "Position in the left menu and in Explore the topics, 1 first.",
            ),
            _f(
                "navLabel",
                "Menu label",
                "TEXT",
                "Name in the left menu. A line break here is a line break in the menu.",
            ),
            _f("cardTitle", "Card title", "TEXT", "Title on the home page card."),
            _f("cardText", "Card text", "TEXT", "One sentence on the home page card."),
            _f("lede", "Introduction", "TEXT", "The paragraph under the page heading."),
            _f(
                "guide",
                "Guide",
                "REFERENCE",
                "The document shown under Start here.",
                ref="Documents",
            ),
            _f(
                "body",
                "Sections",
                "RICH_CONTENT",
                "The big picture, how to learn this topic, recommended books and resources.",
            ),
        ],
    },
    "GallerySets": {
        "displayName": "Gallery",
        "fields": [
            _f(
                "title",
                "Caption",
                "TEXT",
                "His caption for the set, with his line breaks.",
                True,
            ),
            _f(
                "period",
                "Period",
                "TEXT",
                "The quieter last line, for example (during my Ph.D.).",
            ),
            _f("order", "Order", "NUMBER", "Position on the Gallery page, 1 first."),
            _f(
                "media",
                "Photos and video",
                "MEDIA_GALLERY",
                "The photos, or the video, of this set.",
            ),
        ],
    },
    "Photos": {
        "displayName": "Photos",
        "fields": [
            _f(
                "title",
                "Caption",
                "TEXT",
                "Caption shown with the photo. The imported photos carry their set's caption.",
                True,
            ),
            _f(
                "image",
                "Photo",
                "IMAGE",
                "The photo. Leave empty when the item is a video.",
            ),
            _f("video", "Video", "VIDEO", "A video in place of a photo."),
            _f(
                "set",
                "Set",
                "REFERENCE",
                "The set this photo belongs to on the Gallery page.",
                ref="GallerySets",
            ),
            _f("order", "Order", "NUMBER", "Position in the gallery, 1 first."),
        ],
    },
}
# Stage 2 in the duplicate is cancelled: it keeps the three collections it has.
COLLECTIONS = {
    "dup": ["Documents", "Topics", "GallerySets"],
    "studio": ["Documents", "Topics", "GallerySets", "Photos"],
}


def cmd_collections():
    for cid in COLLECTIONS[S["name"]]:
        want = SCHEMAS[cid]
        try:
            have = call("GET", f"/wix-data/v2/collections/{cid}")["collection"]
        except WixError as e:
            if (
                "404" not in str(e)
                and "WDE0025" not in str(e)
                and "not found" not in str(e).lower()
            ):
                raise
            body = {
                "collection": {
                    "id": cid,
                    "displayName": want["displayName"],
                    "displayField": "title",
                    "fields": want["fields"],
                    "permissions": _READ_ANYONE,
                    "plugins": _BY_ORDER,
                }
            }
            got = call("POST", "/wix-data/v2/collections", body)["collection"]
            print(
                f"  created {cid}: {len(got['fields'])} fields, revision {got['revision']}"
            )
            continue
        keys = {f["key"]: f["type"] for f in have["fields"]}
        for f in want["fields"]:
            if f["key"] not in keys:
                call(
                    "POST",
                    "/wix-data/v2/collections/create-field",
                    {"dataCollectionId": cid, "field": f},
                )
                print(f"  {cid}: added field {f['key']} ({f['type']})")
            elif keys[f["key"]] != f["type"]:
                print(
                    f"  !! {cid}.{f['key']} is {keys[f['key']]}, schema says {f['type']}"
                )
        print(f"  {cid}: present")


# ------------------------------------------------------------------ media


def upload_bytes(blob, name, mime, folder):
    """Generate File Upload URL, then PUT the bytes to it (the Upload API)."""
    got = call(
        "POST",
        "/site-media/v1/files/generate-upload-url",
        {
            "mimeType": mime,
            "fileName": name,
            "sizeInBytes": str(len(blob)),
            "filePath": folder,
        },
    )
    return _http("PUT", got["uploadUrl"], raw=blob, headers={"Content-Type": mime})[
        "file"
    ]


def upload_resumable(blob, name, mime, folder, chunk=8 << 20):
    """Generate File Resumable Upload URL, a tus upload, then the finalising PUT
    (the Resumable Upload API): for files over 10 MB."""
    got = call(
        "POST",
        "/site-media/v1/files/generate-resumable-upload-url",
        {
            "mimeType": mime,
            "fileName": name,
            "sizeInBytes": str(len(blob)),
            "filePath": folder,
            "uploadProtocol": "TUS",
        },
    )
    url, token = got["uploadUrl"], got["uploadToken"]
    meta = ",".join(
        f"{k} {base64.b64encode(v.encode()).decode()}"
        for k, v in (("filename", name), ("contentType", mime), ("token", token))
    )
    req = urllib.request.Request(
        url,
        data=b"",
        method="POST",
        headers={
            "Tus-Resumable": "1.0.0",
            "Upload-Length": str(len(blob)),
            "Upload-Metadata": meta,
        },
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        where = urllib.parse.urljoin(url, r.headers["Location"])
    offset = 0
    while offset < len(blob):
        req = urllib.request.Request(
            where,
            data=blob[offset : offset + chunk],
            method="PATCH",
            headers={
                "Tus-Resumable": "1.0.0",
                "Upload-Offset": str(offset),
                "Content-Type": "application/offset+octet-stream",
            },
        )
        with urllib.request.urlopen(req, timeout=600) as r:
            offset = int(r.headers["Upload-Offset"])
    done = _http(
        "PUT",
        f"{url}/{token}?filename={urllib.parse.quote(name)}",
        {},
        {"Content-Type": "application/json"},
    )
    return done["file"]


def _record(f, blob, extra=None):
    img = (f.get("media") or {}).get("image", {}).get("image", {})
    rec = {
        "id": f["id"],
        "url": f.get("url"),
        "status": f.get("operationStatus"),
        "mediaType": f.get("mediaType"),
        "folder": f.get("parentFolderId"),
        "width": img.get("width"),
        "height": img.get("height"),
        "bytes": len(blob),
        "sha256": _sha(blob),
    }
    rec.update(extra or {})
    return rec


def wait_ready(media, rounds=60, pause=6):
    """Uploads are processed asynchronously: poll until every file is READY."""
    for _ in range(rounds):
        pending = [k for k, v in media.items() if v.get("status") != "READY"]
        if not pending:
            break
        for key in pending:
            f = call(
                "GET",
                "/site-media/v1/files/get-file-by-id?fileId="
                + urllib.parse.quote(media[key]["id"], safe=""),
            )["file"]
            img = (f.get("media") or {}).get("image", {}).get("image", {})
            media[key].update(
                status=f.get("operationStatus"),
                url=f.get("url"),
                folder=f.get("parentFolderId"),
                width=img.get("width") or media[key].get("width"),
                height=img.get("height") or media[key].get("height"),
            )
            if f.get("mediaType") == "VIDEO":
                media[key]["descriptor"] = f
        _dump(out("media.json"), media)
        if any(v.get("status") != "READY" for v in media.values()):
            time.sleep(pause)
    return {k: v["status"] for k, v in media.items() if v.get("status") != "READY"}


def cmd_media():
    media = _load(out("media.json"), {})
    jobs = []
    for slug in site_build.DOCS:
        figdir = os.path.join(BUILD, slug, "figures")
        folder = "/documents/" + CMS_SLUG.get(slug, slug)
        for name in sorted(os.listdir(figdir)):
            jobs.append(
                (
                    f"{slug}/{name}",
                    os.path.join(figdir, name),
                    name,
                    "image/png",
                    folder,
                )
            )
    # The three audited Word originals and no other (build.py HOSTED_DOCX): the
    # Signal Processing, Dynamical and Machine Learning files carry his Gmail.
    for slug in site_build.HOSTED_DOCX:
        name = site_build.SRC_DOCX[slug]
        jobs.append(
            (
                f"word/{slug}",
                os.path.join(SRC, name),
                name,
                WORD_MIME,
                "/documents/word",
            )
        )
    for key, path, name, mime, folder in jobs:
        blob = _read(path)
        have = media.get(key)
        if have and have.get("sha256") == _sha(blob):
            continue
        f = upload_bytes(blob, name, mime, folder)
        media[key] = _record(f, blob)
        _dump(out("media.json"), media)
        print(f"  up   {key} -> {f['id']} {f.get('operationStatus')}")
    bad = wait_ready(media)
    print(
        f"media: {len(media)} files, {len(media) - len(bad)} READY"
        + (f", not ready: {bad}" if bad else "")
    )


# ------------------------------------------------------------------ gallery photos

# Chunks a PNG can carry text or camera data in; everything else is image data.
_PNG_DROP = {b"eXIf", b"tEXt", b"zTXt", b"iTXt", b"tIME"}


def strip_png(data):
    """The PNG without its metadata chunks, byte for byte otherwise."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    kept, i = [data[:8]], 8
    while i < len(data):
        size = struct.unpack(">I", data[i : i + 4])[0]
        tag = data[i + 4 : i + 8]
        if tag not in _PNG_DROP:
            kept.append(data[i : i + 12 + size])
        i += 12 + size
        if tag == b"IEND":
            break
    return b"".join(kept)


def strip_jpeg(data):
    """The JPEG without camera data, losslessly: the entropy-coded image and its
    tables are copied; APP1 (Exif, XMP), APP3-APP15 (Photoshop/IPTC, ...), COM
    and every APP2 that is not the ICC profile (MPF) are left out, and so is
    anything after the primary image's EOI (an MPF secondary image carries its
    own Exif)."""
    assert data[:2] == b"\xff\xd8"
    kept, i = [b"\xff\xd8"], 2
    while i < len(data):
        if data[i] != 0xFF:
            raise ValueError(f"no marker at {i}")
        marker = data[i + 1]
        if marker == 0xFF:  # fill byte
            i += 1
            continue
        if marker == 0xD9:  # EOI
            kept.append(b"\xff\xd9")
            return b"".join(kept)
        if 0xD0 <= marker <= 0xD7 or marker == 0x01:
            kept.append(data[i : i + 2])
            i += 2
            continue
        size = struct.unpack(">H", data[i + 2 : i + 4])[0]
        seg = data[i : i + 2 + size]
        body = seg[4:]
        drop = (
            marker == 0xE1
            or (0xE3 <= marker <= 0xEF and marker != 0xEE)  # keep APP14 Adobe
            or marker == 0xFE
            or (marker == 0xE2 and not body.startswith(b"ICC_PROFILE\x00"))
        )
        if not drop:
            kept.append(seg)
        i += 2 + size
        if marker == 0xDA:  # entropy-coded data until the next real marker
            j = i
            while j + 1 < len(data):
                if (
                    data[j] == 0xFF
                    and data[j + 1] not in (0x00,)
                    and not (0xD0 <= data[j + 1] <= 0xD7)
                ):
                    break
                j += 1
            kept.append(data[i:j])
            i = j
    raise ValueError("no EOI")


def findings(data):
    """Camera or location data still in the bytes: [] when clean. The container
    is walked segment by segment (as build.py carries_metadata() does), and
    Pillow must see no Exif either."""
    from PIL import Image

    found = []
    if data[:2] == b"\xff\xd8":
        i = 2
        while i + 4 <= len(data) and data[i] == 0xFF:
            marker = data[i + 1]
            if marker == 0xDA:
                break
            size = struct.unpack(">H", data[i + 2 : i + 4])[0]
            body = data[i + 4 : i + 2 + size]
            if marker == 0xE1:
                found.append(
                    "APP1 " + ("Exif" if body.startswith(b"Exif\x00") else "XMP/other")
                )
            elif marker == 0xED:
                found.append("APP13 Photoshop/IPTC")
            elif marker == 0xFE:
                found.append("COM")
            elif marker == 0xE2 and not body.startswith(b"ICC_PROFILE\x00"):
                found.append("APP2 " + body[:4].decode("latin-1"))
            i += 2 + size
        if data.count(b"\xff\xd8\xff") > 1:
            found.append("a second embedded image")
    elif data[:8] == b"\x89PNG\r\n\x1a\n":
        i = 8
        while i + 8 <= len(data):
            size, tag = struct.unpack(">I", data[i : i + 4])[0], data[i + 4 : i + 8]
            if tag in _PNG_DROP:
                found.append(tag.decode())
            i += 12 + size
    im = Image.open(io.BytesIO(data))
    ex = im.getexif()
    if len(ex):
        found.append(f"Pillow Exif tags {sorted(ex)}")
    if ex.get_ifd(0x8825):
        found.append("GPS IFD")
    for key in ("exif", "xmp", "photoshop", "comment", "XML:com.adobe.xmp"):
        if key in im.info:
            found.append(f"info[{key}]")
    return found


def clean_photo(path, want_w, want_h):
    """(bytes, method): the photo as it may be published. Orientation 1 (or
    none): the metadata stripped losslessly and the pixels proved identical.
    Any other orientation: the pixels turned upright by the Exif tag and saved
    again, JPEG quality 95, ICC profile kept, no Exif."""
    from PIL import Image, ImageOps

    data = _read(path)
    im = Image.open(io.BytesIO(data))
    orient = im.getexif().get(0x0112, 1)
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        new, method = strip_png(data), "png chunks stripped, lossless"
    elif orient in (None, 1):
        new, method = strip_jpeg(data), "jpeg segments stripped, lossless"
    else:
        up = ImageOps.exif_transpose(im)
        buf = io.BytesIO()
        keep = (
            {"icc_profile": im.info["icc_profile"]}
            if im.info.get("icc_profile")
            else {}
        )
        up.save(buf, "JPEG", quality=95, subsampling=2, **keep)
        new, method = (
            buf.getvalue(),
            f"turned upright (Exif orientation {orient}), JPEG q95",
        )
    check = Image.open(io.BytesIO(new))
    check.load()
    if method.endswith("lossless"):
        if Image.open(io.BytesIO(data)).tobytes() != check.tobytes():
            raise SystemExit(f"{path}: pixels changed while stripping")
    if check.size != (want_w, want_h):
        raise SystemExit(
            f"{path}: {check.size} after cleaning, the gallery shows {want_w}x{want_h}"
        )
    return new, method


def _mp4_boxes(data):
    """Top-level and moov boxes of an MP4, to show there is no udta/meta box
    (where a phone writes location)."""
    names, i = [], 0
    while i + 8 <= len(data):
        size, kind = (
            struct.unpack(">I", data[i : i + 4])[0],
            data[i + 4 : i + 8].decode("latin-1"),
        )
        head = 8
        if size == 1:
            size, head = struct.unpack(">Q", data[i + 8 : i + 16])[0], 16
        if size < head:
            break
        names.append(kind)
        if kind == "moov":
            j = i + head
            while j + 8 <= i + size:
                s2, k2 = (
                    struct.unpack(">I", data[j : j + 4])[0],
                    data[j + 4 : j + 8].decode("latin-1"),
                )
                names.append("moov/" + k2)
                if k2 == "trak":
                    names.extend("trak/" + n for n in _children(data, j + 8, j + s2))
                j += max(s2, 8)
        i += size
    return names


def _children(data, start, end):
    got, j = [], start
    while j + 8 <= end:
        s, k = (
            struct.unpack(">I", data[j : j + 4])[0],
            data[j + 4 : j + 8].decode("latin-1"),
        )
        got.append(k)
        j += max(s, 8)
    return got


def _gallery_manifest():
    with open(os.path.join(GALLERY_DIR, "manifest.json"), encoding="utf-8") as fh:
        return json.load(fh)


def cmd_gallery():
    m = _gallery_manifest()
    media = _load(out("media.json"), {})
    os.makedirs(out("gallery"), exist_ok=True)
    for it in m["items"]:
        key = f"gallery/{it['order']:02d}"
        ext = os.path.splitext(it["file"])[1].lower()
        name = f"gallery-{it['order']:02d}{ext}"
        if it["type"] == "photo":
            blob, method = clean_photo(
                os.path.join(GALLERY_DIR, it["file"]), it["width"], it["height"]
            )
            left = findings(blob)
            if left:
                raise SystemExit(f"{it['file']}: still carries {left}")
            with open(out("gallery", name), "wb") as fh:
                fh.write(blob)
            mime = "image/png" if ext == ".png" else "image/jpeg"
            extra = {
                "source": it["file"],
                "source_sha256": it["sha256"],
                "method": method,
                "gps_in_source": bool(it.get("gps_in_file")),
                "checked_before_upload": "no Exif, XMP, IPTC, GPS or text chunks",
            }
        else:
            blob = _read(os.path.join(GALLERY_DIR, it["file"]))
            boxes = _mp4_boxes(blob)
            if any(b.endswith(("udta", "meta")) for b in boxes):
                raise SystemExit(
                    f"{it['file']}: has a udta/meta box {boxes}; strip it first"
                )
            mime, method = (
                "video/mp4",
                "original bytes; no udta/meta box (location lives there)",
            )
            extra = {
                "source": it["file"],
                "source_sha256": it["sha256"],
                "method": method,
                "boxes": boxes,
            }
        have = media.get(key)
        if have and have.get("sha256") == _sha(blob):
            continue
        send = upload_resumable if len(blob) > 10_000_000 else upload_bytes
        f = send(blob, name, mime, "/gallery")
        media[key] = _record(f, blob, extra)
        _dump(out("media.json"), media)
        print(f"  up   {key} {name} -> {f['id']} {f.get('operationStatus')} ({method})")
    bad = wait_ready(media, rounds=100)
    print(
        f"media: {len(media)} files, {len(media) - len(bad)} READY"
        + (f", not ready: {bad}" if bad else "")
    )
    # The copies Wix now serves: the original file behind each photo's URL
    for key, rec in sorted(media.items()):
        if (
            not key.startswith("gallery/")
            or rec.get("mediaType") != "IMAGE"
            or rec.get("served")
        ):
            continue
        req = urllib.request.Request(rec["url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=300) as r:
            served = r.read()
        rec["served"] = {
            "bytes": len(served),
            "same_as_uploaded": _sha(served) == rec["sha256"],
            "findings": findings(served),
        }
        _dump(out("media.json"), media)
        print(
            f"  served {key}: identical={rec['served']['same_as_uploaded']} findings={rec['served']['findings']}"
        )


# ------------------------------------------------------------------ documents


def _text(node):
    return preview._text(node)


def _walk(node):
    yield node
    for c in node.get("nodes", []):
        yield from _walk(c)


def _heading(par, level):
    """A bold line the static site reads as a heading, as a HEADING node. The
    converter never colours a heading (emit.color_on_page); neither does this."""
    runs = []
    for t in par.get("nodes", []):
        t = copy.deepcopy(t)
        if t.get("type") == "TEXT":
            decs = t["textData"].get("decorations", [])
            t["textData"]["decorations"] = [d for d in decs if d.get("type") != "COLOR"]
        runs.append(t)
    return {
        "type": "HEADING",
        "id": par["id"],
        "nodes": runs,
        "headingData": {"level": level, "textStyle": {"textAlignment": "AUTO"}},
    }


def _contents(body, label_id):
    """The chapter list under his "Table of Contents" line: each h2, linked to
    its own node (Ricos Link.anchor: the target node id)."""
    items = []
    for k, h in enumerate(
        n for n in body if n["type"] == "HEADING" and n["headingData"]["level"] == 2
    ):
        items.append(
            {
                "type": "LIST_ITEM",
                "id": f"toc{k}",
                "nodes": [
                    {
                        "type": "PARAGRAPH",
                        "id": f"toc{k}p",
                        "nodes": [
                            {
                                "type": "TEXT",
                                "id": "",
                                "nodes": [],
                                "textData": {
                                    "text": _text(h).strip(),
                                    "decorations": [
                                        {
                                            "type": "LINK",
                                            # SELF: the viewer gives a link with no
                                            # target "__blank", a new tab for a jump
                                            "linkData": {"link": {"anchor": h["id"], "target": "SELF"}},
                                        }
                                    ],
                                },
                            }
                        ],
                        "paragraphData": {
                            "textStyle": {"textAlignment": "AUTO"},
                            "indentation": 0,
                        },
                    }
                ],
            }
        )
    body_out = []
    if label_id is None and items:
        # no line of his to hang it on: a "Contents" line and the list open the body
        body_out.append({
            "type": "PARAGRAPH", "id": "toclabel",
            "nodes": [{"type": "TEXT", "id": "", "nodes": [],
                       "textData": {"text": "Contents",
                                    "decorations": [{"type": "BOLD", "fontWeightValue": 700}]}}],
            "paragraphData": {"textStyle": {"textAlignment": "AUTO"}, "indentation": 0}})
        body_out.append({"type": "BULLETED_LIST", "id": "toc", "nodes": items})
    for n in body:
        body_out.append(n)
        if n["id"] == label_id and items:
            body_out.append({"type": "BULLETED_LIST", "id": "toc", "nodes": items})
    return body_out


def _words(nodes):
    return sum(len(_text(n).split()) for n in nodes)


def _long(body):
    """build.page_doc's rule for a contents list: four chapters and 2,000 words."""
    chapters = [n for n in body if n["type"] == "HEADING" and n["headingData"]["level"] == 2]
    return len(chapters) >= 4 and _words(body) >= 2000


def _gapless(body):
    """Put back the grid Word meant, as preview._table reads it. The converter
    flattens a merged cell (Ricos has no colspan): its content stays in the first
    cell and the columns it covered arrive empty. So a row that says nothing
    goes, and a column empty in every row but the spanning ones (a row whose
    only content is its first cell) goes too; a spanning row keeps its first
    cell. Returns the number of tables changed."""
    def full(c):
        return bool(_text(c).strip()) or any(y["type"] == "IMAGE" for y in _walk(c))

    changed = 0
    for n in body:
        for x in _walk(n):
            if x["type"] != "TABLE":
                continue
            rows = [r for r in x.get("nodes", []) if r["type"] == "TABLE_ROW"]
            kept = [i for i, r in enumerate(rows) if any(full(c) for c in r.get("nodes", []))]
            if not kept:
                continue
            width = max(len(rows[i]["nodes"]) for i in kept)
            span = {i: width > 1 and full(rows[i]["nodes"][0])
                    and not any(full(c) for c in rows[i]["nodes"][1:]) for i in kept}
            keep = [j for j in range(width)
                    if any(not span[i] and j < len(rows[i]["nodes"]) and full(rows[i]["nodes"][j])
                           for i in kept)] or [0]
            if len(keep) == width and len(kept) == len(rows):
                continue
            for i in kept:
                cells = rows[i]["nodes"]
                pick = [0] + keep[1:] if span[i] else keep
                rows[i]["nodes"] = [cells[j] for j in pick if j < len(cells)]
            x["nodes"] = [rows[i] for i in kept]
            dims = x.get("tableData", {}).get("dimensions", {})
            for key in ("colsWidthRatio", "colsMinWidth"):
                if dims.get(key):
                    dims[key] = [dims[key][j] for j in keep if j < len(dims[key])]
            if dims.get("rowsHeight"):
                dims["rowsHeight"] = [dims["rowsHeight"][i] for i in kept if i < len(dims["rowsHeight"])]
            changed += 1
    return changed


def _unjustify(body):
    """Set Word's justified text left, and a long centred table column left, the way
    the static page renders them (preview._para, preview._column_align). Returns the
    number of paragraphs changed."""
    changed = 0
    for n in body:
        for x in _walk(n):
            style = (x.get("paragraphData") or x.get("headingData") or {}).get("textStyle")
            if style and style.get("textAlignment") == "JUSTIFY":
                style["textAlignment"] = "AUTO"
                changed += 1
            if x["type"] != "TABLE":
                continue
            rows = [r for r in x.get("nodes", []) if r["type"] == "TABLE_ROW"]
            ncol = max((len(r.get("nodes", [])) for r in rows), default=0)
            for j in range(ncol):
                cells = [r["nodes"][j] for r in rows if j < len(r.get("nodes", []))]
                paras = [p for c in cells for p in c.get("nodes", [])
                         if p["type"] == "PARAGRAPH" and _text(p).strip()]
                centred = [p for p in paras
                           if p["paragraphData"].get("textStyle", {}).get("textAlignment") == "CENTER"]
                if not paras or len(centred) * 2 <= len(paras):
                    continue
                counts = [len(_text(c).split()) for c in cells if _text(c).strip()]
                short = counts and (len(rows) <= 1 or sum(counts) / len(counts) <= 6)
                if not short:
                    for p in centred:
                        p["paragraphData"]["textStyle"]["textAlignment"] = "AUTO"
                        changed += 1
    return changed


def one_address(nodes, where):
    """His Gmail becomes his institutional address, linked, as build.py does for
    the static pages; any other address stops the tool. Returns replacements."""
    swapped = 0

    def fix(parent):
        nonlocal swapped
        new = []
        for n in parent.get("nodes", []):
            if n.get("type") != "TEXT" or not GMAIL.search(n["textData"]["text"]):
                new.append(n)
                continue
            # a link carries no colour of its own (emit.color_on_page): the site styles it
            decs = [
                d
                for d in n["textData"].get("decorations", [])
                if d.get("type") not in ("LINK", "COLOR")
            ]
            text = n["textData"]["text"]
            pos = 0
            for m in GMAIL.finditer(text):
                if m.start() > pos:
                    new.append(
                        _run(
                            text[pos : m.start()], n["textData"].get("decorations", [])
                        )
                    )
                link = {"type": "LINK", "linkData": {"link": {"url": f"mailto:{MAIL}"}}}
                new.append(_run(MAIL, decs + [link]))
                pos, swapped = m.end(), swapped + 1
            if pos < len(text):
                new.append(_run(text[pos:], n["textData"].get("decorations", [])))
        if "nodes" in parent:
            parent["nodes"] = new
        for c in parent.get("nodes", []):
            fix(c)

    for n in nodes:
        fix(n)
    other = set()
    for n in nodes:
        for x in _walk(n):
            if x.get("type") == "TEXT":
                other |= {
                    a.rstrip(".") for a in ADDRESS.findall(x["textData"]["text"])
                } - {MAIL}
    if other:
        raise SystemExit(
            f"{where}: an address the site must not carry: {sorted(other)}"
        )
    return swapped


def _run(text, decs):
    return {
        "type": "TEXT",
        "id": "",
        "nodes": [],
        "textData": {"text": text, "decorations": copy.deepcopy(decs)},
    }


def int_ratios(ws):
    """Word's column shares as whole percentages summing to 100. The live
    validator parses colsWidthRatio as int32: the converter's fractions
    (0.3107) make it fail outright, HTTP 500 "Not an int32 value" (probes).
    Largest remainder, so no column is lost to rounding."""
    total = sum(ws) or 1
    raw = [100 * w / total for w in ws]
    ints = [int(r) for r in raw]
    for i in sorted(range(len(ws)), key=lambda i: raw[i] - ints[i], reverse=True)[
        : 100 - sum(ints)
    ]:
        ints[i] += 1
    return ints


def read_document(slug, media):
    """(fields, body, report) for one converted document."""
    with open(os.path.join(BUILD, slug, "part-01.json"), encoding="utf-8") as fh:
        doc = json.load(fh)
    nodes = doc["nodes"]
    plan = preview.plan(nodes)
    try:
        role, toc = dict(plan["role"]), plan["toc"]
    finally:
        preview.plan([])
    front = {
        r: n for n in nodes for r in [role.get(n["id"], "")] if r.startswith("fm-")
    }

    levels = [n["headingData"]["level"] for n in nodes if n["type"] == "HEADING"]
    shift = 2 - min(levels) if levels else 0
    body, promoted = [], 0
    for n in nodes:
        r = role.get(n["id"], "")
        if r.startswith("fm-"):
            continue
        n = copy.deepcopy(n)
        if n["type"] == "HEADING":
            n["headingData"]["level"] = min(6, n["headingData"]["level"] + shift)
        elif n["type"] == "PARAGRAPH" and r in ("h2", "h3"):
            n, promoted = _heading(n, int(r[1])), promoted + 1
        body.append(n)
    if toc:
        label = next(n["id"] for n in body if role.get(n["id"]) == "toc")
        body = _contents(body, label)
    elif _long(body):
        body = _contents(body, None)
    gapless = _gapless(body)
    unjustified = _unjustify(body)
    swapped = one_address(body, slug)

    missing, used, tables = [], 0, 0
    for n in body:
        for x in _walk(n):
            dims = x.get("tableData", {}).get("dimensions", {})
            if x["type"] == "TABLE" and dims.get("colsWidthRatio"):
                dims["colsWidthRatio"], tables = (
                    int_ratios(dims["colsWidthRatio"]),
                    tables + 1,
                )
            if x["type"] == "IMAGE":
                src = x["imageData"]["image"]["src"]
                # the static page's alt text for a picture no caption describes
                # (build.ALT: the brochure's four diagrams, an equation set as an image)
                alt = site_build.ALT.get(slug, {}).get(os.path.splitext(src["id"])[0])
                if alt:
                    x["imageData"]["altText"] = alt
                got = media.get(f"{slug}/{src['id']}")
                if got:
                    src["id"], used = got["id"], used + 1
                else:
                    missing.append(src["id"])

    title = (
        _text(front["fm-title"]).strip()
        if "fm-title" in front
        else site_build.DOCS[slug][0]
    )
    fields = {
        "title": title,
        "subtitle": _text(front["fm-dek"]).strip() if "fm-dek" in front else "",
        "byline": _text(front["fm-by"]).strip() if "fm-by" in front else "",
        # his running line where he set one ("Machine Learning: The Complete Picture")
        "seoTitle": _text(front["fm-pre"]).strip() if "fm-pre" in front else title,
    }
    art = front.get("fm-art")
    if art:
        name = art["imageData"]["image"]["src"]["id"]
        got = media.get(f"{slug}/{name}")
        if got:
            fields["coverImage"] = (
                f"wix:image://v1/{got['id']}/{name}#originWidth={got['width']}&originHeight={got['height']}"
            )
        else:
            missing.append(name)
    report = {
        "cover": sorted(front),
        "heading_shift": shift,
        "promoted_headings": promoted,
        "contents_list": "his line" if toc else ("top" if any(n["id"] == "toc" for n in body) else ""),
        "unjustified": unjustified,
        "tables_regridded": gapless,
        "images": used,
        "missing_images": missing,
        "tables_ratio_to_int": tables,
        "gmail_replaced": swapped,
    }
    body = {
        "nodes": body,
        "metadata": doc.get("metadata", {"version": 1}),
        "documentStyle": doc.get("documentStyle", {}),
    }
    return fields, body, report


def documents(media):
    items = []
    for order, slug in enumerate(site_build.DOCS, 1):
        fields, body, report = read_document(slug, media)
        data = {
            "title": fields["title"],
            "slug": CMS_SLUG.get(slug, slug),
            "order": order,
            "subtitle": fields["subtitle"],
            "byline": fields["byline"],
            "summary": site_build.DOCS[slug][1],
            "navLabel": site_build.DOC_LABELS[slug],
            "seoTitle": fields["seoTitle"],
            "sourceFile": site_build.SRC_DOCX[slug],
            "coverImage": fields.get("coverImage", ""),
            "body": body,
        }
        word = media.get(f"word/{slug}")
        if word:
            data["wordFile"] = word["url"]
        data = {k: v for k, v in data.items() if v not in ("", None)}
        items.append((data["slug"], data, report))
    return items


# ------------------------------------------------------------------ topics


def _p(*runs, align="AUTO"):
    return {
        "type": "PARAGRAPH",
        "nodes": [
            {
                "type": "TEXT",
                "id": "",
                "nodes": [],
                "textData": {
                    "text": t,
                    "decorations": [{"type": "BOLD", "fontWeightValue": 700}]
                    if b
                    else [],
                },
            }
            for t, b in runs
        ],
        "paragraphData": {"textStyle": {"textAlignment": align}, "indentation": 0},
    }


def _h2(text):
    return {
        "type": "HEADING",
        "nodes": [
            {
                "type": "TEXT",
                "id": "",
                "nodes": [],
                "textData": {"text": text, "decorations": []},
            }
        ],
        "headingData": {"level": 2, "textStyle": {"textAlignment": "AUTO"}},
    }


PENDING_LEARN = (
    "A recommended learning path, based on my own route into the subject: "
    "what to read in what order, and what can safely wait."
)
PENDING_BOOKS = (
    "The books I found most useful, in the sense that they carry the most "
    "complete and the clearest explanations of the topic."
)

# The three topic pages as build.py main() and parts/topics.py write them. "own"
# is a section his guide already has, under his own heading.
TOPICS = [
    {
        "slug": "vibrations-waves",
        "title": "Vibrations and Waves",
        "navLabel": "Vibrations and Waves",
        "cardTitle": "Vibrations and Waves",
        "cardText": "Wave propagation and dynamics: the mechanics and physics side of my research.",
        "lede": (
            "The mechanics and physics side of my research: wave propagation and dynamics. "
            "This section is written for newcomers: the overall picture, the intuition, and "
            "how the topic connects to signal processing and machine learning."
        ),
        "guide": "dynamical-behavior-of-engineering-structures-and-acoustic-wave-propagation",
        "big": (
            "When vibration and wave methods are used, what problems they solve, where the "
            "same ideas resurface across applications, and how they connect to the data "
            "side of structural health monitoring."
        ),
        "own": {"books": "Recommended Books"},
    },
    {
        "slug": "signal-processing",
        "title": "Signal Processing, System Identification, Estimation, Optimization",
        "navLabel": "Signal Processing,\nSystem Identification,\nEstimation, Optimization",
        "cardTitle": "Signal Processing & Optimization",
        "cardText": "Signal processing, system identification, estimation and optimization: the data side.",
        "lede": "The data side: how measurements become answers.",
        "guide": "signal-processing-system-identification-and-optimization",
        "big": (
            "How a measured signal becomes an answer: what each method is for, which problem "
            "it solves, and why estimation and optimization keep reappearing under different "
            "names."
        ),
        "own": {"books": "The Books"},
    },
    {
        "slug": "machine-learning",
        "title": "Machine Learning",
        "navLabel": "Machine Learning",
        "cardTitle": "Machine Learning",
        "cardText": "AI methods for structural health monitoring, NDT and sound target analysis.",
        "lede": "Machine learning for newcomers: the big picture, with no equations.",
        "guide": "machine-learning-the-complete-picture-and-guide-5",
        "big": "Which model suits which problem, and what each method learns.",
        "own": {
            "learn": "12. How to Learn Machine Learning",
            "books": "Go Deeper With Books",
        },
    },
]


def _doc_heading_id(slug, text):
    """The id of the H2 called `text` in a document's saved body (the viewer draws
    it as id="viewer-<id>", which a link's #fragment can reach)."""
    body = (_load(out("validate", f"Documents-{slug}.json"), {}) or {}).get("sent") or {}
    for n in body.get("nodes", []):
        if n.get("type") == "HEADING" and _text(n).strip() == text.strip():
            return n["id"]
    return None


def _pending(text):
    """A section still in preparation, as the static page's left-ruled block: a
    quote block (one paragraph, the only child Ricos allows) holding the tag in
    bold and the sentence; global.css sets the tag on a line of its own."""
    return {"type": "BLOCKQUOTE", "nodes": [_p(("In preparation ", True), (text, False))],
            "blockquoteData": {"indentation": 0}}


def _row(heading, url, note):
    """The static page's row: his heading, linked to where it is in his guide, and
    the guide's title under it; a one-item list (global.css draws the row)."""
    link = {"type": "LINK", "linkData": {"link": {"url": url, "target": "SELF"}}}
    first = _p((heading, False))
    first["nodes"][0]["textData"]["decorations"] = [link]
    return {"type": "BULLETED_LIST", "nodes": [{"type": "LIST_ITEM", "nodes": [first, _p((note, False))]}]}


def _ids(nodes, prefix):
    """Ids for the nodes nested in a list or a quote (TEXT nodes keep "")."""
    k = 0
    for top in nodes:
        stack = list(top.get("nodes", []))
        while stack:
            n = stack.pop(0)
            if n.get("type") != "TEXT" and not n.get("id"):
                n["id"] = f"{top['id']}c{k}"
                k += 1
            stack.extend(n.get("nodes", []))


def topics():
    items = []
    for order, t in enumerate(TOPICS, 1):
        guide_title = site_build.DOCS[t["guide"]][0]
        guide_slug = CMS_SLUG.get(t["guide"], t["guide"])

        def section(key, pending, t=t, guide_title=guide_title, guide_slug=guide_slug):
            if key in t["own"]:
                # his heading, and where it is in his guide (/doc/<slug>#viewer-<id>)
                hid = _doc_heading_id(guide_slug, t["own"][key])
                url = f"/doc/{guide_slug}" + (f"#viewer-{hid}" if hid else "")
                return [_row(t["own"][key], url, guide_title)]
            return [_pending(pending)]

        nodes = (
            [
                _h2("The big picture"),
                _pending(t["big"]),
            ]
            + [_h2("How to learn this topic")]
            + section("learn", PENDING_LEARN)
            + [_h2("Recommended books & resources")]
            + section("books", PENDING_BOOKS)
        )
        for k, n in enumerate(nodes):
            n["id"] = f"t{order}n{k}"
        _ids(nodes, f"t{order}")
        one_address(nodes, t["slug"])
        data = {
            "title": t["title"],
            "slug": t["slug"],
            "order": order,
            "navLabel": t["navLabel"],
            "cardTitle": t["cardTitle"],
            "cardText": t["cardText"],
            "lede": t["lede"],
            "guide": CMS_SLUG.get(t["guide"], t["guide"]),
            "body": {"nodes": nodes, "metadata": {"version": 1}, "documentStyle": {}},
        }
        items.append((t["slug"], data, {}))
    return items


# ------------------------------------------------------------------ gallery items


def _image_url(mid, name, w, h):
    return f"wix:image://v1/{mid}/{urllib.parse.quote(name)}#originWidth={w}&originHeight={h}"


def _video_url(rec, it):
    """wix:video:// URL of the site's own copy (the documented CMS format)."""
    vid = rec["id"]
    posters = (
        (rec.get("descriptor") or {}).get("media", {}).get("video", {}) or {}
    ).get("posters") or []
    if posters:
        p = posters[0]
        poster, pw, ph = (
            p.get("id") or p.get("url", "").rsplit("/", 1)[-1],
            p.get("width"),
            p.get("height"),
        )
    else:
        poster, pw, ph = f"{vid}f000.jpg", it["poster"]["width"], it["poster"]["height"]
    return f"wix:video://v1/{vid}/video.mp4#posterUri={poster}&posterWidth={pw}&posterHeight={ph}"


def _sets():
    """The sets as the static Gallery shows them: a set that repeats an earlier
    set's files (repeat_of) is left out, as parts/gallery.py does."""
    m = _gallery_manifest()
    order = {}
    for s in m["sets"]:
        if not s.get("repeat_of"):
            order[s["order"]] = len(order) + 1
    for s in m["sets"]:
        if s.get("repeat_of"):
            order[s["order"]] = order[s["repeat_of"]]
    return m, order


def gallery_items(media):
    """GallerySets: one item per set, its photos in the media field. On the
    duplicate the photos are the live site's own files, copied with the site;
    on another site, the cleaned copies this tool uploaded (cmd_gallery)."""
    m, set_no = _sets()
    by_order = {i["order"]: i for i in m["items"]}
    own = S["name"] == "dup"
    items = []
    for s in (s for s in m["sets"] if not s.get("repeat_of")):
        lines = s["lines"]
        period = lines[-1] if lines[-1].startswith("(") else ""
        caption = "\n".join(lines[:-1] if period else lines)
        entries = []
        for k in s["items"]:
            it = by_order[k]
            rec = None if own else media.get(f"gallery/{k:02d}")
            if not own and not rec:
                raise SystemExit(f"gallery item {k} not uploaded: run gallery first")
            if it["type"] == "photo":
                if own:
                    src = _image_url(
                        it["wix_id"],
                        it.get("upload_name") or it["wix_id"],
                        it["width"],
                        it["height"],
                    )
                else:
                    src = _image_url(
                        rec["id"],
                        os.path.basename(rec["id"]),
                        it["width"],
                        it["height"],
                    )
                entries.append(
                    {"type": "image", "title": "", "description": "", "src": src}
                )
            else:
                if own:
                    p = it["poster"]
                    src = (
                        f"wix:video://v1/{it['wix_id']}/video.mp4#posterUri={it['wix_id']}f000.jpg"
                        f"&posterWidth={p['width']}&posterHeight={p['height']}"
                    )
                else:
                    src = _video_url(rec, it)
                entries.append(
                    {"type": "video", "title": "", "description": "", "src": src}
                )
        no = set_no[s["order"]]
        data = {"title": caption, "period": period, "order": no, "media": entries}
        items.append((f"set-{no:02d}", data, {}))
    return items


def photo_items(media):
    """Photos: one item per photo or film, in the live page's order, each
    pointing at its set; its caption is the set's caption, his words."""
    m, set_no = _sets()
    captions = {}
    for s in m["sets"]:
        if not s.get("repeat_of"):
            lines = s["lines"]
            captions[set_no[s["order"]]] = "\n".join(
                lines[:-1] if lines[-1].startswith("(") else lines
            )
    items = []
    for it in m["items"]:
        rec = media.get(f"gallery/{it['order']:02d}")
        if not rec:
            raise SystemExit(
                f"gallery item {it['order']} not uploaded: run gallery first"
            )
        no = set_no[it["set"]]
        data = {"title": captions[no], "set": f"set-{no:02d}", "order": it["order"]}
        if it["type"] == "photo":
            data["image"] = _image_url(
                rec["id"], os.path.basename(rec["id"]), it["width"], it["height"]
            )
        else:
            data["video"] = _video_url(rec, it)
        items.append((f"photo-{it['order']:02d}", data, {}))
    return items


def cms_items(media):
    """(collection, items) in dependency order: a referenced item is saved first."""
    got = [
        ("Documents", documents(media)),
        ("Topics", topics()),
        ("GallerySets", gallery_items(media)),
    ]
    if "Photos" in COLLECTIONS[S["name"]]:
        got.append(("Photos", photo_items(media)))
    if S.get("only"):
        got = [(c, items) for c, items in got if c in S["only"]]
    return got


# ------------------------------------------------------------------ validation


def validate(doc, plugins=PLUGINS):
    return call(
        "POST",
        "/ricos/v1/ricos-document/validate",
        {"document": doc, "plugins": plugins, "fixDocument": True},
    )


def diff(a, b, path="", found=None, limit=100000):
    """Where the validator's validDocument differs from what we sent."""
    found = [] if found is None else found
    if len(found) >= limit:
        return found
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in b:
                found.append(
                    f"{path}.{k}: dropped (was {json.dumps(a[k], ensure_ascii=False)[:90]})"
                )
            elif k not in a:
                found.append(
                    f"{path}.{k}: added {json.dumps(b[k], ensure_ascii=False)[:90]}"
                )
            else:
                diff(a[k], b[k], f"{path}.{k}", found, limit)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            found.append(f"{path}: length {len(a)} -> {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            diff(x, y, f"{path}[{i}]", found, limit)
    elif a != b:
        found.append(
            f"{path}: {json.dumps(a, ensure_ascii=False)[:60]} -> {json.dumps(b, ensure_ascii=False)[:60]}"
        )
    return found


# the defaults validDocument adds to every table and link: listed apart
_DEFAULTS = (
    "cellPadding: added []",
    "colsMinWidth: added []",
    "rowsHeight: added []",
    'target: added "SELF"',
)


def _summ(name, doc, got):
    d = diff(doc, got.get("validDocument", {}))
    quiet = [x for x in d if x.endswith(_DEFAULTS)]
    return {
        "name": name,
        "valid": got.get("valid"),
        "violations": got.get("violations", []),
        "changes": [x for x in d if x not in quiet],
        "default_fields_added": len(quiet),
    }


def cmd_validate():
    media = _load(out("media.json"), {})
    report = []
    for coll, items in cms_items(media):
        for iid, data, rep in items:
            if "body" not in data:
                continue
            got = validate(data["body"])
            _dump(
                out("validate", f"{coll}-{iid}.json"),
                {"sent": data["body"], "answer": got},
            )
            s = _summ(f"{coll}/{iid}", data["body"], got)
            s.update(bytes=nbytes(data), **rep)
            report.append(s)
            print(
                f"  {s['name']}: valid={s['valid']} violations={len(s['violations'])} "
                f"changes={len(s['changes'])} bytes={s['bytes']}"
            )
    # with --only, keep the other collections' earlier answers in the report
    done = {s["name"] for s in report}
    keep = [s for s in _load(out("validate", "report.json"), []) if s["name"] not in done]
    _dump(out("validate", "report.json"), keep + report)


# One node shape per probe, each checked alone so an answer is about that shape.
def _probe_docs(img_id):
    def run(text, decs):
        return {
            "type": "TEXT",
            "id": "",
            "nodes": [],
            "textData": {"text": text, "decorations": decs},
        }

    def para(pid, *runs):
        return {
            "type": "PARAGRAPH",
            "id": pid,
            "nodes": list(runs),
            "paragraphData": {"textStyle": {"textAlignment": "AUTO"}, "indentation": 0},
        }

    def cell(cid, t):
        return {
            "type": "TABLE_CELL",
            "id": cid,
            "nodes": [para(cid + "p", run(t, []))],
            "tableCellData": {},
        }

    def table(ratio):
        return {
            "type": "TABLE",
            "id": "t1",
            "nodes": [
                {
                    "type": "TABLE_ROW",
                    "id": "r1",
                    "nodes": [cell("c1", "a"), cell("c2", "b")],
                },
                {
                    "type": "TABLE_ROW",
                    "id": "r2",
                    "nodes": [cell("c3", "c"), cell("c4", "d")],
                },
            ],
            "tableData": {"rowHeader": True, "dimensions": {"colsWidthRatio": ratio}},
        }

    head = {
        "type": "HEADING",
        "id": "h1",
        "nodes": [run("Target heading", [])],
        "headingData": {"level": 2, "textStyle": {"textAlignment": "AUTO"}},
    }
    color = {"type": "COLOR", "colorData": {"foreground": "#7a0000"}}
    marked = {
        "type": "COLOR",
        "colorData": {"foreground": "#7a0000", "background": "#ffff00"},
    }
    divider = {
        "type": "DIVIDER",
        "id": "d1",
        "nodes": [],
        "dividerData": {"lineStyle": "SINGLE", "width": "LARGE", "alignment": "CENTER"},
    }
    image = {
        "type": "IMAGE",
        "id": "i1",
        "nodes": [],
        "imageData": {
            "containerData": {
                "width": {"custom": "50"},
                "alignment": "CENTER",
                "textWrap": True,
            },
            "image": {"src": {"id": img_id}, "width": 163, "height": 163},
        },
    }
    return {
        "COLOR (foreground)": ([para("p1", run("red words", [color]))], "TEXT_COLOR"),
        "COLOR (foreground + background)": (
            [para("p1", run("marked words", [marked]))],
            "TEXT_HIGHLIGHT",
        ),
        "DIVIDER": (
            [para("p1", run("above", [])), divider, para("p2", run("below", []))],
            "DIVIDER",
        ),
        "STRIKETHROUGH": (
            [
                para(
                    "p1",
                    run(
                        "struck words",
                        [{"type": "STRIKETHROUGH", "strikethroughData": True}],
                    ),
                )
            ],
            None,
        ),
        "IMAGE containerData.width.custom": ([image], "IMAGE"),
        "TABLE tableData.dimensions.colsWidthRatio (fractions, as emitted)": (
            [table([0.3107, 0.6893])],
            "TABLE",
        ),
        "TABLE tableData.dimensions.colsWidthRatio (integers)": (
            [table([31, 69])],
            "TABLE",
        ),
        "LINK link.anchor (contents list)": (
            [
                para(
                    "p1",
                    run(
                        "go to heading",
                        [{"type": "LINK", "linkData": {"link": {"anchor": "h1"}}}],
                    ),
                ),
                head,
            ],
            "LINK",
        ),
        "SUPERSCRIPT (not used by the converter)": (
            [
                para(
                    "p1",
                    run("10", []),
                    run("6", [{"type": "SUPERSCRIPT", "superscriptData": True}]),
                )
            ],
            None,
        ),
    }


def _ask(doc, plugins=PLUGINS):
    """The validator's answer, or the error it raised instead of answering."""
    try:
        return validate(doc, plugins)
    except WixError as e:
        return {"error": str(e)[:600]}


def to_html(doc):
    """How Wix itself renders the shape: Convert From Ricos, target HTML."""
    try:
        return call(
            "POST",
            "/ricos/v1/ricos-document/convert/from-ricos",
            {"document": doc, "targetFormat": "HTML"},
        ).get("html", "")
    except WixError as e:
        return f"error: {str(e)[:300]}"


def cmd_probe():
    media = _load(out("media.json"), {})
    img = next(
        (
            v["id"]
            for k, v in media.items()
            if v.get("mediaType", "IMAGE") == "IMAGE" and "/" in k
        ),
        "image1.png",
    )
    found = []
    for name, (nodes, plugin) in _probe_docs(img).items():
        doc = {"nodes": nodes, "metadata": {"version": 1}, "documentStyle": {}}
        got = _ask(doc)
        s = (
            _summ(name, doc, got)
            if "error" not in got
            else {"name": name, "error": got["error"]}
        )
        if plugin:  # the same document with the shape's own plugin taken out
            without = _ask(doc, [p for p in PLUGINS if p != plugin])
            s["without_plugin"] = (
                {"plugin_removed": plugin, "error": without["error"]}
                if "error" in without
                else {
                    "plugin_removed": plugin,
                    "valid": without.get("valid"),
                    "violations": without.get("violations", []),
                    "changes": _summ(name, doc, without)["changes"],
                }
            )
        s["html"] = to_html(doc)[:700]
        found.append(s)
        print(json.dumps(s, ensure_ascii=False)[:1400])
    _dump(out("validate", "probes.json"), found)


# ------------------------------------------------------------------ save


def cmd_plan():
    media = _load(out("media.json"), {})
    for coll, items in cms_items(media):
        for iid, data, rep in items:
            size = nbytes(data)
            print(
                f"  {coll}/{iid}: {size:,} bytes ({size / LIMIT:.1%})"
                + (f" {rep}" if rep else "")
            )


def cmd_save():
    media = _load(out("media.json"), {})
    checks = {s["name"]: s for s in _load(out("validate", "report.json"), [])}
    log = []
    for coll, items in cms_items(media):
        for iid, data, rep in items:
            if "body" in data:
                s = checks.get(f"{coll}/{iid}")
                if not s:
                    raise SystemExit(
                        f"{coll}/{iid}: not validated yet, run validate first"
                    )
                if not s["valid"]:
                    raise SystemExit(
                        f"{coll}/{iid}: the validator rejected it: {s['violations']}"
                    )
                if rep.get("missing_images"):
                    raise SystemExit(
                        f"{coll}/{iid}: images not uploaded: {rep['missing_images']}"
                    )
                if diff(
                    data["body"],
                    _load(out("validate", f"{coll}-{iid}.json"), {}).get("sent"),
                ):
                    raise SystemExit(
                        f"{coll}/{iid}: changed since it was validated, run validate again"
                    )
            if nbytes(data) >= LIMIT:
                raise SystemExit(
                    f"{coll}/{iid}: {nbytes(data):,} bytes, over the item limit"
                )
            got = call(
                "POST",
                "/wix-data/v2/items/save",
                {"dataCollectionId": coll, "dataItem": {"id": iid, "data": data}},
            )
            _dump(out("items", f"{coll}-{iid}.json"), data)
            log.append(
                {
                    "collection": coll,
                    "id": iid,
                    "action": got.get("action"),
                    "bytes": nbytes(data),
                }
            )
            print(f"  {coll}/{iid}: {got.get('action')} ({nbytes(data):,} bytes)")
    _dump(out("save.json"), log)
    # read every item back and compare it with what was sent
    for coll, items in cms_items(media):
        for iid, data, _rep in items:
            stored = call(
                "GET",
                f"/wix-data/v2/items/{urllib.parse.quote(iid)}?dataCollectionId={coll}",
            )["dataItem"]["data"]
            stored = {
                k: v for k, v in stored.items() if not k.startswith(("_", "link-"))
            }
            d = diff(data, stored)
            print(f"  read back {coll}/{iid}: {'identical' if not d else d[:3]}")


# ------------------------------------------------------------------ blog


def _posts():
    got = []
    for name in sorted(os.listdir(BLOG_DIR)):
        path = os.path.join(BLOG_DIR, name, "post.json")
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                got.append(json.load(fh))
    return got


def blog_bodies(media):
    """Each post's Ricos with the site's own media ids: its pictures, and the Word
    attachment of the wind turbine review (audited like the three: no address,
    no comments, no tracked changes)."""
    got = []
    for post in _posts():
        slug, body = post["slug"], copy.deepcopy(post["body"])
        by_node = {i["node"]: i for i in post["images"]}
        files = {f["node"]: f for f in post.get("files", [])}
        missing = []
        for n in body["nodes"]:
            for x in _walk(n):
                if x["type"] == "IMAGE":
                    rec = media.get(f"blog/{slug}/{by_node[x['id']]['file']}")
                    if rec:
                        x["imageData"]["image"]["src"]["id"] = rec["id"]
                    else:
                        missing.append(x["id"])
                elif x["type"] == "FILE":
                    rec = media.get(f"blog/{slug}/{files[x['id']]['file']}")
                    if rec:
                        x["fileData"]["src"]["id"] = rec["id"]
                        x["fileData"]["path"] = rec["id"]
                        x["fileData"]["size"] = rec["bytes"]
                    else:
                        missing.append(x["id"])
        one_address(body["nodes"], slug)
        got.append((post, body, missing))
    return got


def cmd_blog():
    media = _load(out("media.json"), {})
    # 1. the pictures and the attachment
    for post in _posts():
        slug = post["slug"]
        jobs = [(i["file"], i["file"]) for i in post["images"]]
        jobs += [(f["file"], f["name"]) for f in post.get("files", [])]
        for fname, shown in jobs:
            key = f"blog/{slug}/{fname}"
            blob = _read(os.path.join(BLOG_DIR, slug, fname))
            have = media.get(key)
            if have and have.get("sha256") == _sha(blob):
                continue
            ext = os.path.splitext(fname)[1].lower()
            mime = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".docx": WORD_MIME,
            }[ext]
            f = upload_bytes(blob, shown, mime, f"/blog/{slug[:90]}")
            media[key] = _record(f, blob)
            _dump(out("media.json"), media)
            print(f"  up   {key} -> {f['id']}")
    bad = wait_ready(media)
    if bad:
        raise SystemExit(f"not ready: {bad}")
    # 2. the posts: validated, then created and published together
    state = _load(out("blog.json"), {})
    member = call("GET", "/members/v1/members?paging.limit=100")["members"]
    if OWNER not in {x["id"] for x in member}:
        raise SystemExit(f"the owner {OWNER} is not a member of this site")
    todo = []
    for post, body, missing in blog_bodies(media):
        slug = post["slug"]
        if missing:
            raise SystemExit(f"{slug}: media not uploaded for nodes {missing}")
        got = validate(body, BLOG_PLUGINS)
        _dump(out("validate", f"Blog-{slug}.json"), {"sent": body, "answer": got})
        s = _summ(f"Blog/{slug}", body, got)
        print(
            f"  Blog/{slug}: valid={s['valid']} violations={len(s['violations'])} changes={len(s['changes'])}"
        )
        if not s["valid"] and all(
            v["message"] == "FILE is not supported" for v in s["violations"]
        ):
            # The validator knows no FILE node, whatever plugins it is given: it
            # refuses the live blog's own node the same way. The node is his
            # post's, only its file id is this site's; everything else in the
            # body must still validate clean.
            rest = dict(body, nodes=[n for n in body["nodes"] if n["type"] != "FILE"])
            s = _summ(
                f"Blog/{slug} without its FILE node", rest, validate(rest, BLOG_PLUGINS)
            )
            print(
                f"    without the FILE node: valid={s['valid']} violations={len(s['violations'])}"
            )
            state.setdefault(slug, {})["validator"] = (
                "FILE node not supported by the validator; rest valid"
            )
        if not s["valid"]:
            raise SystemExit(f"{slug}: {s['violations']}")
        try:
            have = call("GET", f"/blog/v3/posts/slugs/{urllib.parse.quote(slug)}")[
                "post"
            ]
        except WixError as e:
            if "404" not in str(e):
                raise
            have = None
        if have:
            state[slug] = {
                "id": have["id"],
                "note": "already on the site, not created again",
            }
            continue
        todo.append(
            {
                "title": post["title"],
                "memberId": OWNER,
                "richContent": body,
                "seoSlug": slug,
                "firstPublishedDate": post["published"],
                "media": {"displayed": True, "custom": False},
            }
        )
    if todo:
        dropped = []
        while True:
            try:
                got = call(
                    "POST",
                    "/blog/v3/bulk/draft-posts/create",
                    {"draftPosts": todo, "publish": True},
                )
                break
            except WixError as e:
                # an optional field the API refuses is left out, and the report says so
                field = next(
                    (
                        f
                        for f in ("media", "firstPublishedDate", "seoSlug")
                        if f.lower() in str(e).lower()
                    ),
                    None,
                )
                if not field or field in dropped:
                    raise
                print(f"  {field} refused ({str(e)[:300]}); creating without it")
                dropped.append(field)
                for d in todo:
                    d.pop(field, None)
        state["_dropped_fields"] = dropped
        for r in got.get("results", []):
            meta = r.get("itemMetadata", {})
            slug = todo[meta.get("originalIndex", 0)]["seoSlug"]
            state[slug] = {
                "draft_id": meta.get("id"),
                "success": meta.get("success"),
                "error": meta.get("error"),
            }
            print(
                f"  created {slug}: success={meta.get('success')} {meta.get('error') or ''}"
            )
        _dump(out("blog.json"), state)
    # 3. read back what was published
    for post in _posts():
        slug = post["slug"]
        try:
            p = call(
                "GET", f"/blog/v3/posts/slugs/{urllib.parse.quote(slug)}?fieldsets=URL"
            )["post"]
        except WixError as e:
            # the slug did not hold: find the post by its title instead
            found = call(
                "POST",
                "/blog/v3/posts/query",
                {"query": {"filter": {"title": {"$startsWith": post["title"]}}}},
            )
            if not found.get("posts"):
                state.setdefault(slug, {})["read_back"] = str(e)[:300]
                print(f"  !! {slug}: {str(e)[:200]}")
                continue
            p = found["posts"][0]
        state.setdefault(slug, {}).update(
            id=p["id"],
            slug=p["slug"],
            firstPublishedDate=p.get("firstPublishedDate"),
            wanted_date=post["published"],
            url=(p.get("url") or {}),
            memberId=p.get("memberId"),
        )
        print(
            f"  post {slug}: id={p['id']} first published {p.get('firstPublishedDate')} (live {post['published']})"
        )
    _dump(out("blog.json"), state)


# ------------------------------------------------------------------ counts, report


def cmd_counts():
    media = _load(out("media.json"), {})
    counts = {"items": {}, "media": {}, "blog": {}}
    for cid in COLLECTIONS[S["name"]]:
        counts["items"][cid] = call(
            "POST", "/wix-data/v2/items/count", {"dataCollectionId": cid}
        ).get("totalCount")
    folders = {}
    for key, rec in media.items():
        group = (
            key.split("/")[0]
            if key.split("/")[0] in ("word", "gallery", "blog")
            else "documents"
        )
        folders.setdefault(group, {"files": 0, "ready": 0, "folder_ids": set()})
        folders[group]["files"] += 1
        folders[group]["ready"] += rec.get("status") == "READY"
        folders[group]["folder_ids"].add(rec.get("folder"))
    for group, v in folders.items():
        on_site = 0
        for fid in v["folder_ids"]:
            if not fid:
                continue
            listed = call(
                "GET",
                f"/site-media/v1/files?parentFolderId={urllib.parse.quote(fid)}&paging.limit=100",
            )
            on_site += len(listed.get("files", []))
        counts["media"][group] = {
            "uploaded": v["files"],
            "ready": v["ready"],
            "listed_in_their_folders": on_site,
        }
    if S["name"] == "studio":
        posts = call(
            "POST", "/blog/v3/posts/query", {"query": {"paging": {"limit": 100}}}
        )
        counts["blog"] = {
            "published_posts": len(posts.get("posts", [])),
            "slugs": sorted(p["slug"] for p in posts.get("posts", [])),
        }
    _dump(out("counts.json"), counts)
    print(json.dumps(counts, indent=1))


def cmd_report():
    """build/wix/<site>/REPORT.md: what the site holds, read back from it, for
    whoever binds the pages to it. Every field key and type comes from the
    site's own schema, not from SCHEMAS."""
    sid, name = _site(), S["name"]
    media = _load(out("media.json"), {})
    counts = _load(out("counts.json"), {})
    blog = _load(out("blog.json"), {})
    usage = call(
        "GET", "/wix-data/v1/site-data-usage/v1/site-data-usage?consistentRead=true"
    )["siteDataUsage"]
    dash = f"https://manage.wix.com/dashboard/{sid}"
    lines = [
        f"# {name}: content report",
        "",
        f"Site `{sid}`, generated {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())} by `python tools/wix_import.py --site {name} report`.",
        "The site is not published and has no domain; nothing here publishes it.",
        "",
        "Links:",
        f"- Editor: https://manage.wix.com/editor/{sid}",
        f"- CMS: {dash}/wix-cms",
        f"- Blog posts: {dash}/blog/posts",
        "",
        "## Collections",
        "",
        "Permissions on every collection: read Anyone; insert, update, remove Admin. Site sort: `order` ascending.",
        f"Data sits in the LIVE environment: {usage['totalUsedLive'].get('items')} items, "
        f"{usage['totalUsedLive'].get('bytes')} bytes; SANDBOX {usage['totalUsedSandbox'].get('items', '0')} items.",
    ]
    for cid in COLLECTIONS[name]:
        col = call("GET", f"/wix-data/v2/collections/{cid}")["collection"]
        ids = sorted(
            i["id"]
            for i in call(
                "POST",
                "/wix-data/v2/items/query",
                {"dataCollectionId": cid, "query": {"paging": {"limit": 100}}},
            )["dataItems"]
        )
        lines += [
            "",
            f'### `{cid}` (shown as "{col["displayName"]}"): {len(ids)} items',
            "",
            f"CMS: {dash}/wix-cms/data/{cid}. Display field: `{col.get('displayField')}`.",
            "",
            "| key | type | label | note |",
            "|---|---|---|---|",
        ]
        for f in col["fields"]:
            ref = ((f.get("typeMetadata") or {}).get("reference") or {}).get(
                "referencedCollectionId"
            )
            note = (
                f"references `{ref}`"
                if ref
                else (
                    "system" if f.get("systemField") else (f.get("description") or "")
                )
            )
            lines.append(
                f"| `{f['key']}` | {f['type']} | {f['displayName']} | {note} |"
            )
        lines += ["", "Item ids: " + ", ".join(f"`{i}`" for i in ids)]
    groups = {}
    for key, rec in media.items():
        g = (
            key.split("/")[0]
            if key.split("/")[0] in ("word", "gallery", "blog")
            else "documents"
        )
        groups.setdefault(g, []).append(rec)
    lines += ["", "## Media Manager", "", "| folder | files | READY |", "|---|---|---|"]
    where = {
        "documents": "/documents/<slug>",
        "word": "/documents/word",
        "gallery": "/gallery",
        "blog": "/blog/<post slug>",
    }
    for g, recs in sorted(groups.items()):
        lines.append(
            f"| `{where[g]}` | {len(recs)} | {sum(r.get('status') == 'READY' for r in recs)} |"
        )
    lines.append(
        f"| total | {len(media)} | {sum(r.get('status') == 'READY' for r in media.values())} |"
    )
    if blog:
        lines += [
            "",
            "## Blog posts (published)",
            "",
            "| slug | post id | first published | path |",
            "|---|---|---|---|",
        ]
        for slug, rec in sorted(blog.items()):
            if slug.startswith("_"):
                continue
            live = call("GET", f"/blog/v3/posts/{rec['id']}?fieldsets=URL")["post"]
            path = (live.get("url") or {}).get("path", "")
            lines.append(
                f"| `{slug}` | `{rec.get('id')}` | {rec.get('firstPublishedDate')} | {path} |"
            )
    lines += [
        "",
        "## Counts read back",
        "",
        "```json",
        json.dumps(counts, indent=1),
        "```",
        "",
    ]
    notes = out("notes.md")  # written by hand: what the numbers do not say
    if os.path.isfile(notes):
        with open(notes, encoding="utf-8") as fh:
            lines += ["", fh.read()]
    with open(out("REPORT.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(out("REPORT.md"))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--site", required=True, choices=sorted(SITES))
    ap.add_argument(
        "command",
        choices=[
            "plan",
            "collections",
            "media",
            "gallery",
            "probe",
            "validate",
            "save",
            "blog",
            "counts",
            "report",
        ],
    )
    ap.add_argument("--only", nargs="*", default=None,
                    help="validate/save only these collections (e.g. --only Documents)")
    args = ap.parse_args()
    S.update(
        name=args.site,
        id=SITES[args.site],
        out=os.path.join(ROOT, "build", "wix", args.site),
        only=args.only,
    )
    _site()
    {
        "plan": cmd_plan,
        "collections": cmd_collections,
        "media": cmd_media,
        "gallery": cmd_gallery,
        "probe": cmd_probe,
        "validate": cmd_validate,
        "save": cmd_save,
        "blog": cmd_blog,
        "counts": cmd_counts,
        "report": cmd_report,
    }[args.command]()


if __name__ == "__main__":
    main()
