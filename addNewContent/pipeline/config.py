"""Pipeline-wide constants. Tuned to match the existing show assets and the
gold-standard MeanGirls burn-in (verified 960x540 in screenShotsSubbed/)."""

import os

# --- output sizing -----------------------------------------------------------
# Downscale every frame to FIT WITHIN this box, preserving aspect, shrink-only.
# Matches the existing show assets; the gold-standard MeanGirls images are 960x540.
BOX_W = 960
BOX_H = 540

# JPEG write quality (cv2.IMWRITE_JPEG_QUALITY). The old scripts used 91.
JPEG_QUALITY = 91

# --- caption burn-in (relative to FRAME HEIGHT) ------------------------------
# The MeanGirls "good" script used a fixed 42px font + 3px outline at H=540:
#   42 / 540 = 0.0778  ;  3 / 540 = 0.00556
# Scaling relative to height keeps that look across every aspect ratio.
FONT_FRAC = 0.078        # font size  ~= FONT_FRAC * H
OUTLINE_FRAC = 0.0055    # outline px ~= OUTLINE_FRAC * H  (min 1)
TEXT_BASELINE_FRAC = 0.90   # y = TEXT_BASELINE_FRAC * H - lineHeight
MAX_LINE_WIDTH_FRAC = 0.9   # wrap any single line wider than this * W

# Font lives alongside the stage scripts (addNewContent/arial.ttf), copied from
# MeanGirlsFiles/arial.ttf. Resolve relative to the package, not the cwd.
_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.normpath(os.path.join(_PKG_DIR, '..', 'arial.ttf'))

# --- frame selection ---------------------------------------------------------
# Grab the frame at this fraction through the subtitle's display window first;
# if it's too blurry, retry the alternates and keep the sharpest above threshold.
PRIMARY_FRAME_FRAC = 0.6
ALT_FRAME_FRACS = (0.45, 0.55, 0.7)
# Laplacian-variance floor: a frame scoring below this is "blurry" (e.g. a hard
# cut / motion blur). If no candidate clears it, keep the sharpest one anyway.
BLUR_THRESHOLD = 100.0

# --- subtitle track classification (ffprobe codec_name) ----------------------
# Text-based subtitle codecs we can burn in directly.
TEXT_CODECS = {'subrip', 'srt', 'ass', 'ssa', 'mov_text', 'webvtt', 'text', 'stl'}
# Image/bitmap subtitle codecs we CANNOT use (would need OCR) -> rejected.
IMAGE_CODECS = {'hdmv_pgs_subtitle', 'dvd_subtitle', 'dvdsub', 'dvb_subtitle', 'xsub', 'pgssub'}

# Language tags considered English.
ENGLISH_LANGS = {'eng', 'en', 'en-us', 'en-gb'}

# --- image host --------------------------------------------------------------
# The original 12 shows are served from colourofloosemetal.com/assets/<dir>/; the
# front end uses that as its default. Everything this pipeline emits is uploaded to
# the DigitalOcean Space instead, so 05_emit_manifest.py stamps this `base` (host
# root before <dir>/<n>.jpg) onto the manifest row. js/app.js reads it per-dir.
ASSET_BASE = 'https://colm-extra-storage.nyc3.cdn.digitaloceanspaces.com/'

# --- video / subtitle file extensions ----------------------------------------
VIDEO_EXTS = ('.mkv', '.mp4', '.avi', '.mov', '.m4v', '.webm')
SUB_EXTS = ('.srt',)

# --- known content sets ------------------------------------------------------
# `src` is relative to addNewContent/. `movies=True` -> single "Movies" dataset
# with a per-film boundary map (locked decision #1). Shared by stages 02/04/05.
SETS = {
    'seinfeld': dict(key='seinfeld', img_dir='seinfeld', name='Seinfeld',
                     src='seinfeld/allEpisodes', movies=False),
    'movies':   dict(key='movies', img_dir='movies', name='Movies',
                     src='movies/All', movies=True),
}
