"""Movie filename -> clean display title.

Ported from moviesNstuff2024/getFileNameLIst.py's token-splitter: drop everything
from the earliest release-junk token (or the first plausible year's end), strip
separators/parens, re-wrap recognised genre words. Leading 2-digit sequence
numbers ("01 ") and bracket-enclosed tags like (Sci-Fi) are stripped; 4-digit
years are kept.

Shared by 01_prep_movies.py (renames files to the cleaned name) and
04_build_dataset.py (stamps the cleaned name into movies_map.json as the card
title, so the display title is clean even when the file on disk was never
renamed — e.g. the movies/All set, which 01 doesn't touch).
"""

import os
import re

# Tokens that mark the start of release-junk; everything from the earliest of
# these (or the first plausible year) is dropped. From getFileNameLIst.py.
SPLIT_TOKENS = ['720p', '1080p', '2160p', '480p', 'eng', 'bluray', 'dvd', '[',
                'bdrip', '1080', '2160', 'webrip', 'brrip', ' cc', 'blu',
                'xvid', 'x264', 'x265', 'hevc', 'web-dl', 'web ',
                't.c.r']
GENRES = ['Sci Fi', 'Comedy', 'Horror', 'Fantasy', 'Adventure', 'Action',
          'Drama', 'Thriller']


def clean_title(name):
    """Strip release junk from a filename, keep the year, return the cleaned
    base (no extension). Mirrors getFileNameLIst.py's split-on-earliest logic."""
    base, ext = os.path.splitext(name)

    # Remove leading 2-digit sequence numbers ("01 Tron..." -> "Tron...").
    # (?!\d) ensures we don't touch 4-digit years that happen to start a name.
    base = re.sub(r'^\d{2}(?!\d)\s+', '', base)
    # Remove bracket-enclosed tags like (Sci-Fi), (Horror) — but keep (YYYY).
    base = re.sub(r'\s*\((?!\d{4}\))[^)]*\)', '', base)
    name = base + ext

    # candidate cut points: end-of-year, and start-of-junk-token (>= index 7)
    cut_points = []
    for m in re.finditer(r'(?:[^\d]|\A)(\d{4})(?:[^\d]|\Z)', name):
        yr = int(m.group(1))
        if 1922 < yr < 2031:
            yi = name.find(m.group(1))
            if yi >= 7:
                cut_points.append(yi + 4)
    for tok in SPLIT_TOKENS:
        i = name.lower().find(tok)
        if i >= 7:
            cut_points.append(i)

    if cut_points:
        cut = min(cut_points)
    else:
        cut = len(base)  # nothing to strip -> drop only the extension

    title = name[:cut]
    title = title.replace('.', ' ').replace('-', ' ').replace('_', ' ')
    title = title.replace('(', '').replace(')', '')
    title = re.sub(r'\s+', ' ', title).strip()
    # re-wrap recognised genre words in parens (the old scripts' convention)
    for g in GENRES:
        title = re.sub(rf'\b{re.escape(g)}\b', f'({g})', title, flags=re.IGNORECASE)
    return title
