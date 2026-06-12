"""Stage 03 (optional opt-in): audio alignment check.

Plays a few audio clips against their subtitle text so you can confirm sync
before a full dataset build. Not part of the default pipeline run — use on
titles you suspect are offset after running stage 02.

    python 03_check_alignment.py path/to/video.mkv
    python 03_check_alignment.py path/to/video.mkv path/to/sub.srt
    python 03_check_alignment.py --set seinfeld
    python 03_check_alignment.py --set movies --src movies/needFix
    python 03_check_alignment.py --set seinfeld --samples 3

Requires ffmpeg + ffplay (bundled together, already on PATH). No extra Python deps.

Controls during playback: press Enter to accept the clip early and move on.
After playback: Enter/y = in sync | n = offset | s = skip title | q = quit
"""

import argparse
import os
import subprocess
import sys
import time

try:
    import msvcrt
    _HAVE_MSVCRT = True
except ImportError:
    _HAVE_MSVCRT = False

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import config, subtitles  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

DEFAULT_SAMPLES = 2


def _sample_indices(total, n):
    """Return n cue indices to sample: near start (idx 5) and near end (idx total-5),
    plus evenly spaced extras. Mirrors the original checkSubsViaAudio positions."""
    if total < 10:
        return []
    start = min(5, total - 1)
    end = max(total - 5, start + 1)
    if n <= 1:
        return [start]
    if n == 2:
        return [start, end]
    step = (end - start) / (n - 1)
    return sorted({int(start + i * step) for i in range(n)})


def _play(video_path, ms_start, ms_end):
    """Extract an exact audio slice via ffmpeg→ffplay pipe and play it.

    ffplay's own -ss seek lands on a container keyframe (often the start of
    the previous subtitle). Piping through ffmpeg avoids that: ffmpeg trims
    to the exact millisecond and hands a plain WAV stream to ffplay.

    Returns True if the user pressed Enter during playback (early accept)."""
    start_s = ms_start / 1000.0
    dur_s = (ms_end - ms_start) / 1000.0

    enc_cmd = [
        'ffmpeg',
        '-ss', f'{start_s:.3f}',
        '-i', video_path,
        '-t', f'{dur_s:.3f}',
        '-vn', '-f', 'wav', 'pipe:1',
        '-loglevel', 'quiet',
    ]
    dec_cmd = [
        'ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet',
        '-f', 'wav', '-i', 'pipe:0',
    ]

    try:
        enc = subprocess.Popen(enc_cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL)
        dec = subprocess.Popen(dec_cmd, stdin=enc.stdout,
                               stderr=subprocess.DEVNULL)
        enc.stdout.close()  # hand sole ownership of the write-end to enc
    except FileNotFoundError as e:
        print(f'  [ERROR] {e.filename} not found on PATH')
        return False

    accepted = False
    if _HAVE_MSVCRT:
        # Poll for Enter keypress while the player is alive (Windows only).
        while dec.poll() is None:
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ('\r', '\n'):
                    accepted = True
                    dec.terminate()
                    try:
                        enc.terminate()
                    except OSError:
                        pass
                    break
            time.sleep(0.05)
    else:
        dec.wait()

    dec.wait()
    enc.wait()
    return accepted


def check_one(video_path, srt_path, n_samples):
    """Check alignment for one video+srt pair.
    Returns True (passed), False (user flagged mismatch), 'skipped', or 'quit'."""
    label = os.path.basename(video_path)
    print(f'\n== {label}')

    if not os.path.exists(srt_path):
        print(f'  [SKIP] no sidecar .srt: {srt_path}')
        return 'skipped'

    subs_list = subtitles.load_subs(srt_path)
    total = len(subs_list)
    if total < 10:
        print(f'  [SKIP] only {total} cues — too few to sample')
        return 'skipped'

    indices = _sample_indices(total, n_samples)
    passed = True

    for s_num, idx in enumerate(indices, 1):
        sub = subs_list[idx]
        text = subtitles.clean_html(sub.text)
        ms_start = subtitles.sub_time_to_ms(sub.start)
        ms_end = subtitles.sub_time_to_ms(sub.end)

        print(f'\n  Sample {s_num}/{len(indices)}  (cue {idx + 1}/{total})')
        print(f'  {sub.start} --> {sub.end}')
        print(f'  {text}')
        print('  [playing... press Enter to accept]')
        early = _play(video_path, ms_start, ms_end)

        if early:
            print('  -> accepted')
            continue

        resp = input('  In sync? [Enter/y = OK | n = offset | s = skip title | q = quit] ').strip().lower()
        if resp == 'q':
            return 'quit'
        if resp == 's':
            print('  [SKIP]')
            return 'skipped'
        if resp == 'n':
            print('  [FAIL] alignment problem noted')
            passed = False
            # keep going through remaining samples for this title
            continue
        # Enter, 'y', or anything else = in sync

    if passed:
        print(f'  [PASS] {len(indices)}/{len(indices)} samples OK')
    return passed


def main():
    ap = argparse.ArgumentParser(
        description='Optional: spot-check subtitle sync by playing a few audio clips.')
    ap.add_argument('video', nargs='?',
                    help='video file (single-file mode)')
    ap.add_argument('srt', nargs='?',
                    help='subtitle file (default: same-basename .srt)')
    ap.add_argument('--set', choices=sorted(config.SETS),
                    help='process all videos in a content set')
    ap.add_argument('--src',
                    help='source folder override (relative to addNewContent/ or absolute)')
    ap.add_argument('--samples', type=int, default=DEFAULT_SAMPLES,
                    help=f'cues to sample per video (default: {DEFAULT_SAMPLES})')
    args = ap.parse_args()

    if args.video and args.set:
        ap.error('specify either a video path or --set, not both')
    if not args.video and not args.set:
        ap.error('specify a video path or --set <name>')

    # --- single-file mode -------------------------------------------------------
    if args.video:
        video_path = os.path.abspath(args.video)
        if not os.path.exists(video_path):
            ap.error(f'video not found: {video_path}')
        if args.srt:
            srt_path = os.path.abspath(args.srt)
        else:
            srt_path = os.path.splitext(video_path)[0] + '.srt'
        result = check_one(video_path, srt_path, args.samples)
        if result is False:
            print('\n[FAIL] subtitle sync issue — check the offset.')
        elif result == 'quit':
            print('\nAborted.')
        return

    # --- set mode ---------------------------------------------------------------
    cfg = config.SETS[args.set]
    src = args.src or cfg['src']
    src_dir = src if os.path.isabs(src) else os.path.join(HERE, src)
    if not os.path.isdir(src_dir):
        ap.error(f'source folder not found: {src_dir}')

    videos = sorted(
        (f for f in os.listdir(src_dir) if f.lower().endswith(config.VIDEO_EXTS)),
        key=subtitles.natural_key,
    )
    print(f'== check_alignment "{args.set}" in {src_dir} ({len(videos)} video(s))')
    print('   During playback: Enter = accept early')
    print('   After playback:  Enter/y = OK  |  n = offset  |  s = skip  |  q = quit\n')

    passed, failed, skipped = [], [], []
    for v in videos:
        base = os.path.splitext(v)[0]
        result = check_one(
            os.path.join(src_dir, v),
            os.path.join(src_dir, base + '.srt'),
            args.samples,
        )
        if result == 'quit':
            print('\nAborted.')
            break
        elif result is True:
            passed.append(v)
        elif result is False:
            failed.append(v)
        else:
            skipped.append(v)

    print(f'\n== done: {len(passed)} passed  {len(failed)} failed  {len(skipped)} skipped')
    if failed:
        print('Alignment issues (check subtitle offset):')
        for f in failed:
            print(f'  - {f}')
    print('\n   next: run 04_build_dataset.py --set ' + args.set)


if __name__ == '__main__':
    main()
