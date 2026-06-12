"""Subtitle parsing + caption cleaning.

`clean_caption` MUST reproduce pythonUtilityStuff/getKeyFromJson.py:clean_line
byte-for-byte so the data/<key>.txt this pipeline emits matches the existing
12 shows exactly. clean_line calls remove_non_ascii at BOTH ends and does NOT
.strip() — replicated here verbatim.

`clean_html` is the SEPARATE cleaner used for the text BURNED ONTO the image:
it strips tags/braces but KEEPS the cue's own line breaks (a multi-line cue
stays multi-line on the picture, but collapses to one corpus line).
"""

import re

import pysrt


# ---------------------------------------------------------------------------
# corpus caption cleaning  (mirror of getKeyFromJson.clean_line — keep EXACT)
# ---------------------------------------------------------------------------
def remove_non_ascii(text):
    return re.sub(r'[^\x00-\x7F]', ' ', text)


def clean_caption(raw):
    """Exact mirror of getKeyFromJson.clean_line. One corpus line per cue:
    newlines collapse to spaces here. Do NOT 'improve' this — it must match."""
    line = remove_non_ascii(raw).lower().replace('\n', ' ')
    line = re.sub(r'\s*\{.*?\}\s*', ' ', line)
    line = re.sub(r'\s+', ' ', line)
    line = line.replace('</b>', ' ').replace('<b>', ' ')
    line = line.replace('</i>', ' ').replace('<i>', ' ')
    line = line.replace('\\"', '"')
    return remove_non_ascii(line)


# ---------------------------------------------------------------------------
# burn-in text cleaning  (keeps line breaks; ported from createMapFromVideo)
# ---------------------------------------------------------------------------
_TAG_CLEANER = re.compile('<.*?>')
_BRACKET_CLEANER = re.compile('{.*?}')


def clean_html(text):
    """Strip html-like tags + {brace} junk and leading dialogue dashes, but
    PRESERVE the cue's line breaks (used for what gets drawn on the image)."""
    if "\n- " in text or "\n-" in text:
        text = text.replace("\n- ", "\n").replace("\n-", "\n")
    if text.startswith("- "):
        text = text[2:]
    elif text.startswith("-"):
        text = text[1:]
    text = re.sub(_TAG_CLEANER, '', text)
    text = re.sub(_BRACKET_CLEANER, '', text)
    return text


# ---------------------------------------------------------------------------
# ordering + timing helpers
# ---------------------------------------------------------------------------
def natural_key(string_):
    """Human sort: 's2e10' after 's2e9'. http://www.codinghorror.com/blog/archives/001018.html"""
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]


def sub_time_to_ms(t):
    """pysrt SubRipTime -> total milliseconds."""
    return (t.hours * 3600 + t.minutes * 60 + t.seconds) * 1000 + t.milliseconds


def frame_time_ms(sub, frac):
    """Milliseconds into the video to grab for this cue: `frac` of the way
    through its display window (matches the old 0.6 default)."""
    start = sub_time_to_ms(sub.start)
    end = sub_time_to_ms(sub.end)
    return start + (end - start) * frac


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------
def load_subs(path):
    """Open a .srt with utf-8 first (freshly ffmpeg-extracted subs are utf-8),
    falling back to iso-8859-1 (what the old hand-collected .srt files used)."""
    try:
        return pysrt.open(path, encoding='utf-8')
    except (UnicodeDecodeError, UnicodeError):
        return pysrt.open(path, encoding='iso-8859-1')
