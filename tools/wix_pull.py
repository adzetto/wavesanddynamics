"""Copy the live Gallery and Blog of wavesanddata.com into content/, read only.

    python tools/wix_pull.py             both
    python tools/wix_pull.py gallery     content/gallery/: photos, video, manifest.json
    python tools/wix_pull.py blog        content/blog/<slug>/: post.json and its media,
                                         and content/blog/posts.json, the index

The live site is the source. Nothing here writes to Wix; every request is one
the public site itself makes (the one POST is the blog's own post query).

Gallery. The page is ten Wix sections. A section is a grid: each row holds one
caption (an h2) and the photos, or the video, beside it, so a row is a "set".
The rows come from the section's CSS (grid-area), the words from the server-
rendered HTML, and each photo's real size and name from the page model the
browser loads (thunderbolt-features). Files are the originals Wix keeps
(static.wixstatic.com/media/<id>, video.wixstatic.com/video/<id>/file): the
largest the site can serve.

Blog. Each post's body is the Ricos document the post page itself fetches
(blog-frontend-adapter-public/v2/post-page). It is saved verbatim as "body".
The server-rendered page is read too, and its text and pictures are checked
against the document, so what is saved is what a visitor sees.

Words are never edited. Captions keep his line breaks; only the whitespace the
HTML source puts around a <br> is dropped, as a browser drops it.
"""

import datetime
import hashlib
import html
import http.cookiejar
import json
import os
import re
import sys
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(HERE, "content")
MEDIA_REF = os.path.join(HERE, "reference", "wix-media")
SITE = "https://www.wavesanddata.com"
MEDIA = "https://static.wixstatic.com/media/"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
BLOG_APP = "22bef345-3c5b-4c18-b782-74d4085112ff"   # the instance the post page uses
TODAY = datetime.date.today().isoformat()

JAR = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(JAR))


def get(url, headers=None, data=None, method=None):
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"User-Agent": UA, **(headers or {})})
    with OPENER.open(req, timeout=120) as r:
        return r.read()


def text(url, **kw):
    return get(url, **kw).decode("utf-8", "replace")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fetch(url, dst):
    """Download once; a file already on disk is kept (Wix never changes the
    bytes behind an id). Returns (bytes, sha256)."""
    if not os.path.exists(dst):
        tmp = dst + ".part"
        with open(tmp, "wb") as fh:
            fh.write(get(url))
        os.replace(tmp, dst)
    return os.path.getsize(dst), sha256(dst)


def local_name(wix_id):
    """ce0a40_...~mv2.png -> ce0a40_..._mv2.png, the name reference/wix-media uses."""
    return wix_id.replace("~", "_")


def ref_check(name, digest):
    """Same bytes as the copy in reference/wix-media? None when there is none."""
    ref = os.path.join(MEDIA_REF, name)
    return None if not os.path.exists(ref) else sha256(ref) == digest


def pixels(path):
    """(width, height) as displayed, and the EXIF orientation that gets there."""
    from PIL import Image
    with Image.open(path) as im:
        w, h = im.size
        o = im.getexif().get(274, 1) or 1
    return (h, w, o) if o in (5, 6, 7, 8) else (w, h, o)


def gps(path):
    from PIL import Image
    with Image.open(path) as im:
        return 34853 in im.getexif()


def write_json(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


# ---------------------------------------------------------------- gallery

def lines_of(markup):
    """His caption as lines: split at <br>, tags dropped, entities read, the
    source's whitespace around each break dropped, empty lines gone."""
    out = []
    for part in re.split(r"<br\b[^>]*>", markup):
        t = html.unescape(re.sub(r"<[^>]+>", "", part)).replace(" ", " ")
        t = re.sub(r"[ \t\r\n]+", " ", t).strip()
        if t:
            out.append(t)
    return out


def page_model(page_html, ids):
    """The thunderbolt-features JSON of this page: the one whose compProps
    carry the page's own components."""
    urls = {u.replace("&amp;", "&") for u in re.findall(
        r'https://siteassets\.parastorage\.com/pages/pages/thunderbolt\?[^"\s\']+', page_html)}
    for u in sorted(urls):
        if "module=thunderbolt-features" not in u:
            continue
        model = json.loads(text(u))
        props = model.get("props", {}).get("render", {}).get("compProps", {})
        if any(i in props for i in ids):
            return model
    sys.exit("gallery: no page model carries the page's components")


def gallery():
    out = os.path.join(CONTENT, "gallery")
    os.makedirs(os.path.join(out, "photos"), exist_ok=True)
    os.makedirs(os.path.join(out, "video"), exist_ok=True)
    page = text(f"{SITE}/gallery")
    body = page[page.find('id="PAGES_CONTAINER"'):]
    if 'id="SITE_FOOTER"' in body:
        body = body[:body.find('id="SITE_FOOTER"')]

    sections = re.findall(r'<section id="(comp-[a-z0-9]+)"', body)
    rich = {m.group(1): m.group(2) for m in re.finditer(
        r'<div id="(comp-[a-z0-9]+)" class="[^"]*wixui-rich-text[^"]*"[^>]*>(.*?)</div>',
        body, re.S)}
    model = page_model(page, list(rich))
    comps = model["structure"]["components"]
    props = model["props"]["render"]["compProps"]

    def row(cid):
        """The grid row a component starts on (a photo may span several)."""
        m = re.search(r'\[id="%s"\][^{]*\{[^}]*grid-area:(\d+) /' % re.escape(cid), page)
        return int(m.group(1)) if m else 1

    # A caption opens a band of rows that runs to the next caption; a photo
    # belongs to the band its first row falls in. Within a band the photos keep
    # the editor's order, which is the order they read on the page.
    sets = []
    for sec in sections:
        kids = comps.get(sec, {}).get("components", [])
        caps = sorted((row(c), n, c) for n, c in enumerate(kids)
                      if comps[c]["componentType"] == "WRichText")
        if not caps:
            sys.exit(f"gallery: section {sec} has no caption")
        bands = [{"lines": lines_of(rich[c]), "media": []} for _, _, c in caps]
        for cid in kids:
            if comps[cid]["componentType"] not in ("WPhoto", "VideoPlayer"):
                continue
            starts = [k for k, (r, _, _) in enumerate(caps) if r <= row(cid)]
            if not starts:
                sys.exit(f"gallery: {cid} in {sec} sits above every caption")
            bands[starts[-1]]["media"].append(cid)
        sets.extend(bands)

    items, seen, manifest_sets, keys = [], {}, [], []
    for k, s in enumerate(sets, 1):
        caption = "\n".join(s["lines"])
        entry = {"order": k, "caption": caption, "lines": s["lines"], "items": []}
        key = [props[c].get("uri") or props[c].get("src") for c in s["media"]]
        if key in keys:
            entry["repeat_of"] = keys.index(key) + 1
        keys.append(key)
        for cid in s["media"]:
            p = props[cid]
            if comps[cid]["componentType"] == "VideoPlayer":
                vid = re.search(r"/video/([^/]+)/", p["src"]).group(1)
                src = f"https://video.wixstatic.com/video/{vid}/file"
                name = f"{vid}.mp4"
                size, digest = fetch(src, os.path.join(out, "video", name))
                poster = p["playableConfig"]["poster"]
                pname = local_name(poster["uri"])
                psize, pdig = fetch(MEDIA + poster["uri"], os.path.join(out, "video", pname))
                rec = {"type": "video", "file": f"video/{name}", "caption": caption,
                       "width": poster["width"], "height": poster["height"],
                       "duration": p.get("duration"), "bytes": size, "sha256": digest,
                       "wix_id": vid, "source": src,
                       "renditions": {q: f"https://video.wixstatic.com/video/{vid}/{q}/mp4/file.mp4"
                                      for q in ("480p", "720p", "1080p")},
                       "poster": {"file": f"video/{pname}", "width": poster["width"],
                                  "height": poster["height"], "bytes": psize, "sha256": pdig},
                       "wix_title": p.get("title")}
            else:
                name = local_name(p["uri"])
                path = os.path.join(out, "photos", name)
                size, digest = fetch(MEDIA + p["uri"], path)
                w, h, orient = pixels(path)
                if (w, h) != (p["width"], p["height"]):
                    print(f"!! {name}: file is {w}x{h}, Wix says {p['width']}x{p['height']}")
                rec = {"type": "photo", "file": f"photos/{name}", "caption": caption,
                       "width": w, "height": h, "exif_orientation": orient,
                       "gps_in_file": gps(path), "bytes": size, "sha256": digest,
                       "wix_id": p["uri"], "upload_name": p.get("name"),
                       "alt_on_wix": p.get("alt"), "same_as_reference": ref_check(name, digest)}
            if rec["file"] not in seen:
                seen[rec["file"]] = len(items) + 1
                items.append({"order": seen[rec["file"]], "set": k, **rec})
            entry["items"].append(seen[rec["file"]])
        manifest_sets.append(entry)

    manifest = {
        "source": f"{SITE}/gallery",
        "captured": TODAY,
        "note": ("The live page, in its order. 'sets' are its rows: one caption, in his words "
                 "and his line breaks, and the photos or video beside it (item numbers). "
                 "'items' lists every file once, in order of first appearance, with the "
                 "caption of the set it first appears in. A set with 'repeat_of' shows the "
                 "same files as an earlier set. Files are the originals Wix serves; width and "
                 "height are as displayed (EXIF orientation applied). The photos have no "
                 "captions of their own on the live page and no links; 'upload_name' and "
                 "'alt_on_wix' are his upload file names, not text he wrote for visitors."),
        "sets": manifest_sets,
        "items": items,
    }
    write_json(os.path.join(out, "manifest.json"), manifest)
    ignore = os.path.join(out, ".gitignore")
    if not os.path.exists(ignore):
        with open(ignore, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("# source media stays on disk, out of the repository (as content/blog/)\n"
                     "photos/\nvideo/\n")
    photos = [i for i in items if i["type"] == "photo"]
    print(f"gallery: {len(manifest_sets)} sets on the page "
          f"({sum(1 for s in manifest_sets if 'repeat_of' in s)} repeat an earlier set), "
          f"{len(photos)} photos, {len(items) - len(photos)} video, "
          f"{sum(i['bytes'] for i in items) / 1e6:.1f} MB of originals")
    for s in manifest_sets:
        rep = f"  (repeat of set {s['repeat_of']})" if "repeat_of" in s else ""
        print(f"  {s['order']:2d}. {' / '.join(s['lines'])}  items {s['items']}{rep}")


# ---------------------------------------------------------------- blog

def token():
    tokens = json.loads(text(f"{SITE}/_api/v1/access-tokens"))
    return tokens["apps"][BLOG_APP]["instance"]


def api(path, tok, body=None):
    headers = {"authorization": tok, "accept": "application/json"}
    if body is not None:
        headers["content-type"] = "application/json"
        return json.loads(get(SITE + path, headers, json.dumps(body).encode(), "POST"))
    return json.loads(get(SITE + path, headers))


def walk(nodes):
    for n in nodes or []:
        yield n
        yield from walk(n.get("nodes"))


def plain(node):
    return "".join(k["textData"]["text"] for k in walk(node.get("nodes"))
                   if k.get("type") == "TEXT")


def ssr_body(slug):
    """What the server-rendered post page shows: its paragraphs' text and its
    pictures, in order, from the content viewer only (not the related posts)."""
    page = text(f"{SITE}/post/{slug}")
    i = page.find('data-id="content-viewer"')
    seg = page[i:page.find('data-hook="rcv-block-last"', i)]
    paras = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m))).strip()
             for m in re.findall(r'<p [^>]*id="viewer-[^"]+"[^>]*>(.*?)</p>', seg, re.S)]
    pics = re.findall(r'<wow-image id="([^"]+)"', seg)
    kinds = re.findall(r'<div type="([^"]+)" data-hook="rcv-block\d+"', seg)
    return [p for p in paras if p], pics, kinds


def blog():
    out = os.path.join(CONTENT, "blog")
    os.makedirs(out, exist_ok=True)
    tok = token()
    listing = api("/_api/communities-blog-node-api/v3/posts/query", tok,
                  {"paging": {"limit": 100, "offset": 0}})
    posts = sorted(listing["posts"], key=lambda p: p["firstPublishedDate"], reverse=True)
    total = listing.get("metaData", {}).get("total")
    if total is not None and total != len(posts):
        sys.exit(f"blog: the query returned {len(posts)} of {total} posts")
    cats = api("/_api/communities-blog-node-api/v3/categories?paging.limit=100", tok)
    categories = {c["id"]: c.get("label") or c.get("title")
                  for c in cats.get("categories", [])}

    index = []
    for p in posts:
        slug = p["slug"]
        d = os.path.join(out, slug)
        os.makedirs(d, exist_ok=True)
        page = api(f"/_api/blog-frontend-adapter-public/v2/post-page/{slug}"
                   f"?postId={slug}&translationsName=main&languageCode=en", tok)
        post = page["postPage"]["post"]
        doc = post["richContent"]

        images, videos, files, links, problems = [], [], [], [], []
        for n in walk(doc["nodes"]):
            t = n.get("type")
            if t == "IMAGE":
                img = n["imageData"]["image"]
                wid = img["src"]["id"]
                name = local_name(wid)
                size, digest = fetch(MEDIA + wid, os.path.join(d, name))
                w, h, _ = pixels(os.path.join(d, name))
                if (w, h) != (img["width"], img["height"]):
                    problems.append(f"{name} is {w}x{h}, the node says "
                                    f"{img['width']}x{img['height']}")
                images.append({"node": n["id"], "file": name, "width": w, "height": h,
                               "bytes": size, "sha256": digest, "wix_id": wid,
                               "alt": n["imageData"].get("altText", ""),
                               "caption": "".join(plain(k) for k in n.get("nodes", [])
                                                  if k.get("type") == "CAPTION"),
                               "same_as_reference": ref_check(name, digest)})
            elif t == "VIDEO":
                v = n["videoData"]
                url = v["video"]["src"].get("url") or ""
                rec = {"node": n["id"], "url": url, "duration": v["video"].get("duration")}
                yt = re.search(r"(?:v=|youtu\.be/|/embed/)([A-Za-z0-9_-]{11})", url)
                if yt:
                    meta = json.loads(text("https://www.youtube.com/oembed?format=json&url="
                                           + urllib.parse.quote(url, safe="")))
                    thumb = v.get("thumbnail", {}).get("src", {}).get("url", "")
                    tname = f"youtube-{yt.group(1)}.jpg"
                    tsize, tdig = fetch(thumb, os.path.join(d, tname)) if thumb else (0, "")
                    rec.update({"provider": "youtube", "id": yt.group(1),
                                "embed": f"https://www.youtube-nocookie.com/embed/{yt.group(1)}",
                                "title": meta.get("title"), "author": meta.get("author_name"),
                                "thumbnail": {"file": tname, "url": thumb,
                                              "width": v.get("thumbnail", {}).get("width"),
                                              "height": v.get("thumbnail", {}).get("height"),
                                              "bytes": tsize, "sha256": tdig,
                                              "note": "YouTube's frame of a third-party "
                                                      "video, kept for reference"}})
                videos.append(rec)
            elif t == "FILE":
                f = n["fileData"]
                fid = f["src"].get("id") or f.get("path")
                size, digest = fetch(f"https://static.wixstatic.com/ugd/{fid}",
                                     os.path.join(d, fid))
                if f.get("size") and size != f["size"]:
                    problems.append(f"{fid} is {size} bytes, the node says {f['size']}")
                files.append({"node": n["id"], "file": fid, "name": f.get("name"),
                              "type": f.get("type"), "bytes": size, "sha256": digest,
                              "live_url": f"{SITE}/_files/ugd/{fid}"})
            elif t == "TEXT":
                for dec in n["textData"].get("decorations", []):
                    if dec.get("type") == "LINK":
                        links.append({"text": n["textData"]["text"],
                                      "url": dec["linkData"]["link"].get("url")})
            elif t not in ("PARAGRAPH", "HEADING", "CAPTION", "BULLETED_LIST",
                           "ORDERED_LIST", "LIST_ITEM", "DIVIDER", "BLOCKQUOTE"):
                problems.append(f"node type {t} ({n.get('id')}) is not recorded")

        # the page a visitor sees, against the document we keep
        paras, pics, kinds = ssr_body(slug)
        doc_paras = [re.sub(r"\s+", " ", plain(n)).strip() for n in doc["nodes"]
                     if n["type"] in ("PARAGRAPH", "HEADING")]
        if paras != [x for x in doc_paras if x]:
            problems.append("the page's paragraphs differ from the document's")
        if pics != [i["wix_id"] for i in images]:
            problems.append("the page's pictures differ from the document's")

        media = post.get("media") or {}
        cover_img = (media.get("wixMedia") or {}).get("image")
        cover = None
        if cover_img and media.get("displayed", True):
            cname = local_name(cover_img["id"])
            fetch(MEDIA + cover_img["id"], os.path.join(d, cname))
            cover = {"file": cname, "width": cover_img["width"], "height": cover_img["height"],
                     "wix_id": cover_img["id"],
                     "chosen": ("by him" if media.get("custom")
                                else "by Wix: the post's first picture")}

        record = {
            "slug": slug,
            "title": post["title"],
            "date": post["firstPublishedDate"][:10],
            "published": post["firstPublishedDate"],
            "updated": post.get("lastPublishedDate"),
            "category": None,
            "categories": [categories.get(c, c) for c in post.get("categoryIds", [])],
            "tags": post.get("tagIds", []),
            "hashtags": post.get("hashtags", []),
            "url": f"{SITE}/post/{slug}",
            "minutes_to_read": post.get("minutesToRead"),
            "excerpt_by_wix": post.get("excerpt"),
            "cover": cover,
            "images": images,
            "videos": videos,
            "files": files,
            "links": links,
            "page_blocks": kinds,
            "source": (f"{SITE}/_api/blog-frontend-adapter-public/v2/post-page/{slug}, "
                       f"checked against {SITE}/post/{slug}, {TODAY}"),
            "body": doc,
        }
        if record["categories"]:
            record["category"] = record["categories"][0]
        write_json(os.path.join(d, "post.json"), record)
        index.append({k: record[k] for k in ("slug", "title", "date", "published", "updated",
                                             "category", "url", "minutes_to_read")}
                     | {"cover": cover and cover["file"],
                        "images": [i["file"] for i in images],
                        "videos": [v["url"] for v in videos],
                        "files": [f["name"] for f in files],
                        "manifest": f"{slug}/post.json"})
        flag = "  !! " + "; ".join(problems) if problems else ""
        print(f"{record['date']}  {len(images):2d} img {len(videos)} vid {len(files)} file "
              f"{len(links)} link  {post['title'][:60]}{flag}")

    write_json(os.path.join(out, "posts.json"), index)
    print(f"blog: {len(index)} posts, categories on the site: {len(categories)}")


if __name__ == "__main__":
    for what in sys.argv[1:] or ["gallery", "blog"]:
        {"gallery": gallery, "blog": blog}[what]()
