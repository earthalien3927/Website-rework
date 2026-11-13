#!/usr/bin/env python3
"""Build the site pages.

For every pages/<name>.html this writes:
  dist/<name>.html          WordPress-ready: shared CSS inlined, images point at
                            the live site. Paste into a Custom HTML block.
  .preview/<name>/index.html
                            Preview copy for the private preview link. Images are
                            downloaded once, resized to WebP and embedded in the page,
                            because preview pages can't load images from other sites.

A page can contain a <!-- newest:start --> ... <!-- newest:end --> block inside
an element with data-count="N". The build fills it with the N newest artworks
from the site's artwork list, so the page shows real pieces even before (or
without) the live refresh that runs on the real site.

Usage: python3 tools/build.py [name ...]
"""
import base64
import hashlib
import html as htmllib
import io
import json
import pathlib
import re
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ROOT / "pages"
DIST = ROOT / "dist"
PREVIEW = ROOT / ".preview"
CACHE = ROOT / ".preview" / "_cache"
SITE_CSS = ROOT / "assets" / "site.css"

UPLOAD_RE = re.compile(r'https://www\.fineartbyscotty\.com/wp-content/uploads/[^"\'\s)]+?\.(?:jpe?g|png|webp)')
SIZE_RE = re.compile(r'-\d+x\d+(\.\w+)$')
CSS_LINK = '<link rel="stylesheet" href="../assets/site.css">'
MAX_EDGE = 1600


SITE = "https://www.fineartbyscotty.com/wp-json/wp/v2/"
NEWEST_RE = re.compile(r'(data-count="(\d+)"(?: data-exclude="([^"]*)")?>\s*<!-- newest:start -->).*?(<!-- newest:end -->)', re.S)
ASSET_URL_RE = re.compile(r'url\("\.\./assets/([^"]+)"\)')
ART_URL_RE = re.compile(r'\.\./assets/(art-new/[A-Za-z0-9._-]+)')   # new artwork not on the site yet


def get_json(path: str):
    req = urllib.request.Request(SITE + path, headers={"User-Agent": "Mozilla/5.0 (site build)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r), int(r.headers.get("X-WP-TotalPages") or 1)


def nice_title(raw: str):
    """'SPOILED KITTEN SZ136' -> ('Spoiled Kitten', '136'). Mirrors niceTitle() in the page."""
    t = htmllib.unescape(raw).strip()
    m = re.search(r"\s+SZ\s*(\d+)\s*$", t, re.I)
    num = m.group(1) if m else ""
    if m:
        t = t[: m.start()]
    t = re.sub(r"(^|[\s(/-])([a-z])", lambda x: x.group(1) + x.group(2).upper(), t.lower())
    return t, num


def newest_key(post):
    """Newest first: piece number (SZ###) decides; unnumbered pieces follow, by date.
    Mirrors newestFirst() in the page."""
    num = nice_title(post["title"]["rendered"])[1]
    return (int(num) if num else 0, post["date"])


def work_html(w) -> str:
    """One framed piece + placard from {title, num, meta, img, width, height, full}.
    Mirrors workHTML() in the page."""
    orient = "portrait" if int(w.get("height") or 0) > int(w.get("width") or 0) else "landscape"
    meta = " · ".join(x for x in ("No. " + w["num"] if w.get("num") else "", w.get("meta") or "") if x) or "by Scotty"
    e = lambda v: htmllib.escape(str(v), quote=True)
    return (
        f'          <article class="work work--{orient}{" work--large" if w.get("large") else ""}{" work--fill" if w.get("fill") else ""}">'
        f'<button class="frame" type="button" data-full="{e(w.get("full") or w["img"])}" aria-label="View {e(w["title"])} full size">'
        f'<span class="frame__mat"><img src="{e(w["img"])}" alt="{e(w["title"])}" width="{e(w.get("width", ""))}" height="{e(w.get("height", ""))}" loading="lazy"></span></button>'
        f'<div class="placard"><p class="label label--gold">{e(meta)}</p><h3>{e(w["title"])}</h3>'
        f'<div class="placard__links"><button type="button" class="link-view">View full size</button>'
        f'<a href="#quote" class="link-quote" data-title="{e(w["title"])}">Request a quote →</a></div></div></article>\n'
    )


def from_site(post, media, cat_name):
    if not media or not media.get("source_url"):
        return None
    details = media.get("media_details", {})
    sizes = details.get("sizes", {})
    img = sizes.get("1536x1536") or sizes.get("large") or {
        "source_url": media["source_url"], "width": details.get("width", ""), "height": details.get("height", "")}
    title, num = nice_title(post["title"]["rendered"])
    return {"title": title, "num": num, "meta": cat_name, "img": img["source_url"],
            "width": img.get("width"), "height": img.get("height"), "full": media["source_url"]}


key = lambda t: re.sub(r"[^a-z0-9]", "", str(t).lower())


def newest_pieces(count: int, exclude: set, skip_titles: set):
    cats, _ = get_json("fine-art-category?per_page=100&_fields=id,name,slug")
    names = {c["id"]: htmllib.unescape(c["name"]) for c in cats}
    skip = {c["id"] for c in cats if c["slug"] in exclude}
    posts = all_posts()
    keep = [p for p in posts if p.get("featured_media") and not skip & set(p.get("fine-art-category", []))
            and key(nice_title(p["title"]["rendered"])[0]) not in skip_titles]
    top = sorted(keep, key=newest_key, reverse=True)[:count]
    media, _ = get_json("media?_fields=id,source_url,media_details&per_page=100&include="
                        + ",".join(str(p["featured_media"]) for p in top))
    by_id = {m["id"]: m for m in media}
    out = [from_site(p, by_id.get(p["featured_media"]), names.get((p.get("fine-art-category") or [None])[0])) for p in top]
    return [w for w in out if w]


_POSTS = None


def all_posts():
    """Every artwork post on the site (cached for the build)."""
    global _POSTS
    if _POSTS is None:
        fields = "per_page=100&_fields=id,date,title,link,featured_media,fine-art-category&page="
        posts, pages = get_json("fine-art?" + fields + "1")
        for pg in range(2, pages + 1):
            posts += get_json("fine-art?" + fields + str(pg))[0]
        _POSTS = posts
    return _POSTS


PIECES_RE = re.compile(r"<!-- pieces:start -->.*?<!-- pieces:end -->", re.S)


def fill_pieces(html: str, picks: dict) -> str:
    """The quote form's dropdown: newest 8 by number, then everything A-Z.
    Mirrors fillPieces() in the page."""
    seen, pieces = set(), []
    for n in [(w["title"], w.get("num", "")) for w in picks.get("pinned", [])] + \
             [nice_title(p["title"]["rendered"]) for p in all_posts()]:
        if key(n[0]) and key(n[0]) not in seen:
            seen.add(key(n[0])); pieces.append(n)
    e = lambda v: htmllib.escape(str(v), quote=True)
    opt = lambda n: f'                <option value="{e(n[0])}">{e(n[0])}{f" (No. {n[1]})" if n[1] else ""}</option>\n'
    newest = sorted([n for n in pieces if n[1]], key=lambda n: -int(n[1]))[:8]
    az = sorted(pieces, key=lambda n: n[0].lower())
    block = ("<!-- pieces:start -->\n              <optgroup label=\"Newest work\">\n" + "".join(map(opt, newest)) +
             "              </optgroup>\n              <optgroup label=\"Full collection, A–Z\">\n" + "".join(map(opt, az)) +
             "              </optgroup>\n<!-- pieces:end -->")
    print(f"pieces:  {len(az)} in the quote form list")
    return PIECES_RE.sub(lambda m: block, html)


PICKS_RE = re.compile(r'<script type="application/json" id="gallery-picks">(.*?)</script>', re.S)


def fill_newest(html: str) -> str:
    pm = PICKS_RE.search(html)
    picks = json.loads(pm.group(1)) if pm else {}

    def repl(m):
        exclude = {x.strip() for x in (m.group(3) or "").split(",") if x.strip()}
        count = int(m.group(2))
        live = newest_pieces(count, exclude, {key(t) for t in picks.get("skip", [])})
        live_keys = {key(w["title"]) for w in live}
        pinned = [w for w in picks.get("pinned", []) if key(w["title"]) not in live_keys]
        works = (pinned + live)[:count]
        order = [key(t) for t in picks.get("order", [])]
        last = [key(t) for t in picks.get("last", [])]
        rank = lambda w: (2000 + last.index(key(w["title"]))) if key(w["title"]) in last else (
            order.index(key(w["title"])) if key(w["title"]) in order else 1000)
        works = sorted(works, key=rank)           # stable: ties keep newest-first
        large = {key(t) for t in picks.get("large", [])}
        fill = {key(t) for t in picks.get("fill", [])}
        for w in works:
            w["fill"] = key(w["title"]) in fill
            w["large"] = key(w["title"]) in large or w["fill"]
        print("gallery: " + ", ".join(w["title"] + (" (pinned)" if w in pinned else "") for w in works))
        return m.group(1) + "\n" + "".join(work_html(w) for w in works) + m.group(4)
    return fill_pieces(NEWEST_RE.sub(repl, html), picks)


# ---- Art page: every piece, filterable ------------------------------------
# A page can contain <!-- all:start --> ... <!-- all:end --> inside an element
# with data-all. The build fills it with every artwork, newest first (pinned
# pieces from the page's gallery-picks first), and fills <!-- cats:start -->
# ... <!-- cats:end --> with one filter button per category and
# <span data-total>N</span> with the number of pieces.
ALL_RE = re.compile(r'(data-all[^>]*>\s*<!-- all:start -->).*?(<!-- all:end -->)', re.S)
CATS_RE = re.compile(r'<!-- cats:start -->.*?<!-- cats:end -->', re.S)
TOTAL_RE = re.compile(r'(<span data-total>)[^<]*(</span>)')
HIDDEN_CATS = {"uncategorized"}        # no filter button; those pieces still show under All


def card_html(w, unframed=frozenset()) -> str:
    """One framed piece + name plate for the art page. Mirrors cardHTML() in the page."""
    e = lambda v: htmllib.escape(str(v), quote=True)
    wd, ht = int(w.get("width") or 1), int(w.get("height") or 1)
    orient = "portrait" if ht > wd else "landscape"
    meta = " · ".join(x for x in ("No. " + w["num"] if w.get("num") else "", w.get("meta") or "") if x) or "by Scotty"
    details = (f'<a href="{e(w["link"])}" class="link-details">Details</a>') if w.get("link") else ""
    return (
        f'<article class="work work--{orient}" data-cats="{e(" ".join(w.get("cats", [])))}">'
        f'<div class="work__art"><button class="frame{" frame--bare" if key(w["title"]) in unframed else ""}" type="button" style="--ar:{wd / ht:.4f}" data-full="{e(w.get("full") or w["img"])}" aria-label="View {e(w["title"])} full size">'
        f'<span class="frame__mat"><img src="{e(w["img"])}" alt="{e(w["title"])}" width="{wd}" height="{ht}" loading="lazy"></span></button></div>'
        f'<div class="placard"><p class="label label--gold">{e(meta)}</p><h3>{e(w["title"])}</h3>'
        f'<div class="placard__links"><button type="button" class="link-view">View</button>{details}'
        f'<a href="#quote" class="link-quote" data-title="{e(w["title"])}">Request a quote →</a></div></div></article>\n'
    )


def fill_all(html: str) -> str:
    if not ALL_RE.search(html):
        return html
    pm = PICKS_RE.search(html)
    picks = json.loads(pm.group(1)) if pm else {}
    skip = {key(t) for t in picks.get("skip", [])}
    cats, _ = get_json("fine-art-category?per_page=100&_fields=id,name,slug,count")
    by_id = {c["id"]: c for c in cats}
    posts = sorted((p for p in all_posts() if p.get("featured_media")
                    and key(nice_title(p["title"]["rendered"])[0]) not in skip), key=newest_key, reverse=True)
    media = {}
    ids = [p["featured_media"] for p in posts]
    for i in range(0, len(ids), 100):
        got, _ = get_json("media?_fields=id,source_url,media_details&per_page=100&include=" + ",".join(map(str, ids[i:i + 100])))
        media.update({m["id"]: m for m in got})
    works, counts = [], {}
    for p in posts:
        pc = [by_id[c] for c in p.get("fine-art-category", []) if c in by_id]
        w = from_site(p, media.get(p["featured_media"]), htmllib.unescape(pc[0]["name"]) if pc else "")
        if not w:
            continue
        sizes = media[p["featured_media"]].get("media_details", {}).get("sizes", {})
        img = sizes.get("medium_large") or sizes.get("large")
        if img:                                   # a lighter file for the wall; full size opens in the viewer
            w.update(img=img["source_url"], width=img["width"], height=img["height"])
        w["cats"] = [c["slug"] for c in pc]
        w["link"] = p.get("link", "")
        for c in pc:
            counts[c["slug"]] = counts.get(c["slug"], 0) + 1
        works.append(w)
    live_keys = {key(w["title"]) for w in works}
    pinned = [dict(w, cats=w.get("cats", [])) for w in picks.get("pinned", []) if key(w["title"]) not in live_keys]
    works = pinned + works
    e = lambda v: htmllib.escape(str(v), quote=True)
    chips = "".join(
        f'<button type="button" class="chip" data-cat="{e(c["slug"])}" aria-pressed="false">{e(htmllib.unescape(c["name"]))} <span>{counts[c["slug"]]}</span></button>\n'
        for c in sorted(cats, key=lambda c: c["name"].lower()) if counts.get(c["slug"]) and c["slug"] not in HIDDEN_CATS)
    html = CATS_RE.sub(lambda m: "<!-- cats:start -->\n" + chips + "<!-- cats:end -->", html)
    html = TOTAL_RE.sub(lambda m: m.group(1) + str(len(works)) + m.group(2), html)
    print(f"wall:    {len(works)} pieces ({len(pinned)} pinned), {chips.count('<button')} filters")
    unframed = frozenset(key(t) for t in picks.get("unframed", []))
    return ALL_RE.sub(lambda m: m.group(1) + "\n" + "".join(card_html(w, unframed) for w in works) + m.group(2), html)


def inline_assets(html: str) -> str:
    """Embed local assets as data: URIs: CSS backgrounds (the pebble texture) and
    new artwork in assets/art-new/ that isn't on the site yet."""
    def repl(m):
        f = ROOT / "assets" / m.group(1)
        mime = {"webp": "image/webp", "png": "image/png", "jpg": "image/jpeg", "svg": "image/svg+xml"}[f.suffix[1:]]
        return f'url("data:{mime};base64,{base64.b64encode(f.read_bytes()).decode()}")'
    html = ASSET_URL_RE.sub(repl, html)

    def repl_art(m):
        f = ROOT / "assets" / m.group(1)
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}[f.suffix[1:].lower()]
        return f"data:{mime};base64,{base64.b64encode(f.read_bytes()).decode()}"
    return ART_URL_RE.sub(repl_art, html)


def inline_css(html: str) -> str:
    css = SITE_CSS.read_text()
    assert CSS_LINK in html, "page must link ../assets/site.css"
    return html.replace(CSS_LINK, "<style>\n" + css + "</style>")


def wordpress_version(html: str) -> str:
    html = re.sub(r"<title>.*?</title>\n?", "", html, count=1)
    html = re.sub(r'<meta name="claude:[^>]*>\n?', "", html)
    html = re.sub(r'<meta name="description"[^>]*>\n?', "", html)
    return html


def fetch(url: str) -> bytes:
    CACHE.mkdir(parents=True, exist_ok=True)
    key = CACHE / hashlib.sha1(url.encode()).hexdigest()
    if not key.exists():
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (site build)"})
        with urllib.request.urlopen(req, timeout=60) as r:
            key.write_bytes(r.read())
    return key.read_bytes()


EDITS = ROOT / "assets" / "art-edits"


def source_bytes(url: str) -> bytes:
    """Image bytes for a live-site URL, using an edited copy from assets/art-edits
    when one exists (matched on the original file name; sized variants such as
    -768x432 are resized from the edit)."""
    name = url.rsplit("/", 1)[1]
    base = SIZE_RE.sub(r"\1", name)
    edit = EDITS / base
    if not edit.exists():
        return fetch(url)
    from PIL import Image
    im = Image.open(edit)
    m = re.search(r"-(\d+)x(\d+)\.\w+$", name)
    if m:
        im = im.copy()
        im.thumbnail((int(m.group(1)), int(m.group(2))))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    print(f"edited:  {name} <- assets/art-edits/{base}")
    return buf.getvalue()


def to_webp(data: bytes, dest: pathlib.Path, edge: int = MAX_EDGE, quality: int = 82) -> None:
    from PIL import Image
    im = Image.open(io.BytesIO(data))
    im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
    im.thumbnail((edge, edge))
    im.save(dest, "WEBP", quality=quality, method=6)


def preview_version(name: str, html: str) -> None:
    out = PREVIEW / name
    (out / "img").mkdir(parents=True, exist_ok=True)
    urls = sorted(set(UPLOAD_RE.findall(html)))
    sized = {SIZE_RE.sub(r"\1", u): u for u in urls if SIZE_RE.search(u)}
    # A page with many images can ask for smaller preview copies so the preview
    # stays under its size limit: <meta name="claude:preview-edge" content="640">
    em = re.search(r'<meta name="claude:preview-edge" content="(\d+)">', html)
    edge = int(em.group(1)) if em else MAX_EDGE
    mapping = {}
    for u in urls:
        src = sized.get(u, u)  # full-size originals reuse their resized copy
        local = "img/" + re.sub(r"[^a-zA-Z0-9]+", "-", src.split("/uploads/")[1].rsplit(".", 1)[0]).strip("-") + ".webp"
        if not (out / local).exists():
            to_webp(source_bytes(src), out / local, edge, 82 if edge == MAX_EDGE else 74)
        mapping[u] = local
    # The lightbox falls back to the thumbnail, so drop the full-size links
    # rather than embedding every artwork twice.
    html = re.sub(r' data-full="[^"]*"', "", html)
    # Embed images as data: URIs. The preview viewer only reliably shows
    # images that live inside the page itself.
    for u in sorted(mapping, key=len, reverse=True):
        data = base64.b64encode((out / mapping[u]).read_bytes()).decode()
        html = html.replace(u, "data:image/webp;base64," + data)
    (out / "index.html").write_text(html)
    print(f"preview: .preview/{name}/index.html ({len(mapping)} images)")


def main(names):
    DIST.mkdir(exist_ok=True)
    pages = [PAGES / f"{n}.html" for n in names] if names else sorted(PAGES.glob("*.html"))
    for page in pages:
        html = inline_assets(fill_newest(fill_all(inline_css(page.read_text()))))
        (DIST / page.name).write_text(wordpress_version(html))
        print(f"dist:    dist/{page.name}")
        preview_version(page.stem, html)


if __name__ == "__main__":
    main(sys.argv[1:])
