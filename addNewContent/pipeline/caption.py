"""Burn the caption onto a frame.

Port of moviesNstuff2024/saveImagesWithSubText-fromMGoriginally.py (the user's
tuned "good" placement, matching the gold-standard 960x540 MeanGirls images):
white text, ~3px black outline via nested range(-b,b+1) double-draw, centered
horizontally, baseline ~90% of frame height, the cue's own line breaks kept.

Two changes from the original:
  * font/outline sizes are RELATIVE to frame height (FONT_FRAC / OUTLINE_FRAC)
    instead of a hard-coded 42px/3px, so it looks right across aspect ratios.
  * modern Pillow: textlength / textbbox instead of the removed textsize.

Input/output are cv2 BGR numpy frames (that's what frames.py produces and what
dataset.py writes with cv2.imwrite); we hop into PIL only to draw.
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import config


def _wrap_long_line(draw, line, font, max_w):
    """Greedily wrap a single physical line whose rendered width exceeds max_w.
    Most .srt lines are already pre-broken, so this rarely fires."""
    if draw.textlength(line, font=font) <= max_w:
        return [line]
    words = line.split(' ')
    out, cur = [], ''
    for word in words:
        trial = word if cur == '' else cur + ' ' + word
        if draw.textlength(trial, font=font) <= max_w or cur == '':
            cur = trial
        else:
            out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


def burn_caption(frame_bgr, text):
    """Return a new BGR frame with `text` burned in. `text` should already be
    clean_html'd (tags stripped, cue line breaks preserved)."""
    image = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
    W, H = image.size
    draw = ImageDraw.Draw(image)

    font_size = max(1, round(config.FONT_FRAC * H))
    outline = max(1, round(config.OUTLINE_FRAC * H))
    font = ImageFont.truetype(config.FONT_PATH, size=font_size)

    # Keep the cue's own breaks; only wrap a physical line if it's too wide.
    max_w = config.MAX_LINE_WIDTH_FRAC * W
    lines = []
    for raw_line in text.split('\n'):
        lines.extend(_wrap_long_line(draw, raw_line, font, max_w))
    caption = '\n'.join(lines)

    # Width = the longest rendered line (matches the original's longest-line calc).
    w = max((draw.textlength(li, font=font) for li in lines), default=0)
    ascent, descent = font.getmetrics()
    line_h = ascent + descent

    x = 0.5 * (W - w)
    y = config.TEXT_BASELINE_FRAC * H - line_h

    # Black outline: draw the text shifted in every direction within the border,
    # then the white fill on top. Same nested-range double-draw as the original.
    for dx in range(-outline, outline + 1):
        for dy in range(-outline, outline + 1):
            draw.multiline_text((x + dx, y + dy), caption, fill='black',
                                font=font, align='center')
    draw.multiline_text((x, y), caption, fill=(255, 255, 255),
                        font=font, align='center')

    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
