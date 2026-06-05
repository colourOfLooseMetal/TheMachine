# The Machine (ft. WAMS)

Client-side **fuzzy caption search** over ~365,697 subtitle lines spanning 12
animated shows/movies. You type a phrase; it fuzzy-matches every caption line
and shows the screenshot each matching line came from. The matcher is C++
(`wams.cpp`) compiled to WebAssembly via emscripten; the front end is a static
page (`MachineFtWams.html` + `css/styles.css` + `js/app.js`). Live at
https://colourofloosemetal.com; images served from
`https://colourofloosemetal.com/assets/<dir>/<num>.jpg`.

WAMS = "Web Assembly Machine Searcher."

## How a search works (runtime flow)

1. User selects shows via the checkboxes above the search box (desktop: all
   checked by default; mobile: all unchecked). `corpusDirty` tracks whether the
   selection has changed since the last corpus build. User types in `#txt-search`;
   Enter or the Search button fires `search()` (in `js/app.js`). The query is
   `.toLowerCase()`'d JS-side before crossing into wasm (the corpus is all lowercase).
2. If `corpusDirty` is set, `search()` calls `loadSelection(selected)` first —
   fetches and loads the checked shows into wasm memory, then clears the flag.
   On desktop the corpus is also pre-loaded eagerly at startup so the first search
   is instant. On mobile the first search triggers the load.
3. `search()` calls the wasm export via `cwrap('search', …)` →
   `extern "C" search()` in `wams.cpp` → `cppSearch(query)`.
4. **Stage 1 — filter (bitap):** `SearchStringFuzzy` runs fuzzy Bitap
   (Baeza-Yates–Gonnet, edit distance `k = queryLen/2`, patterns ≤31 chars)
   against every line in `g_corpus` (via `lineAt(i)`). Hits set a flag in
   `g_bitSet` and record the match offset in `g_matchIndex`.
5. **Stage 2 — score (jaro window):** for each filtered line,
   `jaro_sliding_window` slides the query across the line with space-padding
   and scores via Jaro-style char matching (`jaro_actual_search*`). Score is
   then penalized by match index (`-idx*.002`) and length difference
   (`-lenDiff*.0005`) so earlier, tighter matches rank higher.
6. **Sort:** `hashSortIndices` does an O(n) counting sort over all scores
   (groups equal scores, maps each to its first sorted slot) → `sortedIndices`.
7. **Return:** top 450 results packed as `["text",corpusIndex, …]END000` JSON
   (`Scores::to_json`, `escape_json`), handed to JS by calling `egg(json)` via
   `EM_ASM`. The `END000` sentinel is trimmed JS-side (stray-char workaround).
8. **Render:** `egg()` parses the JSON; `get_dir_and_index_from_biglistnum`
   binary-searches `loadedShows[]` to convert each active-corpus index →
   `[showDir, perShowImageNum]`;
   `advSearchProcessResult` builds the image+caption card (cards are
   accumulated in the `outputContent[]` array, not the DOM directly). Infinite
   scroll via `loadMore()` (window `onscroll` reveals 10 more cards at a time).
   Each card also has ← / → buttons that swap the `<img>` src to the adjacent
   per-show image number, letting you scrub neighbouring screenshots. A
   `#contrib` checkbox toggles `contribMode` + a `changeList` for in-page
   caption corrections (the contrib/correction submit path is stubbed/partial).

## The engine (`wams.cpp`)

Function roster, top to bottom — the two stages plus their helpers:

- `escape_json(s)` — JSON-escape one caption for the result payload.
- **Corpus management exports** (called from JS to load show data at runtime):
  `reserveCorpus(totalBytes, totalLines)` — exact-size pre-allocation so
  subsequent show loads never reallocate.
  `showWritePtr(byteLen)` — grows `g_corpus` by `byteLen` and returns a pointer
  to the new region; JS writes the show's bytes there directly (the ONE copy).
  `commitShow(byteLen)` — indexes the region in-place (`\n`→`\0`, records
  offsets in `g_lineOffsets`), bumps `g_totalLines`, returns #lines added.
  `clearCorpus()` — frees all corpus memory (swap idiom, actually releases
  capacity) and resets `g_totalLines`; called before loading a new selection.
- `lineAt(i)` — inline: returns `g_corpus.data() + g_lineOffsets[i]`, the null-
  terminated caption string for line `i` in the active corpus.
- `ensureWorkArrays(n)` — resizes `scoresArr`, `sortedIndices`, `g_bitSet`,
  `g_matchIndex` to `n` when corpus size changes; no-op when already correct size.
- `hashSortIndices(values, n, sortedIndices)` — **stage 3**, the O(n) counting
  sort. Counts each distinct score in a `map<double,int>`, maps each score to
  its first slot in descending order, then scatters every original index into
  `sortedIndices` grouped by score (and rewrites `values[]` into sorted order).
- `printArray(...)` — debug dump of the top 100 (only called when `cLog`).
- `jaro_actual_search(s1,s2,l1,l2,match_distance)` — Jaro-style char match used
  when the query is **longer** than the line (no sliding). Score
  `= (actualMatches + t) / l2`, where `t` adds 0.1 per matched-but-displaced
  char.
- `jaro_actual_search_but_with_window_bs(...)` — the windowed variant: same Jaro
  core, but discounts the space-padding around the query so leading/trailing
  matches don't inflate the denominator (`extraSpaceLoc` = 0 both / 1 prefix /
  2 suffix). Its long comment block is the canonical scoring explanation.
- `jaro_sliding_window(string,strLen,pattern,patLen,max_distance,matchIndex)` —
  **stage 2**. Slides the space-padded query across the line near `matchIndex`
  (window `[matchIndex-1 … matchIndex+patLen+2]`), scores each offset with the
  windowed Jaro, returns the max. Lines shorter than the query fall back to
  `jaro_actual_search`.
- `SearchString(text,pattern)` — exact (non-fuzzy) Bitap. **Unused** at runtime,
  kept as reference.
- `SearchStringFuzzy(text,pattern,k)` — **stage 1**, fuzzy Bitap (Levenshtein
  ≤ k). Returns the match offset, or -1.
- `cppSearch(query)` — orchestrates stage 1 → 2 → 3, filling `scoresArr` and
  `sortedIndices`. Calls `ensureWorkArrays(g_totalLines)` at the top; resets
  `g_bitSet` and `g_matchIndex` each call.
- `Score` / `Scores` — tiny result holders; `Scores::to_json()` emits
  `["text",idx,…]END000`.
- `extern "C" search(query)` — the wasm export: runs `cppSearch`, packs top
  `min(450, g_totalLines)` via `Scores`, calls `egg(json)` through `EM_ASM`,
  then resets `scoresArr` and `sortedIndices`.
- `main()` — native entry point; mostly commented-out timing/debug scaffold.

Scoring constants: stage-1 edit budget `k = queryLen/2`; stage-2
`match_distance = 2` (a swapped char up to 2 away still scores); rank penalties
`-matchIndex*0.002` and `-lengthDiff*0.0005`. All debug output is gated behind
the global `const bool cLog` (default `false`).

## The front end (`MachineFtWams.html` + `css/` + `js/`)

Originally one ~4.5k-line HTML file; now split three ways (behaviour unchanged):

- `MachineFtWams.html` (~250 lines) — the HTML5UP "Future Imperfect" markup:
  header/menu, the show-selection checkboxes (`#checkboxes`), the `#txt-search`
  box + Search button, the `#filter-records` results container, and the footer
  (dark-mode toggle). `<head>` loads `wams.js` (emscripten glue) → jQuery →
  `css/styles.css`; the end of `<body>` loads `js/app.js`. Many disabled features
  live on in HTML comments (advanced-search token table, max-results selector)
  — left in place as a roadmap.
- `css/styles.css` — all page styles: the extracted template CSS followed by the
  page overrides (dark mode, `#loading`, footer). The template uses Font Awesome
  for custom checkbox rendering via `input[type="checkbox"] + label:before` —
  checkboxes must be `<input>` + `<label>` siblings, not nested.
- `js/app.js` — all page logic. Key functions:
  - `loadSelection(selectedShows)` — clears corpus, calls `reserveCorpus` with
    exact totals, then fetches each show's `.txt`, writes bytes directly into
    wasm memory via `showWritePtr`/`commitShow`, builds `loadedShows[]`.
  - `search()` — async; checks `corpusDirty` and awaits `loadSelection` if needed,
    then calls `wamsSearch(query.toLowerCase())`.
  - `egg(json)` — wasm→JS callback: trims `END000`, `JSON.parse`, builds cards.
  - `advSearchProcessResult([text,idx])` — one result card.
  - `get_dir_and_index_from_biglistnum(n)` — binary-searches `loadedShows[]` to
    map active-corpus index → `[dir, perShowImageNum]`.
  - `loadMore()` — infinite scroll (reveals 10 more cards per scroll event).
  - `darkMode()`, and the ← / → image-scrubbing handlers.
  - `Module.onRuntimeInitialized` (async) — fetches `manifest.json`, generates
    show checkboxes (desktop: all checked; mobile: all unchecked), wires the
    `change` listener to set `corpusDirty`, does the eager initial load on desktop.

## Active-corpus index → show map

The active corpus is all *selected* shows concatenated in manifest order.
`loadedShows` in `js/app.js` tracks `{key, dir, start, lines}` for each loaded
show; `get_dir_and_index_from_biglistnum` binary-searches it at render time.
**`manifest.json`** is the single source of truth for show order, line counts,
per-file byte sizes, and image dirs. Generated by `getKeyFromJson.py` (needs
`showMapData/`) or `generateFromDataJson.py` (uses `data_mapTextData.json`).

Full-corpus ranges when all 12 shows are loaded (for reference):

```
start    end       key          name
0        60940     sm           Sailor Moon
60941    61837     cw2003       Clone Wars 2003
61838    65819     swPrequel    Star Wars Prequels
65820    98079     recess       Recess
98080    142917    DisPix       Disney Pixar
142918   167908    JohnnyBravo  Johnny Bravo
167909   194671    ghibli       Ghibli
194672   214151    looneyTunes  Looney Tunes
214152   245631    db           Dragon Ball
245632   305583    dbz          Dragon Ball Z
305584   314266    dbzMov       Dragon Ball Z Movies
314267   365696    jojo         JoJo's Bizarre Adventure
```

## Build & deploy

**`build.ps1`** (PowerShell, repo root) — one command builds the wasm, assembles
`dist/`, and optionally serves for local testing:

```powershell
.\build.ps1                 # release build (-O3)  -> assembles dist/
.\build.ps1 -Debug          # fast build (-O1) for iterating
.\build.ps1 -Serve          # build + serve dist/ at http://localhost:8000/MachineFtWams.html
.\build.ps1 -Debug -Serve   # the usual dev/test loop
.\build.ps1 -Serve -Port 9000
```

**`dist/` is the deploy folder.** After a build, drag its contents into FileZilla
to update the live site. It contains:
```
dist/
  MachineFtWams.html  manifest.json  wams.js  wams.wasm
  css/styles.css
  js/app.js
  data/<key>.txt  (12 files, ~12 MB uncompressed)
```

Notes:
- **emsdk lives at `D:\emsdk`** (emcc 5.0.7); `build.ps1` activates it
  automatically (`EMSDK_QUIET=1`). To build by hand, run `D:\emsdk\emsdk_env.ps1`
  first, then `emcc`.
- **`-Serve` is required to actually test** — browsers refuse to load `.wasm`
  over `file://`. The script uses `python -m http.server --directory dist`.
- `wams.js`/`wams.wasm` are build artifacts output to `dist/`; they are gitignored
  at the repo root. `dist/` itself is gitignored.
- `.claude/launch.json` defines a `machine` server (`python -m http.server 8010
  --directory dist`) so Claude Code's preview tool can verify changes.

**Raw emcc command** (what `build.ps1` runs):

```powershell
emcc -O3 .\wams.cpp -o .\dist\wams.js -s WASM=1 `
  -s EXPORTED_FUNCTIONS="['_search','_reserveCorpus','_showWritePtr','_commitShow','_clearCorpus','_malloc','_free']" `
  -s EXPORTED_RUNTIME_METHODS="['cwrap','UTF8ToString','HEAPU8']" `
  -s ALLOW_MEMORY_GROWTH=1
```

No static corpus is compiled in. `HEAPU8` is required for the JS→wasm byte-copy
idiom. `ALLOW_MEMORY_GROWTH=1` lets the heap expand as shows load.

## Files

```
CLAUDE.md               — this file
README.md               — WAMS scoring walkthrough (worked "hello" example)
build.ps1               — one-command build + deploy assembly:
                          activates D:\emsdk, compiles wams.cpp -> dist/wams.js +
                          dist/wams.wasm, copies all deploy files into dist/,
                          optional local HTTP server (-Serve). See "Build & deploy"
manifest.json           — SINGLE SOURCE OF TRUTH for show order, per-show line
                          counts, uncompressed byte sizes, and image dirs.
                          Generated by pythonUtilityStuff/getKeyFromJson.py or
                          generateFromDataJson.py. Loaded by app.js at startup.
data/                   — per-show caption files: one <key>.txt per show, captions
                          joined by '\n' (trailing '\n' so last line is null-
                          terminated by commitShow). Serve with Content-Encoding:
                          gzip + Cache-Control max-age on the live server.
.claude/launch.json     — `machine` server def (python http.server 8010
                          --directory dist) for Claude Code's preview tool
MachineFtWams.html      — front-end markup: HTML5UP "Future Imperfect" template.
                          <head> loads wams.js + jQuery + css/styles.css;
                          end of <body> loads js/app.js
css/styles.css          — all page styles (extracted template CSS + overrides)
js/app.js               — all page logic: corpus load, show checkboxes, lazy
                          rebuild (corpusDirty), search/egg/render, infinite
                          scroll, dark mode, img scrubbing

wams.cpp                — THE engine: bitap filter + jaro sliding-window scorer +
                          counting sort + JSON/egg() bridge + corpus management
                          exports (reserveCorpus/showWritePtr/commitShow/clearCorpus)
data.h                  — legacy header (static corpus externs, now all commented
                          out; kept so standalone .cpp experiments don't break)

dist/                   — GITIGNORED — assembled deploy output, created by build.ps1.
                          Drag its contents to FileZilla to deploy.

pythonUtilityStuff/     — offline data-prep + asset compression:
  getKeyFromJson.py     — reads per-show showMapData/*.json → cleaned, lowercased
                          data/<key>.txt files + manifest.json. The SHOWS table at
                          the top defines corpus order. Needs showMapData/ populated
                          (gitignored). To add a show: add a row, drop its JSON in
                          showMapData/, run the script, deploy new .txt + manifest.json.
  generateFromDataJson.py — one-shot converter: reads data_mapTextData.json (the
                          old corpus array, gitignored locally) → data/*.txt +
                          manifest.json without needing showMapData/. Use this if
                          showMapData/ is not available.
  combineTxt.py         — ad-hoc: concat ./texts/*.txt + grep-style word search
  create2gramDict.py    — experiment: 2-letter bitset prefilter (numpy) — an
                          unused alternative to the bitap stage
  getSmNames.py         — extract character names from sm.json → smNames.txt
  compressJson.py       — brotli-compress an asset (.br)
  compressJsonGzip.py   — gzip-compress an asset (.gz)
  compressBLB.py        — gzip wams.wasm → wams.wasm.gz

data_mapTextData.json   — GITIGNORED — the flat corpus array from the old data.cpp,
data_eachTextLen.json     stored locally as JSON. Source data for generateFromDataJson.py.
                          Do NOT open in full (~14 MB).
```

Gitignored: `*.json *.txt *.BLB *.br *.exe /showMapData /generatedwasm dist/ wams.js wams.wasm`
Exceptions tracked: `manifest.json`, `data/`, `data/*.txt` (explicit `!` rules in `.gitignore`).

## Working in this repo — cautions

- **The maintainer handles all Git/GitHub commits and pushes themselves.** Do
  not run `git commit`, `git push`, or open PRs unless explicitly asked in that
  moment.
- **Never open `data_mapTextData.json` or other `*.json` data files in full** —
  they are multi-MB. Read small ranges or grep if you must inspect them.
- **Adding a show:** (1) drop `<key>.json` in `showMapData/`, (2) add a row to
  the SHOWS table in `getKeyFromJson.py`, (3) run it → generates `data/<key>.txt`
  + updated `manifest.json`, (4) add screenshots under `/assets/<dir>/` on the
  server, (5) run `build.ps1` to rebuild `dist/`, (6) deploy. No C++ recompile
  needed.
- `g_totalLines` is the runtime corpus size (set as shows load via `commitShow`).
  Work arrays are resized automatically via `ensureWorkArrays`. There is no static
  corpus size constant anymore.
- The codebase is intentionally rough (commented-out scratch, profiling prints
  behind `cLog`). Preserve the existing comment voice when editing.
- Debug output is gated behind `const bool cLog` (default `false`) — flip to
  `true` to get per-search console prints.
- The front end is split across `MachineFtWams.html`, `css/styles.css`, and
  `js/app.js`. Keep the `<head>` load order (`wams.js` → jQuery → styles) and
  the end-of-`<body>` `js/app.js` load intact — `app.js` runs at parse time and
  needs jQuery and `Module`/`cwrap` already present.
- Checkbox HTML must use `<input> + <label>` as **siblings** (not input inside
  label). The template CSS selector `input[type="checkbox"] + label:before`
  draws the custom checkbox box via Font Awesome; nesting breaks it.

## Known rough edges (candidates when refining)

- Bitap patterns are capped at 31 chars (`if (m > 31) return -1;`) — queries
  longer than 31 chars silently match nothing in stage 1.
- Result count is hard-capped at `min(450, g_totalLines)` in `search()`.
- `data/*.txt` files should be served with `Content-Encoding: gzip` and
  `Cache-Control: max-age=86400` on the live server for efficient show re-selection.
