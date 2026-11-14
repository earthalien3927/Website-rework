# Project notes: Fine Art by Scotty website rework

Read this first when picking the project up in a new session.

## Where things stand

- **Homepage:** design approved, not yet installed on WordPress.
  - Source: `pages/home.html` + shared styles `assets/site.css`
  - WordPress-ready output: `dist/home.html` (built by `python3 tools/build.py home`)
  - Preview link (update this same link, don't make a new one): https://claude.ai/artifact/VPNkJvE2YWGCc2sHxuhYyn
- **Art page (`/fine-art/`):** first version built, waiting on Scotty's feedback.
  - Source: `pages/art.html` (same shared styles). Output: `dist/art.html` (`python3 tools/build.py art`)
  - Preview link (its own; update this same link): https://claude.ai/artifact/JDNJoTznqp4y1reGv4WFHT
- **Waiting on:** WordPress access through the site's developer (see below).

## Ground rules from Scotty

- **Don't touch WordPress until the developer has given access and agreed the approach.** She built much of the site, including the current art page, with custom code and custom permissions. Nothing we do should break that. Until then, work only in this repo and read the live site's public pages and API.
- The site was **hacked**: about 17,500 casino spam posts (Dec 2025, from user IDs 8 and 16). Scotty has been told; the developer needs to know too.
- Run the build without cutting its output short (no `| head`): that once stopped the preview from updating.

## Design system (keep every page consistent)

- **Feel:** high-end and aspirational (Rolex, Lamborghini, private jets), sexy, "Tastefully Edgy". Dark gallery after hours.
- **Colours** (tokens in `assets/site.css`): near-black `--ink`, champagne gold `--gold` for buttons and accents only, bone text. Red comes only from the paintings.
- **Type:** DM Serif Display for headings (Scotty found Bodoni hard to read, so don't go back to it), Manrope for body text, Syncopate for small caps labels.
- **Header:** one row. Logo and "Fine Art *by Scotty*" in brushed stainless (`--steel`), "Tastefully Edgy" under it, menu on the right. Pinned; slims on scroll.
- **Frames: this is how Scotty builds them.** A charcoal brushed-metal outer tube, a brighter brushed-silver liner directly inside it against the painting, and **no black mat**. Long drop shadow. Use this frame for every painting (`.frame` > `.frame__mat` > `img`).
- **Signature plates:** some image files have a black plate behind the signature. `tools/fix_signature.py` removes it (see `assets/art-edits/README.md`). Black bars baked into image files are trimmed in the browser automatically.
- **No overlapping images.**
- **Copy:** short, confident, no invented claims (no made-up delivery times, awards or collectors).

## Homepage specifics

- **Hero:** Spoiled Kitten, blurred behind the headline and sharp to the right. "Own the *room.*", with no gold line above it.
- **Statement:** Sunday Morning in the studio frame, with a dark emerald glow from the bottom right that fades toward the left.
- **Collection:** framed paintings staggered on a generated onyx pebble background (`tools/make_pebbles.py`; stones 25% darker, highlights 10% dimmer than the first version). It fills itself from the site's artwork list; the hand-picked list is the `gallery-picks` JSON in the page:
  - `pinned`: Community Property (SZ144). Its image is in `assets/art-new/` because it isn't on the site yet.
  - `skip`: Pre Flight, Trouble, Power Ball, Soul Keeper (Nov 14: swapped out for Heartstrings)
  - `order`: Community Property, then Spoiled Kitten
  - `last`: Heartstrings (pinned on the homepage too, image in assets/art-new)
  - `large`: Spoiled Kitten. `fill`: Community Property (as big as fits on screen, centred between the page edge and its label).
  - `data-count="4"`; Sculpture and Uncategorized categories are excluded.
- **"Newest first"** = highest SZ number in the title, then publish date. The older 136 pieces have no SZ number yet. The price sheet is in Dropbox (`Price Data and Labels/Retail Price Sheet - Fine Art by Scotty SKU Order.pdf`).
- **Quote form:** a dropdown of every piece (newest first, then A–Z) plus "Something else". On the live site it sends through the **existing Elementor form** (page 4676, form `dfb2b92`, field ids in the page). Page 4676 must stay published after the homepage switch. Send one real test after going live.

## Art page specifics

- **The live art page is the developer's custom build** (Elementor + Unlimited Elements post grid with a checkbox filter, a second hidden loop grid with JetPopup "quick view", and per-piece pages at `/fine-art/<name>/` that show the size and a "Get a Quote" button to `/contact/`). `/fine-art/` is also the address of every piece's page, so don't replace or rename anything there. Plan: install ours as a **new draft page** and only switch the menu link once she agrees.
- **Layout:** "The *collection.*" heading → pinned filter bar (one button per subject with counts, Uncategorized has no button but its pieces show under All; Newest / A–Z sort) → every piece on the onyx pebble wall in the studio frame with a homepage-style name plate (No. · subject, title, View / Details / Request a quote) → the homepage's quote form → footer.
- 3 columns (2 on tablet, 1 on phone); frames in a row sit on one line so the name plates line up. 24 pieces show, then "Show more".
- Fills itself from the site's artwork list (build snapshot + live refresh). `gallery-picks` in the page: Community Property pinned first; `skip` is empty (the homepage skips Pre Flight, Trouble, Power Ball).
- Sizes (e.g. 28×49) are only in each piece's own page, not the API, so they aren't shown yet.
- The frame/name plate/pebble/viewer/quote CSS is copied from `pages/home.html`. If one changes, change both (or move them into `site.css`).
- Preview uses smaller images (`<meta name="claude:preview-edge" content="560">`) to stay under the preview size limit.

## New artwork not yet on the site (from Dropbox `NEW ART 2026.docx`)

SZ142 The Visionary · SZ143 Low Key · SZ144 Community Property · SZ145 Heartstrings · SZ146 Fully Charged · SZ147 The Healer.
Images are in the Dropbox Team Folder (`Paintings/Signed & Signeted High Res Paintings`). Fully Charged, Heartstrings, Low Key, The Visionary and Done Deal (no number yet) are now pinned at the top of the art page; web copies are in `assets/art-new/`. The Healer still has no image. Downloading from Dropbox needs `*.dropboxusercontent.com` allowed in the environment's network settings, or Scotty can drop the images into the chat.

## Installing on WordPress (once access is agreed)

Planned approach: an Application Password (requested through the secure credential form, never pasted in chat). Then: upload new images → create the page as a **draft** on a blank (Elementor Canvas) template inside a Custom HTML block → Scotty reviews → switch the front page. Keep the old homepage page (4676) published for the form.

## Session setup

Use the **website-rework** environment (it allows fineartbyscotty.com) and connect the Dropbox connector.

## Art page decisions (Nov 2026)

- The art page is **paintings only**: the Sculpture category and the jewellery (Custom Cuff by Scotty, Mermaid Tail Pendant, filed under Uncategorized) are left off via `skipCats` / `skip`. They'll get their own page or section later; on WordPress a Jewellery category would make this automatic.
- Pre Flight, Trouble and Power Ball DO show on the art page (only the homepage skips them).
- Layout: one piece per row, large, staggered left/right with the name plate beside it; landscape pieces span the full width with the plate underneath. 12 at a time, then "Show more".
- Photographed frames are cut off and replaced with our studio frame via the `crop` pick (left, top, right, bottom fractions). Done for all 16 photographed-frame pieces (Scotty approved cropping Reverence, If You See Kay, Sabrina, Rustic Elegance and Moon Shine too, "for now").
- Full-size viewer (both pages): × sits in the top corner; the enlarged picture uses the same black-bar trim as the wall.

- `unavailable` pick (both pages): pieces no longer offered are left off the wall and out of the quote list. Currently: Rustic Elegance.
- Venetian Plaster pieces show a small "VENETIAN PLASTER" plate under the frame (from the venetian-plaster category; automatic for new ones).
- `swap` pick (art page): trades two pieces' places. Currently Trouble <-> Sunday Morning, Wine Me Up <-> Wine Roper, and Heartstrings <-> Soul Keeper.
- High Tide and Wine Time (from Dropbox, no numbers yet) lead the art page with a gold "Scotty's Newest" tag (`tag` field on a pinned piece). Pieces wider than 1.15:1 go full width; squares hang like portraits.
- `large` pick (art page): hangs a piece about 40% bigger. Currently Moon Tale.
- Art page order picks: `moveTo` (Pick Me -> 9th), `sold` (If You See Kay: red "Sold Out" tag, no quote link, out of the quote list), `series` ("A Full Day": Good Morning, Good Afternoon, Good Evening hung together with a silver "A Full Day · n of 3" tag and a note), `large` also Double Dipping. Sabrina removed from the wall (skip). Reverence is standalone: no studio frame, black background cut away (`assets/art-edits/20.png`, upload to WordPress to use live).
- `medium` pick (art page): corrects the material plate where the site category is wrong. Sixth And Ariel = Carved Wood (also dropped from the Venetian Plaster filter). WordPress category should be fixed too.
- Menu: "Pop Flamingo" tab (pink, after Toy Box) on both pages, links to #pop-flamingo until the page exists. Compact menu button now below 1181px wide.
- Homepage: the Toy Box section is now a full-width Pop Flamingo banner ("Pushing the boundaries.", pink "See Scotty's crazy build" button to #pop-flamingo, plus "Explore the Toy Box"). Photo is a STAND-IN from the 2018 Chula Vista marina shoot (boat named ODESSA) in assets/art-new/pop-flamingo-standin.jpg; replace with a real Pop Flamingo on-the-water photo.
- Pop Flamingo page: pages/pop-flamingo.html, preview https://claude.ai/artifact/RQbZpBLakzFPdsJ8yY9KqD (real address /pop-flamingo/). Homepage banner = After (pink marina shot, dock post and bench retouched out) and Before (white boat, Pop web-2 / IMG_1481) nose to nose. ~170 full-size build photos were uploaded loose to the Team Folder root on 2026-11-14 (IMG_xxxx.HEIC); the two pink photos used so far are small chat copies (480px) — swap for full-size originals.
- Homepage Pop banner simplified (Nov 14): one big photo of the finished boat (3:2) with the heading, one line and ONE pink button ("See Scotty's crazy build") on the water, and the white "before" as a tilted snapshot at the bottom middle, beside the button, keeping the bow and anchor clear (bottom-left of the photo on phones) (Scotty asked for the before "in it, all in one area"). Toy Box button dropped (it's in the menu). Phone: words go under the photo; the snapshot stays in the photo's corner.
- Lead photo retouch: dock post + bench removed, the white boat behind Pop removed so the Marriott Marquis tower runs straight down (`tools/pop_remove_boat.py`), then a dramatic grade (`tools/pop_grade.py`: contrast, richer pink, deeper sky, vignette). Still the 480px chat copy, so it's soft when large. Scotty is finding the full-size original; when it arrives, redo both steps on it (the boat mask coordinates are for the 480x360 copy, scale them). None of the ~137 phone photos in the Team Folder root is that shot.
- Pop banner, third layout (Scotty: the polaroid looked out of place): heading row ABOVE the photo (label, "Pushing the boundaries.", one line, pink button on the right). Photo is `pop-after-marina-wide.jpg`, a crop of the retouched shot (480px copy, crop box 48,16,470,280) so Pop sits big to the bottom right with the bow and anchor dominant. The "before" sits in the very top-left corner (left 1.2%, top 1.8%, 15% wide; phone 20%), clear of Pop: small, thin white border, pink "Before" tag, no tilt.
- **Pop lead photo is now full size** (Nov 14): Scotty's IMG_7710.HEIC (Team Folder root, 3024x4032). Edits, in order: `tools/pop7710_cleanup.py` (centre/right/left dock posts and the stool out; top of the white Prestige boat beside Pop removed so the Marriott runs straight down; its hull is kept), `tools/pop7710_clone.py` (left post, the boat's antenna and right post cloned over cleanly), `tools/pop_nameplate.py` (the lit POP FLAMINGO honeycomb nameplate from IMG_8444.HEIC set onto the wheelhouse face, a composite Scotty asked for), `tools/pop7710_hullfix.py`, then crop (500,1000)-(3024,2893) and `tools/pop_grade.py` (fixed so white clouds don't blotch). Output `assets/art-new/pop-lead.jpg` 1800x1350. Banner stage is now 4:3; Before floats in the sky above the radar arch.
- Scotty prefers the ANGLED shot (bow toward the camera, front end looks long) over IMG_7710 (more side-on, bow looks short), even though it's fuzzier. Homepage switched back to `pop-after-marina-wide.jpg`. The IMG_7710 version (`pop-lead.jpg`, scripts in tools/) is kept in case it's wanted. Still waiting for the full-size original of the angled shot (probably taken the same day as IMG_7710); when it arrives redo: posts + stool out, top of neighbouring boat out, nameplate into the angled side recess on the upper deck (not on the front face), grade, crop.
- Nameplate on the angled photo (Nov 14): Scotty's POP FLAMINGO logo (from IMG_8444.HEIC) set into the small triangular side panel at the top left of the wheelhouse ("11 o'clock"). Done at 4x (photo enlarged to 1920x1440 first so the lettering stays crisp): `tools/pop_nameplate_angled.py`, then `tools/pop_grade.py`, crop (192,64)-(1880,1120) -> `pop-after-marina-wide.jpg` 1688x1056. The photo itself is still the soft 480px chat copy.
- Nameplate refit (Nov 14): now sits exactly in the wheelhouse side slot on the angled photo (slot traced in 1x px of the 480 copy: top edge (130.5,116.5)->(160.5,102.6), curved lower lip back to (131.5,129.4)). Affine fit (no flipping), darkened to sit in the recess's shade, inner shadow under the top edge, the lit lower lip kept. `tools/pop_nameplate_angled.py`. An AI upscaler (OpenCV EDSR) was tried for the soft photo but running it wasn't permitted in this session; the full-size original of the angled shot is still the real fix.
- Pop banner layout v4 (Nov 14): heading row = label, the one-line lede, then "Pushing the boundaries." sitting right on the photo, with the Before snapshot beside it. The pink "See Scotty's crazy build" button is ON the photo, top-left corner, with a black outline. Sky and towers darkened ~17% (`tools/pop_sky.py`) so the boat pops.

## Branding: the POP FLAMINGO sign and the Tribangle (Nov 14)

- **Pop Flamingo sign** = the brand header for Pop Flamingo everywhere. Cut from Scotty's photo IMG_8448.HEIC (the lit oval sign on the boat): `assets/art-new/pop-flamingo-sign.png` (transparent, 1600x401, `tools/cut_pop_sign.py`). Used as the homepage Pop section header (replaces the "Pop Flamingo" text label) and as the H1 on the Pop Flamingo page.
- **The Tribangle** (Scotty's name for it): the polished stainless triangle-through-a-square on Pop's back deck, cut from IMG_8451.HEIC with a hand-traced mask (`tools/cut_tribangle.py` + `tools/tribangle_geom.json`), then turned into clean neutral polished steel with the boat's purple/glitter reflections removed (`tools/tribangle_steel.py`). Files: `assets/art-new/tribangle.png` (1000px) and `tribangle-sm.png` (200px, for small marks).
- **The story, in Scotty's words:** you are the triangle, the world is the box, and you don't fit in the box. That's the lifestyle and the vibe. Every new painting from now on has a triangle in it somewhere: it's the consistent thread through his art.
- **Where it shows:** homepage "The Tribangle" section after the statement ("You are the triangle." / "The world is the box. You don't fit in it, and you were never meant to."), plus a small Tribangle mark (`.tri-mark` in site.css) before the "The Collection" and "Private acquisitions" labels and in the footer line. Keep it a quiet recurring thread, not plastered everywhere. Ideas for later: art page heading, a "find the triangle" note on new pieces, favicon.
- **Pop Flamingo page build story (Nov 14, revised):** "Follow the build" jumps to Scotty's phone photos (Team Folder root) in five chapters: Where she started (1481, 4335 ODESSA, 1444 haul-out) · Down to the bones (3018, 3075, 7233) · Built in the shop (3311, 4797, 7100, 4283, 6979, 8247 pink dome) · Back on board (4346, 3151, 3156 two people with the white boat (Scotty mentioned Angie; not named on the page until confirmed), 9633 turbine tower, 1099, 1182 pink lights on the still-white hull) · Lights on (lead: 8449 pink Pop from the back with Tribangle and tower; then 9638 tower lit purple, 0564 bar under the truss, 7451 blue brick bar, 1448, 1520, 6621), then "The reveal". Web copies in `assets/art-new/build/pop-build-<n>.jpg`. Tap for a full-size viewer. Still wanted: a night photo of pink Pop lit up.