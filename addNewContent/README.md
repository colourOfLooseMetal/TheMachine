# addNewContent — content ingestion pipeline

Turns a folder of videos + subtitles into the exact artifacts The Machine's
runtime consumes:

- numbered burned-in screenshots `out/<dir>/0.jpg … N-1.jpg` (staged for upload),
- a `data/<key>.txt` caption file (one cleaned lowercase caption per image),
- a `manifest.json` row, and
- (movies only) a `data/movies_map.json` per-film attribution table.

**Core invariant:** 1 subtitle cue = 1 corpus line = 1 image, in the same order.
A multi-line cue becomes ONE corpus line (newlines → spaces) but keeps its line
breaks when burned onto the picture.

The search engine (`wams.cpp` / wasm) is **never touched** — every new show or
movie set is just one more dataset loaded at runtime. Checkboxes on the site are
generated from `manifest.json`, so a new set needs **no HTML/JS edit** to appear.

See `../addNewContent-pipeline-plan.md` for the full design rationale + history.

---

## 1. Requirements (one-time setup)

- **`ffmpeg` / `ffprobe`** on PATH (tested 8.0.1). Used to probe + extract subs.
- **Python 3.13** with: `pip install opencv-python pysrt Pillow numpy`
  - stage 03 only (optional audio check, off by default): `pip install pydub playsound`
- **`arial.ttf`** is already in this folder (the burn-in font). Don't remove it.
- **emsdk** at `D:\emsdk` — only needed for the final `build.ps1` deploy step,
  which recompiles the wasm. `build.ps1` activates it automatically.

---

## 2. Layout

```
pipeline/            shared core (config, subtitles, titles, tracks, frames, caption, dataset)
01_prep_movies.py    MOVIES ONLY: clean messy filenames + pair .srt to video basename (interactive)
02_extract_subs.py   ensure every video has a sidecar .srt (auto-picks the eng/non-forced track)
03_check_alignment.py  OPTIONAL audio<->text spot check (deferred; not in the default flow)
04_build_dataset.py  MAIN: cue -> sharpest frame -> downscale -> burn -> numbered jpg + data/<key>.txt
05_emit_manifest.py  merge the set's row into manifest.json + print the deploy checklist
out/                 GITIGNORED generated screenshots, staged for upload
```

All tunables — output box size, JPEG quality, font/outline fractions, blur
threshold, the image host, and the **set registry** — live in
`pipeline/config.py`.

---

## 3. Register the set (do this first for ANY new content)

Every stage takes `--set <name>`, and `<name>` **must** exist in
`pipeline/config.py:SETS`. Add one entry per new show / movie collection:

```python
SETS = {
    # ...existing entries...
    'myshow': dict(
        key='myshow',          # data/<key>.txt filename + manifest key (unique!)
        img_dir='myshow',      # image folder name -> out/<img_dir>/ and <host>/<img_dir>/<n>.jpg
        name='My Show',        # display name on the site's checkbox
        src='myshow/episodes', # source video folder, relative to addNewContent/ (or absolute)
        movies=False,          # True only for a multi-film "one checkbox + title map" set
    ),
}
```

Then drop the source videos in `addNewContent/<src>/`. Subtitles can be either
**sidecar `.srt`** files next to each video (same basename) **or embedded
tracks** inside the video — stage 02 handles both.

> Pick `key`/`img_dir` carefully: `key` names the corpus file and must be unique
> across all shows; `img_dir` is the folder images are served from. They're
> usually the same string. Order in `manifest.json` = global corpus order; a new
> set is appended last (its images live in their own `<img_dir>/`, so order only
> affects internal indexing, never the image URLs).

---

## 4. Build a regular show (clean videos, embedded or sidecar subs)

Example: a set registered as `seinfeld`.

```powershell
# 1. ensure each video has a sidecar .srt (extracts the eng/non-forced embedded
#    track when there isn't one; prompts only when the track choice is ambiguous)
python 02_extract_subs.py --set seinfeld          # add --yes to never prompt

# 2. TEST FIRST — eyeball sizing/placement on one episode, a few cues, before a full run
python 04_build_dataset.py --set seinfeld --limit-titles 1 --lines-per-title 6
#    -> inspect out/seinfeld/0.jpg … : ~960x540 box, white centred text ~90% height

# 3. FULL run (no limits). Re-running overwrites data/seinfeld.txt + out/seinfeld/ cleanly.
python 04_build_dataset.py --set seinfeld

# 4. write/refresh the manifest.json row + print the deploy checklist
python 05_emit_manifest.py --set seinfeld
```

A test run (step 2) writes real files into `data/` and `out/` — that's fine: the
full run in step 3 starts from scratch (it truncates, not appends) and overwrites
them. Just always finish with a full, unlimited run before deploying.

---

## 5. Build the movies set (one "Movies" checkbox + per-film title map)

Movies are messier: junk filenames, mismatched `.srt`, foreign/forced tracks.
The set is registered with `movies=True`, which gives a single manifest row plus
`data/movies_map.json` (`[{title, start, lines}, …]`) so each result card can show
which film it came from.

```powershell
# 1. (needFix/ only) clean filenames + pair each .srt to its video. PREVIEW FIRST:
python 01_prep_movies.py --src movies/needFix --dry-run   # shows original -> proposed, renames nothing
python 01_prep_movies.py --src movies/needFix             # interactive: Enter=accept / type name / s=skip
#    (movies/All/ is already clean and doesn't need this; titles are auto-cleaned at build time anyway)

# 2. give every film a sidecar .srt (run once per source folder)
python 02_extract_subs.py --set movies --src movies/All
python 02_extract_subs.py --set movies --src movies/needFix

# 3. TEST FIRST — a couple of cues across a few films of different aspect ratios
python 04_build_dataset.py --set movies --src movies/All --limit-titles 4 --lines-per-title 2

# 4. FULL build. All/ first (starts fresh), then needFix/ APPENDED (continues numbering + map).
python 04_build_dataset.py --set movies --src movies/All
python 04_build_dataset.py --set movies --src movies/needFix --append

# 5. manifest row (+ finalises movies_map.json) + deploy checklist
python 05_emit_manifest.py --set movies
```

Films are ordered by cleaned title within each run; the displayed title comes
from `clean_title()` (in `pipeline/titles.py`), so cards are tidy even for files
that were never renamed.

> **`--append` warning:** append resumes image numbering from the existing
> `data/movies_map.json` / `data/<key>.txt` line count. It does **not** re-create
> earlier images, so `out/movies/` must still hold images `0…N-1` from the first
> run. If `out/` was cleared (it's gitignored), rebuild from scratch (drop
> `--append`, run All/ then needFix/ back-to-back) instead — the writer prints a
> warning if it detects a gap.

### Adding more films later
Register the new films' folder (or reuse `--src`), then:
```powershell
python 02_extract_subs.py --set movies --src movies/moreFilms
python 04_build_dataset.py --set movies --src movies/moreFilms --append   # continues numbering + map
python 05_emit_manifest.py --set movies
```
Upload only the **new** `out/movies/*.jpg` (the higher-numbered ones) to the Space.

---

## 6. Updating / re-running an existing set

- **Rebuild a show from scratch** (e.g. better frames, fixed subs): delete
  `out/<dir>/` first (so no stale higher-numbered jpgs linger if the new run is
  shorter), then re-run step 4 *without* `--append`. `04` truncates
  `data/<key>.txt` and re-numbers `out/<dir>/` from 0, then `05` **replaces** that
  set's manifest row in place (order preserved). Re-upload the whole `out/<dir>/`.
- **Fix one show's captions only:** edit nothing by hand — re-run the pipeline for
  that `--set`. The emitted `data/<key>.txt` must stay byte-compatible with the
  engine (see Notes), so don't hand-edit it.

---

## 7. Verify locally, then deploy

```powershell
..\build.ps1 -Serve         # recompiles wasm + assembles dist/ + serves it
#  open http://localhost:8000/MachineFtWams.html , tick the new set, search a known line,
#  confirm the screenshot + caption render. (Images only resolve once uploaded to the host.)
```

Then deploy (`05_emit_manifest.py` prints this same checklist):

1. **Images** — upload `out/<dir>/*.jpg` to the **DigitalOcean Space** at `<dir>/`
   (Space root, **no** `assets/` prefix), served from
   `https://colm-extra-storage.nyc3.cdn.digitaloceanspaces.com/<dir>/<n>.jpg`.
2. **Captions** — `data/<key>.txt` (+ `data/movies_map.json` for movies) are
   already in the repo's `data/`; `build.ps1` copies all of `data/` into `dist/`.
3. **Manifest** — `manifest.json` row was written by stage 05.
4. **Build + upload** — run `..\build.ps1`, then drag the **contents** of `dist/`
   into FileZilla. (`build.ps1` recompiles the wasm and re-assembles `dist/`; it
   commits nothing and the engine is unchanged — the rebuild is just so `dist/`
   is complete.)

> The maintainer handles all git commits/pushes. `data/*.txt`, `manifest.json`,
> and `data/movies_map.json` are tracked in git; the screenshots are not (they
> live on the host).

---

## 8. How image hosting is chosen (legacy host vs the Space)

It's per-show, keyed off the manifest row — no global switch, no code edit:

- A manifest row may carry an optional **`base`** = the host root before
  `<dir>/<n>.jpg`. `05_emit_manifest.py` stamps `base = config.ASSET_BASE` (the
  DigitalOcean Space) onto every row it writes.
- `js/app.js` builds a `dir → base` map at load (`r.base || DEFAULT_ASSET_BASE`).
  Rows **without** `base` — the original 12 shows — fall back to the legacy host
  `https://colourofloosemetal.com/assets/<dir>/`.

So pipeline-emitted sets automatically load from the Space; the legacy shows are
untouched. Moving any show between hosts later is a one-field edit on its
manifest row (add/remove `base`) — no rebuild logic, no front-end change.

---

## 9. Notes / gotchas

- `clean_caption()` in `pipeline/subtitles.py` is a **byte-exact mirror** of
  `pythonUtilityStuff/getKeyFromJson.py:clean_line` so emitted captions match the
  existing 12 shows. Do **not** "improve" it or hand-edit `data/<key>.txt`.
- Sub-track selection auto-picks the English / non-forced / text track and logs
  every decision; image-based subs (PGS/VobSub) are skipped (no OCR). It prompts
  only when genuinely ambiguous — pass `--yes` to force the first candidate.
- A cue whose frame can't be read, or whose text is empty, is dropped from BOTH
  the image set and the corpus together, so the 1-cue=1-line=1-image invariant
  always holds (numbering stays contiguous).
- Frame sizing, blur threshold, font fractions, codec sets, and the image host
  all live in `pipeline/config.py`.
- Stage 03 (audio alignment) is intentionally deferred — not part of the default
  flow.
