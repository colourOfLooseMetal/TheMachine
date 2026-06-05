# Resume: Runtime corpus-loading refactor — The Machine (ft. WAMS)

Paste this into a new chat to continue. Everything needed to pick up is here.

---

## What this project is

**The Machine** is a client-side fuzzy caption search over ~365k subtitle lines
from 12 animated shows. A C++ engine (`wams.cpp`) compiled to WebAssembly does
the matching; a static HTML/CSS/JS front end (`MachineFtWams.html`, `css/styles.css`,
`js/app.js`) renders results as screenshot + caption cards.

Search pipeline:
1. Stage 1 — fuzzy Bitap filter (edit distance ≤ queryLen/2, patterns ≤31 chars)
2. Stage 2 — Jaro sliding-window scorer for filter survivors
3. Stage 3 — O(n) counting sort
4. Top 450 results packed as JSON, handed to JS via `EM_ASM` → `egg()` callback

Images are served from `http://colourofloosemetal.com/assets/<dir>/<num>.jpg`.
Build tool: emscripten (emsdk at `D:\emsdk`, emcc 5.0.7). Build via `.\build.ps1`.

---

## What we just refactored (all code written, not yet compiled/tested)

**The old problem:** The entire 365k-line corpus was baked into `data.cpp`
(14 MB), compiled into `wams.wasm` (12 MB / 5.6 MB gzipped). The whole thing
downloaded upfront. Adding a show meant regenerating data.cpp, recompiling,
and hand-editing a hardcoded JS if-ladder.

**The new approach:** Each show's captions live in a small `data/<key>.txt` file
(captions joined by `\n`). A `manifest.json` describes all shows (order, line
counts, byte sizes, image dirs). JS fetches and loads shows at runtime by writing
bytes directly into C++ memory — no intermediate copy, no JS-side cache.

---

## Files changed (all edits complete)

### `wams.cpp`
The core change. Removed `#include "data.h"` and the static corpus. Added:

```cpp
// Single-copy corpus store:
std::string           g_corpus;        // all loaded lines, '\0'-terminated, concatenated
std::vector<uint32_t> g_lineOffsets;   // byte offset of each line within g_corpus
int                   g_totalLines = 0;
inline const char*    lineAt(int i) { return g_corpus.data() + g_lineOffsets[i]; }

// Work arrays — vectors now, sized to active corpus only:
std::vector<double>   scoresArr;
std::vector<int>      sortedIndices;
std::vector<uint8_t>  g_bitSet;      // was std::bitset<1000000>
std::vector<short>    g_matchIndex;  // was a local 1M-element vector inside cppSearch
```

Four new `extern "C"` exports for JS to call:

```cpp
void  reserveCorpus(int totalBytes, int totalLines);
// Exact pre-allocation. Called ONCE before the per-show load loop.
// This is the only place wasm memory may grow — done upfront so
// subsequent showWritePtr calls never trigger a realloc.

char* showWritePtr(int byteLen);
// Grows g_corpus by byteLen, returns pointer to the new region.
// JS does: Module.HEAPU8.set(showBytes, ptr)  ← the ONE copy of the text.

int   commitShow(int byteLen);
// Walks the last byteLen bytes of g_corpus in-place:
// replaces each '\n' with '\0', records g_lineOffsets entries.
// .txt files must end with '\n' (getKeyFromJson.py guarantees this).
// Bumps g_totalLines. Returns #lines added.

void  clearCorpus();
// Frees everything via swap idiom (actually releases capacity).
// g_totalLines = 0; s_workArrayLen = 0.
```

`ensureWorkArrays(n)` resizes all four work vectors when g_totalLines changes —
so a mobile subset uses proportionally less RAM.

All `mapTextData[i]` → `lineAt(i)`, all `searchTextLen` → `g_totalLines`.
Stage 1/2/3 search math is completely unchanged.
`hashSortIndices` now takes `std::vector<double>&` instead of `double[]`.
`search()` clamps top-N to `std::min(450, g_totalLines)`.

### `build.ps1`
Removed `data.cpp` from compile inputs. Updated emcc call:
- New exports: `_reserveCorpus`, `_showWritePtr`, `_commitShow`, `_clearCorpus`
- Added `HEAPU8` to `EXPORTED_RUNTIME_METHODS`
- Removed `INITIAL_MEMORY` (corpus grows dynamically)

### `data.h`
All externs commented out. `wams.cpp` no longer includes it. Kept so other
standalone .cpp files don't immediately break.

### `pythonUtilityStuff/getKeyFromJson.py`
Complete rewrite of the output section (cleaning pipeline unchanged).

Has a `SHOWS` table at the top — add a row to add a show:
```python
SHOWS = [
    ('sm.json',    'sm',        'sm',          'Sailor Moon'),
    ('cw.json',    'cw2003',    'cw2003',      'Clone Wars 2003'),
    # ... etc
]
```

Outputs:
- `../data/<key>.txt` per show — captions joined by `\n`, trailing `\n`
- `../manifest.json` — list of `{key, dir, name, lines, bytes, file}` per show.
  `bytes` is the exact uncompressed size, drives `reserveCorpus` for exact alloc.

**Needs `showMapData/` populated** (gitignored, not on disk here). Once it is:
```powershell
python pythonUtilityStuff/getKeyFromJson.py
```

### `js/app.js`
Key additions:
- `var loadedShows = []` — `{key, dir, start, lines}` per loaded show, in order
- `var g_manifest = null` — fetched once on init, cached
- `async loadSelection(selectedShows)`:
  ```js
  Module._clearCorpus();
  Module._reserveCorpus(totalBytes, totalLines);  // exact alloc
  for each show:
      fetch(s.file) → new Uint8Array(arrayBuffer) // transient — GC after copy
      ptr = Module._showWritePtr(u8.length)
      Module.HEAPU8.set(u8, ptr)                  // ONE copy into wasm
      added = Module._commitShow(u8.length)
      loadedShows.push({key, dir, start, lines: added})
  ```
- `Module.onRuntimeInitialized` is now `async`:
  1. Fetch `manifest.json`
  2. Detect mobile via existing UA regex
  3. Generate show-selection checkboxes into `#checkboxes` div from manifest
  4. Wire checkbox `change` → re-call `loadSelection(stillChecked)`
  5. Initial `loadSelection` → `loadDone()`
- `get_dir_and_index_from_biglistnum` replaced: was a 12-arm hardcoded if-ladder,
  now a binary search over `loadedShows[]`:
  ```js
  function get_dir_and_index_from_biglistnum(blNum) {
      var lo = 0, hi = loadedShows.length - 1;
      while (lo < hi) {
          var mid = (lo + hi + 1) >> 1;
          if (loadedShows[mid].start <= blNum) lo = mid;
          else hi = mid - 1;
      }
      var show = loadedShows[lo];
      return [show.dir, blNum - show.start];
  }
  ```

### `MachineFtWams.html`
No changes. The `<div class="row" id="checkboxes">` at line 186 already exists;
`app.js` generates checkboxes into it at runtime.

### `.gitignore`
Added `!manifest.json`, `!data/`, `!data/*.txt` (otherwise `*.json`/`*.txt`
rules would suppress these generated-but-deployable files).

### `CLAUDE.md`
All stale sections updated: stage descriptions, function roster (corpus management
exports added), show-map section replaced with manifest explanation, build command
updated, Files section updated, add-a-show workflow added.

---

## What's left to do (requires the build environment)

### Step 1 — Compile
```powershell
.\build.ps1 -Debug    # -O1 fast build, check for C++ errors
```
Expected: clean compile. Stage 1/2/3 math is untouched; only data source changed.

If it fails, most likely causes:
- `ensureWorkArrays` declared as `static void` — may need to move its definition
  earlier in the file (before cppSearch)
- `hashSortIndices` call site: now passes `scoresArr` (vector) not `scoresArr.data()`

### Step 2 — Generate corpus files
```powershell
python pythonUtilityStuff/getKeyFromJson.py
```
Needs `showMapData/` populated. Outputs `data/*.txt` + `manifest.json`.

### Step 3 — Test locally
```powershell
.\build.ps1 -Serve    # build + serve at http://localhost:8000/MachineFtWams.html
```
Check in browser console:
- "loaded Sailor Moon: 60941 lines" etc. on init
- Search returns results; image paths match production (colourofloosemetal.com)
- Toggling a checkbox re-loads corpus without doubling memory
- Mobile UA in DevTools → only sm/jojo/dbz load by default

### Step 4 — Server config
On colourofloosemetal.com, serve `data/*.txt` with:
- `Content-Encoding: gzip` (browser decompresses transparently on fetch)
- `Cache-Control: max-age=86400` (re-selection uses disk cache, not network)

---

## Key invariants (don't break)

- `reserveCorpus` MUST be called before any `showWritePtr`. Skipping it means
  `g_corpus.resize()` inside `showWritePtr` can realloc, moving the string's
  internal buffer and breaking the pointer contract.
- Read `Module.HEAPU8` fresh after every wasm call that might grow memory
  (especially after `reserveCorpus`). Never cache it in a JS variable.
- Every `.txt` file must end with `\n`. `commitShow` replaces the last `\n` with
  `\0` to null-terminate the final line in-place.
- `clearCorpus` uses the swap idiom (`std::string().swap(g_corpus)`) not `.clear()`
  or `.resize(0)` — those don't release capacity, so mobile memory wouldn't recover.
- The `SHOWS` table order in `getKeyFromJson.py` defines the corpus order and must
  match the image folder names on the server. `manifest.json` is generated from
  this table and is the single source of truth going forward.

---

## Corpus order (for reference — full 12-show load)

```
start    end       key          img dir       show name
0        60940     sm           sm            Sailor Moon
60941    61837     cw2003       cw2003        Clone Wars 2003
61838    65819     swPrequel    swPrequel     Star Wars Prequels
65820    98079     recess       recess        Recess
98080    142917    DisPix       DisPix        Disney Pixar
142918   167908    JohnnyBravo  JohnnyBravo   Johnny Bravo
167909   194671    ghibli       ghibli        Ghibli
194672   214151    looneyTunes  looneyTunes   Looney Tunes
214152   245631    db           db            Dragon Ball
245632   305583    dbz          dbz           Dragon Ball Z
305584   314266    dbzMov       dbzMov        Dragon Ball Z Movies
314267   365697    jojo         jojo          JoJo's Bizarre Adventure
```

This matches the old hardcoded if-ladder — results should be identical when all
shows are loaded.
