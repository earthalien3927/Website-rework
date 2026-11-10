#!/usr/bin/env python3
"""Build the site pages.

For every pages/<name>.html this writes:
  dist/<name>.html          WordPress-ready: shared CSS inlined, images point at
                            the live site. Paste into a Custom HTML block.
  .preview/<name>/index.html
                            Preview copy for the private preview link. Images are
                            downloaded once, resized to WebP and embedded in the page,
                            because preview pages can't load images from other sites.

Usage: python3 tools/build.py [name ...]
"""
import base64
import hashlib
import io
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
        html = inline_css(page.read_text())
        (DIST / page.name).write_text(wordpress_version(html))
        print(f"dist:    dist/{page.name}")
        preview_version(page.stem, html)


if __name__ == "__main__":
    main(sys.argv[1:])
