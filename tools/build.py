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
NEWEST_RE = re.compile(r'(data-count="(\d+)">\s*<!-- newest:start -->).*?(<!-- newest:end -->)', re.S)


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


def piece_html(post, media) -> str:
    if not media or not media.get("source_url"):
        return ""
    details = media.get("media_details", {})
    sizes = details.get("sizes", {})
    thumb = sizes.get("medium_large") or sizes.get("large") or {
        "source_url": media["source_url"], "width": details.get("width", ""), "height": details.get("height", "")}
    title, num = nice_title(post["title"]["rendered"])
    e = lambda v: htmllib.escape(str(v), quote=True)
    return (
        f'          <button class="piece" type="button" data-full="{e(media["source_url"])}" data-link="{e(post["link"])}">'
        f'<span class="piece__frame"><img src="{e(thumb["source_url"])}" alt="{e(title)}" width="{e(thumb.get("width", ""))}" height="{e(thumb.get("height", ""))}" loading="lazy"></span>'
        f'<span class="piece__cap"><span class="label">{e(title)}</span><span>{"No. " + e(num) if num else "by Scotty"}</span></span></button>\n'
    )


def newest_pieces(count: int):
    fields = "per_page=100&_fields=id,date,title,link,featured_media&page="
    posts, pages = get_json("fine-art?" + fields + "1")
    for pg in range(2, pages + 1):
        posts += get_json("fine-art?" + fields + str(pg))[0]
    top = sorted((p for p in posts if p.get("featured_media")), key=newest_key, reverse=True)[:count]
    media, _ = get_json("media?_fields=id,source_url,media_details&per_page=100&include="
                        + ",".join(str(p["featured_media"]) for p in top))
    by_id = {m["id"]: m for m in media}
    return [(p, by_id.get(p["featured_media"])) for p in top]


def fill_newest(html: str) -> str:
    def repl(m):
        pieces = newest_pieces(int(m.group(2)))
        print("newest:  " + ", ".join(nice_title(p["title"]["rendered"])[0] for p, _ in pieces))
        return m.group(1) + "\n" + "".join(piece_html(p, md) for p, md in pieces) + m.group(3)
    return NEWEST_RE.sub(repl, html)


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
            to_webp(fetch(src), out / local)
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
        html = fill_newest(inline_css(page.read_text()))
        (DIST / page.name).write_text(wordpress_version(html))
        print(f"dist:    dist/{page.name}")
        preview_version(page.stem, html)


if __name__ == "__main__":
    main(sys.argv[1:])
