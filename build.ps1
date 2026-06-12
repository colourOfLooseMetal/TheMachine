<#
.SYNOPSIS
  Build the WAMS WebAssembly search engine, assemble the deploy folder, and
  (optionally) serve the page locally for testing.

.DESCRIPTION
  Compiles wams.cpp -> dist/wams.js + dist/wams.wasm, then copies the remaining
  deploy files (MachineFtWams.html, css/, js/, data/, manifest.json) into dist/.
  After a build, dist/ contains everything needed for deployment — drag its
  contents into FileZilla to update the live site.

  The emscripten SDK at D:\emsdk is activated automatically if `emcc` isn't
  already on PATH, so you can run this from any fresh PowerShell window.

.PARAMETER Debug
  Compile with -O1 (fast build, for iterating) instead of -O3 (release, default).

.PARAMETER Serve
  After a successful build, serve dist/ over HTTP and open the page.
  Required to actually run the page: browsers won't load .wasm over file://.

.PARAMETER Port
  Port for -Serve (default 8000).

.EXAMPLE
  .\build.ps1               # release build (-O3) -> assembles dist/
  .\build.ps1 -Debug        # fast build (-O1)    -> assembles dist/
  .\build.ps1 -Serve        # build + serve dist/ at http://localhost:8000/MachineFtWams.html
  .\build.ps1 -Debug -Serve # fast build + serve (the usual dev/test loop)
#>
param(
    [switch]$Debug,
    [switch]$Serve,
    [int]$Port = 8000
)

# NOTE: deliberately NOT 'Stop'. emcc and emsdk write to stderr (warnings, the
# activation banner); under -ErrorAction Stop PowerShell turns that stderr into a
# fatal NativeCommandError even on success. We check exit codes explicitly instead.
$ErrorActionPreference = 'Continue'
$root = $PSScriptRoot
$dist = "$root\dist"

# --- locate / activate emscripten -----------------------------------------
if (-not (Get-Command emcc -ErrorAction SilentlyContinue)) {
    $emsdkEnv = 'D:\emsdk\emsdk_env.ps1'
    if (-not (Test-Path $emsdkEnv)) {
        Write-Host "ERROR: emcc is not on PATH and emsdk was not found at $emsdkEnv." -ForegroundColor Red
        Write-Host "Install emsdk or edit the path in build.ps1." -ForegroundColor Red
        exit 1
    }
    Write-Host "Activating emscripten ($emsdkEnv)..." -ForegroundColor DarkGray
    $env:EMSDK_QUIET = 1   # silence the "Setting up EMSDK environment" banner
    & $emsdkEnv *> $null
    if (-not (Get-Command emcc -ErrorAction SilentlyContinue)) {
        Write-Host "ERROR: activated emsdk but emcc still isn't on PATH." -ForegroundColor Red
        exit 1
    }
}

# --- build -----------------------------------------------------------------
$opt = if ($Debug) { '-O1' } else { '-O3' }
Write-Host "Building wams.js / wams.wasm ($opt) ..." -ForegroundColor Cyan
$sw = [Diagnostics.Stopwatch]::StartNew()

# Corpus is loaded at runtime from per-show data/*.txt files (see manifest.json),
# so no static data file is compiled in. ALLOW_MEMORY_GROWTH lets the heap expand
# as shows load. HEAPU8 is needed for the JS->wasm byte-copy idiom.
New-Item -ItemType Directory -Force $dist | Out-Null
emcc $opt `
    "$root\wams.cpp" `
    -o "$dist\wams.js" `
    -s WASM=1 `
    -s EXPORTED_FUNCTIONS="['_search','_reserveCorpus','_showWritePtr','_commitShow','_clearCorpus','_malloc','_free']" `
    -s EXPORTED_RUNTIME_METHODS="['cwrap','UTF8ToString','HEAPU8']" `
    -s ALLOW_MEMORY_GROWTH=1

$code = $LASTEXITCODE
$sw.Stop()

if ($code -ne 0) {
    Write-Host "Build FAILED (exit $code)" -ForegroundColor Red
    exit $code
}
Write-Host ("Build OK in {0:N1}s  ->  dist/wams.js + dist/wams.wasm" -f $sw.Elapsed.TotalSeconds) -ForegroundColor Green

# --- assemble deploy folder ------------------------------------------------
# Copy folder CONTENTS (src\*) into pre-created dirs, not the folder itself.
# Copy-Item src -Recurse on an existing dest would nest (dist\data\data), so
# we use src\* to merge contents directly — safe on both first and re-builds.
Copy-Item "$root\MachineFtWams.html" $dist -Force
Copy-Item "$root\manifest.json"      $dist -Force
New-Item -ItemType Directory -Force "$dist\css"  | Out-Null
New-Item -ItemType Directory -Force "$dist\js"   | Out-Null
New-Item -ItemType Directory -Force "$dist\data" | Out-Null
Copy-Item "$root\css\*"  "$dist\css"  -Recurse -Force
Copy-Item "$root\js\*"   "$dist\js"   -Recurse -Force
Copy-Item "$root\data\*" "$dist\data" -Recurse -Force
Write-Host "Deploy folder assembled -> dist/   (drag contents to FileZilla to deploy)" -ForegroundColor Green

# --- optional local server -------------------------------------------------
if ($Serve) {
    $url = "http://localhost:$Port/MachineFtWams.html"
    Write-Host "Serving dist/ at $url   (Ctrl+C to stop)" -ForegroundColor Cyan
    Start-Process $url
    python -m http.server $Port --directory "$dist"
}
