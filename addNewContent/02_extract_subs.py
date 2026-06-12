"""Stage 02: ensure every video has a usable sidecar .srt of the same basename.

For each video in the set's source folder:
  * If a non-empty same-basename .srt already exists (the movies/All case),
    keep it.
  * Otherwise probe embedded subtitle tracks (tracks.py), auto-pick the
    English / non-forced / text track (prompt only when ambiguous), and extract
    it with `ffmpeg -map 0:s:<idx> -c:s srt` to a sidecar .srt.
  * Titles whose only subtitles are image-based (PGS/VobSub) are skipped + flagged.

Every track decision is logged. Run this before 04_build_dataset.py.

    python 02_extract_subs.py --set seinfeld
    python 02_extract_subs.py --set movies --src movies/needFix
    python 02_extract_subs.py --set seinfeld --yes      # never prompt
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import config, tracks  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def srt_has_text(path):
    """A non-empty .srt has at least one line with actual caption text."""
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            for line in f:
                s = line.strip()
                if s and '-->' not in s and not s.isdigit():
                    return True
    except OSError:
        return False
    return False


def main():
    ap = argparse.ArgumentParser(description='Extract/validate sidecar .srt for each video.')
    ap.add_argument('--set', required=True, choices=sorted(config.SETS))
    ap.add_argument('--src', help='override source folder (relative to addNewContent/ or absolute)')
    ap.add_argument('--yes', action='store_true', help='never prompt; auto-pick the best candidate')
    args = ap.parse_args()

    cfg = config.SETS[args.set]
    src = args.src or cfg['src']
    src_dir = src if os.path.isabs(src) else os.path.join(HERE, src)
    if not os.path.isdir(src_dir):
        ap.error(f'source folder not found: {src_dir}')

    videos = sorted(f for f in os.listdir(src_dir)
                    if f.lower().endswith(config.VIDEO_EXTS))
    print(f'== extracting subs for "{args.set}" in {src_dir} ({len(videos)} video(s))')

    have, extracted, skipped = 0, 0, []
    for v in videos:
        base = os.path.splitext(v)[0]
        video_path = os.path.join(src_dir, v)
        srt_path = os.path.join(src_dir, base + '.srt')

        if os.path.exists(srt_path) and srt_has_text(srt_path):
            print(f'[HAVE]  {v} -> {base}.srt already present')
            have += 1
            continue

        try:
            trks = tracks.probe_subtitle_tracks(video_path)
        except RuntimeError as e:
            print(f'[ERR]   {v}: {e}')
            skipped.append(v)
            continue

        chosen = tracks.pick_subtitle_track(
            trks, video_label=v, interactive=not args.yes)
        if chosen is None:
            skipped.append(v)
            continue

        try:
            tracks.extract_track(video_path, chosen.sub_index, srt_path)
            if srt_has_text(srt_path):
                extracted += 1
            else:
                print(f'[WARN]  {v}: extracted .srt has no text — flagging')
                skipped.append(v)
        except RuntimeError as e:
            print(f'[ERR]   {v}: {e}')
            skipped.append(v)

    print(f'\n== done: {have} already had subs, {extracted} extracted, {len(skipped)} skipped/flagged')
    if skipped:
        for s in skipped:
            print(f'   - {s}')
    print('\n   next: run 04_build_dataset.py --set ' + args.set)


if __name__ == '__main__':
    main()
