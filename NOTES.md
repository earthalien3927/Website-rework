# Project notes: Fine Art by Scotty website rework

Read this first when picking the project up in a new session.

## Where things stand

- **Homepage:** design approved, not yet installed on WordPress.
  - Source: `pages/home.html` + shared styles `assets/site.css`
  - WordPress-ready output: `dist/home.html` (built by `python3 tools/build.py home`)
  - Preview link (update this same link, don't make a new one): https://claude.ai/artifact/VPNkJvE2YWGCc2sHxuhYyn
- **Next page:** the art page (`/fine-art/`). Build it as `pages/art.html` with its **own** preview link, so the homepage preview stays as approved.
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
  - `skip`: Pre Flight, Trouble, Power Ball
  - `order`: Community Property, then Spoiled Kitten
  - `last`: Soul Keeper
  - `large`: Spoiled Kitten. `fill`: Community Property (as big as fits on screen, centred between the page edge and its label).
  - `data-count="4"`; Sculpture and Uncategorized categories are excluded.
- **"Newest first"** = highest SZ number in the title, then publish date. The older 136 pieces have no SZ number yet. The price sheet is in Dropbox (`Price Data and Labels/Retail Price Sheet - Fine Art by Scotty SKU Order.pdf`).
- **Quote form:** a dropdown of every piece (newest first, then A–Z) plus "Something else". On the live site it sends through the **existing Elementor form** (page 4676, form `dfb2b92`, field ids in the page). Page 4676 must stay published after the homepage switch. Send one real test after going live.

## New artwork not yet on the site (from Dropbox `NEW ART 2026.docx`)

SZ142 The Visionary · SZ143 Low Key · SZ144 Community Property · SZ145 Heartstrings · SZ146 Fully Charged · SZ147 The Healer.
Images are in the Dropbox Team Folder. Downloading from Dropbox needs `*.dropboxusercontent.com` allowed in the environment's network settings, or Scotty can drop the images into the chat.

## Installing on WordPress (once access is agreed)

Planned approach: an Application Password (requested through the secure credential form, never pasted in chat). Then: upload new images → create the page as a **draft** on a blank (Elementor Canvas) template inside a Custom HTML block → Scotty reviews → switch the front page. Keep the old homepage page (4676) published for the form.

## Session setup

Use the **website-rework** environment (it allows fineartbyscotty.com) and connect the Dropbox connector.
