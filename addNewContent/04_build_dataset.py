"""Stage 04 (MAIN): caption -> frame -> downscale -> burn -> numbered jpg +
data/<key>.txt (+ movies_map.json for movies).

Assumes each video already has a sidecar .srt of the same basename (run
02_extract_subs.py first for embedded subs). Episodes are processed in
natural_key order; movies in cleaned-title order. One non-empty cue produces
exactly one image and one corpus line, in lock-step.

Test mode (eyeball sizing without a full run):
    python 04_build_dataset.py --set seinfeld --limit-titles 1
    python 04_build_dataset.py --set movies --lines-per-title 2
Append more films onto an existing movies set:
    python 04_build_dataset.py --set movies --src .../moreMovies --append

Output images land in addNewContent/out/<dir>/ ; data/<key>.txt is written
straight into the repo's data/ so it's build-ready.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import config, frames, caption, dataset, subtitles  # noqa: E402
from pipeline.titles import clean_title  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(HERE, '..'))
OUT_ROOT = os.path.join(HERE, 'out')

SETS = config.SETS


def find_videos(src_dir):
    return [f for f in os.listdir(src_dir)
            if f.lower().endswith(config.VIDEO_EXTS)]


def sidecar_srt(src_dir, video_file):
    """The same-basename .srt next to the video, or None."""
    base = os.path.splitext(video_file)[0]
    cand = os.path.join(src_dir, base + '.srt')
    return cand if os.path.exists(cand) else None


def title_from_filename(video_file):
    """Display/map title for a movie. Always run through clean_title so the card
    shows a tidy title even when the file on disk was never renamed (e.g. the
    movies/All set, which 01_prep_movies doesn't touch). For already-clean names
    this is a no-op beyond stripping the extension."""
    return clean_title(os.path.basename(video_file))


def process_video(video_path, srt_path, writer, lines_limit=None, log=print):
    """Burn every non-empty cue of one video. Returns #images written."""
    subs = subtitles.load_subs(srt_path)
    written = 0
    with frames.FrameGrabber(video_path) as fg:
        for sub in subs:
            if lines_limit is not None and written >= lines_limit:
                break
            if not sub.text.strip():
                continue
            frame = fg.grab_best_frame(sub)
            if frame is None:
                log(f'    !! no frame for cue @ {sub.start} — skipped')
                continue
            burned = caption.burn_caption(frame, subtitles.clean_html(sub.text))
            writer.write_frame(burned, subtitles.clean_caption(sub.text))
            written += 1
    return written


def main():
    ap = argparse.ArgumentParser(description='Build a Machine dataset from videos + sidecar .srt.')
    ap.add_argument('--set', required=True, choices=sorted(SETS), help='which corpus to build')
    ap.add_argument('--src', help='override source folder (relative to addNewContent/ or absolute)')
    ap.add_argument('--append', action='store_true', help='movies: continue numbering + map')
    ap.add_argument('--limit-titles', type=int, default=None, metavar='N',
                    help='test mode: process at most N videos')
    ap.add_argument('--lines-per-title', type=int, default=None, metavar='N',
                    help='test mode: at most N cues per video')
    args = ap.parse_args()

    cfg = SETS[args.set]
    src = args.src or cfg['src']
    src_dir = src if os.path.isabs(src) else os.path.join(HERE, src)
    if not os.path.isdir(src_dir):
        ap.error(f'source folder not found: {src_dir}')

    videos = find_videos(src_dir)
    # episodes: natural sort; movies: by cleaned title
    if cfg['movies']:
        videos.sort(key=lambda v: subtitles.natural_key(title_from_filename(v).lower()))
    else:
        videos.sort(key=subtitles.natural_key)
    if args.limit_titles is not None:
        videos = videos[:args.limit_titles]

    print(f'== building set "{args.set}" from {src_dir}')
    print(f'   {len(videos)} video(s); movies={cfg["movies"]} append={args.append}')

    missing, total = [], 0
    with dataset.DatasetWriter(cfg['key'], cfg['img_dir'], REPO_ROOT, OUT_ROOT,
                               movies=cfg['movies'], append=args.append) as writer:
        for v in videos:
            srt = sidecar_srt(src_dir, v)
            if srt is None:
                print(f'   [MISS] {v}: no sidecar .srt — run 02_extract_subs first; skipping')
                missing.append(v)
                continue
            if cfg['movies']:
                writer.start_film(title_from_filename(v))
            print(f'   [{writer.next_index:6d}] {v}')
            n = process_video(os.path.join(src_dir, v), srt, writer,
                              lines_limit=args.lines_per_title)
            total += n
            print(f'            +{n} images (total {writer.count})')
        final_count = writer.count

    print(f'\n== done: {total} images written, corpus now {final_count} lines')
    print(f'   images : {os.path.join(OUT_ROOT, cfg["img_dir"])}')
    print(f'   captions: {os.path.join(REPO_ROOT, "data", cfg["key"] + ".txt")}')
    if cfg['movies']:
        print(f'   map     : {os.path.join(REPO_ROOT, "data", "movies_map.json")}')
    if missing:
        print(f'   {len(missing)} video(s) skipped for missing .srt:')
        for m in missing:
            print(f'      - {m}')
    print('\n   next: run 05_emit_manifest.py --set ' + args.set)


if __name__ == '__main__':
    main()
