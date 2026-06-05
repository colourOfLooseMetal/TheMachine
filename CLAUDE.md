# The Machine (ft. WAMS)

Client-side **fuzzy caption search** over ~365,697 subtitle lines spanning 12
animated shows/movies. You type a phrase; it fuzzy-matches every caption line
and shows the screenshot each matching line came from. The matcher is C++
(`wams.cpp`) compiled to WebAssembly via emscripten; the front end is a static
page (`MachineFtWams.html` + `css/styles.css` + `js/app.js`). Live at
colourofloosemetal.com; images served from
`http://colourofloosemetal.com/assets/<dir>/<num>.jpg`.

WAMS = "Web Assembly Machine Searcher."

## How a search works (runtime flow)

1. User types in `#txt-search`; Enter fires `search()` (in `js/app.js`).
   The query is `.toLowerCase()`'d JS-side before crossing into wasm (the
   corpus is all lowercase — see `getKeyFromJson.py`).
2. `search()` calls the wasm export via `cwrap('search', …)` →
   `extern "C" search()` in `wams.cpp` → `cppSearch(query)`.
3. **Stage 1 — filter (bitap):** `SearchStringFuzzy` runs fuzzy Bitap
   (Baeza-Yates–Gonnet, edit distance `k = queryLen/2`, patterns ≤31 chars)
   against every line in `mapTextData`. Hits set a bit in `bitSetOfMatches`
   and record the match offset in `matchIndex`.
4. **Stage 2 — score (jaro window):** for each filtered line,
   `jaro_sliding_window` slides the query across the line with space-padding
   and scores via Jaro-style char matching (`jaro_actual_search*`). Score is
   then penalized by match index (`-idx*.002`) and length difference
   (`-lenDiff*.0005`) so earlier, tighter matches rank higher.
5. **Sort:** `hashSortIndices` does an O(n) counting sort over all scores
   (groups equal scores, maps each to its first sorted slot) → `sortedIndices`.
6. **Return:** top 450 results packed as `["text",globalIndex, …]END000` JSON
   (`Scores::to_json`, `escape_json`), handed to JS by calling `egg(json)` via
   `EM_ASM`. The `END000` sentinel is trimmed JS-side (stray-char workaround).
7. **Render:** `egg()` parses the JSON; `get_dir_and_index_from_biglistnum`
   converts each global index → `[showDir, perShowImageNum]`;
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
  `sortedIndices`.
- `Score` / `Scores` — tiny result holders; `Scores::to_json()` emits
  `["text",idx,…]END000`.
- `extern "C" search(query)` — the wasm export: runs `cppSearch`, packs the top
  450 via `Scores`, calls `egg(json)` through `EM_ASM`, then resets `scoresArr`
  and `sortedIndices`. (`bitSetOfMatches` is the third piece of cross-search
  state; it's cleared at the top of `cppSearch`.)
- `main()` — native (`egg.exe`) entry point; mostly commented-out timing/debug
  scaffold.

Scoring constants: stage-1 edit budget `k = queryLen/2`; stage-2
`match_distance = 2` (a swapped char up to 2 away still scores); rank penalties
`-matchIndex*0.002` and `-lengthDiff*0.0005`. All debug output is gated behind
the global `const bool cLog` (default `false`).

## The front end (`MachineFtWams.html` + `css/` + `js/`)

Originally one ~4.5k-line HTML file; now split three ways (behaviour
unchanged):

- `MachineFtWams.html` (~250 lines) — the HTML5UP "Future Imperfect" markup:
  header/menu, the `#txt-search` box + Search button, the `#filter-records`
  results container, the footer (dark-mode toggle) and `#loadMore`. `<head>`
  loads `wams.js` (emscripten glue) → jQuery → `css/styles.css`; the end of
  `<body>` loads the template scripts → `js/app.js`. Many disabled features
  live on in HTML comments (per-show filter checkboxes, an advanced-search
  token table, a max-results selector) — left in place as a roadmap.
- `css/styles.css` — all page styles: the extracted template CSS followed by the
  page overrides (dark mode, `#loading`, footer). Was two separate inline
  `<style>` blocks, concatenated in their original order. (Note: the two
  `@import`s near the top sit *after* rules, so browsers already ignore them —
  pre-existing, preserved.)
- `js/app.js` — all page logic (was two inline `<script>` blocks). Key
  functions: `search()` (lowercases the query, resets state, calls
  `wamsSearch`), `egg(json)` (wasm→JS callback: trims `END000`, `JSON.parse`,
  builds the cards), `advSearchProcessResult([text,idx])` (one result card),
  `get_dir_and_index_from_biglistnum(n)` (global index → `[dir,num]` via the
  range if-ladder), `loadMore()` (infinite scroll), `darkMode()`, and the
  ← / → image-scrubbing handlers. `wamsSearch = cwrap('search','string',
  ['string'])`; the wasm calls `egg()` back when it finishes.

Deploy: the page needs `MachineFtWams.html`, `css/styles.css`, `js/app.js`, and
`wams.js`/`wams.wasm` shipped together in the same relative layout.

## Global-index → show map

`mapTextData` is all shows concatenated. `get_dir_and_index_from_biglistnum`
(in the HTML) and the asset folders use these contiguous ranges:

```
0      – 60940   sm          (Sailor Moon)
60941  – 61837   cw2003
61838  – 65819   swPrequel
65820  – 98079   recess
98080  – 142917  DisPix
142918 – 167908  JohnnyBravo
167909 – 194671   ghibli
194672 – 214151  looneyTunes
214152 – 245631  db          (Dragon Ball)
245632 – 305583  dbz
305584 – 314266  dbzMov
314267 – 365697  jojo
```

## Build & deploy test

**Easy path — `build.ps1`** (PowerShell, repo root). One command builds the wasm
*and* (optionally) serves the page for a deploy test:

```powershell
.\build.ps1                 # release build (-O3)  -> wams.js + wams.wasm
.\build.ps1 -Debug          # fast build (-O1) for iterating
.\build.ps1 -Serve          # build, then serve http://localhost:8000/MachineFtWams.html
.\build.ps1 -Debug -Serve   # the usual deploy-test loop
.\build.ps1 -Serve -Port 9000
```

The script outputs `wams.js` / `wams.wasm` **straight into the repo root**, which
is exactly where `MachineFtWams.html` loads them — no rename step. It activates
the emscripten SDK automatically (see below) if `emcc` isn't already on PATH.

- **emsdk lives at `D:\emsdk`** (emcc 5.0.7) but is *not* on PATH by default;
  `build.ps1` sources `D:\emsdk\emsdk_env.ps1` for you (with `EMSDK_QUIET=1`).
  To build by hand in a shell, run that env script first, then `emcc`.
- **`-Serve` is required to actually run the page** — browsers refuse to load
  `.wasm` over `file://`, so you need an HTTP server. The script uses
  `python -m http.server`; served `.wasm` comes back as `application/wasm`.
- `wams.js` / `wams.wasm` at the repo root are **not** gitignored (only
  `/generatedwasm` is) — deploy needs both shipped alongside the page, so they
  show up as untracked after a build. Committing the ~12 MB `wams.wasm` vs.
  building on deploy is the maintainer's call.
- `.claude/launch.json` defines a `machine` server (`python -m http.server 8010`)
  so Claude Code's preview tool can spin the page up for verification.

**Raw command** (what `build.ps1` runs; the comment at the bottom of `wams.cpp`
is the older form). `-O3` for release, `-O1` for testing:

```powershell
emcc -O3 .\wams.cpp .\data.cpp -o .\wams.js -s WASM=1 `
  -s EXPORTED_FUNCTIONS="['_search','_malloc','_free']" `
  -s EXPORTED_RUNTIME_METHODS="['cwrap','UTF8ToString']" `
  -s INITIAL_MEMORY=28311552 -s ALLOW_MEMORY_GROWTH=1
```

The `wams.cpp` comment uses the legacy flag names `EXTRA_EXPORTED_RUNTIME_METHODS`
/ `TOTAL_MEMORY` and outputs `generatedWasm/test.js`; emcc 5 prefers
`EXPORTED_RUNTIME_METHODS` / `INITIAL_MEMORY`, and `build.ps1` outputs `wams.*`
directly. `egg.exe` is a native (g++) build for local debugging — `main()` and
the `Score`/`Scores` classes are compiled in only for the wasm/native targets
respectively (see the "comment out … for normal compile" note in `wams.cpp`).

## Files

```
CLAUDE.md               — this file
README.md               — WAMS scoring walkthrough (worked "hello" example)
build.ps1               — one-command build (-Debug/-Serve/-Port): activates
                          D:\emsdk, compiles wams.cpp+data.cpp -> wams.js/.wasm
                          in repo root, optional local HTTP server. See "Build
                          & deploy test" above
.claude/launch.json     — `machine` server def (python http.server 8010) for
                          Claude Code's preview tool
MachineFtWams.html      — front-end markup (~250 lines): HTML5UP "Future
                          Imperfect" template. <head> loads wams.js + jQuery +
                          css/styles.css; end of <body> loads js/app.js
css/styles.css          — all page styles (extracted template CSS + overrides)
js/app.js               — all page logic: search()/egg() glue, result-card
                          rendering, infinite scroll, dark mode, img scrubbing

wams.cpp                — THE engine: bitap filter + jaro sliding-window
                          scorer + counting sort + JSON/egg() bridge.
                          Compiles to wasm (search export) and native (egg.exe)
data.h                  — extern decls for the big arrays + searchTextLen
                          (365697) + the bitset sample_map prototype
data.cpp                — GENERATED, ~14 MB: the `mapTextData[]` char* array
                          (all caption lines). DO NOT open/read in full
bitapTest.cpp           — standalone bitap experiment, ~2 MB embedded data.
                          DO NOT open in full
mapData.cpp             — tiny: std::vector load of mapTextData from a json
largeStringArrTest.cpp  — tiny: reads machineTextTextCombined.json into the
                          array (proved large char* arrays compile to wasm)
test.cpp                — emscripten "hello"/Friends EM_ASM smoke test
smText.json             — ~2 MB caption text data (gitignored class: *.json)
egg.exe                 — native debug build of wams.cpp (gitignored: *.exe)

pythonUtilityStuff/     — offline data-prep + asset compression:
  getKeyFromJson.py     — combine per-show showMapData/*.json (sm, cw, sw, rc,
                          dispix, jb, gib, lt, db, dbz, dbzm, jojo) → cleaned,
                          lowercased machineTextTextCombined.json (the source
                          of mapTextData; defines the global-index order above)
  combineTxt.py         — ad-hoc: concat ./texts/*.txt + grep-style word search
  create2gramDict.py    — experiment: 2-letter bitset prefilter (numpy) — an
                          unused alternative to the bitap stage
  getSmNames.py         — extract character names (non-dictionary capitalized
                          tokens) from sm.json → smNames.txt
  compressJson.py       — brotli-compress an asset (.br)
  compressJsonGzip.py   — gzip-compress an asset (.gz)
  compressBLB.py        — gzip wams.wasm → wams.wasm.gz
  wams.wasm / .gz       — committed build artifact + gzip
  test.js / test.wasm   — emscripten glue + earlier wasm build
```

Gitignored: `*.json *.txt *.BLB *.br *.exe /showMapData /generatedwasm`
(`data.cpp` is tracked despite its size; the per-show `showMapData/*.json`
sources and `generatedwasm/` build output are not).

## Working in this repo — cautions

- **The maintainer handles all Git/GitHub commits and pushes themselves.** Do
  not run `git commit`, `git push`, or open PRs unless explicitly asked in that
  moment — make and explain the edits, then leave staging/committing/pushing to
  them. (HTTPS push auth isn't available from the agent shell here anyway.)
- **Never open `data.cpp`, `bitapTest.cpp`, or the `*.json` data files in
  full** — they are multi-MB generated/embedded data. Read small ranges or
  grep if you must inspect them.
- `searchTextLen` (365697) is hard-coded in both `data.h` and `wams.cpp` and is
  the dimension of `scoresArr`/`sortedIndices`/`mapTextData`. Changing the
  corpus means regenerating `data.cpp`, updating `searchTextLen`, and updating
  the index-range map in the HTML — keep all three in sync.
- The codebase is intentionally rough (lots of commented-out scratch, profiling
  prints behind `cLog`). Preserve the existing comment voice when editing.
- Debug output is gated behind the global `const bool cLog` (default `false`) —
  flip it to `true` to get the per-search prints back. (Earlier revisions of
  `cppSearch` printed some of these unconditionally; they're now all gated.)
- The front end is split across `MachineFtWams.html`, `css/styles.css`, and
  `js/app.js`. When editing, keep the `<head>` load order (`wams.js` → jQuery →
  styles) and the end-of-`<body>` `js/app.js` load intact — `app.js` runs at
  parse time and needs jQuery and the emscripten `Module`/`cwrap` already
  present.

## Known rough edges (candidates when refining)

- Bitap patterns are capped at 31 chars (`if (m > 31) return -1;`) — queries
  longer than 31 chars silently match nothing in stage 1.
- Result count is hard-capped at 450 (`search()` loop) and the global-index →
  show map is duplicated in two places (C++ comment table + the JS
  `get_dir_and_index_from_biglistnum` if-ladder); keep them in sync.
</content>
</invoke>
