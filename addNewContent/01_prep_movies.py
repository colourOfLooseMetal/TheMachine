"""Stage 01 (MOVIES ONLY, helper): clean messy movie filenames and pair each
video with its .srt, renaming the .srt to the video's basename so 02/04 can
find it by basename.

Ported from moviesNstuff2024/getFileNameLIst.py (filename token-splitter) and
renameSubFiles.py (video<->srt pairing with ambiguity flags). Nothing is
renamed without confirmation.

    python 01_prep_movies.py --src movies/needFix            # interactive
    python 01_prep_movies.py --src movies/needFix --dry-run  # preview only
    python 01_prep_movies.py --src movies/All --dry-run      # sanity pass
    python 01_prep_movies.py --src movies/needFix --yes       # accept all proposals

Targets needFix/ (the messy set). For All/ this is mostly a basename sanity
pass — most pairs are already clean.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import config  # noqa: E402
from pipeline.titles import clean_title  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def list_videos(folder):
    return sorted(f for f in os.listdir(folder)
                  if f.lower().endswith(config.VIDEO_EXTS))


def list_srts(folder):
    return sorted(f for f in os.listdir(folder) if f.lower().endswith('.srt'))


def confirm(prompt, yes):
    if yes:
        print(prompt + ' -> auto-yes')
        return True
    return input(prompt + ' [Y/n] ').strip().lower() in ('', 'y', 'yes')


def main():
    ap = argparse.ArgumentParser(description='Clean movie filenames + pair .srt files.')
    ap.add_argument('--src', default='movies/needFix',
                    help='folder of movies (relative to addNewContent/ or absolute)')
    ap.add_argument('--dry-run', action='store_true', help='preview only; rename nothing')
    ap.add_argument('--yes', action='store_true', help='accept every proposal without prompting')
    args = ap.parse_args()

    src_dir = args.src if os.path.isabs(args.src) else os.path.join(HERE, args.src)
    if not os.path.isdir(src_dir):
        ap.error(f'source folder not found: {src_dir}')

    videos = list_videos(src_dir)
    srts = list_srts(src_dir)
    print(f'== prep {src_dir}: {len(videos)} video(s), {len(srts)} .srt')
    if args.dry_run:
        print('   (DRY RUN — nothing will be renamed)\n')

    renamed_vid, renamed_srt, flagged = 0, 0, []
    for v in videos:
        proposed = clean_title(v) + os.path.splitext(v)[1]
        print(f'\nVIDEO: {v}')
        print(f'   proposed: {proposed}')

        new_v = v
        if proposed != v:
            if args.dry_run:
                print('   would rename video.')
            elif args.yes:
                os.rename(os.path.join(src_dir, v), os.path.join(src_dir, proposed))
                new_v = proposed
                renamed_vid += 1
                print('   renamed video.')
            else:
                ans = input('   accept (Enter) / type new name / [s]kip: ').strip()
                if ans.lower() == 's':
                    print('   skipped.')
                else:
                    target = proposed if ans == '' else ans
                    os.rename(os.path.join(src_dir, v), os.path.join(src_dir, target))
                    new_v = target
                    renamed_vid += 1
                    print(f'   renamed video -> {target}')

        new_base = os.path.splitext(new_v)[0]
        # find the .srt to pair: exact basename match wins; else fuzzy by title
        srt_match = pair_srt(src_dir, v, new_v)
        if srt_match is None:
            print('   no sidecar .srt found (embedded subs? 02 will probe).')
            continue
        if os.path.splitext(srt_match)[0] == new_base:
            print(f'   .srt already matches: {srt_match}')
            continue
        target_srt = new_base + '.srt'
        print(f'   SRT: {srt_match}  ->  {target_srt}')
        if args.dry_run:
            print('   would rename .srt.')
        elif confirm('   rename this .srt?', args.yes):
            dst = os.path.join(src_dir, target_srt)
            if os.path.exists(dst):
                print('   !! target .srt already exists — flagging, not overwriting.')
                flagged.append(v)
            else:
                os.rename(os.path.join(src_dir, srt_match), dst)
                renamed_srt += 1
                print('   renamed .srt.')

    print(f'\n== done: {renamed_vid} video(s) renamed, {renamed_srt} .srt renamed')
    if flagged:
        print('   flagged (manual attention):')
        for f in flagged:
            print(f'      - {f}')
    print('\n   next: run 02_extract_subs.py --set movies --src ' + args.src)


def pair_srt(folder, orig_video, new_video):
    """Best-guess the .srt for a video. Exact basename match (orig or new) wins;
    otherwise compare cleaned titles."""
    srts = list_srts(folder)
    orig_base = os.path.splitext(orig_video)[0]
    new_base = os.path.splitext(new_video)[0]
    for s in srts:
        sb = os.path.splitext(s)[0]
        if sb in (orig_base, new_base):
            return s
    # fuzzy: matching cleaned title
    want = clean_title(orig_video).lower()
    for s in srts:
        if clean_title(s).lower() == want:
            return s
    return None


if __name__ == '__main__':
    main()
