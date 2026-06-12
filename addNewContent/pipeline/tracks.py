"""Subtitle-track inspection + selection.

The old extractSubs.py always grabbed `0:s:0` (stream 0) blindly. Real files
have up to 11 language tracks, forced/foreign tracks, and image-based (PGS)
tracks we can't use. This module probes the streams with ffprobe, classifies
them text-vs-image, and auto-picks the English / non-forced / text track —
prompting only when the choice is genuinely ambiguous. Every decision is logged.
"""

import json
import subprocess

from . import config


class SubTrack:
    """One subtitle stream. `sub_index` is the 0-based index AMONG subtitle
    streams (what `ffmpeg -map 0:s:<n>` wants), distinct from the absolute
    stream index."""

    def __init__(self, sub_index, abs_index, codec, lang, title, forced, default):
        self.sub_index = sub_index
        self.abs_index = abs_index
        self.codec = (codec or '').lower()
        self.lang = (lang or '').lower()
        self.title = title or ''
        self.forced = bool(forced)
        self.default = bool(default)

    @property
    def kind(self):
        if self.codec in config.TEXT_CODECS:
            return 'text'
        if self.codec in config.IMAGE_CODECS:
            return 'image'
        return 'unknown'

    @property
    def is_english(self):
        if self.lang in config.ENGLISH_LANGS:
            return True
        # Fall back to an English-ish title when the language tag is missing.
        t = self.title.lower()
        return self.lang == '' and ('english' in t or t.strip() == 'eng')

    @property
    def title_says_forced(self):
        return 'forced' in self.title.lower()

    def __repr__(self):
        bits = [f's:{self.sub_index}', f'#{self.abs_index}', self.codec,
                self.lang or '??', self.kind]
        if self.title:
            bits.append(repr(self.title))
        if self.forced or self.title_says_forced:
            bits.append('FORCED')
        if self.default:
            bits.append('default')
        return 'SubTrack(' + ', '.join(bits) + ')'


def probe_subtitle_tracks(video_path):
    """Return the list of SubTrack for `video_path`, in subtitle-stream order."""
    cmd = [
        'ffprobe', '-v', 'error', '-select_streams', 's',
        '-show_entries',
        'stream=index,codec_name:stream_tags=language,title:stream_disposition=forced,default',
        '-of', 'json', video_path,
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if out.returncode != 0:
        raise RuntimeError(f'ffprobe failed on {video_path}:\n{out.stderr.strip()}')
    streams = json.loads(out.stdout or '{}').get('streams', [])
    tracks = []
    for sub_i, s in enumerate(streams):
        tags = s.get('tags', {}) or {}
        disp = s.get('disposition', {}) or {}
        tracks.append(SubTrack(
            sub_index=sub_i,
            abs_index=s.get('index'),
            codec=s.get('codec_name'),
            lang=tags.get('language'),
            title=tags.get('title'),
            forced=disp.get('forced'),
            default=disp.get('default'),
        ))
    return tracks


def _is_forced(t):
    return t.forced or t.title_says_forced


def pick_subtitle_track(tracks, video_label='', interactive=True, log=print):
    """Choose the best subtitle track. Returns the chosen SubTrack, or None if
    there is no usable text track.

    Heuristic (locked decision #2 — auto-pick, confirm only when ambiguous):
      1. Keep only TEXT tracks (image/PGS rejected -> can't burn without OCR).
      2. Prefer English, non-forced.
      3. Exactly one candidate -> auto-pick. Several -> prompt. None English but
         exactly one text track overall -> auto-pick it. Otherwise prompt.
    Every decision is logged via `log`.
    """
    label = f'[{video_label}] ' if video_label else ''
    text_tracks = [t for t in tracks if t.kind == 'text']
    image_only = [t for t in tracks if t.kind == 'image']

    if not text_tracks:
        if image_only:
            log(f'{label}REJECT: only image-based subtitle tracks '
                f'({", ".join(t.codec for t in image_only)}) — needs OCR, skipping.')
        else:
            log(f'{label}REJECT: no subtitle tracks found.')
        return None

    eng_unforced = [t for t in text_tracks if t.is_english and not _is_forced(t)]

    if len(eng_unforced) == 1:
        chosen = eng_unforced[0]
        log(f'{label}AUTO-PICK {chosen} (sole English non-forced text track).')
        return chosen

    if not eng_unforced and len(text_tracks) == 1:
        chosen = text_tracks[0]
        log(f'{label}AUTO-PICK {chosen} (only one text track; lang tag '
            f'{chosen.lang or "missing"}).')
        return chosen

    # Ambiguous: several English candidates, or several non-English text tracks.
    candidates = eng_unforced if eng_unforced else text_tracks
    log(f'{label}AMBIGUOUS — {len(candidates)} candidate text track(s):')
    for t in candidates:
        log(f'    {t}')

    if not interactive:
        chosen = candidates[0]
        log(f'{label}non-interactive: defaulting to first candidate {chosen}.')
        return chosen

    return _prompt_for_track(candidates, text_tracks, label, log)


def _prompt_for_track(candidates, text_tracks, label, log):
    pool = candidates if len(candidates) > 1 else text_tracks
    print(f'\n{label}Select subtitle track to use:')
    for i, t in enumerate(pool):
        print(f'  [{i}] {t}')
    print('  [s] skip this title')
    while True:
        ans = input('  choice (default 0): ').strip().lower()
        if ans == '':
            ans = '0'
        if ans == 's':
            log(f'{label}user SKIPPED.')
            return None
        if ans.isdigit() and int(ans) < len(pool):
            chosen = pool[int(ans)]
            log(f'{label}user picked {chosen}.')
            return chosen
        print('  invalid choice.')


def extract_track(video_path, sub_index, out_srt, log=print):
    """Extract subtitle stream `sub_index` to `out_srt` as SubRip text."""
    cmd = [
        'ffmpeg', '-y', '-v', 'error', '-i', video_path,
        '-map', f'0:s:{sub_index}', '-c:s', 'srt', out_srt,
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if out.returncode != 0:
        raise RuntimeError(f'ffmpeg extract failed (0:s:{sub_index}) on '
                           f'{video_path}:\n{out.stderr.strip()}')
    log(f'    extracted 0:s:{sub_index} -> {out_srt}')
    return out_srt
