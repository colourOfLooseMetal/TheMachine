<#
.SYNOPSIS
  Build the WAMS WebAssembly search engine and (optionally) serve the page.

.DESCRIPTION
  Compiles wams.cpp + data.cpp -> wams.js / wams.wasm in the repo root, which is
  exactly where MachineFtWams.html loads them from. The emscripten SDK at
  D:\emsdk is activated automatically if `emcc` isn't already on PATH, so you can
  run this from any fresh PowerShell window.

  Output names (wams.js / wams.wasm) differ from the historical command in
  wams.cpp (which emitted generatedWasm/test.js); building straight to wams.*
  means no rename step before a deploy test.

.PARAMETER Debug
  Compile with -O1 (fast build, for iterating) instead of -O3 (release, default).

.PARAMETER Serve
  After a successful build, open MachineFtWams.html and serve the repo root over
  HTTP. Required to actually run the page: browsers won't load .wasm over file://.

.PARAMETER Port
  Port for -Serve (default 8000).

.EXAMPLE
  .\build.ps1               # release build (-O3) -> wams.js + wams.wasm
  .\build.ps1 -Debug        # fast build (-O1)
  .\build.ps1 -Serve        # build, then serve at http://localhost:8000/MachineFtWams.html
  .\build.ps1 -Debug -Serve # fast build + serve (the usual deploy-test loop)
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

# Corpus is now loaded at runtime from per-show .txt files (see manifest.json),
# so data.cpp is no longer compiled in. INITIAL_MEMORY starts small; ALLOW_MEMORY_GROWTH
# lets the heap expand as shows load. HEAPU8 is needed for the JS->wasm copy idiom.
emcc $opt `
    "$root\wams.cpp" `
    -o "$root\wams.js" `
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
Write-Host ("Build OK in {0:N1}s  ->  wams.js + wams.wasm" -f $sw.Elapsed.TotalSeconds) -ForegroundColor Green

# --- optional local server -------------------------------------------------
if ($Serve) {
    $url = "http://localhost:$Port/MachineFtWams.html"
    Write-Host "Serving $root at $url   (Ctrl+C to stop)" -ForegroundColor Cyan
    Start-Process $url
    Set-Location $root
    python -m http.server $Port
}
