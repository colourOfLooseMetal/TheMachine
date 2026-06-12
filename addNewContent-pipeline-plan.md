# addNewContent — a clean content-ingestion pipeline for The Machine

> **Status: IMPLEMENTED + VERIFIED** (2026-06-05). All pipeline code written and
> the core paths verified (track selection, Seinfeld build, movies sizing+map,
> front-end title rendering in-browser). Remaining work is OPERATIONAL, not code:
> run full builds on the real corpora + deploy (see "What's left" below).
> This plan was written in a prior planning session; implementation was done in a
> fresh chat. Everything needed to start cold is captured below — the reviewer of
> the old scripts won't be in context, so the "Reference material" section
> reproduces the concrete findings.
> work though this plan updating status and anything else needed as you work so that if interrupted
> you can resume with ease

## ▶ PROGRESS TRACKER (resume here if interrupted)

Legend: ⬜ not started · 🔄 in progress · ✅ done · ⏭ skipped/deferred

**Environment (verified 2026-06-05):** Python 3.13.9 ✓, ffmpeg/ffprobe 8.0.1 ✓.
Core deps `opencv-python pysrt Pillow numpy` → installing (see below).
`pydub playsound` deferred (only needed for optional stage 03).

| # | Component | Status | Notes |
|---|---|---|---|
| 0 | Scaffold `pipeline/` package + `out/` gitignore | ✅ | `__init__.py` created; out/ gitignore still TODO (component 13) |
| 1 | `pipeline/config.py` | ✅ | BOX 960x540, JPEG 91, FONT_FRAC .078, OUTLINE_FRAC .0055, blur thresh 100, codec sets, FONT_PATH resolves to addNewContent/arial.ttf |
| 2 | `pipeline/subtitles.py` | ✅ | `clean_caption` VERIFIED byte-identical to clean_line (13 test cases, 0 mismatch). Also clean_html (keeps line breaks for burn-in), natural_key, sub_time_to_ms, frame_time_ms, load_subs (utf-8→iso-8859-1 fallback). NOTE: burn-in script is in moviesNstuff2024/ not MeanGirlsFiles/ (plan table mislabeled path) |
| 3 | `pipeline/tracks.py` | ✅ | ffprobe(subprocess)+SubTrack+pick_subtitle_track+extract_track. VERIFIED on all 4 plan fixtures (s01e01 auto, Rebecca picks eng/10 langs, Get Out picks eng rejects ita-forced, Fight Club single eng). sub_index = 0:s:N map index |
| 4 | `pipeline/frames.py` | ✅ | FrameGrabber(ctx mgr)+detect_blur(Laplacian, now wired in)+grab_best_frame(primary@.6, fallback alts, sharpest)+downscale_to_box(shrink-only, INTER_AREA). Smoke-tested: 1440x1080→720x540 |
| 5 | `pipeline/caption.py` | ✅ | burn_caption ports MG placement, RELATIVE sizing (font .078H, outline .0055H), textlength/textbbox (no textsize), keeps cue line breaks, BGR in/out. Visually matches gold standard. arial.ttf copied to addNewContent/ |
| 6 | `pipeline/dataset.py` | ✅ | DatasetWriter: numbered jpgs, incremental data/<key>.txt (newline='\n', byte-identical contract), movies_map (start_film/lines), append support, manifest_row() helper |
| 7 | `01_prep_movies.py` | ✅ | clean_title (port of getFileNameLIst token-split) + srt pairing (exact basename or fuzzy cleaned-title). --dry-run/--yes. Dry-run validated on real needFix (57 vids): strips junk keeps year, `.eng.srt`→`.srt` paired. Interactive rename not auto-tested (destructive) |
| 8 | `02_extract_subs.py` | ✅ | sidecar-or-extract per video; srt_has_text validation; --yes non-interactive. Uses tracks.py. (full-folder run not executed to avoid extracting 171 eps; single-extract path proven via 04 test) |
| 9 | `03_check_alignment.py` | ⏭ | optional opt-in (audio verify) — deferred per decision #4 |
| 10 | `04_build_dataset.py` | ✅ | MAIN. SETS in config. natural_key/title order, sidecar discovery, FrameGrabber loop, test-mode --limit-titles/--lines-per-title, --append. VERIFIED: seinfeld 1ep/6lines → 6 jpgs + 6-line txt, trailing \n, contract matches getKeyFromJson |
| 11 | `05_emit_manifest.py` | ✅ | reads data/<key>.txt → manifest row, insert/replace preserving order, prints deploy checklist (DO Spaces url). VERIFIED on manifest backup (append → 13 rows → restored) |
| 12 | `js/app.js` movies-title change | ✅ | added g_moviesMap global, best-effort fetch of data/movies_map.json near manifest fetch (graceful 404), movieTitleForImageNum() binary search, render film title in <small> when dir==='movies'. NOT yet browser-verified |
| 13 | `.gitignore` add `!data/movies_map.json` + ignore `addNewContent/out/` | ✅ | also ignored addNewContent/seinfeld/, addNewContent/movies/, *.srt (multi-GB media protection). Verified with git check-ignore: pipeline code+arial.ttf+movies_map.json+data/*.txt tracked-able, media ignored |
| 14 | `addNewContent/README.md` (arial.ttf ✅ copied) | ✅ | workflow + deploy steps + image-host caveat |
| 15 | Verification (track sel ✅ / seinfeld test ✅ / movies test ✅ / front-end ✅) | ✅ | ALL PASS. Front-end: temp-added movies row, built dist, preview server, searched "indiana jones" → card <small> showed film title "01 Indiana Jones..." (not bare "movies"); other shows still show dir; g_moviesMap loaded (8 films); no console errors. Temp manifest row + 16-line test data REVERTED, dist rebuilt clean |

**Last worked on:** component 15 — full front-end verification PASSED. ALL 16 components done (03 deferred by design).

## What's left (OPERATIONAL — no more code needed)
1. **Seinfeld full run:** `python 02_extract_subs.py --set seinfeld` (extracts
   171 sidecar .srt — takes a while), then `04_build_dataset.py --set seinfeld`,
   then `05_emit_manifest.py --set seinfeld`. Upload out/seinfeld/*.jpg.
2. **Movies full run:** `01_prep_movies.py` on needFix/ (interactive), then
   `02` on All/ + needFix/, then `04 --set movies` (All/) and
   `04 --set movies --src movies/needFix --append`, then `05`. Upload out/movies/*.jpg.
   - The js/app.js movies-title change is ALREADY done (verified). Just deploy.
   - Consider the credit-cue refinement (see Findings) before a full movies run if
     the title/release-info cues prove too noisy in results.
3. **Deploy:** images → DigitalOcean Space assets/<dir>/; `.\build.ps1` → FileZilla.
   - Mind the image-host caveat (Findings) if movies images go to the DO Space.
4. **build.ps1 dist-nesting bug — FIXED (2026-06-05 review).** Re-builds used to
   nest dist/data→dist/data/data (Copy-Item -Recurse onto an existing dir). Now
   build.ps1 pre-creates dist/{css,js,data} and copies folder *contents* (`src\*`),
   which merges safely on both first and re-builds. No manual dist/ delete needed.
   (Note: still no clean step, so files DELETED from src linger stale in dist/ —
   acceptable; flag if it ever bites.)

### Findings / refinement candidates (discovered during impl)
- **Credit/title cues in fan .srt files:** many movie .srt start (and sometimes
  end) with uploader/release cues (e.g. "<title> 1080p [H264-mp4] English",
  "Subtitles by..."). These currently become real images + corpus lines. Low-value
  search noise. Candidate refinement: strip leading/trailing non-dialogue cues in
  subtitles.py. NOT done (out of current scope; flagged).
- **Image host for new sets — RESOLVED (2026-06-05 review).** js/app.js used to
  hard-code colourofloosemetal.com/assets/<dir>/, so movies images on the DO Space
  would 404. Now the host is per-show: a manifest row may carry an optional `base`
  (host root before <dir>/<n>.jpg); rows without one fall back to the legacy host.
  05_emit_manifest.py stamps `base = config.ASSET_BASE` (the DO Space) onto every
  row it writes, so ALL pipeline-emitted sets (not just movies) load from the Space.
  app.js builds a dir->base map at manifest load; the ←/→ scrub handlers inherit it
  automatically (they re-use the prefix parsed off the existing <img> src).
- **Genre re-wrap cosmetic:** clean_title produces "(Sci Fi)" not "(Sci-Fi)"
  (hyphen lost in the . / - → space pass). Cosmetic only; map titles still readable.
- **clean_title now shared (2026-06-05 review).** Moved out of 01_prep_movies.py into
  pipeline/titles.py so 04_build_dataset.py applies it to the movies_map display
  title too. The card title is therefore clean even for the movies/All set (which
  01 never renames) — display title is decoupled from whether the file on disk was
  physically renamed.
- **--append image/corpus reconciliation (2026-06-05 review).** DatasetWriter now
  warns when appending if out/<dir>/ doesn't already hold the 0..count-1 images the
  corpus line count implies (out/ is gitignored / easily cleared). Prevents silently
  shipping a set with numbering gaps.

## Context

Adding a new show/movie-set to The Machine today is a messy pile of one-off
scripts (the 9 files reviewed in `moviesNstuff2024/` and `MeanGirlsFiles/`):
hard-coded absolute paths, copy-pasted helpers, dead blur-detection code, the
screenshot step and the text-burn step split across two runs, no subtitle-track
selection (always grabs stream 0), fixed font size regardless of resolution, and
no downscaling. We're going to **start fresh** in `addNewContent/`, copying the
good ideas from those scripts as inspiration, and produce one coherent pipeline
whose output drops straight into the existing web build.

Two test corpora are already staged in the repo:
- `addNewContent/seinfeld/allEpisodes/` — **171** `.mkv`, the **simple** case
  (single `subrip` English text track, 1440×1080).
- `addNewContent/movies/{All,needFix}/` — the **hard** case. `All/` = 506 files
  (~253 mostly-clean `.mp4`+`.srt` pairs); `needFix/` = 117 files (mix of
  `.mp4`+`.srt`, `.mkv`+`.srt`, and `.mkv` with embedded subs), messy filenames
  with genre/resolution junk + `.srt` names that often don't match the video.

**End goal of a pipeline run:** for each new content set, produce
(a) a folder of sequentially numbered `0.jpg…N-1.jpg` screenshots with the
subtitle burned in, (b) `data/<key>.txt` (one cleaned lowercase caption per
image, same order), and (c) a `manifest.json` row — exactly the contract the
runtime already consumes. Movies additionally get a per-movie boundary map so
each result card can show which film it came from.

### Decisions locked (from clarifying Q&A — do not re-ask)
1. **Movies = one "Movies" dataset/checkbox + a title map.** Single manifest row
   (`key: movies`, `dir: movies`); a `data/movies_map.json` boundary table gives
   per-film attribution. Small `js/app.js` change shows the title on each card.
   Append-friendly: add more films later by continuing image numbering + map.
2. **Subtitle track selection = auto-pick, confirm only when ambiguous.** Log
   every decision.
3. **Downscale = fit within a 960×540 box**, preserving aspect (matches existing
   show assets; the gold-standard MeanGirls images are 960×540).
4. **Audio-alignment verifier = build as an optional opt-in stage**, skipped in
   the default run.

---

## Reference material (read first on a cold start)

### Environment / tooling (verified present this session)
- `ffmpeg` / `ffprobe` **8.0.1** (gyan build) on PATH.
- `python` **3.13.9** on PATH. Shell is PowerShell on Windows 11.
- `emsdk` at `D:\emsdk` (emcc 5.0.7); `build.ps1` activates it automatically.
- **Pillow gotcha:** modern Pillow removed `ImageDraw.textsize` — the old burn-in
  scripts use it. Use `ImageDraw.textbbox` / `ImageFont.getbbox` / `textlength`.
- `pysrt.open(..., encoding='iso-8859-1')` is what the old scripts use; freshly
  ffmpeg-extracted `.srt` will be UTF-8 — open with utf-8 and fall back.
- Python deps to install: `opencv-python pysrt Pillow numpy pydub playsound`
  (ffmpeg-python optional; can call `ffmpeg`/`ffprobe` via `subprocess` instead).

### Real subtitle-track findings (use these as test fixtures)
From `ffprobe -select_streams s`:
- `seinfeld/allEpisodes/s01e01.mkv` → **stream 2** `subrip` `eng` only. Video
  stream 0 `hevc` **1440×1080** @ ~23.976fps; audio stream 1 `aac` eng.
  (Single clean text track → must auto-pick with no prompt.)
- `movies/needFix/1940 Rebecca.mkv` → **11** `subrip` tracks, streams 2–12:
  eng, hrv, cze, dan, fre, hun, pol, por, rum, rus, spa. Video h264 **1480×1080**.
  (Pick `eng`, ignore the other 10.)
- `movies/needFix/Get Out 2017.mkv` → stream 3 `subrip ita "Italiano Forced"`,
  stream 4 `subrip ita "Italiano"`, stream 5 `subrip eng "English"`. Video hevc
  **1920×800**. (Pick stream 5 eng; reject the forced/foreign tracks.)
- `movies/needFix/Fight Club 1999.mkv` → single `subrip eng` with a release-group
  string in the title tag. Video hevc **1280×528**. (Single eng → auto-pick.)

Note the **aspect-ratio spread** (1440×1080≈4:3, 1480×1080≈1.37, 1920×800=2.40,
1280×528≈2.42) — this is exactly why downscale-to-box + relative subtitle
placement are mandatory.

### Source scripts to mine (absolute-ish paths, repo-relative) — what to copy
| Script | What's worth reusing |
|---|---|
| `moviesNstuff2024/createMapFromVideo - ver3.py` | Frame grab at `sub.start + 0.6×(end−start)` via `CAP_PROP_POS_MSEC`; `sub_time_to_ms`, `natural_key`, `clean_html`; `cv2.imwrite(..., JPEG_QUALITY=91)`. **`detect_blur` (Laplacian variance) + `detect_blur_fft` (FFT) are defined but never called — wire one in.** Commented resolution-aware resize block is a starting point. |
| `MeanGirlsFiles/saveImagesWithSubText-fromMGoriginally.py` | **THE burn-in placement** (the user's tuned "good" one): white text, 3px black outline via nested `range(-3,4)` double-draw, longest-line width calc, `x=0.5·(W−w)`, `y=0.90·H−h`, centered multiline. Currently fixed `font size=42` — replace with relative sizing. |
| `MeanGirlsFiles/main.py` | Per-episode loop, resize-to-half, the `Meme{num,text,timeStamp}` JSON map + `"Show h:mm:ss"` timestamp formatting. |
| `MeanGirlsFiles/createScreenshotsAndMapFromVideo - ver2.py` | Movie↔srt pairing by sorted lists + basename mismatch check (pauses on `wuh woh`); both blur fns. |
| `MeanGirlsFiles/extractSubs.py` | Cleanest existing ffmpeg srt extractor (`ffmpeg-python`, `map="0:s:0"`, skip-if-exists). Add the track *selection* it lacks. |
| `moviesNstuff2024/checkSubsViaAudio.py` | `pydub` `saveAudioSegment` slice export; samples subs at positions 5 and len−5; writes `audioSegmentInfo.txt` (`[mp3, idx, text]`). |
| `moviesNstuff2024/playAudioSlices.py` | `playsound` playback + manual confirm loop over `audioSegmentInfo.txt`. |
| `moviesNstuff2024/getFileNameLIst.py` | Filename token-splitter: splits on year regex + quality/genre tokens (`720p,1080p,bluray,xvid,…`), strips `()`/`.`/`-`, re-wraps genres. `os.rename` is commented (preview-only). |
| `moviesNstuff2024/renameSubFiles.py` | Video↔srt pairing with ambiguity flags (multiple movies in folder / multiple subs / no sub). Has `input()` confirms. |

### Existing runtime contract (must match exactly)
- **Image URL:** `https://colourofloosemetal.com/assets/<dir>/<n>.jpg` where `<n>`
  is the per-set image number (0-based, one image per caption cue). Most images are
  stored here right now, however a digital ocean space is being utilized for future uploads
  with the url being `https://colm-extra-storage.nyc3.cdn.digitaloceanspaces.com/<dir>/<n>.jpg`
- **Invariant:** 1 subtitle cue = 1 corpus line = 1 image, in the same order.
  A multi-line cue becomes ONE corpus line (newlines→spaces) but keeps its line
  breaks when burned onto the image.
- **`data/<key>.txt`:** one cleaned lowercase caption per line, trailing `\n`.
  `clean_caption` must reproduce `pythonUtilityStuff/getKeyFromJson.py:clean_line`
  exactly: `re.sub(r'[^\x00-\x7F]',' ',s)` → `.lower()` → `\n`→space →
  `re.sub(r'\s*\{.*?\}\s*',' ',·)` → `re.sub(r'\s+',' ',·)` → strip
  `<b>/</b>/<i>/</i>` → `\\"`→`"`.
- **`manifest.json` row schema:** `{key, dir, name, lines, bytes, file:"data/<key>.txt"}`
  plus an OPTIONAL `base` (image-host root before `<dir>/<n>.jpg`; added 2026-06-05).
  Rows without `base` use the legacy host `colourofloosemetal.com/assets/`; pipeline
  rows set it to the DO Space. Order in the array defines global corpus order.
  Generated today by `pythonUtilityStuff/getKeyFromJson.py` (SHOWS table). 12 shows currently.
- **`js/app.js` lines that matter:** `160` `loadSelection` (fetches `s.file`,
  copies bytes into wasm, pushes `loadedShows{key,dir,start,lines}`); `193`
  manifest fetch in `Module.onRuntimeInitialized`; `319`
  `get_dir_and_index_from_biglistnum` (binary-search `loadedShows` → `[dir, n]`);
  `332` `advSearchProcessResult` builds the card; `338–341` img `src`; **`355`
  `output += "<p><small>"+dirNnum[0]+"</small></p>"`** ← the bare dir caption to
  replace with the movie title for `dir==='movies'`; `401/423` ←/→ scrub handlers
  (parse number from src ±1).
- **`build.ps1`** copies `MachineFtWams.html`, `manifest.json`, `css/`, `js/`,
  and the **whole `data/` folder** into `dist/` — so `data/movies_map.json`
  auto-deploys with no build change. `-Serve` is required to test (no `file://`).
- **`.gitignore`** ignores `*.json` + `*.txt` globally, with `!manifest.json`,
  `!data/`, `!data/*.txt` exceptions. **Add `!data/movies_map.json`.**

### Gold standard for burn-in
`MeanGirlsFiles/screenShotsSubbed/*.jpg` (verified **960×540**): white text,
~3px black outline, centered horizontally, baseline ~90% of frame height, wrapped
to centered lines keeping the `.srt`'s own breaks. The MeanGirls scripts used a
fixed `42`px font at 540px height → scale relative to height:
**`font ≈ 0.078·H`, outline ≈ `0.0055·H`**. Raw source frames are in
`MeanGirlsFiles/subScreenshots/`; subbed results in `screenShotsSubbed/`.

### Repo cautions (from CLAUDE.md)
- The maintainer handles all git commits/pushes — don't commit unless asked.
- Never open `data_mapTextData.json` / multi-MB `*.json` data files in full.
- The codebase is intentionally rough; preserve the existing comment voice.

---

## Proposed structure

```
addNewContent/
  pipeline/                 # shared, reusable core (replaces the copy-paste)
    __init__.py
    config.py               # BOX=(960,540), JPEG_QUALITY=91, FONT_FRAC=0.078, OUTLINE_FRAC=0.0055,
                            #   blur threshold, candidate-frame fractions, TEXT/IMAGE codec sets
    subtitles.py            # parse .srt (pysrt, utf-8+iso-8859-1 fallback); clean_caption() mirrors
                            #   getKeyFromJson.clean_line EXACTLY; sub_time_to_ms; natural_key
    tracks.py               # ffprobe stream inspection; TEXT vs IMAGE codec classify;
                            #   English/non-forced/longest heuristic; extract chosen track -> .srt
    frames.py               # grab frame at 60% of sub window; blur check (Laplacian) + alternate-frame
                            #   retry across window; downscale_to_box (min-scale, INTER_AREA, shrink-only)
    caption.py              # burn-in: relative font sizing + placement (port saveImagesWithSubText;
                            #   modern Pillow textbbox, not textsize)
    dataset.py              # write out/<dir>/<n>.jpg, append data/<key>.txt, build/extend movies_map
  01_prep_movies.py         # MOVIES ONLY: filename-clean + srt<->video match HELPER (interactive confirm)
  02_extract_subs.py        # pick text/English/non-forced track -> sidecar .srt (auto, confirm if unsure)
  03_check_alignment.py     # OPTIONAL opt-in: splice audio at a few subs, play, confirm vs text
  04_build_dataset.py       # MAIN: caption -> frame -> downscale -> burn -> numbered jpg + data/<key>.txt (+map)
  05_emit_manifest.py       # merge new row(s) into manifest.json + movies_map; print deploy checklist
  arial.ttf                 # burn-in font (copied alongside; referenced relatively)
  README.md                 # the workflow + manual deploy steps
  out/                      # GITIGNORED generated output: out/<dir>/*.jpg staged for upload
```

`pipeline/` is a plain package shared by every stage script — no more re-walking
folders or re-pasting `clean_html`/`sub_time_to_ms`/`natural_key`.

## Stage detail

### Shared core (`pipeline/`)
- **`tracks.py`** — `TEXT_CODECS={subrip,srt,ass,ssa,mov_text,webvtt,text,stl}`,
  `IMAGE_CODECS={hdmv_pgs_subtitle,dvd_subtitle,dvb_subtitle,xsub}` (rejected →
  satisfies "text only"). Heuristic: text-codec ∧ English (`eng/en`, or
  English-ish title) ∧ not forced ∧ longest extracted track. One candidate →
  auto; several close / none clear → print track list + prompt. Always log.
- **`frames.py`** — frame grab (`sub.start + 0.6×(end−start)`); revive
  `detect_blur` (Laplacian variance) so it actually runs: try candidate fractions
  (0.6, then 0.45/0.55/0.7), keep sharpest above threshold. `downscale_to_box`:
  `scale = min(960/w, 540/h)`, shrink only.
- **`caption.py`** — port `writeTextOnImage` placement, size from frame height,
  use `textbbox`. Keep `.srt` line breaks; wrap any over-long single line to ≤0.9·W.

### `01_prep_movies.py` (movies only, helper)
Port `getFileNameLIst.py` token logic + `renameSubFiles.py` pairing, driven
interactively: per video show `original → proposed`, accept (Enter) / edit / skip;
then confirm/rename the matching `.srt` to the video basename. Nothing renamed
without confirmation. Targets `needFix/`; `All/` gets a quick basename sanity pass.

### `02_extract_subs.py`
Sidecar `.srt` matching the basename (the `All/` case) → validate non-empty text,
use it. Else probe embedded tracks via `tracks.py`, auto-pick (confirm if unsure),
`ffmpeg -map 0:s:<idx> -c:s srt` to a sidecar `.srt`. Skip + flag titles whose only
subs are image-based.

### `03_check_alignment.py` (optional opt-in)
Port `checkSubsViaAudio.py` + `playAudioSlices.py`: slice audio (`pydub`) at a few
sub timestamps, play (`playsound`), print expected text, wait for confirm. Run only
on suspect titles; not in the default flow.

### `04_build_dataset.py` (main)
Per set, in deterministic order (episodes by `natural_key`; movies by cleaned
title): each non-empty caption → sharpest frame in window → downscale to box →
burn caption (relative sizing) → save `out/<dir>/<n>.jpg` (n increments globally
across the set) → append `clean_caption(text)` to `data/<key>.txt`. Movies also
record `{title, start, lines}` per film into `data/movies_map.json`. Writes
`data/<key>.txt` straight into repo `data/` so it's build-ready.
- **Test mode (required):** `--limit-titles N` (one Seinfeld episode) and
  `--lines-per-title N` (2–3 lines/movie) to eyeball sizing across aspect ratios
  without a full run. `--append` (movies) continues numbering + map from the
  existing `movies_map.json`.

### `05_emit_manifest.py`
Insert/replace the set's row in `manifest.json` (same schema, preserve order);
finalize `data/movies_map.json` for movies; print the manual deploy checklist.

## Front-end change (movies attribution) — small, contained
- `data/movies_map.json` = `[{title,start,lines}, …]` ascending by `start`.
  `build.ps1` already copies all of `data/` → no build change; add
  `!data/movies_map.json` to `.gitignore`.
- `js/app.js`: fetch `data/movies_map.json` once near the manifest fetch
  (~line 193). In `advSearchProcessResult` (~332), when `dirNnum[0]==='movies'`,
  binary-search the map (same pattern as `get_dir_and_index_from_biglistnum`) to
  turn the per-set image number into a film title; render it in the `<small>` at
  line 355 instead of the bare `"movies"`. Non-movie shows unchanged.
- **Known minor edge:** the ←/→ scrub handlers (lines 401/423) step the raw image
  number, so on a movie's first/last frame they'd cross into the neighbouring
  film. Acceptable for now; could clamp to the film's `[start, start+lines)` using
  the map later.
- Engine (`wams.cpp`) is **untouched** — movies are just one more dataset.

## Integration / deploy checklist (printed by stage 05)
1. `out/<dir>/*.jpg` → upload to DigitalOcean Space at `assets/<dir>/`.
2. `data/<key>.txt` (+ `data/movies_map.json` for movies) — already in repo `data/`.
3. `manifest.json` row added.
4. `js/app.js` movies-title change (one-time, only for the movies set).
5. `.\build.ps1` → drag `dist/` contents into FileZilla.

## Verification
- **Track selection:** run `02` on `s01e01.mkv` (expect: auto-picks lone `eng
  subrip`, no prompt); on `Rebecca.mkv` + `Get Out 2017.mkv` (expect: picks eng,
  skips the 10 langs / the `ita Forced` track, logs choice).
- **Show path end-to-end (test mode):** `04 --limit-titles 1` on Seinfeld →
  inspect `out/seinfeld/0.jpg…` for 960×540-box sizing, centered text ~90%
  height matching gold standard; confirm `data/seinfeld.txt` line count == image
  count and order matches.
- **Movies path (test mode):** `04 --lines-per-title 2` over a few `All/` movies
  of different aspect ratios → verify text scales per resolution; `movies_map.json`
  offsets line up with the burned images.
- **Front-end:** `.\build.ps1 -Serve`, then preview tools: load page, check the
  **Movies** box, search a known line, confirm the card shows the correct film
  title; confirm existing shows still render unchanged.

## Out of scope (for now)
- Recompiling/altering `wams.cpp`.
- Auto-uploading to DigitalOcean (manual FileZilla step stays).
- Cleaning up the old `moviesNstuff2024/` / `MeanGirlsFiles/` scripts (kept only
  as reference; the new pipeline supersedes them).
