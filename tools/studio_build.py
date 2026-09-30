# -*- coding: utf-8 -*-
"""Emit Wix Studio JSX bundles for the wavesanddata-studio site.

    python tools/studio_build.py            # writes build/studio/pages/*.json

Each file is what the editor's document API takes (build/studio/FORMAT.md):
  a page:   {version, structure:{type:'jsx'}, style, layout:{type:'css'}, unmapped:{type:'json'}}
            -> DS.importExport.pages.jsx.replace(pageRef, bundle) / .add(bundle)
  a global: {name, path:'global-components', export:<same shape>}
            -> DS.importExport.global.jsx.replace({components:[bundle]})

The content comes from the static site (site/build.py PROF_* constants, NAV,
DOCS, CONTACT; site/parts/topics.py TOPICS), so the professor's sentences stay
verbatim, and the design numbers from site/parts/theme.py and the part modules.
Ids are ours and readable; the importer renames them (page imports) and keeps
the mapping inside one bundle.
"""
import html
import json
import os
import re
import sys
from html.parser import HTMLParser

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# tools/inspect.py would shadow the standard library's inspect, which build.py imports
sys.path[:] = [q for q in sys.path if os.path.abspath(q or ".") != HERE]
sys.path.insert(0, os.path.join(ROOT, "site"))
import build as SB  # noqa: E402  the static site: PROF_*, NAV, DOCS, CONTACT

OUT = os.path.join(ROOT, "build", "studio", "pages")
MEDIA = json.load(open(os.path.join(ROOT, "build", "studio", "media.json"), encoding="utf-8"))

# ---------------------------------------------------------------- site facts
# Global components of the site (from DS.importExport.global.jsx.export()).
HEADER = "HeaderSection_kbgajy18"
HEADER_ID = "comp-kbgajy18"
FOOTER = "FooterSection_kbgakgyt"
FOOTER_ID = "comp-kbgakgyt"
MENUCONT = "MenuContainer_kd5px9hr"
MENUCONT_ID = "comp-kd5px9hr"
# The column. Built inside the header and pinned there, it became a global component
# of its own (DS.components.responsiveLayout.pin moved it to masterPage): every page
# shows it through a ref, as it shows the menu container.
SIDE = "Container_mueept8t"
SIDE_ID = "comp-mueept8t"

# Page ids in the Studio document, filled by the placeholder pass (pages.json)
PAGES_FILE = os.path.join(ROOT, "build", "studio", "pageids.json")
PAGE_IDS = json.load(open(PAGES_FILE, encoding="utf-8")) if os.path.exists(PAGES_FILE) else {}
# Menus created in the document (menus.json): {"main": id, "side1": id, ...}
MENUS_FILE = os.path.join(ROOT, "build", "studio", "menuids.json")
MENU_IDS = json.load(open(MENUS_FILE, encoding="utf-8")) if os.path.exists(MENUS_FILE) else {}

# ---------------------------------------------------------------- tokens
# theme.py light tokens, and the theme colour slots they were written to
C = dict(
    page="#FBF9F6", surface="#F6F3EF", card="#F2EFE9", wash="#FEEBDB", rule="#E5E1DB",
    line="#D7D2CA", line_strong="#8A857C", ink="#27221C", body="#544F48", muted="#6F6A64",
    nav="#043052", nav_hover="#104169", nav_press="#002341", nav_deep="#001C35",
    nav_mute="#C3CDD5", nav_mix="#0A385E", accent="#A5510B", accent2="#E7813B",
    link="#095A94", link_hover="#004170", tint="#E6F0F9", tint_hover="#DCEAF8",
    tint_press="#D2E4F5", ink4="#F3F0ED", ink5="#F0EEEB", ink7="#ECEAE7", ink8="#EAE8E5",
)
SLOT = dict(page="color_11", card="color_12", rule="color_13", muted="color_14", ink="color_15",
            nav_mute="color_16", link="color_17", nav="color_18", nav_hover="color_19",
            nav_deep="color_20", wash="color_21", accent2="color_22", accent="color_23",
            surface="color_26", line="color_27", body="color_29")
# Source Serif 4 and Source Sans 3, uploaded to the site (build/studio/fonts/, OFL): Wix makes
# each file a family of its own with one weight, so a semibold is its own family at "normal";
# global.css gives the Regular families their SemiBold file as the bold face
SERIF_R = "wfont_ce0a40_13ed4dbfeb5e4c98b4e49442945711f8,wf_13ed4dbfeb5e4c98b4e494429,orig_source_serif_4_regular"
SERIF_SB = "wfont_ce0a40_f779e44a632944279f569b4b260acf04,wf_f779e44a632944279f569b4b2,orig_source_serif_4_semibold"
SANS_R = "wfont_ce0a40_a73a70f70a444b6abeb4f35916e50973,wf_a73a70f70a444b6abeb4f3591,orig_source_sans_3_regular"
SANS_SB = "wfont_ce0a40_57c803a5e5a248408cb809a6226d79eb,wf_57c803a5e5a248408cb809a62,orig_source_sans_3_semibold"
SPX = {"refWidth": 1280, "resolverType": "scale"}
BP = (1000, 750)   # Studio breakpoints: tablet <=1000, mobile <=750


def rgba(hexs, a=1):
    h = hexs.lstrip("#")
    return "rgba(%d,%d,%d,%s)" % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def media_id(name):
    return MEDIA[name]["id"]


# ---------------------------------------------------------------- nodes
class N:
    """A component: tag, id, skin, data, props, children, desktop layout, breakpoint
    layouts, unmapped (style/design/...)."""
    _ids = set()

    def __init__(self, tag, cid, skin=None, data=None, props=None, kids=(), css=None, bp=None,
                 um=None, attrs=None):
        assert cid not in N._ids, cid
        N._ids.add(cid)
        self.tag, self.id, self.skin, self.data, self.props = tag, cid, skin, data, props
        self.kids = list(kids)
        self.css = css or {}
        self.bp = bp or {}
        self.um = um or {}
        self.attrs = attrs or {}

    def walk(self):
        yield self
        for k in self.kids:
            yield from k.walk()


def reset_ids():
    N._ids = set()


MENUREF = re.compile(r'"@@MENUREF:([A-Za-z0-9_]+)@@"')


def jsx_attr(obj):
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return "{" + MENUREF.sub(lambda m: m.group(1) + ".items", s) + "}"


def jsx(node, depth=1):
    pad = "    " * depth
    a = [f'id="{node.id}"']
    for k, v in node.attrs.items():
        a.append(f'{k}="{v}"')
    if node.skin:
        a.append(f'skin="{node.skin}"')
    lines = [pad + "<" + node.tag + " " + " ".join(a)]
    if node.data is not None:
        lines.append(pad + "    data=" + jsx_attr(node.data))
    if node.props is not None:
        lines.append(pad + "    props=" + jsx_attr(node.props))
    if getattr(node, "conn", None):
        lines.append(pad + "    connections={[" + node.conn + "]}")
    if not node.kids:
        lines[-1] += " />"
        return "\n".join(lines)
    lines[-1] += ">"
    for k in node.kids:
        lines.append(jsx(k, depth + 1))
    lines.append(pad + "</" + node.tag + ">")
    return "\n".join(lines)


def css_block(sel, props, indent="", spx=True):
    out = [indent + sel + " {"]
    items = []
    if spx:
        items += [("--spx-ref-width", "1280"), ("--spx-resolver-type", "scale")]
    items += list(props.items())
    if "position" not in props:
        items.append(("position", "relative"))
    out.append(";\n".join(indent + "    " + f"{k}: {v}" for k, v in items))
    out.append(indent + "}")
    return "\n".join(out)


CONTAINER_KEYS = ("--container-layout-type", "display", "grid-template-columns", "grid-template-rows",
                  "row-gap", "column-gap", "padding-top", "padding-right", "padding-bottom", "padding-left",
                  "flex-direction", "flex-wrap", "align-items", "justify-content", "overflow-x", "overflow-y")


def bp_rule(n, bp):
    """A breakpoint override. The importer keeps an item or size override on its own,
    but drops a container override (columns, rows, gaps, padding) unless the rule
    restates the whole container layout, as the editor's own export does."""
    over = dict(n.bp[bp])
    if any(k in CONTAINER_KEYS for k in over if k != "display") and "--container-layout-type" in n.css:
        full = {k: v for k, v in n.css.items() if k in CONTAINER_KEYS}
        for wider in [b for b in BP if b > bp]:     # the phone inherits the tablet's overrides
            full.update({k: v for k, v in n.bp.get(wider, {}).items() if k in CONTAINER_KEYS})
        full.update({k: v for k, v in over.items() if k in CONTAINER_KEYS})
        over = {**{k: v for k, v in over.items() if k not in CONTAINER_KEYS}, **full}
    return over


def layout_css(root_scope, nodes):
    parts = []
    for n in nodes:
        if n.css:
            parts.append(css_block("#" + n.id, n.css))
    for bp in BP:
        rules = [css_block("#" + n.id, bp_rule(n, bp), "        ", spx=False) for n in nodes if n.bp.get(bp)]
        if rules and root_scope:
            parts.append("@scope (#%s) {\n    @media (min-width: 1px) and (max-width: %dpx) {\n%s\n    }\n}"
                         % (root_scope, bp, "\n".join(rules)))
        elif rules:
            # a component with no breakpoints of its own (the column): bare @media,
            # resolved through its export's dependencies.references.variants
            parts.append("@media (min-width: 1px) and (max-width: %dpx) {\n%s\n}" % (bp, "\n".join(rules)))
    return "\n".join(parts) + "\n"


# ---------------------------------------------------------------- layout helpers
def grid_item(row, col, **kw):
    d = {"--item-layout-type": "GridItemLayout", "grid-row": row, "grid-column": col,
         "align-self": kw.pop("align", "start"), "justify-self": kw.pop("justify", "stretch")}
    for side in ("top", "bottom", "left", "right"):
        d["margin-" + side] = kw.pop("m" + side[0], "0px")
    d.update(kw)
    return d


def flex_item(**kw):
    d = {"--item-layout-type": "FlexItemLayout"}
    if "align" in kw:
        d["align-self"] = kw.pop("align")
    for side in ("top", "bottom", "left", "right"):
        if "m" + side[0] in kw:
            d["margin-" + side] = kw.pop("m" + side[0])
    d.update(kw)
    return d


def size(w=None, h="auto", minh=None, maxw=None):
    d = {}
    if w is not None:
        d["width"] = w
    d["height"] = h
    d["--height-type"] = ("auto" if h == "auto" else "vh" if str(h).endswith("vh")
                          else "percentage" if str(h).endswith("%") else "px")
    if minh:
        d["min-height"] = minh
    if maxw:
        d["max-width"] = maxw
    return d


def grid_box(cols="minmax(0px, 1fr)", rows="auto", cgap=None, rgap=None, pad=None):
    d = {"--container-layout-type": "GridContainerLayout", "display": "grid",
         "grid-template-columns": cols, "grid-template-rows": rows}
    if rgap:
        d["row-gap"] = rgap
    if cgap:
        d["column-gap"] = cgap
    d.update(padding(pad))
    return d


def flex_box(direction="column", gap=None, pad=None, align=None, justify=None, wrap=None):
    d = {"--container-layout-type": "FlexContainerLayout", "display": "flex",
         "flex-direction": direction}
    if gap:
        d["row-gap" if direction == "column" else "column-gap"] = gap
    if align:
        d["align-items"] = align
    if justify:
        d["justify-content"] = justify
    if wrap:
        d["flex-wrap"] = wrap
    d.update(padding(pad))
    return d


def padding(pad):
    if not pad:
        return {}
    t, r, b, l = pad
    return {"padding-top": t, "padding-right": r, "padding-bottom": b, "padding-left": l}


# ---------------------------------------------------------------- styles (unmapped)
def cstyle(cls, skin, props=None, source=None, override=None):
    props = props or {}
    src = {k: (source or {}).get(k, "value") for k in props}
    st = {"properties": props, "propertiesSource": src, "groups": {}}
    if override:
        st["propertiesOverride"] = override
    return {"style": {"variants": [], "default": {
        "type": "ComponentStyle", "style": st, "componentClassName": cls, "pageId": "",
        "spx": SPX, "compId": "", "skin": skin}}, "layout": {"variants": []}}


def box_style(bg=None, alpha=1, border=None, bw="0px", radius="0px"):
    props = {"shd": "0px 0px 0px 0px rgba(0,0,0,0.6)", "rd": radius,
             "alpha-brd": "1" if border else "0", "brd": border or "#000000",
             "alpha-bg": str(alpha if bg else 0), "bg": bg or "#FFFFFF", "brw": bw,
             "boxShadowToggleOn-shd": "false"}
    return cstyle("mobile.core.components.Container", "wysiwyg.viewer.skins.area.DefaultAreaSkin", props)


def text_style():
    return cstyle("wysiwyg.viewer.components.WRichText", "wysiwyg.viewer.skins.WRichTextNewSkin", {})


def section_style(bg=None):
    s = cstyle("responsive.components.Section", "wysiwyg.viewer.skins.area.RectangleArea",
               {"alpha-bg": "0", "bg": "color_11"}, {"bg": "theme"})
    s["design"] = {"variants": [], "default": {"type": "MediaContainerWithDividers", "background": {
        "type": "BackgroundMedia", "colorOverlay": "", "colorOverlayOpacity": 1,
        "colorLayers": [{"fill": {"type": "SolidColor", "color": bg or "color_11"},
                         "opacity": 1 if bg else 0, "type": "SolidColorLayer"}]}}}
    return s


def image_style(radius="0", bg_alpha=1):
    return cstyle("wixui.ImageX", "wixui.skins.ImageX", {
        "borderWidth": "0", "boxShadowToggleOn-boxShadow": "false",
        "boxShadow": "0px 0px 0px 0px rgba(0,0,0,0)", "borderColor": "#ffffff",
        "cornerRadius": radius, "backgroundColor": C["card"], "alpha-backgroundColor": bg_alpha})


def vector_style():
    s = cstyle("wysiwyg.viewer.components.VectorImage", "skins.viewer.VectorImageSkin", {})
    s["design"] = {"variants": [], "default": {"type": "VectorImageDesignData", "overrideColors": None,
                   "shapeStyle": {"opacity": 1, "strokeWidth": 0, "stroke": "#000000",
                                  "strokeOpacity": 1, "enableStroke": False}}}
    return s


def font(fam, size_px, weight, color, lh="1.4em", ls="0em"):
    return {"fontStyle": "normal", "fontWeight": weight, "fontVariant": "normal",
            "fontSize": size_px, "fontFamily": fam, "color": color, "lineHeight": lh,
            "letterSpacing": ls}


def button_style(bg, fg, bg_hover, fg_hover, pad=("0px", "20px", "0px", "20px"), radius="999px",
                 icon=False, icon_color=None, gap="6px", label=True, fsize="15px", row="row",
                 face=None, lh="1.2em", ls="0.01em", align="center"):
    t, r, b, l = pad
    props = {
        "background": rgba(bg, 1) if bg else "rgba(255,255,255,0)",
        "hover-background": rgba(bg_hover, 1) if bg_hover else "rgba(255,255,255,0)",
        "disabled-background": "rgba(199,199,199,1)",
        "color": rgba(fg), "hover-color": rgba(fg_hover), "disabled-color": "#000000",
        "font": "font_5",
        "padding-top": t, "padding-right": r, "padding-bottom": b, "padding-left": l,
        "border-top-left-radius": radius, "border-top-right-radius": radius,
        "border-bottom-left-radius": radius, "border-bottom-right-radius": radius,
        "border-top": "0px solid rgba(0,0,0,1)", "border-right": "0px solid rgba(0,0,0,1)",
        "border-bottom": "0px solid rgba(0,0,0,1)", "border-left": "0px solid rgba(0,0,0,1)",
        "hover-border-top": "0px solid rgba(0,0,0,1)", "hover-border-right": "0px solid rgba(0,0,0,1)",
        "hover-border-bottom": "0px solid rgba(0,0,0,1)", "hover-border-left": "0px solid rgba(0,0,0,1)",
        "disabled-border-top": "1px solid rgba(199,199,199,1)", "disabled-border-right": "1px solid rgba(199,199,199,1)",
        "disabled-border-bottom": "1px solid rgba(199,199,199,1)", "disabled-border-left": "1px solid rgba(199,199,199,1)",
        "box-shadow": "", "text-shadow": "0px 0px 0px transparent",
        "icon-display": "initial" if icon else "none", "hover-icon-display": "initial" if icon else "none",
        "icon-size": "20px", "hover-icon-size": "20px",
        "icon-color": rgba(icon_color or fg), "hover-icon-color": rgba(fg_hover),
        "icon-rotation": "0", "hover-icon-rotation": "0", "disabled-icon-rotation": "0",
        "content-gap": gap, "content-horizontal-alignment": align,
        # the label comes first in the button's DOM: row puts the icon after it
        "container-align-items": "center", "container-flex-direction": row,
        "direction": "ltr", "label-display": "initial" if label else "none", "label-overflow": "wrap",
        "text-align": {"center": "center", "start": "left"}.get(align, align),
    }
    return cstyle("wixui.StylableButton", "wixui.skins.Button", props, {"font": "theme"},
                  {"font": font(face or SANS_SB, fsize, "normal", fg, lh, ls)})


# ---------------------------------------------------------------- rich text
class _Rich(HTMLParser):
    """The static site's HTML (his PROF_* blocks) -> Wix rich text HTML: class
    font_N on block tags, inline styles as Wix writes them, links through the
    linkList (dataquery). A list item's own text sits in a <p>, closed before a
    nested list."""

    def __init__(self, cls, link_fn, color=None, size=None, lh=None, ls=None, underline=True):
        super().__init__(convert_charrefs=True)
        self.cls, self.link_fn, self.underline = cls, link_fn, underline
        self.color, self.size, self.lh, self.ls = color, size, lh, ls
        self.out, self.links, self.li_open = [], [], []

    def _pstyle(self):
        return f' style="line-height:{self.lh};"' if self.lh else ""

    def _span(self):
        st = ""
        if self.color:
            st += f"color:{self.color};"
        if self.size:
            st += f"font-size:{self.size};"
        if self.ls:
            st += f"letter-spacing:{self.ls};"
        return f'<span style="{st}">' if st else "<span>"

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("p", "h1", "h2", "h3", "h4"):
            cls = {"h1": "font_0", "h2": "font_2", "h3": "font_3", "h4": "font_4"}.get(tag, self.cls)
            ps = self._pstyle() if tag == "p" else ""
            self.out.append(f'<{tag} class="{cls}"{ps}>' + self._span())
        elif tag in ("ol", "ul"):
            if self.li_open and self.li_open[-1]:
                self.out.append("</span></p>")
                self.li_open[-1] = False
            self.out.append(f'<{tag} class="{self.cls}">')
        elif tag == "li":
            self.out.append(f'<li><p class="{self.cls}"{self._pstyle()}>' + self._span())
            self.li_open.append(True)
        elif tag in ("strong", "b"):
            self.out.append('<span style="font-weight:bold;">')
        elif tag == "a":
            lid = self.link_fn(a.get("href", ""), self.links)
            deco = "underline" if self.underline else "none"
            self.out.append(f'<span style="text-decoration:{deco};"><a dataquery="#{lid}">')
        elif tag == "span":
            st = a.get("style")
            self.out.append(f'<span style="{st}">' if st else "<span>")
        elif tag == "br":
            self.out.append("<br>")

    def handle_endtag(self, tag):
        if tag in ("p", "h1", "h2", "h3", "h4"):
            self.out.append(f"</span></{tag}>")
        elif tag in ("ol", "ul"):
            self.out.append(f"</{tag}>")
        elif tag == "li":
            if self.li_open.pop():
                self.out.append("</span></p>")
            self.out.append("</li>")
        elif tag in ("strong", "b", "span"):
            self.out.append("</span>")
        elif tag == "a":
            self.out.append("</a></span>")

    def handle_data(self, data):
        if "\xa0" in data and not data.replace("\xa0", "").strip():
            self.out.append(data.replace("\xa0", "&nbsp;"))      # a deliberate non-breaking space
            return
        if not data.strip():
            # whitespace between inline pieces of text is a space; between blocks it is nothing
            if self.out and not re.search(r"(</?(p|h[1-4]|ol|ul|li)[^>]*>|<span[^>]*>)$", self.out[-1]):
                self.out.append(" ")
            return
        lead = " " if data[:1].isspace() and self.out and not self.out[-1].endswith(">") else ""
        if data[:1].isspace() and self.out and self.out[-1].endswith("</span>"):
            lead = " "
        trail = " " if data[-1:].isspace() else ""
        self.out.append(lead + html.escape(" ".join(data.split()), quote=False) + trail)


_LINKS = [0]


def rich(src_html, cls="font_7", links=None, **kw):
    """-> (wix html, linkList)"""
    pages = links or {}

    def link_fn(href, acc):
        _LINKS[0] += 1
        lid = f"textLink_w{_LINKS[0]}"
        if href.startswith("mailto:"):
            acc.append({"type": "EmailLink", "id": lid, "recipient": href[7:]})
        elif href.startswith("http"):
            acc.append({"type": "ExternalLink", "id": lid, "url": href, "target": "_blank"})
        elif href.startswith(("doc/", "topic/")):
            kind, slug = href.split("/", 1)
            acc.append({"type": "DynamicPageLink", "id": lid, "innerRoute": slug, "anchorDataId": "",
                        "routerId": DOC_ROUTER_ID if kind == "doc" else TOPIC_ROUTER_ID, "target": "_self"})
        else:
            key = href.split("#")[0].replace(".html", "")
            pid = PAGE_IDS.get(key)
            if pid:
                acc.append({"type": "PageLink", "id": lid, "pageId": "#" + pid, "rel": []})
            else:
                acc.append({"type": "ExternalLink", "id": lid, "url": "/" + key, "target": "_self"})
        return lid

    p = _Rich(cls, link_fn, **kw)
    p.feed(src_html)
    out = "".join(p.out)
    out = re.sub(r"<span>\s*</span>", "", out)
    out = re.sub(r"\s+</span></p>", "</span></p>", out)
    return out, p.links


def rtext(cid, src_html, cls="font_7", css=None, bp=None, **kw):
    text, links = rich(src_html, cls, **kw)
    return N("WRichText", cid, "wysiwyg.viewer.skins.WRichTextNewSkin",
             data={"type": "StyledText", "text": text, "stylesMapId": "CK_EDITOR_PARAGRAPH_STYLES",
                   "linkList": links},
             props={"type": "WRichTextProperties", "packed": True},
             css=css, bp=bp, um=text_style())


def box(cid, kids=(), css=None, bp=None, **style):
    return N("Container", cid, "wysiwyg.viewer.skins.area.DefaultAreaSkin", kids=kids, css=css, bp=bp,
             um=box_style(**style))


def section(cid, kids, css, bp=None, bg=None, name=None):
    um = section_style(bg)
    if name:
        um["anchors"] = {"type": "AnchorInfo", "id": "anchors-" + cid[5:], "name": name}
    return N("Section", cid, "wysiwyg.viewer.skins.area.RectangleArea", kids=kids, css=css, bp=bp, um=um)


def image(cid, name, alt, w, h, css=None, bp=None, radius="0", bg_alpha=1):
    mid = media_id(name)
    return N("ImageX", cid, "wixui.skins.ImageX",
             data={"type": "ImageX", "image": {"mediaType": "picture", "uri": mid, "width": w, "height": h,
                                               "alt": alt, "title": alt, "name": name}},
             css=css, bp=bp, um=image_style(radius, bg_alpha))


def vector(cid, name, alt, css=None, bp=None):
    return N("VectorImage", cid, "skins.viewer.VectorImageSkin",
             data={"type": "VectorImage", "alt": alt, "svgId": media_id(name), "title": name},
             props={"type": "VectorImageProperties", "displayMode": "fit"},
             css=css, bp=bp, um=vector_style())


def page_link(key):
    pid = PAGE_IDS.get(key)
    return {"type": "PageLink", "pageId": "#" + pid, "target": "_self"} if pid else None


def button(cid, label, link, style, css=None, bp=None, icon=None):
    data = {"type": "StylableButton", "label": label, "direction": "inherit"}
    if icon:
        data["svgId"] = media_id(icon)
    if link:
        data["link"] = link
    return N("StylableButton", cid, "wixui.skins.Button", data=data,
             props={"type": "StylableButtonProperties"}, css=css, bp=bp, um=style)


# ---------------------------------------------------------------- references
PAGEREF = re.compile(r'"pageId":\s*"#([A-Za-z0-9]+)"')


def data_refs(nodes):
    """export.dependencies.references.data: every page a link points at and every menu
    a Menu shows. Without them the importer turns each reference into a fresh id that
    does not exist (missingReferenceError)."""
    blob = json.dumps([x.data for x in nodes], ensure_ascii=False)
    refs = {}
    for pid in sorted(set(PAGEREF.findall(blob))):
        refs[pid] = {"target": pid, "type": "Page"}
    for name in sorted(set(MENUREF.findall(blob))):
        mid = next((v for v in MENU_IDS.values() if v.replace("-", "_") == name), name)
        refs[mid] = {"target": mid, "type": "CustomMenu"}
    return refs


# ---------------------------------------------------------------- pages
def breakpoints(owner):
    """The three Studio breakpoints; a root without them cannot resolve its @media rules
    ("Cannot resolve breakpoint ... against knownBreakpoints")."""
    vid = "variants-w" + re.sub(r"[^a-z0-9]", "", owner.lower())[:10]
    return {"type": "BreakpointsData", "componentId": owner, "values": [
        {"type": "BreakpointRange", "id": vid, "min": 1, "max": 2147483647, "canvasSize": 1280},
        {"type": "BreakpointRange", "id": vid + "1", "min": 1, "max": 1000, "canvasSize": 768},
        {"type": "BreakpointRange", "id": vid + "2", "min": 1, "max": 750, "canvasSize": 390}]}


def page_bundle(pid, title, uri, sections, desktop_pad="240px", extra=None, page_data=None):
    """A page: header ref, our sections, footer ref, menu-container ref, the column's
    ref. `extra` are page-level components with no layout (datasets); `page_data`
    overrides the page's data (a dynamic page: hidePage, managingAppDefId)."""
    reset_ids()
    refs = dict(h="comp-wref-h-" + pid, f="comp-wref-f-" + pid, m="comp-wref-m-" + pid)
    hdr = N(HEADER, refs["h"], "wysiwyg.viewer.skins.ResponsiveContainerRefSkin",
            attrs={"sharedCompId": HEADER_ID},
            css={**size("auto"), **grid_item("1 / 2", "1 / 2", align="stretch"),
                 "--container-layout-type": "GridContainerLayout", "display": "grid",
                 "grid-template-columns": "1fr", "grid-template-rows": "1fr"},
            # the phone bar stays at the top (Header settings > Scroll effect: Freeze, which
            # Studio keeps on each page's header reference, per breakpoint). The rule restates
            # the grid item: `position: sticky` alone imports as a FixedItemLayout (a pinned
            # layer the height of the window)
            bp={1000: {"--item-layout-type": "GridItemLayout", "grid-row": "1 / 2", "grid-column": "1 / 2",
                       "position": "sticky", "top": "0%", "bottom": "auto", "z-index": "calc(infinity)",
                       "align-self": "stretch", "justify-self": "stretch", "margin-top": "0px",
                       "margin-bottom": "0px", "margin-left": "0px", "margin-right": "0px"}})
    n = len(sections)
    for i, s in enumerate(sections):
        s.css.update(grid_item(f"{i + 2} / {i + 3}", "1 / 2", align="stretch"))
    ftr = N(FOOTER, refs["f"], "wysiwyg.viewer.skins.ResponsiveContainerRefSkin",
            attrs={"sharedCompId": FOOTER_ID},
            css={**size("auto"), **grid_item(f"{n + 2} / {n + 3}", "1 / 2", align="stretch"),
                 "--container-layout-type": "GridContainerLayout", "display": "grid",
                 "grid-template-columns": "1fr", "grid-template-rows": "1fr"})
    mc = N(MENUCONT, refs["m"], "wysiwyg.viewer.skins.ResponsiveContainerRefSkin",
           attrs={"sharedCompId": MENUCONT_ID},
           css={"width": "auto", "height": "auto", "--height-type": "auto", "visibility": "visible",
                "--item-layout-type": "FixedItemLayout", "align-self": "start", "justify-self": "end",
                "margin-top": "0px", "margin-right": "0px",
                "--container-layout-type": "GridContainerLayout", "display": "grid",
                "grid-template-columns": "1fr", "grid-template-rows": "1fr"})
    sd = N(SIDE, "comp-wref-s-" + pid, "wysiwyg.viewer.skins.ResponsiveContainerRefSkin",
           attrs={"sharedCompId": SIDE_ID},
           css={"width": "auto", "height": "auto", "--height-type": "auto", "visibility": "visible",
                "--item-layout-type": "FixedItemLayout", "align-self": "start", "justify-self": "start",
                "margin-top": "0px", "margin-left": "0px",
                "--container-layout-type": "GridContainerLayout", "display": "grid",
                "grid-template-columns": "1fr", "grid-template-rows": "1fr"},
           bp={1000: {"visibility": "hidden"}})
    kids = [hdr] + sections + [ftr] + list(extra or []) + [mc, sd]
    data = {"type": "Page", "id": pid, "title": title, "hideTitle": True, "icon": "",
            "descriptionSEO": "", "metaKeywordsSEO": "", "pageTitleSEO": "", "pageUriSEO": uri,
            "hidePage": False, "underConstruction": False, "tpaApplicationId": 0,
            "pageSecurity": {"requireLogin": False},
            "pageBackgrounds": {
                "desktop": {"custom": True, "ref": {"type": "BackgroundMedia", "color": "{color_11}",
                                                    "alignType": "top", "fittingType": "fill",
                                                    "scrollType": "fixed"}, "isPreset": True},
                "mobile": {"custom": True, "ref": {"type": "BackgroundMedia", "color": "{color_11}",
                                                   "alignType": "top", "fittingType": "fill",
                                                   "scrollType": "fixed", "colorOverlay": "",
                                                   "colorOverlayOpacity": 0},
                           "isPreset": True, "mediaSizing": "viewport"}},
            "translationData": {"uriSEOTranslated": False}, "ignoreBottomBottomAnchors": True,
            "ogImage": ""}
    data.update(page_data or {})
    page = N("Page", pid, "wysiwyg.viewer.skins.page.ResponsivePageWithColorBG", data=data, kids=kids,
             attrs={"codeName": "page_" + re.sub(r"\W", "", uri)[:20]},
             css={"height": "auto", "--height-type": "auto", "--container-layout-type": "GridContainerLayout",
                  "display": "grid", "grid-template-columns": "minmax(0px, 1fr)",
                  "grid-template-rows": " ".join(["auto"] * (n + 2)),
                  "padding-top": "0px", "padding-right": "0px", "padding-bottom": "0px",
                  "padding-left": desktop_pad, "overflow-x": "clip", "overflow-y": "clip"},
             bp={1000: {"padding-left": "0px"}})
    page.um = {"style": {"variants": [], "default": {
        "type": "ComponentStyle", "style": {"properties": {"alpha-bg": "1", "bg": "color_11"},
                                            "propertiesSource": {"alpha-bg": "value", "bg": "theme"},
                                            "groups": {}},
        "componentClassName": "mobile.core.components.Page", "pageId": "", "spx": SPX, "compId": "",
        "skin": "wysiwyg.viewer.skins.page.ResponsivePageWithColorBG"}}}
    page.um["breakpointVariants"] = breakpoints(pid)
    imports = sorted({x.tag for x in page.walk()} - {HEADER, FOOTER, MENUCONT, SIDE})
    bindings = "import {connect} from 'document/bindings'\n" if any(
        getattr(x, "conn", None) for x in page.walk()) else ""
    structure = ("import {%s} from 'document'\nimport {%s, %s, %s, %s} from 'global-components'\n%s\n"
                 "const Structure = () => (\n%s\n)\n"
                 % (", ".join(imports), SIDE, FOOTER, HEADER, MENUCONT, bindings, jsx(page)))
    nodes = list(page.walk())
    unm = {"export": {"dependencies": {"references": {"components": {
        HEADER_ID: {"target": HEADER_ID, "type": "Container"},
        FOOTER_ID: {"target": FOOTER_ID, "type": "Container"},
        MENUCONT_ID: {"target": MENUCONT_ID, "type": "Container"},
        SIDE_ID: {"target": SIDE_ID, "type": "Container"}}, "data": data_refs(nodes)}}},
        "components": {x.id: x.um for x in nodes if x.um}}
    return {"version": "0.41.0", "structure": {"type": "jsx", "content": structure},
            "style": {"type": "css", "content": ""},
            "layout": {"type": "css", "content": layout_css(pid, nodes)},
            "unmapped": {"type": "json", "content": json.dumps(unm, ensure_ascii=False, indent=1)}}


def wrap(cid, kids, pad_top="56px", pad_bottom="0px", gap=None, css_extra=None, bp=None):
    """The static .wrap: 1020px centred in the space the column leaves, 48px inside
    (22px from 1000px down)."""
    css = {**size("100%", maxw="1020px"), **grid_item("1 / 2", "1 / 2", justify="center"),
           **flex_box("column", gap, (pad_top, "48px", pad_bottom, "48px"))}
    css.update(css_extra or {})
    bpx = {1000: {"padding-left": "22px", "padding-right": "22px"}}
    for k, v in (bp or {}).items():
        bpx.setdefault(k, {}).update(v)
    return box(cid, kids, css=css, bp=bpx)


def plain_section(cid, kids):
    return section(cid, kids, {**size(), **grid_box("minmax(0px, 1fr)", "auto")})


def placeholder(key, title):
    pid = PAGE_IDS.get(key, "wadpg" + key[:6])
    h1 = rtext("comp-wph1", f"<h1>{html.escape(title)}</h1>", css={**size("100%"), **flex_item()})
    return page_bundle(pid, title, key, [plain_section("comp-wpsec", [wrap("comp-wpwrap", [h1], pad_bottom="96px")])])


# ---------------------------------------------------------------- home
def home():
    pid = PAGE_IDS.get("home", "c1dmp")
    FI = flex_item
    full = size("100%")

    # hero: h1, portrait, body (intro, bio, actions), card
    h1 = rtext("comp-whh1", "<h1>Korkut Kaynardag, PhD</h1>",
               css={**size("100%"), **grid_item("1 / 2", "1 / 2")},
               bp={750: grid_item("1 / 2", "1 / 2")})
    portrait = image("comp-whpic", "portrait-kaynardag.jpg", "Korkut Kaynardag", 526, 657, radius="8px",
                     css={"width": "100%", "aspect-ratio": "4 / 5", "--height-type": "aspectRatio",
                          **grid_item("1 / 3", "2 / 3"), "max-width": "280px"},
                     bp={750: {**grid_item("2 / 3", "1 / 2"), "max-width": "280px"}})
    intro_html = SB.PROF_INTRO.replace('<p class="lede">', "<p>")
    lede_html, rest_html = intro_html.split("</p>", 1)
    lede = rtext("comp-whlede", lede_html + "</p>", "font_7", size="21px", lh="1.52em", ls="-0.004em",
                 css={**full, **FI()})
    # global.css (.hero-list): amber numerals, the sub-list as the static left-ruled block
    lst = cls(rtext("comp-whlist", rest_html, "font_7", color=C["ink"], css={**full, **FI(mt="12px")}),
              "hero-list")
    bio_head, bio_rest = SB.PROF_BIO.split("</p>", 1)
    myself = rtext("comp-whmy", bio_head + "</p>", css={**full, **FI(mt="28px")})
    bio = rtext("comp-whbio", bio_rest, css={**full, **FI(mt="19px")})
    b_about = button("comp-whbtn1", "About me", page_link("about"),
                     button_style(C["tint"], C["link"], C["tint_hover"], C["link_hover"]),
                     css={**size("auto", minh="44px"), **FI()})
    b_more = button("comp-whbtn2", "My research areas", page_link("research"),
                    button_style(None, C["link"], C["tint_hover"], C["link_hover"],
                                 pad=("0px", "8px", "0px", "20px"), icon=True),
                    css={**size("auto", minh="44px"), **FI()}, icon="arrow.svg")
    act = box("comp-whact", [b_about, b_more],
              css={**size("100%"), **FI(mt="32px"), **flex_box("row", "12px", align="center", wrap="wrap")})
    body = box("comp-whbody", [lede, lst, myself, bio, act],
               css={**size("100%"), **grid_item("2 / 4", "1 / 2"), **flex_box("column")},
               bp={750: grid_item("3 / 4", "1 / 2")})
    ids = rtext("comp-whids", f"<p>{SB.CONTACT['department']}</p><p>{SB.CONTACT['institution']}</p>",
                "font_8", color=C["ink"], css={**full, **FI(), "visibility": "hidden"},
                bp={1000: {"visibility": "visible"}})
    addr = rtext("comp-whaddr",
                 f"<p>{SB.CONTACT['city']}</p>", "font_8", color=C["body"], css={**full, **FI()})
    mail = rtext("comp-whmail",
                 f'<p><a href="mailto:{SB.CONTACT["email"]}">{SB.CONTACT["email"]}</a></p>',
                 "font_8", color=C["link"], css={**full, **FI(mt="12px")})
    card = box("comp-whcard", [ids, addr, mail],
               css={**size("100%"), **grid_item("3 / 4", "2 / 3"), **flex_box("column")},
               bp={750: {**grid_item("4 / 5", "1 / 2"), "padding-top": "24px"}})
    hero_grid = box("comp-whgrid", [h1, portrait, body, card],
                    css={**size("100%"), **FI(),
                         **grid_box("minmax(0px, 589fr) minmax(0px, 280fr)", "auto auto minmax(0px, 1fr)", "55px", "24px")},
                    bp={750: {"grid-template-columns": "minmax(0px, 1fr)",
                              "grid-template-rows": "auto auto auto auto", "column-gap": "0px",
                              "row-gap": "32px"}})
    hero = plain_section("comp-whsec", [wrap("comp-whwrap", [hero_grid])])

    # motivation: his block, restaged (parts/motivation.py)
    m = re.search(r"<h2>(.*?)</h2>.*?<p>(.*?)</p>\s*<ul>(.*?)</ul>\s*<p>(.*?)</p>\s*<p>(.*?)</p>",
                  SB.PROF_MOTIVATION, re.S)
    h2, p1, ul, aha, last = m.groups()
    points = re.findall(r"<li>(.*?)</li>", ul, re.S)
    mh2 = rtext("comp-wmh2", f"<h2>{h2}</h2>", css={**full, **FI()})
    mp1 = rtext("comp-wmp1", f"<p>{p1}</p>", css={**size("100%", maxw="608px"), **FI(mt="21px")})
    cells = []
    pads = [("0px", "32px", "28px", "0px"), ("0px", "0px", "28px", "32px"),
            ("28px", "32px", "0px", "0px"), ("28px", "0px", "0px", "32px")]
    for i, pt in enumerate(points):
        num = rtext(f"comp-wmn{i}", f"<p>{i + 1}</p>", "font_9", color=C["accent"], size="28px", lh="1em",
                    css={**full, **FI()})
        txt = rtext(f"comp-wmt{i}", f"<p>{pt}</p>", "font_7", color=C["ink"], size="21px", lh="1.4em",
                    ls="-0.004em", css={**full, **FI(mt="8px")})
        r, c = divmod(i, 2)
        cells.append(box(f"comp-wmc{i}", [num, txt],
                         css={**size("100%"), **grid_item(f"{r + 1} / {r + 2}", f"{c + 1} / {c + 2}",
                                                          align="stretch"),
                              **flex_box("column", pad=pads[i])},
                         bp={750: {**grid_item(f"{i + 1} / {i + 2}", "1 / 2", align="stretch"),
                                   "padding-top": "0px" if i == 0 else "14px",
                                   "padding-bottom": "0px" if i == 3 else "15px",
                                   "padding-left": "0px", "padding-right": "0px"}}))
    vline = box("comp-wmvl", [], css={**size("1px", "100%"), **grid_item("1 / 3", "2 / 3", align="stretch",
                                                                         justify="start")},
                bp={750: {"visibility": "hidden"}}, bg=C["rule"])
    hline = box("comp-wmhl", [], css={**size("100%", "1px"), **grid_item("2 / 3", "1 / 3", align="start")},
                bp={750: {"visibility": "hidden"}}, bg=C["rule"])
    grid4 = box("comp-wmgrid", cells + [vline, hline],
                css={**size("100%", maxw="720px"), **FI(mt="36px"),
                     **grid_box("minmax(0px, 1fr) minmax(0px, 1fr)", "auto auto")},
                bp={750: {"grid-template-columns": "minmax(0px, 1fr)",
                          "grid-template-rows": "auto auto auto auto", "margin-top": "28px"}})
    maha = rtext("comp-wmaha", f"<p>{aha}</p>", "font_7", color=C["ink"], size="28px", lh="1.3em",
                 ls="-0.01em", css={**size("100%", maxw="720px"), **FI(mt="28px")},
                 bp={750: {"margin-top": "24px"}})
    mlast = rtext("comp-wmlast", f"<p>{last}</p>", css={**size("100%", maxw="608px"), **FI(mt="36px")})
    motiv = plain_section("comp-wmsec", [wrap("comp-wmwrap", [mh2, mp1, grid4, maha, mlast], pad_top="47px")])

    # topics: three cards
    import importlib.util
    spec = importlib.util.spec_from_file_location("topics", os.path.join(ROOT, "site", "parts", "topics.py"))
    tmod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tmod)
    th2 = rtext("comp-wth2", "<h2>Explore the topics</h2>", css={**full, **FI()})
    cards = []
    icons = ["topic-waves.svg", "topic-window.svg", "topic-boundary.svg"]
    for i, (href, _svg, title, desc) in enumerate(tmod.TOPICS):
        key = href.replace(".html", "")
        rule = box(f"comp-wtr{i}", [], css={**size("100%", "1px"), **FI()}, bg=C["rule"])
        ic = vector(f"comp-wti{i}", icons[i], "", css={**size("28px", "28px"), **FI(mt="24px")})
        tt = cls(rtext(f"comp-wtt{i}", f'<h3><a href="topic/{key}">{title}</a></h3>', "font_3", underline=False,
                       css={**size("100%"), **FI(mt="16px")}), "topic-card-title")
        td = rtext(f"comp-wtd{i}", f"<p>{desc}</p>", "font_7", lh="1.5em",
                   css={**size("100%"), **FI(mt="8px", mb="20px")})
        card = cls(box(f"comp-wtc{i}", [rule, ic, tt, td],
                       css={**size("100%"), **grid_item("1 / 2", f"{i + 1} / {i + 2}", align="stretch"),
                            **flex_box("column")},
                       bp={750: grid_item(f"{i + 1} / {i + 2}", "1 / 2", align="stretch")}), "topic-card")
        card.attrs["codeName"] = f"topicCard{i}"
        cards.append(card)
    tgrid = box("comp-wtgrid", cards,
                css={**size("100%", maxw="924px"), **FI(mt="21px"),
                     **grid_box("minmax(0px, 1fr) minmax(0px, 1fr) minmax(0px, 1fr)", "auto", "40px")},
                bp={750: {"grid-template-columns": "minmax(0px, 1fr)", "grid-template-rows": "auto auto auto",
                          "column-gap": "0px"}})
    topics = plain_section("comp-wtsec", [wrap("comp-wtwrap", [th2, tgrid], pad_top="47px", pad_bottom="0px")])
    return page_bundle(pid, "Home", "home", [hero, motiv, topics])


# ================================================================ B2 helpers
def cls(n, *names):
    """Custom CSS classes on a component (the `classnames` feature): global.css
    targets them, written without the wixui- prefix."""
    n.um["classnames"] = {"type": "Classnames", "classnames": list(names)}
    return n


def part_mod(name):
    """One of the static site's parts (site/parts/<name>.py), for its words."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "site", "parts", name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def untag(s):
    """Markup of the static parts to the plain text Wix shows: <time> goes, the
    entities stay (the rich-text converter reads them)."""
    return re.sub(r"</?time[^>]*>", "", s)


# ================================================================ About Me
def about():
    """about.html: his About text beside the portrait, At a glance (the three
    figures of his last paragraph, parts/about.py) and the Career route
    (parts/timeline.py). Every word is a native text the editor edits; the route
    is drawn by global.css (.career-*) on empty boxes, and each role's heading
    comes before its dates in the page, as on the static site."""
    pid = PAGE_IDS["about"]
    reset_ids()
    FI = flex_item
    full = size("100%")
    h1 = rtext("comp-wah1", "<h1>About Me</h1>", css={**full, **FI()})

    # his text | portrait, CV line, profiles (static .hero.about: 1fr | 230px, 48px apart)
    text = cls(rtext("comp-watext", SB.PROF_ABOUT,
                     css={**size("100%", maxw="608px"), **grid_item("1 / 2", "1 / 2")},
                     bp={1000: grid_item("1 / 2", "1 / 2")}), "prose")
    pic = image("comp-wapic", "portrait-kaynardag.jpg", "Korkut Kaynardag", 526, 657, radius="8px",
                css={"width": "100%", "aspect-ratio": "4 / 5", "--height-type": "aspectRatio", **FI()},
                bp={1000: {"max-width": "220px"}})
    cv = rtext("comp-wacv", "<p>Curriculum vitae, coming soon.</p>", "font_8", color=C["muted"],
               css={**full, **FI(mt="20px")})
    profiles = cls(rtext("comp-waprof", "".join(f"<p>{n} (coming soon)</p>" for n in
                                                ("Google Scholar", "LinkedIn", "ResearchGate")),
                         "font_8", color=C["muted"], css={**full, **FI(mt="16px")}), "gap6")
    aside = box("comp-waaside", [pic, cv, profiles],
                css={**size("100%"), **grid_item("1 / 2", "2 / 3"), **flex_box("column")},
                bp={1000: grid_item("2 / 3", "1 / 2", mt="32px")})
    hero = box("comp-wahero", [text, aside],
               css={**full, **FI(mt="32px"),
                    **grid_box("minmax(0px, 646fr) minmax(0px, 230fr)", "auto", "48px")},
               bp={1000: {"grid-template-columns": "minmax(0px, 1fr)", "grid-template-rows": "auto auto",
                          "column-gap": "0px"}})

    # At a glance: three figures under hairlines, three across, one per row on a phone
    ab = part_mod("about")
    gh2 = rtext("comp-wagh2", "<h2>At a glance</h2>", css={**size("auto"), **FI()})
    gwhen = rtext("comp-wagwhen", "<p><strong>September 2026</strong></p>", "font_9", color=C["muted"],
                  size="14px", lh="1.5em", ls="0.01em", css={**size("auto"), **FI()})
    ghead = box("comp-waghead", [gh2, gwhen],
                css={**full, **FI(mt="47px"), **flex_box("row", "12px", align="end", wrap="wrap")})
    cards = []
    for i, (fig, label, note) in enumerate(ab.FIGURES):
        rule = box(f"comp-wagr{i}", [], css={**size("100%", "1px"), **grid_item("1 / 2", "1 / 2")},
                   bp={750: grid_item("1 / 2", "1 / 3")}, bg=C["rule"])
        f = rtext(f"comp-wagf{i}", f"<p>{fig}</p>", "font_7", color=C["accent"], size="40px", lh="1em",
                  ls="-0.014em", css={**full, **grid_item("2 / 3", "1 / 2", mt="24px")},
                  bp={750: grid_item("2 / 3", "1 / 2", mt="20px")})
        lab = rtext(f"comp-wagl{i}", f"<p>{label}</p>", "font_4", color=C["ink"],
                    css={**full, **grid_item("3 / 4", "1 / 2", mt="12px")},
                    bp={750: grid_item("2 / 3", "2 / 3", mt="20px", align="end")})
        kids = [rule, f, lab]
        if note:
            kids.append(rtext(f"comp-wagn{i}", f"<p>{note}</p>", "font_8", color=C["muted"],
                              css={**full, **grid_item("4 / 5", "1 / 2", mt="4px")},
                              bp={750: grid_item("3 / 4", "2 / 3", mt="4px")}))
        cards.append(box(f"comp-wagc{i}", kids,
                         css={**full, **grid_item("1 / 2", f"{i + 1} / {i + 2}", align="stretch"),
                              **grid_box("minmax(0px, 1fr)", "auto auto auto auto minmax(0px, 1fr)")},
                         bp={750: {**grid_item(f"{i + 1} / {i + 2}", "1 / 2", align="stretch"),
                                   "grid-template-columns": "minmax(0px, 60fr) minmax(0px, 286fr)",
                                   "grid-template-rows": "auto auto auto minmax(0px, 1fr)", "column-gap": "16px",
                                   "padding-bottom": "0px" if i == 2 else "20px"}}))
    ggrid = box("comp-wagg", cards,
                css={**full, **FI(mt="21px"),
                     **grid_box("minmax(0px, 1fr) minmax(0px, 1fr) minmax(0px, 1fr)", "auto", "40px")},
                bp={750: {"grid-template-columns": "minmax(0px, 1fr)", "grid-template-rows": "auto auto auto",
                          "column-gap": "0px"}})

    # Career: the route (parts/timeline.py). Grid per role: dates | rail | role, place,
    # note; on a phone rail | dates, role, place, note. The page lists the role first.
    tl = part_mod("timeline")
    ch2 = rtext("comp-wach2", "<h2>Career</h2>", css={**full, **FI(mt="47px")})
    items = []
    n = len(tl.ROLES)
    for i, (role, start, end, place, note, lane) in enumerate(tl.ROLES):
        now = end is None
        below = tl.ROLES[i + 1][5] if i + 1 < n else lane
        yrs = 0 if now else end - start
        classes = ["career-item", f"yrs-{yrs}"]
        classes += ["career-item--now"] if now else []
        classes += ["career-item--out"] if lane == 0 else []
        classes += ["career-item--turn"] if below != lane else []
        rows = 3 if note else 2
        r_role = cls(rtext(f"comp-wcr{i}", f"<h3>{role}</h3>", "font_3", color=C["ink"], size="21px",
                           lh="1.3em", ls="-0.004em",
                           css={**full, **grid_item("1 / 2", "3 / 4")},
                           bp={750: grid_item("2 / 3", "2 / 3")}), "career-role")
        dates = "Since 2026" if now else f"{start}&#8211;{end}"
        r_when = cls(rtext(f"comp-wcw{i}", f"<p><strong>{dates}</strong></p>", "font_9",
                           color=C["accent"] if now else C["muted"], size="14px", lh="1.5em", ls="0.01em",
                           css={**size("auto"), **grid_item("1 / 2", "1 / 2", justify="end", mt="2px")},
                           bp={750: grid_item("1 / 2", "2 / 3", justify="start")}), "career-when")
        r_place = rtext(f"comp-wcp{i}", "<p>" + ", ".join(place) + "</p>", "font_8", color=C["body"],
                        css={**full, **grid_item("2 / 3", "3 / 4", mt="4px")},
                        bp={750: grid_item("3 / 4", "2 / 3", mt="4px")})
        kids = [r_role, r_when, r_place]
        if note:
            kids.append(rtext(f"comp-wcn{i}", f"<p>{untag(note)}</p>", "font_8", color=C["muted"],
                              css={**full, **grid_item("3 / 4", "3 / 4", mt="4px")},
                              bp={750: grid_item("4 / 5", "2 / 3", mt="4px")}))
        rail = cls(box(f"comp-wcrl{i}", [cls(box(f"comp-wcrs{i}", [], css={**size("100%", "10px"),
                                                                             **grid_item("1 / 2", "1 / 2")}),
                                             "career-rest"),
                                         cls(box(f"comp-wcli{i}", [], css={**size("100%", "10px"),
                                                                            **grid_item("1 / 2", "1 / 2")}),
                                             "career-lit"),
                                         cls(box(f"comp-wcnd{i}", [], css={**size("100%", "10px"),
                                                                            **grid_item("1 / 2", "1 / 2")}),
                                             "career-node")],
                             css={**size("100%", "100%"), **grid_item(f"1 / {rows + 1}", "2 / 3", align="stretch"),
                                  **grid_box("minmax(0px, 1fr)", "minmax(0px, 1fr)")},
                             bp={750: grid_item(f"1 / {rows + 2}", "1 / 2", align="stretch")}),
                   "career-rail")
        last = i == n - 1
        items.append(cls(box(f"comp-wci{i}", kids + [rail],
                             css={**full, **FI(),
                                  **grid_box("minmax(0px, 80fr) minmax(0px, 34fr) minmax(0px, 582fr)",
                                             " ".join(["auto"] * rows), "12px",
                                             pad=("0px", "0px", "0px" if last else "36px", "0px"))},
                             bp={750: {"grid-template-columns": "minmax(0px, 34fr) minmax(0px, 300fr)",
                                       "grid-template-rows": " ".join(["auto"] * (rows + 1)),
                                       "padding-bottom": "0px" if last else "28px"}}),
                         *classes))
    clist = cls(box("comp-wacl", items, css={**size("100%", maxw="720px"), **FI(mt="21px"),
                                             **flex_box("column")}), "career-list")
    body = wrap("comp-wawrap", [h1, hero, ghead, ggrid, ch2, clist])
    return page_bundle(pid, "About Me", "about", [plain_section("comp-wasec", [body])])


# ================================================================ My Research Areas
DOC_ROUTER_ID = "routers-muefipcl"     # the Documents item router (prefix doc)
WORD_FILES = json.load(open(os.path.join(ROOT, "build", "studio", "wordfiles.json"), encoding="utf-8")) \
    if os.path.exists(os.path.join(ROOT, "build", "studio", "wordfiles.json")) else {}


def doc_link(slug, anchor=None):
    """A link to one document's page (/doc/<slug>), as the editor writes it."""
    return {"type": "DynamicPageLink", "routerId": DOC_ROUTER_ID, "innerRoute": slug,
            "anchorDataId": "", "target": "_self"}


def research():
    """research.html: his text, the four document boxes (parts/rboxes.py: his deck's
    labels, the plates, the drawing arrow, the Word line under each) and the
    educational sections. The title and the arrow of a box are links; the page's
    code (build/studio/research.js) makes the whole box open the document."""
    pid = PAGE_IDS["research"]
    reset_ids()
    FI = flex_item
    full = size("100%")
    rb = part_mod("rboxes")
    h1 = rtext("comp-wrh1", "<h1>My Research Areas</h1>", css={**full, **FI()})
    his = cls(rtext("comp-wrhis", SB.PROF_RESEARCH.replace('<p class="lede">', "<p>"),
                    css={**size("100%", maxw="608px"), **FI(mt="18px")}), "prose")
    dh2 = rtext("comp-wrdh2", "<h2>Documents</h2>", css={**full, **FI(mt="47px")})
    title_st = button_style(None, C["ink"], None, C["ink"], pad=("0px", "0px", "0px", "0px"), radius="0px",
                            fsize="19px", face=SERIF_SB, lh="1.35em", ls="0em", align="start")
    arrow_st = button_style(None, C["muted"], None, C["body"], pad=("0px", "0px", "0px", "0px"), radius="0px",
                            icon=True, gap="0px", label=False)
    dl_st = button_style(None, C["link"], None, C["link_hover"], pad=("0px", "4px", "0px", "0px"), radius="8px",
                         icon=True, gap="8px", fsize="14px", row="row-reverse")
    items = []
    sizes = {d["slug"]: d["mb"] for d in rb._DOCS if d.get("slug")}
    for i, d in enumerate(rb._DOCS):
        slug = d.get("slug")
        wait = not slug
        title = d["title"]
        if wait:
            t = rtext(f"comp-wrbt{i}", f"<p>{title}</p>", "font_4", color=C["ink"], lh="1.35em",
                      css={**full, **grid_item("1 / 2", "1 / 3")},
                      bp={750: grid_item("1 / 2", "2 / 3", align="center")})
        else:
            t = button(f"comp-wrbt{i}", title, doc_link(slug), title_st,
                       css={**full, **grid_item("1 / 2", "1 / 3")},
                       bp={750: grid_item("1 / 2", "2 / 3", align="center")})
            cls(t, "rcard-title")
        plate = vector(f"comp-wrbp{i}", f"plate-{d['icon']}{'-wait' if wait else ''}.svg", "",
                       css={**size("56px", "56px"), **grid_item("2 / 3", "1 / 2", align="end", ml="-5px")},
                       bp={750: grid_item("1 / 2", "1 / 2", align="center", ml="-5px")})
        kids = [t, plate]
        if not wait:
            kids.append(cls(button(f"comp-wrba{i}", "Open", doc_link(slug), arrow_st, icon="arrow-draw.svg",
                                   css={**size("24px", "24px"), **grid_item("2 / 3", "2 / 3", align="end",
                                                                          justify="end", mb="0px")},
                                   bp={750: grid_item("1 / 2", "3 / 4", align="center", justify="end")}),
                            "rcard-arrow"))
        card = box(f"comp-wrbc{i}", kids,
                   css={**size("calc(100% + 24px)"), **FI(ml="-12px"), "flex-grow": "1", "flex-basis": "auto",
                        **grid_box("minmax(0px, 1fr) minmax(0px, 1fr)", "auto minmax(0px, 1fr)", "16px", "24px",
                                   pad=("20px", "12px", "16px", "12px"))},
                   bp={750: {"grid-template-columns": "minmax(0px, 56fr) minmax(0px, 230fr) minmax(0px, 24fr)",
                             "grid-template-rows": "auto", "row-gap": "0px", "flex-grow": "0",
                             "padding-top": "16px", "padding-bottom": "16px"}})
        cls(card, "rcard", *(["rcard--wait"] if wait else []))
        if not wait:
            card.attrs["codeName"] = f"rcard{i}"
        under = []
        if wait:
            under.append(rtext(f"comp-wrbw{i}", "<p><strong>Presentation, coming soon</strong></p>", "font_9",
                               color=C["muted"], size="14px", lh="1.3em", ls="0.01em",
                               css={**size("auto"), **FI(mt="14px")}))
        elif WORD_FILES.get(slug):
            dl = button(f"comp-wrbd{i}", "Download Word",
                        {"type": "ExternalLink", "url": WORD_FILES[slug], "target": "_blank"}, dl_st,
                        icon="download.svg", css={**size("auto", "44px"), **FI(ml="-5px")})
            mb = rtext(f"comp-wrbm{i}", f"<p><strong>{sizes[slug]}&nbsp;MB</strong></p>", "font_9",
                       color=C["muted"], size="14px", lh="1.3em", ls="0.01em", css={**size("auto"), **FI()})
            under.append(box(f"comp-wrbl{i}", [dl, mb],
                             css={**size("auto"), **FI(mt="4px"), **flex_box("row", "2px", align="center")}))
        items.append(box(f"comp-wrbi{i}", [card] + under,
                         css={**full, **grid_item("1 / 2", f"{i + 1} / {i + 2}", align="stretch"),
                              **flex_box("column", align="start")},
                         bp={1000: grid_item(f"{i // 2 + 1} / {i // 2 + 2}", f"{i % 2 + 1} / {i % 2 + 2}",
                                             align="stretch"),
                             750: grid_item(f"{i + 1} / {i + 2}", "1 / 2", align="stretch")}))
    grid4 = box("comp-wrbg", items,
                css={**full, **FI(mt="21px"),
                     **grid_box("minmax(0px, 1fr) minmax(0px, 1fr) minmax(0px, 1fr) minmax(0px, 1fr)", "auto",
                                "32px", "40px")},
                bp={1000: {"grid-template-columns": "minmax(0px, 1fr) minmax(0px, 1fr)",
                           "grid-template-rows": "auto auto"},
                    750: {"grid-template-columns": "minmax(0px, 1fr)", "grid-template-rows": "auto auto auto auto",
                          "column-gap": "0px", "row-gap": "24px"}})
    eh2 = rtext("comp-wreh2", "<h2>The educational sections</h2>", css={**full, **FI(mt="47px")})
    more = cls(rtext("comp-wrmore", SB.PROF_RESEARCH_MORE, css={**size("100%", maxw="608px"), **FI(mt="21px")}),
               "prose")
    body = wrap("comp-wrwrap", [h1, his, dh2, grid4, eh2, more])
    return page_bundle(pid, "My Research Areas", "research", [plain_section("comp-wrsec", [body])])


# ================================================================ Contact
def contact():
    """contact.html: where to find him (department, the one address, office) and
    the profiles still to come. No form: the static page has none."""
    pid = PAGE_IDS["contact"]
    reset_ids()
    FI = flex_item
    full = size("100%")
    muted = f'style="color:{C["muted"]};"'
    h1 = rtext("comp-wch1", "<h1>Contact</h1>", css={**full, **FI()})
    lede = rtext("comp-wclede", "<p>Feel free to reach out about research, collaboration, or the educational "
                 "sections of this site, especially if you are a student or newcomer to these topics.</p>",
                 "font_7", size="21px", lh="1.52em", ls="-0.004em", color=C["body"],
                 css={**size("100%", maxw="608px"), **FI(mt="18px")})
    fh2 = rtext("comp-wcfh2", "<h2>Where to find me</h2>", css={**full, **FI(mt="47px")})
    mail = SB.CONTACT["email"]
    find = cls(rtext("comp-wcfind",
                     f"<p><strong>{SB.CONTACT['department']}</strong><br>"
                     f"<span {muted}>{SB.CONTACT['institution']}, {SB.CONTACT['city']}</span></p>"
                     f'<p><strong>Email</strong><br><a href="mailto:{mail}"><span style="color:{C["link"]};">'
                     f"{mail}</span></a></p>"
                     f"<p><strong>Office</strong><br><span {muted}>Coming soon</span></p>",
                     "font_7", color=C["ink"], css={**size("100%", maxw="608px"), **FI(mt="24px")}), "find")
    eh2 = rtext("comp-wceh2", "<h2>Elsewhere</h2>", css={**full, **FI(mt="47px")})
    col = rtext("comp-wccol", "<p>My academic profiles and CV will be linked here.</p>", "font_7", color=C["body"],
                css={**size("100%", maxw="608px"), **FI(mt="21px")})
    links = cls(rtext("comp-wclinks", "".join(f"<p>{n} (coming soon)</p>" for n in
                                              ("Google Scholar", "LinkedIn", "ResearchGate")),
                      "font_8", color=C["muted"], css={**full, **FI(mt="16px")}), "gap6")
    body = wrap("comp-wcwrap", [h1, lede, fh2, find, eh2, col, links])
    return page_bundle(pid, "Contact", "contact", [plain_section("comp-wcsec", [body])])


# ================================================================ documents (CMS)
DOC_ROUTER_PAGE = "jqsq0"                    # "Documents (Item)", router prefix doc, pattern /{slug}
DOC_ITEM_DATASET = "dataItem-lljy9q0w6"     # its router dataset (made by the editor; keep the id)
DOC_LINK_FIELD = "link-documents-1-title"   # the collection's PAGE_LINK field for that page


def connect(role, to, props=None, events=None):
    """document/bindings connect(...), as the editor exports it."""
    cfg = []
    if props:
        cfg.append("properties: {%s}" % ", ".join(f"{k}: {{fieldName: '{v}'}}" for k, v in props.items()))
    if events:
        cfg.append("events: {%s}" % ", ".join(f"{k}: {{action: '{v}'}}" for k, v in events.items()))
    return f"connect('{role}', {{to: '{to}', primary: true, config: {{{', '.join(cfg)}}}}})"


def dataset(cid, name, ds_id, collection=None, router=False, code="dataset1"):
    if router:
        settings = {"dataset": {"readWriteType": "READ"}}
        ctype = "router_dataset"
    else:
        settings = {"dataset": {"collectionName": collection, "readWriteType": "READ", "filter": None,
                                "sort": None, "includes": None, "includeFieldGroups": None, "nested": [],
                                "pageSize": 100}}
        ctype = "dataset"
    n = N("AppController", cid, None if router else "platform.components.skins.controllerSkin",
          data={"type": "AppController", "applicationId": "dataBinding", "name": name, "controllerType": ctype,
                "settings": json.dumps(settings, separators=(",", ":")), "id": ds_id},
          attrs={"codeName": code})
    return n


def repeater_layout(mt="24px"):
    """A Repeater keeps its own layout in unmapped (the export has no CSS rule for it)."""
    px = lambda v: {"type": "px", "value": v}
    return {"variants": [], "default": {
        "type": "SingleLayoutData", "spx": SPX,
        "containerLayout": {"type": "FlexContainerLayout", "direction": "column", "rowGap": px(0),
                            "columnGap": px(0), "justifyContent": "start", "wrap": "nowrap",
                            "overflowX": "visible", "overflowY": "visible", "hideScrollbar": False},
        "componentLayout": {"type": "ComponentLayout", "width": {"type": "percentage", "value": 100},
                            "height": {"type": "auto"}, "maxWidth": px(744), "hidden": False},
        "itemLayout": {"type": "FlexItemLayout",
                       "margins": {"top": px(int(mt[:-2])), "left": px(-12), "right": px(0), "bottom": px(0)}}}}


def documents_index():
    """The documents, one row each, from the Documents collection: a new CMS row is a
    new row here (and a new page at /doc/<slug>) with no editor work."""
    pid = PAGE_IDS["documents"]
    reset_ids()
    FI = flex_item
    ds_id = "dataItem-wdocsds"
    h1 = rtext("comp-wdh1", "<h1>Documents</h1>", css={**size("100%"), **FI()})
    lede = rtext("comp-wdlede", "<p>The documents introduced under My Research Areas, plus the guides behind "
                 "each topic section.</p>", "font_7", size="21px", lh="1.52em", ls="-0.004em",
                 css={**size("100%", maxw="608px"), **FI(mt="18px")})
    # the title is a link (a text's link binding draws no link in Studio): a button
    # whose label is the title and whose link is the item's page
    tstyle = button_style(None, C["ink"], None, C["ink"], pad=("0px", "0px", "0px", "0px"), radius="0px",
                          fsize="19px", face=SERIF_SB, lh="1.35em", ls="0em", align="start")
    title = button("comp-wdrt", "Document title", None, tstyle, css={**size("100%"), **FI()})
    title.conn = connect("siteButtonRole", ds_id, {"label": "title", "link": DOC_LINK_FIELD})
    title.attrs["codeName"] = "docTitle"
    note = rtext("comp-wdrn", "<p>Summary</p>", "font_8", color=C["muted"], lh="1.5em",
                 css={**size("100%"), **FI(mt="4px")})
    note.conn = connect("textRole", ds_id, {"$text": "summary"})
    text = box("comp-wdrtext", [title, note], css={**size("calc(100% - 48px)"), **FI(), **flex_box("column")})
    astyle = button_style(None, C["muted"], None, C["body"], pad=("0px", "0px", "0px", "0px"), radius="0px",
                          icon=True, gap="0px", label=False)
    arrow = cls(button("comp-wdrarr", "Open", None, astyle, icon="arrow-draw.svg",
                       css={**size("24px", "24px"), **FI()}), "rcard-arrow")
    arrow.conn = connect("siteButtonRole", ds_id, {"link": DOC_LINK_FIELD})
    row = box("comp-wdrrow", [text, arrow],
              css={**size("100%"), **FI(), **flex_box("row", "24px", pad=("20px", "12px", "20px", "12px"),
                                                     align="center", justify="space-between")})
    # global.css (.doc-row): the row takes the static hover tint
    row.um["classnames"] = {"type": "Classnames", "classnames": ["doc-row"]}
    rule = box("comp-wdrrule", [], css={**size("calc(100% - 24px)", "1px"), **FI(ml="12px")}, bg=C["rule"])
    item = box("comp-wdritem", [rule, row],
               css={**size("100%"), "--item-layout-type": "FlexItemLayout", "flex-basis": "auto",
                    "flex-grow": "0", "flex-shrink": "0", **flex_box("column")})
    rep = N("Repeater", "comp-wdrep", "wysiwyg.viewer.skins.area.DefaultAreaSkin",
            data={"type": "Repeater", "items": ["item1"]},
            props={"type": "CardsLayoutProperties", "gap": {"vertical": 0, "horizontal": 0}},
            kids=[item], um=box_style())
    rep.um["layout"] = repeater_layout()
    rep.conn = connect("repeaterRole", ds_id)
    wrapd = wrap("comp-wdwrap", [h1, lede, rep], pad_bottom="0px")
    ds = dataset("comp-wdds", "Documents dataset", ds_id, "Documents", code="documentsDataset")
    return page_bundle(pid, "Documents", "documents", [plain_section("comp-wdsec", [wrapd])], extra=[ds])


def document_item():
    """One page per Documents row (router /doc/{slug}), laid out as the static
    .docpage: back link, the cover picture (coverImage), his title, subtitle and
    byline, "Download Word" (wordFile), a rule, then the document in a Rich Content
    Viewer, all in the 672px reading column. The page's code (build/studio/doc-item.js)
    collapses the cover and the Word line for an item without them; global.css
    (.doc-body) sets the text in the static page's type."""
    pid = DOC_ROUTER_PAGE
    reset_ids()
    FI = flex_item
    ds_id = DOC_ITEM_DATASET
    back = button_style(None, C["muted"], C["ink5"], C["ink"], pad=("0px", "10px", "0px", "2px"),
                        radius="8px", icon=True, gap="4px", fsize="14px", row="row-reverse")
    crumb = button("comp-wicrumb", "Documents", page_link("documents"), back, icon="chevron-left.svg",
                   css={**size("auto", "44px"), **FI(align="start", mt="-10px", ml="-6px")})
    crumb.attrs["codeName"] = "docCrumb"
    # static: crumb, 20px, the picture, 36px, the title; the picture's own margins go
    # with it when an item has none
    # fitted whole (doc-item.js); what the frame leaves around a wider picture is the page
    cover = image("comp-wicover", "portrait-kaynardag.jpg", "", 526, 657, radius="8px", bg_alpha=0,
                  css={"width": "100%", "aspect-ratio": "1 / 0.25", "--height-type": "aspectRatio",
                       **FI(mt="20px", mb="16px")})
    cover.conn = connect("imageRole", ds_id, {"src": "coverImage"})
    cover.attrs["codeName"] = "docCover"
    h1 = rtext("comp-wih1", "<h1>Document title</h1>", css={**size("100%"), **FI(mt="20px")})
    h1.conn = connect("textRole", ds_id, {"$text": "title"})
    # global.css: on a phone the title and subtitle step down as on the static page
    h1.um["classnames"] = {"type": "Classnames", "classnames": ["doc-title"]}
    sub = rtext("comp-wisub", "<p>Subtitle</p>", "font_7", size="21px", lh="1.45em", ls="-0.004em",
                color=C["body"], css={**size("100%"), **FI(mt="16px")})
    sub.conn = connect("textRole", ds_id, {"$text": "subtitle"})
    sub.um["classnames"] = {"type": "Classnames", "classnames": ["doc-dek"]}
    sub.attrs["codeName"] = "docSub"
    by = rtext("comp-wiby", "<p>Byline</p>", "font_8", color=C["muted"], css={**size("100%"), **FI(mt="14px")})
    by.conn = connect("textRole", ds_id, {"$text": "byline"})
    by.attrs["codeName"] = "docBy"
    dl = button_style(None, C["link"], None, C["link_hover"], pad=("0px", "4px", "0px", "0px"),
                      radius="8px", icon=True, gap="8px", fsize="14px", row="row-reverse")
    word = button("comp-wiword", "Download Word", None, dl, icon="download.svg",
                  css={**size("auto", "44px"), **FI(align="start", mt="12px", ml="-5px")})
    word.conn = connect("siteButtonRole", ds_id, {"link": "wordFile"})
    word.attrs["codeName"] = "docWord"
    rule = box("comp-wirule", [], css={**size("100%", "1px"), **FI(mt="32px")}, bg=C["rule"])
    body = N("RichContentViewer", "comp-wibody", None,
             data={"type": "wixui.RichContentViewer", "trimEnabled": False},
             css={**size("100%"), **FI(mt="40px")},
             um={"classnames": {"type": "Classnames", "classnames": ["doc-body"]}})
    body.conn = connect("richContentRole", ds_id, {"content": "body"})
    body.attrs["codeName"] = "docBody"
    col = box("comp-wicol", [crumb, cover, h1, sub, by, word, rule, body],
              css={**size("100%", maxw="768px"), **grid_item("1 / 2", "1 / 2", justify="center"),
                   **flex_box("column", pad=("40px", "48px", "0px", "48px"))},
              bp={1000: {"padding-left": "22px", "padding-right": "22px"}})
    ds = dataset("comp-wids", "Documents Item", ds_id, router=True, code="dynamicDataset")
    b = page_bundle(pid, "Documents (Item)", "blank", [plain_section("comp-wisec", [col])], extra=[ds],
                    page_data={"hidePage": True, "managingAppDefId": "dataBinding"})
    return b


# ================================================================ Topics (dynamic)
TOPIC_ROUTER_PAGE = "npfs3"                  # "Topics (Item)", router prefix topic, pattern /{slug}
TOPIC_ROUTER_ID = "routers-muelmf01"
TOPIC_ITEM_DATASET = "dataItem-lljy9q0w6"    # its router dataset (made by the editor)
TOPIC_LINK_FIELD = "link-topics-title"       # the collection's link to that page


def topic_link(slug):
    return {"type": "DynamicPageLink", "routerId": TOPIC_ROUTER_ID, "innerRoute": slug,
            "anchorDataId": "", "target": "_self"}


def topic_item():
    """One page per Topics row (/topic/<slug>), as the static topic pages: the title,
    the introduction, "Start here" (the row to its guide, filled by the page's code
    from the row's guide, build/studio/topic-item.js) and the sections from the
    row's body in a Rich Content Viewer (global.css .topic-body: a quote block is
    a section in preparation, a one-item list is a row into the guide)."""
    pid = TOPIC_ROUTER_PAGE
    reset_ids()
    FI = flex_item
    full = size("100%")
    ds_id = TOPIC_ITEM_DATASET
    h1 = rtext("comp-wth1", "<h1>Topic title</h1>", css={**full, **FI()})
    h1.conn = connect("textRole", ds_id, {"$text": "title"})
    lede = rtext("comp-wtlede", "<p>Introduction</p>", "font_7", size="21px", lh="1.52em", ls="-0.004em",
                 color=C["body"], css={**size("100%", maxw="608px"), **FI(mt="18px")})
    lede.conn = connect("textRole", ds_id, {"$text": "lede"})
    sh2 = rtext("comp-wtsh2", "<h2>Start here</h2>", css={**full, **FI(mt="47px")})
    sh2.attrs["codeName"] = "startHead"
    title_st = button_style(None, C["ink"], None, C["ink"], pad=("0px", "0px", "0px", "0px"), radius="0px",
                            fsize="19px", face=SERIF_SB, lh="1.35em", ls="0em", align="start")
    arrow_st = button_style(None, C["muted"], None, C["body"], pad=("0px", "0px", "0px", "0px"), radius="0px",
                            icon=True, gap="0px", label=False)
    t = button("comp-wtst", "The guide", None, title_st, css={**full, **FI()})
    t.attrs["codeName"] = "startTitle"
    note = rtext("comp-wtsn", "<p>Its summary</p>", "font_8", color=C["muted"], lh="1.5em",
                 css={**full, **FI(mt="4px")})
    note.attrs["codeName"] = "startNote"
    text = box("comp-wtstx", [t, note], css={**size("calc(100% - 48px)"), **FI(), **flex_box("column")})
    arrow = cls(button("comp-wtsa", "Open", None, arrow_st, icon="arrow-draw.svg",
                       css={**size("24px", "24px"), **FI()}), "rcard-arrow")
    arrow.attrs["codeName"] = "startArrow"
    row = cls(box("comp-wtsr", [text, arrow],
                  css={**full, **FI(), **flex_box("row", "24px", pad=("20px", "12px", "20px", "12px"),
                                                  align="center", justify="space-between")}), "doc-row")
    r1 = box("comp-wtr1", [], css={**size("calc(100% - 24px)", "1px"), **FI(ml="12px")}, bg=C["rule"])
    r2 = box("comp-wtr2", [], css={**size("calc(100% - 24px)", "1px"), **FI(ml="12px")}, bg=C["rule"])
    group = box("comp-wtsg", [r1, row, r2],
                css={**size("calc(100% + 24px)", maxw="744px"), **FI(mt="21px", ml="-12px"), **flex_box("column")})
    group.attrs["codeName"] = "startRow"
    body = N("RichContentViewer", "comp-wtbody", None,
             data={"type": "wixui.RichContentViewer", "trimEnabled": False},
             css={**full, **FI()},
             um={"classnames": {"type": "Classnames", "classnames": ["doc-body", "topic-body"]}})
    body.conn = connect("richContentRole", ds_id, {"content": "body"})
    body.attrs["codeName"] = "topicBody"
    col = wrap("comp-wtwrap", [h1, lede, sh2, group, body])
    ds = dataset("comp-wtds", "Topics Item", ds_id, router=True, code="dynamicDataset")
    return page_bundle(pid, "Topics (Item)", "topic-item", [plain_section("comp-wtsec", [col])], extra=[ds],
                       page_data={"hidePage": True, "managingAppDefId": "dataBinding"})


# ================================================================ gallery (CMS)
# The Pro Gallery widget (Media > Pro Galleries in the Add panel). Its layout
# settings are the widget's style params, set in the browser at import
# (runner.js __importGallery), since the bundle cannot carry the widget's style.
PRO_GALLERY = {"widgetId": "142bb34d-3439-576a-7118-683e690a1e0d", "applicationId": "39",
               "appDefinitionId": "14271d6f-ba62-d045-549b-ab972ae1f70e", "usesCssPerBreakpoint": False,
               "referenceId": "4a1927cc-80dc-450d-8e5a-84ee723ef468", "type": "TPAWidget"}
# the ids the two widgets have in the document now (a page import gives every
# component of the bundle a new id; __importGallery copies the style by these)
GALLERY_WIDE = ("comp-muemrnd39", "data-muemrnd311")     # one row per set (above 750px)
GALLERY_PHONE = ("comp-muemrnd5", "data-muemrnd52")      # pairs (750px and below)


def pro_gallery(ids, css, bp, code):
    cid, did = ids
    n = N("TPAWidget", cid, "wysiwyg.viewer.skins.TPAWidgetSkin", data={**PRO_GALLERY, "id": did},
          css=css, bp=bp, attrs={"codeName": code})
    return n


def gallery():
    """gallery.html: his sets in his order (GallerySets, through the repeater's
    dataset), each under his caption and its period, with the set's photos and
    the film from the Photos collection in their order. The page's code
    (build/studio/gallery.js) gives each set's two galleries their items and the
    set's box its proportions (global.css .gal-box: the row stops at 380px tall,
    330px under 1200px, as the static row does). A new Photos row, or a new set,
    shows with no editor work."""
    pid = PAGE_IDS["gallery"]
    reset_ids()
    FI = flex_item
    full = size("100%")
    ds_id = "dataItem-wgsetsds"
    h1 = rtext("comp-wgh1", "<h1>Gallery</h1>", css={**full, **FI()})
    title = cls(rtext("comp-wgt", "<h2>Set caption</h2>", css={**size("100%", maxw="608px"), **FI()}), "gset-h")
    # not bound to the dataset: a binding writes his line breaks as <br> and could win the race
    # with the page's code, which sets the caption as one line
    title.attrs["codeName"] = "setTitle"
    era = cls(rtext("comp-wge", "<p>(during my studies)</p>", "font_8", color=C["muted"],
                    css={**size("100%", maxw="608px"), **FI(mt="2px")}), "gset-era")
    era.conn = connect("textRole", ds_id, {"$text": "period"})
    era.attrs["codeName"] = "setEra"
    wide = pro_gallery(GALLERY_WIDE, {**full, **FI()}, {750: {"visibility": "hidden"}}, "setGallery")
    phone = pro_gallery(GALLERY_PHONE, {**full, **FI(), "visibility": "hidden"},
                        {750: {"visibility": "visible"}}, "setGalleryPhone")
    gbox = cls(box("comp-wgbox", [wide, phone], css={**full, **FI(mt="16px"), **flex_box("column")},
                   bp={750: {"margin-top": "14px"}}), "gal-box")
    gbox.attrs["codeName"] = "setBox"
    item = box("comp-wgitem", [title, era, gbox],
               css={**full, "--item-layout-type": "FlexItemLayout", "flex-basis": "auto",
                    "flex-grow": "0", "flex-shrink": "0", **flex_box("column", pad=("56px", "0px", "0px", "0px"))},
               bp={750: {"padding-top": "44px"}})
    rep = N("Repeater", "comp-wgrep", "wysiwyg.viewer.skins.area.DefaultAreaSkin",
            data={"type": "Repeater", "items": ["item1"]},
            props={"type": "CardsLayoutProperties", "gap": {"vertical": 0, "horizontal": 0}},
            kids=[item], um=box_style(), attrs={"codeName": "setList"})
    px = lambda v: {"type": "px", "value": v}
    rep.um["layout"] = {"variants": [], "default": {
        "type": "SingleLayoutData", "spx": SPX,
        "containerLayout": {"type": "FlexContainerLayout", "direction": "column", "rowGap": px(0),
                            "columnGap": px(0), "justifyContent": "start", "wrap": "nowrap",
                            "overflowX": "visible", "overflowY": "visible", "hideScrollbar": False},
        "componentLayout": {"type": "ComponentLayout", "width": {"type": "percentage", "value": 100},
                            "height": {"type": "auto"}, "hidden": False},
        "itemLayout": {"type": "FlexItemLayout",
                       "margins": {"top": px(-16), "left": px(0), "right": px(0), "bottom": px(0)}}}}
    rep.conn = connect("repeaterRole", ds_id)
    body = wrap("comp-wgwrap", [h1, rep], pad_bottom="0px")
    ds = dataset("comp-wgds", "Gallery sets dataset", ds_id, "GallerySets", code="setsDataset")
    return page_bundle(pid, "Gallery", "gallery", [plain_section("comp-wgsec", [body])], extra=[ds])


# ================================================================ blog (the Blog app's pages)
def component_bundle(root):
    """One component and its children, for DS.importExport.components.jsx.add into
    a container of a page (the Blog's pages, whose app sections are left as they
    stand). No breakpoint rules: global.css carries the narrower padding."""
    nodes = list(root.walk())
    imports = sorted({x.tag for x in nodes})
    structure = ("import {%s} from 'document'\n\nconst Structure = () => (\n%s\n)\n"
                 % (", ".join(imports), jsx(root)))
    refs = data_refs(nodes)
    unm = {"export": {"dependencies": {"references": {"data": refs}}} if refs else {},
           "components": {x.id: x.um for x in nodes if x.um}}
    return {"version": "0.41.0", "structure": {"type": "jsx", "content": structure},
            "style": {"type": "css", "content": ""},
            "layout": {"type": "css", "content": layout_css(None, nodes)},
            "unmapped": {"type": "json", "content": json.dumps(unm, ensure_ascii=False, indent=1)}}


def blog_head():
    """blog.html's heading and lede, above the Blog app's feed (class blog-head:
    global.css gives it the static .wrap's padding, 22px from 1000px down)."""
    reset_ids()
    FI = flex_item
    h1 = rtext("comp-wbh1", "<h1>Blog</h1>", css={**size("100%"), **FI()})
    lede = rtext("comp-wblede", "<p>Shorter pieces on structural health monitoring, wave propagation and the "
                 "data side of the work.</p>", "font_7", size="21px", lh="1.52em", ls="-0.004em", color=C["body"],
                 css={**size("100%", maxw="608px"), **FI(mt="18px")})
    head = cls(box("comp-wbhead", [h1, lede],
                   css={**size("100%", maxw="1020px"), **grid_item("1 / 2", "1 / 2", justify="center"),
                        **flex_box("column", None, ("56px", "48px", "0px", "48px"))}), "blog-head")
    return component_bundle(head)


def post_crumb():
    """The static post page's crumb back to the Blog, above the Blog app's post
    (its box centred on the post's text column; class post-crumb)."""
    reset_ids()
    FI = flex_item
    back = button_style(None, C["muted"], C["ink5"], C["ink"], pad=("0px", "10px", "0px", "2px"),
                        radius="8px", icon=True, gap="4px", fsize="14px", row="row-reverse")
    crumb = button("comp-wpcb", "Blog", page_link("blog"), back, icon="chevron-left.svg",
                   css={**size("auto", "44px"), **FI(align="start", ml="-6px")})
    head = cls(box("comp-wpcrumb", [crumb],
                   css={**size("100%", maxw="740px"), **grid_item("1 / 2", "2 / 3", justify="center"),
                        **flex_box("column", None, ("46px", "0px", "0px", "0px"))}), "post-crumb")
    return component_bundle(head)


# ================================================================ the shell
MENU_BASE = json.load(open(os.path.join(HERE, "studio", "menu_vertical_base.json"), encoding="utf-8"))
HDR_BP = {"all": "variants-ljclok8y", 1000: "variants-ljclok8y1", 750: "variants-ljclok8y2"}
# a Menu's inner parts, by role, and the template header menu's ids for them: their
# styles are long stylable-CSS strings, copied in the page (the bundle's "copy" list)
MENU_PARTS = ["mega", "sub", "root", "open", "overlay", "cont", "content", "close"]
TEMPLATE_PARTS = dict(mega="comp-mb5540ni1", sub="comp-mb5540nj5", root="comp-mb5540nl1",
                      open="comp-mb5540nm5", overlay="comp-mb5540no", cont="comp-mb5540np4",
                      content="comp-mb5540nq12", close="comp-mb5540nr1")
MENU_FONT_KEYS = ("item-font", "dropdown-menu-item-font", "dropdown-menu-item-hover-font",
                  "dropdown-menu-item-selected-font", "dropdown-menu-sub-item-font")


def menu_props(kind):
    """The column's list: white sans 600 15px labels at x=20, the current page on
    --nav-hover with a 3px --accent-2 rail, hover half a step lighter than the
    column; the list under Documents one step quieter, indented to x=32."""
    p = dict(MENU_BASE["properties"])
    white = "rgba(255,255,255,1)"
    clear = "0px solid rgba(255,255,255,0)"
    p.update({
        "orientation": "vertical", "display-mode": "hamburger" if kind == "drawer" else "navbar",
        "container-align": "start", "menu-items-justification": "start",
        "menu-items-main-axis-gap": "0px", "menu-items-cross-axis-gap": "0px", "item-text-align": "start",
        "container-background": "rgba(255,255,255,0)",
        "item-font": "font_5", "item-color": white, "item-hover-color": white, "item-selected-color": white,
        "item-line-height": "1.4em", "item-letter-spacing": "0.006em",
        "item-vertical-padding": "16px", "item-horizontal-padding": "17px",
        "item-background": "rgba(255,255,255,0)", "item-hover-background": rgba(C["nav_mix"]),
        "item-selected-background": rgba(C["nav_hover"]),
        "item-border-left": "3px solid rgba(255,255,255,0)",
        "item-hover-border-left": "3px solid rgba(255,255,255,0)",
        "item-selected-border-left": "3px solid " + rgba(C["accent2"]),
        "item-border-top": clear, "item-border-bottom": clear, "item-border-right": clear,
        "item-hover-border-top": clear, "item-hover-border-bottom": clear, "item-hover-border-right": clear,
        "item-selected-border-top": clear, "item-selected-border-bottom": clear,
        "item-selected-border-right": clear,
        "item-hover-text-decoration": "none", "item-selected-text-decoration": "none",
        "item-icon-color": rgba(C["nav_mute"]), "item-hover-icon-color": white,
        "item-selected-icon-color": white, "item-icon-size": "12px",
        # the documents list is open wherever it is shown: masterPage.js puts it under
        # "Documents" on the Documents page and on a document's page only (static: open
        # there, folded elsewhere); expandCollapse would keep it shut on a document's page
        "vertical-dropdown-display": "alwaysOpen",
        "dropdown-menu-item-font": "font_9", "dropdown-menu-item-hover-font": "font_9",
        "dropdown-menu-item-selected-font": "font_9",
        "dropdown-menu-item-color": rgba(C["nav_mute"]), "dropdown-menu-item-hover-color": white,
        "dropdown-menu-item-selected-color": white,
        "dropdown-menu-item-hover-text-decoration": "none",
        "dropdown-menu-item-selected-text-decoration": "none",
        # static .nav__sub a: text at x=32 (29px padding after the 3px rail every state carries)
        "dropdown-menu-item-vertical-padding": "8px", "dropdown-menu-item-horizontal-padding": "29px",
        "dropdown-menu-item-border-left": "3px solid rgba(255,255,255,0)",
        "dropdown-menu-item-hover-border-left": "3px solid rgba(255,255,255,0)",
        "dropdown-menu-item-selected-border-left": "3px solid " + rgba(C["accent2"]),
        "dropdown-menu-item-vertical-spacing": "0px", "dropdown-menu-container-horizontal-padding": "0px",
        "dropdown-menu-container-vertical-padding": "0px",
        "dropdown-menu-item-background": "rgba(255,255,255,0)",
        "dropdown-menu-item-hover-background": rgba(C["nav_mix"]),
        "dropdown-menu-item-selected-background": rgba(C["nav_hover"]),
        "dropdown-menu-sub-items-vertical-spacing-before": "0px",
        "dropdown-menu-sub-items-vertical-spacing-between": "0px",
    })
    return p


def menu_style(kind, border_top=False, variants=None):
    p = menu_props(kind)
    if border_top:
        p["container-border-top"] = "1px solid rgba(255,255,255,0.14)"
    src = {k: ("theme" if k in MENU_FONT_KEYS else "value") for k in p}
    white = "#FFFFFF"
    ov = {"item-font": font(SANS_SB, "15px", "normal", white, "1.4em", "0.006em"),
          "dropdown-menu-item-font": font(SANS_R, "14px", "normal", C["nav_mute"], "1.35em", "0.004em"),
          "dropdown-menu-item-hover-font": font(SANS_R, "14px", "normal", white, "1.35em", "0.004em"),
          "dropdown-menu-item-selected-font": font(SANS_SB, "14px", "normal", white, "1.35em", "0.004em"),
          "dropdown-menu-sub-item-font": font(SANS_R, "14px", "normal", C["nav_mute"], "1.35em", "0.004em")}
    st = {"properties": p, "propertiesSource": src, "groups": {}, "propertiesOverride": ov}
    base = {"type": "ComponentStyle", "style": st, "componentClassName": "wixui.Menu", "pageId": "",
            "spx": SPX, "compId": "", "skin": "wixui.skins.Menu"}
    vs = []
    for cond, extra in (variants or []):
        v = json.loads(json.dumps(base))
        v["style"]["properties"].update(extra)
        vs.append({"conditions": ["#" + cond], "value": v})
    return {"style": {"variants": vs, "default": base}, "layout": {"variants": []}}


def menu_node(cid, menu_key, kind, border_top=False, css=None, bp=None, variants=None, prefix=None,
              top=None):
    """A wixui.Menu with the inner parts every Studio menu carries. `top`: nodes that
    fill a hamburger drawer instead of the menu's own list (which is kept, hidden),
    one row each; the close button sits on the first."""
    p = prefix or cid
    ref = "@@MENUREF:" + MENU_IDS[menu_key].replace("-", "_") + "@@"
    parts = {r: f"{p}{r}" for r in MENU_PARTS}
    sub = N("Submenu", parts["sub"], "wixui.skins.Submenu",
            data={"subItemDirection": "inherit", "itemDirection": "inherit", "direction": "inherit",
                  "type": "Submenu"},
            css={**size("auto"), **grid_item("1 / 2", "1 / 2", ml="10px", mr="10px")})
    mega = N("MegaMenuContainerItem", parts["mega"], "wixui.skins.Dropdown",
             data={"type": "wixui.MegaMenuContainerItem"}, kids=[sub],
             css={**size("100%", minh="75px"), **grid_item("1 / 2", "1 / 2", justify="start"),
                  **grid_box("minmax(0px, 1fr)", "minmax(75px, auto)", "0px", "0px")})
    close = N("HamburgerCloseButton", parts["close"], "wixui.skins.Skinless",
              data={"type": "StylableButton", "label": "Close",
                    "svgId": "6ededf_8b853d30a66e4a24a19a3a1b252afc51.svg"},
              props={"type": "HamburgerCloseButtonProperties"},
              css={**size("40px", "40px"),
                   **grid_item("1 / 2", "1 / 2", align="start", justify="end",
                               mt="20px" if top else "12px", mr="8px" if top else "12px")})
    k = len(top or [])
    content = N("HamburgerMenuContent", parts["content"], "wixui.skins.Skinless",
                css={**size("100%"), **grid_item(f"{k + 1} / {k + 2}", "1 / 2", justify="start",
                                                 mt="0px" if top else "64px"),
                     **({"visibility": "hidden"} if top else {})})
    kids = [content, close]
    if top:
        for i, t in enumerate(top):
            t.css.update(grid_item(f"{i + 1} / {i + 2}", "1 / 2", align="stretch"))
        kids = list(top) + [content, close]
    cont = N("HamburgerMenuContainer", parts["cont"], "wixui.skins.Skinless",
             data={"type": "wixui.HamburgerMenuContainer"}, props={"type": "HamburgerMenuContainerProperties"},
             kids=kids,
             css={**size("240px", "100vh"), **grid_item("1 / 2", "1 / 2", align="stretch", justify="start"),
                  **grid_box("minmax(0px, 1fr)", " ".join(["auto"] * k + ["minmax(0px, 1fr)"]) if top
                             else "minmax(400px, auto)", "0px", "0px"),
                  "overflow-x": "hidden", "overflow-y": "scroll"})
    overlay = N("HamburgerOverlay", parts["overlay"], "wixui.skins.Skinless",
                data={"type": "wixui.HamburgerOverlay"}, props={"type": "DefaultProperties"}, kids=[cont])
    opener = N("HamburgerOpenButton", parts["open"], "wixui.skins.Skinless",
               data={"type": "StylableButton", "label": "Menu",
                     "svgId": "6ededf_794cc12c49d8465c97d1f8b0c27846f8.svg"},
               props={"type": "HamburgerOpenButtonProperties"},
               css={**size("auto"), **grid_item("1 / 2", "1 / 2", align="stretch")})
    root = N("HamburgerMenuRoot", parts["root"], "wixui.skins.Skinless",
             data={"type": "wixui.HamburgerMenuRoot"}, props={"type": "DefaultProperties"}, kids=[opener, overlay],
             css={**size("100%", "100%"), **grid_item("1 / 2", "1 / 2", justify="start"), **grid_box("1fr", "1fr")})
    um = menu_style(kind, border_top, variants)
    um["slots"] = {"type": "DynamicSlots", "slots": {"slot-" + cid[5:]: parts["mega"]}}
    m = N("Menu", cid, "wixui.skins.Menu", data={"direction": "inherit", "menuRef": ref, "type": "MenuData"},
          props={"type": "DefaultProperties"}, kids=[mega, root], css=css, bp=bp, um=um)
    m.parts = parts
    return m


def global_bundle(name, root, copy, scope=True, variants=None):
    nodes = list(root.walk())
    imports = sorted({x.tag for x in nodes})
    menus = sorted({m.group(1) for m in MENUREF.finditer(json.dumps([x.data for x in nodes]))})
    head = "import {%s} from 'document'\n" % ", ".join(imports)
    if menus:
        head += "import {%s} from 'global-menus'\n" % ", ".join(menus)
    structure = head + "\nconst Structure = () => (\n%s\n)\n" % jsx(root, 1)
    refs = {"data": data_refs(nodes)}
    if variants:
        refs["variants"] = variants
    unm = {"export": {"dependencies": {"references": refs}},
           "components": {x.id: x.um for x in nodes if x.um}}
    return {"name": name, "path": "global-components", "copy": copy, "export": {
        "version": "0.41.0", "structure": {"type": "jsx", "content": structure},
        "style": {"type": "css", "content": ""},
        "layout": {"type": "css", "content": layout_css(root.id if scope else None, nodes)},
        "unmapped": {"type": "json", "content": json.dumps(unm, ensure_ascii=False)}}}


def side_global():
    """The column: identity above the three menus, pinned top left, 240px by the
    viewport's height; hidden at 1000px and below, where the phone bar takes over.
    A global component of its own (SIDE); its @media rules resolve against the
    header's breakpoints, which its export lists as references."""
    reset_ids()
    FI = flex_item
    full = size("100%")
    name = rtext("comp-wsname", '<p><a href="index.html">Korkut Kaynardag</a></p>', "font_4",
                 color=C["ink"], size="20px", lh="1.2em", ls="-0.01em", underline=False, css={**full, **FI()})
    role = rtext("comp-wsrole", "<p>PhD, Assistant Professor</p>", "font_9", color=C["ink"],
                 css={**full, **FI(mt="5px")})
    org = rtext("comp-wsorg", f"<p>{SB.CONTACT['department']}<br>{SB.CONTACT['institution']}</p>",
                "font_9", color=C["muted"], css={**full, **FI(mt="10px")})
    name.css["margin-right"] = "32px"          # clear of the fold button, as in theme.py
    ident = box("comp-wsid", [name, role, org],
                css={**size("100%"), **grid_item("1 / 2", "1 / 2", align="stretch"),
                     **flex_box("column", pad=("28px", "20px", "24px", "20px"))},
                bg=C["page"])
    # THE FOLD (theme.py): a button beside the name hides the column, the same glyph at
    # the top left brings it back. masterPage.js (build/studio/masterPage.js) does the
    # showing and hiding and keeps the choice in local storage "wad:sidebar".
    glyph = button_style(None, C["muted"], C["ink5"], C["ink"], pad=("0px", "0px", "0px", "0px"),
                         radius="8px", icon=True, gap="0px", label=False)
    fold = button("comp-wsfold", "Hide sidebar", None, glyph, icon="panel.svg",
                  css={**size("40px", "40px"), **grid_item("1 / 2", "1 / 2", justify="end", mt="20px", mr="8px")})
    fold.attrs["codeName"] = "sideFold"
    # the three lists; masterPage.js puts the Documents collection under "Documents" in
    # sideNavA (and in the phone drawer), sorted by `order`, and marks the current page
    navs = [menu_node("comp-wsnava", "side1", "side", css={**size("100%"), **grid_item("1 / 2", "1 / 2")}),
            menu_node("comp-wsnavb", "side2", "side", True, css={**size("100%"), **grid_item("2 / 3", "1 / 2")}),
            menu_node("comp-wsnavc", "side3", "side", True, css={**size("100%"), **grid_item("3 / 4", "1 / 2")})]
    for m, code in zip(navs, ("sideNavA", "sideNavB", "sideNavC")):
        m.attrs["codeName"] = code
    # static .side: the identity stays, the list under it scrolls in a short window; the
    # navy runs to the bottom of the viewport whatever the list's length (the last row
    # takes the rest). global.css (.side-nav) turns the scrollbar thin and blue, shown
    # only when the list is longer than the column
    navlist = box("comp-wsnavs", navs,
                  css={**size("100%", "100%"), **grid_item("2 / 3", "1 / 2", align="stretch"),
                       **grid_box("minmax(0px, 1fr)", "auto auto auto minmax(0px, 1fr)"),
                       "overflow-x": "hidden", "overflow-y": "scroll"})
    navlist.um["classnames"] = {"type": "Classnames", "classnames": ["side-nav"]}
    navlist.attrs["codeName"] = "sideNav"
    panel = box("comp-wspanel", [ident, fold, navlist],
                css={**size("100%", "100%"), **grid_item("1 / 2", "1 / 2", align="stretch"),
                     **grid_box("minmax(0px, 1fr)", "auto minmax(0px, 1fr)")},
                bg=C["nav"])
    panel.attrs["codeName"] = "sidePanel"
    show = button("comp-wsshow", "Show sidebar", None, glyph, icon="panel.svg",
                  css={**size("40px", "40px"), **grid_item("1 / 2", "1 / 2", justify="start", mt="20px", ml="8px")})
    show.attrs["codeName"] = "sideShow"
    # the show button comes first, so the column covers it until the script hides it
    side = box(SIDE_ID, [show, panel],
               css={"width": "240px", "height": "100vh", "--height-type": "vh", "visibility": "visible",
                    "--item-layout-type": "FixedItemLayout", "align-self": "start", "justify-self": "start",
                    "margin-top": "0px", "margin-left": "0px", **grid_box("minmax(0px, 1fr)", "minmax(0px, 1fr)")},
               bp={1000: {"visibility": "hidden"}})
    side.attrs["codeName"] = "sideColumn"
    # global.css (.side-column) takes the free site's 30px "Built on Wix" bar off its
    # height, so the list's last row stays reachable on a free site too
    side.um["classnames"] = {"type": "Classnames", "classnames": ["side-column"]}
    variants = {HDR_BP[1000]: {"target": HDR_BP[1000], "type": "BreakpointRange",
                               "info": {"min": 1, "max": 1000, "canvasSize": 768}},
                HDR_BP[750]: {"target": HDR_BP[750], "type": "BreakpointRange",
                              "info": {"min": 1, "max": 750, "canvasSize": 390}}}
    copy = [[m.parts[r], TEMPLATE_PARTS[r]] for m in navs for r in MENU_PARTS]
    return global_bundle(SIDE, side, copy, scope=False, variants=variants)


def header():
    """The phone bar: his name and the drawer's button, at 1000px and below. Above
    1000px the header is empty and 0px tall; the column is SIDE."""
    reset_ids()
    barname = rtext("comp-wsbar", '<p><a href="index.html">Korkut Kaynardag</a></p>', "font_4",
                    color=C["ink"], size="17px", lh="1.2em", ls="-0.004em", underline=False,
                    css={**size("auto"), **grid_item("1 / 2", "1 / 2", align="center", justify="start", ml="22px"),
                         "visibility": "hidden"},
                    bp={1000: {"visibility": "visible"}})
    barrule = box("comp-wsrule", [], css={**size("100%", "1px"), **grid_item("1 / 2", "1 / 2", align="end"),
                                          "visibility": "hidden"},
                  bp={1000: {"visibility": "visible"}}, bg=C["rule"])
    ham = {"display-mode": "hamburger"}
    # static: the drawer is the column itself, his name and post on the page colour at
    # its top, the list on navy under it
    dname = rtext("comp-wsdname", '<p><a href="index.html">Korkut Kaynardag</a></p>', "font_4",
                  color=C["ink"], size="20px", lh="1.2em", ls="-0.01em", underline=False,
                  css={**size("100%"), **flex_item(), "margin-right": "32px"})
    drole = rtext("comp-wsdrole", "<p>PhD, Assistant Professor</p>", "font_9", color=C["ink"],
                  css={**size("100%"), **flex_item(mt="5px")})
    dorg = rtext("comp-wsdorg", f"<p>{SB.CONTACT['department']}<br>{SB.CONTACT['institution']}</p>",
                 "font_9", color=C["muted"], css={**size("100%"), **flex_item(mt="10px")})
    dident = box("comp-wsdid", [dname, drole, dorg],
                 css={**size("100%"), **flex_box("column", pad=("28px", "20px", "24px", "20px"))},
                 bg=C["page"])
    # the drawer's list is the column's three lists (hairlines between the groups, the
    # documents under "Documents" from masterPage.js); the hamburger menu's own list
    # (the main menu) is kept but hidden: Studio's drawer list shows no sub-items that
    # code puts in
    dnavs = [menu_node("comp-wsdnava", "side1", "side", css={**size("100%")}),
             menu_node("comp-wsdnavb", "side2", "side", True, css={**size("100%")}),
             menu_node("comp-wsdnavc", "side3", "side", True, css={**size("100%")})]
    for m, code in zip(dnavs, ("drawerNavA", "drawerNavB", "drawerNavC")):
        m.attrs["codeName"] = code
        m.um["classnames"] = {"type": "Classnames", "classnames": ["drawer-nav"]}
    hamb = menu_node("comp-mb5540mw", "main", "drawer",
                     css={**size("44px", "44px"),
                          **grid_item("1 / 2", "1 / 2", align="center", justify="end", mr="8px"),
                          "visibility": "hidden",
                          **grid_box("minmax(0px, 1fr)", "minmax(min-content, 1fr)", "0px", "0px"),
                          "overflow-x": "visible", "overflow-y": "visible"},
                     bp={1000: {"visibility": "visible"}},
                     variants=[(HDR_BP[1000], ham), (HDR_BP[750], ham)], prefix="comp-wsham",
                     top=[dident] + dnavs)
    hamb.attrs["codeName"] = "navDrawer"
    root = N("HeaderSection", HEADER_ID, "wysiwyg.viewer.skins.area.RectangleArea",
             kids=[barname, barrule, hamb], attrs={"codeName": "section3"},
             css={**size(), "min-height": "0px", **grid_item("1 / 2", "1 / 2", align="stretch"),
                  **grid_box("minmax(0px, 1fr)", "minmax(0px, auto)")},
             bp={1000: {"min-height": "60px", "grid-template-rows": "minmax(60px, auto)"}},
             um=section_style(SLOT["page"]))
    root.um["breakpointVariants"] = {"type": "BreakpointsData", "componentId": HEADER_ID, "values": [
        {"type": "BreakpointRange", "id": HDR_BP["all"], "min": 1, "max": 2147483647, "canvasSize": 1280},
        {"type": "BreakpointRange", "id": HDR_BP[1000], "min": 1, "max": 1000, "canvasSize": 768},
        {"type": "BreakpointRange", "id": HDR_BP[750], "min": 1, "max": 750, "canvasSize": 390}]}
    copy = [[m.parts[r], TEMPLATE_PARTS[r]] for m in [hamb] + dnavs for r in MENU_PARTS]
    return global_bundle(HEADER, root, copy)


def footer():
    reset_ids()
    FI = flex_item
    rule = box("comp-wfrule", [], css={**size("100%", "1px"), **FI()}, bg=C["rule"])
    who = rtext("comp-wfwho",
                f'<p><span style="color:{C["ink"]};font-weight:bold;">Korkut Kaynardag, PhD</span><br>'
                "Assistant Professor, Department of Civil "
                "Engineering<br>Izmir Institute of Technology, Izmir, Turkey</p>",
                "font_8", color=C["muted"], size="14px", lh="1.6em", css={**size("auto"), **FI()})
    # the static footer's 24px gap at 14px: one space, letter-spaced (Wix rich text
    # collapses en and em spaces into a plain one), then a plain space, where a
    # narrow screen may break the line (static: the links wrap)
    links = '<span style="letter-spacing:1.3em;">&nbsp;</span> '.join(f'<a href="{h}">{t}</a>' for h, t in (
        ("about.html", "About"), ("research.html", "Research"), ("documents.html", "Documents"),
        ("gallery.html", "Gallery"), ("blog", "Blog"), ("contact.html", "Contact")))
    nav = rtext("comp-wfnav", f"<p>{links}</p>", "font_8", color=C["muted"], size="14px", lh="1.6em",
                underline=False,
                css={**size("auto"), **FI()})
    row = box("comp-wfrow", [who, nav],
              css={**size("100%"), **FI(mt="32px"),
                   **flex_box("row", "32px", align="start", justify="space-between", wrap="wrap"),
                   "row-gap": "24px"})
    wrapf = box("comp-wfwrap", [rule, row],
                css={**size("100%", maxw="1020px"), **grid_item("1 / 2", "1 / 2", justify="center"),
                     **flex_box("column", pad=("96px", "48px", "48px", "48px"))},
                bp={1000: {"padding-left": "22px", "padding-right": "22px"}})
    root = N("FooterSection", FOOTER_ID, "wysiwyg.viewer.skins.area.RectangleArea", kids=[wrapf],
             css={**size(), **grid_item("1 / 2", "1 / 2", align="stretch"), **grid_box("minmax(0px, 1fr)", "auto")},
             um=section_style())
    root.um["breakpointVariants"] = breakpoints(FOOTER_ID)
    return global_bundle(FOOTER, root, [])


# ---------------------------------------------------------------- main
# the pages that were placeholders in stage A are built now; the three topic pages
# became one dynamic page (topic_item, /topic/<slug>) in B2
PLACEHOLDERS = []


def main():
    os.makedirs(OUT, exist_ok=True)
    out = {}
    for key, title in PLACEHOLDERS:
        out[f"placeholder-{key}"] = placeholder(key, title)
    out["home"] = home()
    out["about"] = about()
    out["research"] = research()
    out["topic-item"] = topic_item()
    out["contact"] = contact()
    out["gallery"] = gallery()
    out["blog-head"] = blog_head()
    out["post-crumb"] = post_crumb()
    out["documents"] = documents_index()
    out["document-item"] = document_item()
    out["header"] = header()
    out["side"] = side_global()
    out["footer"] = footer()
    for name, b in out.items():
        with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8") as fh:
            json.dump(b, fh, ensure_ascii=False)
    print("wrote", ", ".join(sorted(out)))
    em = [n for n, b in out.items() if "—" in json.dumps(b, ensure_ascii=False)]
    if em:
        print("!! em dash in", em)


if __name__ == "__main__":
    main()
