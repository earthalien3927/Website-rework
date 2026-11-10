# Fine Art by Scotty: website rework

Page-by-page redesign of fineartbyscotty.com.

- `assets/site.css`: shared styles (colours, type, header, footer, buttons, forms)
- `pages/<page>.html`: source for each page
- `dist/<page>.html`: WordPress-ready version (shared CSS inlined, images from the live site)
- `tools/build.py`: builds `dist/` and the local preview (`.preview/`, not committed)

Build: `python3 tools/build.py home`
