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
        f'          <article class="work work--{orient}{" work--large" if w.get("large") else ""}">'
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
    fields = "per_page=100&_fields=id,date,title,link,featured_media,fine-art-category&page="
    posts, pages = get_json("fine-art?" + fields + "1")
    for pg in range(2, pages + 1):
        posts += get_json("fine-art?" + fields + str(pg))[0]
    keep = [p for p in posts if p.get("featured_media") and not skip & set(p.get("fine-art-category", []))
            and key(nice_title(p["title"]["rendered"])[0]) not in skip_titles]
    top = sorted(keep, key=newest_key, reverse=True)[:count]
    media, _ = get_json("media?_fields=id,source_url,media_details&per_page=100&include="
                        + ",".join(str(p["featured_media"]) for p in top))
    by_id = {m["id"]: m for m in media}
    out = [from_site(p, by_id.get(p["featured_media"]), names.get((p.get("fine-art-category") or [None])[0])) for p in top]
    return [w for w in out if w]


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
        for w in works:
            w["large"] = key(w["title"]) in large
        print("gallery: " + ", ".join(w["title"] + (" (pinned)" if w in pinned else "") for w in works))
        return m.group(1) + "\n" + "".join(work_html(w) for w in works) + m.group(4)
    return NEWEST_RE.sub(repl, html)


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


def to_webp(data: bytes, dest: pathlib.Path) -> None:
    from PIL import Image
    im = Image.open(io.BytesIO(data))
    im = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
    im.thumbnail((MAX_EDGE, MAX_EDGE))
    im.save(dest, "WEBP", quality=82, method=6)


def preview_version(name: str, html: str) -> None:
    out = PREVIEW / name
    (out / "img").mkdir(parents=True, exist_ok=True)
    urls = sorted(set(UPLOAD_RE.findall(html)))
    sized = {SIZE_RE.sub(r"\1", u): u for u in urls if SIZE_RE.search(u)}
    mapping = {}
    for u in urls:
        src = sized.get(u, u)  # full-size originals reuse their resized copy
        local = "img/" + re.sub(r"[^a-zA-Z0-9]+", "-", src.split("/uploads/")[1].rsplit(".", 1)[0]).strip("-") + ".webp"
        if not (out / local).exists():
            to_webp(source_bytes(src), out / local)
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
        html = inline_assets(fill_newest(inline_css(page.read_text())))
        (DIST / page.name).write_text(wordpress_version(html))
        print(f"dist:    dist/{page.name}")
        preview_version(page.stem, html)


if __name__ == "__main__":
    main(sys.argv[1:])
