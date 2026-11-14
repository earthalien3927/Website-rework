"""Writes the "Follow the build" photo story into pages/pop-flamingo.html.
Edit CHAPTERS, then run: python3 tools/pop_build_story.py && python3 tools/build.py pop-flamingo"""
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parent.parent
P = '../assets/art-new/build/pop-build-'
CHAPTERS = [
 ("Where she started", "A plain white cruiser, still wearing her old name.", None, [
   ("1481", "White, at the dock. The blank canvas."), ("4335", "Still called ODESSA."), ("1444", "Hauled out on the travel lift.")]),
 ("Down to the bones", "Ceilings down, wiring out, everything opened up.", None, [
   ("3018", "The helm, ceiling down."), ("3075", "Cabin stripped to the beams."), ("7233", "Demolition below deck.")]),
 ("Built in the shop", "Back at Scotty's shop, the new pieces get made by hand.", None, [
   ("3311", "Scotty's shop."), ("4797", "Railing panels taking shape."), ("7100", "Flamingos cut in wood."),
   ("4283", "A spiral staircase, built from scratch."), ("6979", "A panel painted by hand."), ("8247", "Fresh pink paint in the shop.")]),
 ("Back on board", "The new pieces go on, one by one.", None, [
   ("4346", "The spiral stairs go aboard."), ("3151", "New railings going on."), ("3156", "New rails on, still white."),
   ("9633", "The turbine tower."), ("1099", "A flamingo set into the deck."), ("e7e6", "The new name, lit up at night.")]),
 ("Lights on", "After dark, Pop comes alive.", ("3130", "The back of Pop Flamingo, open and lit up at night, with the tower on top."), [
   ("9644", "Lit from bow to tower."), ("1205", "The stairs and tower, glowing."), ("4071", "Doors closed, lights on."),
   ("9638", "The turbine tower, lit up."), ("0564", "The bar, lit up under the truss."), ("7451", "The brick bar, glowing blue."),
   ("1448", "Pink below deck."), ("1520", "A Scotty mural in the lounge."), ("6621", "The brick passage going in.")]),
]
REVEAL = [("8449", "All pink, with the Tribangle on deck and the turbine tower up top."), ("6426", "Pink at the dock, at dusk.")]

def size(n):
    return Image.open(ROOT / f'assets/art-new/build/pop-build-{n}.jpg').size
def li(n, cap):
    w, h = size(n)
    return f'            <li><button class="pf-shot" type="button"><img src="{P}{n}.jpg" alt="{cap}" width="{w}" height="{h}" loading="lazy"></button><p>{cap}</p></li>\n'
def grid(ph, cols=None):
    cols = cols or {2: 2, 3: 3, 5: 5, 6: 3, 9: 3}.get(len(ph), 4)
    return f'          <ul class="pf-grid" style="--cols:{cols}">\n' + ''.join(li(n, c) for n, c in ph) + '          </ul>\n'

out = ['''    <section class="pf-build" id="build" aria-labelledby="pf-build-title">
      <div class="wrap">
        <div class="pf-build__head">
          <p class="label label--pink">The build</p>
          <h2 id="pf-build-title">From the dock <em>to the spotlight.</em></h2>
          <p class="lede">How a tired white cruiser became Pop Flamingo. Tap any photo to see it bigger.</p>
        </div>
''']
for i, (t, line, lead, ph) in enumerate(CHAPTERS, 1):
    out.append(f'        <div class="pf-ch">\n          <div class="pf-ch__head"><p class="label label--pink">Chapter {i}</p><h3>{t}</h3><p>{line}</p></div>\n')
    if lead:
        n, cap = lead; w, h = size(n)
        out.append(f'          <figure class="pf-lead"><button class="pf-shot pf-shot--lead" type="button"><img src="{P}{n}.jpg" alt="{cap}" width="{w}" height="{h}" loading="lazy"></button><figcaption>{cap}</figcaption></figure>\n')
    out.append(grid(ph) + '        </div>\n')
out.append('''        <div class="pf-ch pf-ch--end">
          <div class="pf-ch__head"><p class="label label--pink">The reveal</p><h3>Pop Flamingo.</h3><p>Pink from bow to stern, and impossible to miss in any marina.</p></div>
          <figure class="pf-photo"><img src="../assets/art-new/pop-after-marina-wide.jpg" alt="Pop Flamingo finished in pink in the marina" width="1688" height="1056" loading="lazy"></figure>
''' + grid(REVEAL, 2) + '''        </div>
      </div>
    </section>
''')
page = ROOT / 'pages/pop-flamingo.html'
s = page.read_text()
a = s.index('    <section class="pf-build"'); b = s.index('    <div class="pf-viewer"')
page.write_text(s[:a] + ''.join(out) + s[b:])
used = {n for _, _, lead, ph in CHAPTERS for n, _ in ph + ([lead] if lead else [])} | {n for n, _ in REVEAL}
for f in (ROOT / 'assets/art-new/build').glob('pop-build-*.jpg'):
    if f.stem.replace('pop-build-', '') not in used:
        print('unused:', f.name)
