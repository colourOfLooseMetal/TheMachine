"""Stage 05: merge the freshly-built set into manifest.json and print the
deploy checklist.

Reads the lines/bytes from the data/<key>.txt that 04 wrote, builds the
manifest row ({key,dir,name,lines,bytes,file}), and inserts or replaces it in
manifest.json. Order in the array defines global corpus order; an existing key
is replaced in place, a new key is appended (so the 12 current shows keep their
order and the new set lands last — matching the image folders on the server).

    python 05_emit_manifest.py --set seinfeld
    python 05_emit_manifest.py --set movies
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import config  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(HERE, '..'))
MANIFEST = os.path.join(REPO_ROOT, 'manifest.json')


def build_row(cfg):
    txt_path = os.path.join(REPO_ROOT, 'data', cfg['key'] + '.txt')
    if not os.path.exists(txt_path):
        raise SystemExit(f'data file missing: {txt_path}\n'
                         f'   run 04_build_dataset.py --set {cfg["key"]} first.')
    with open(txt_path, encoding='utf-8') as f:
        lines = sum(1 for _ in f)
    return {
        'key':   cfg['key'],
        'dir':   cfg['img_dir'],
        'name':  cfg['name'],
        'lines': lines,
        'bytes': os.path.getsize(txt_path),
        'file':  'data/' + cfg['key'] + '.txt',
        # New sets are uploaded to the DigitalOcean Space, not the legacy host; tell
        # the front end where to fetch this dir's images. (Omit -> legacy default.)
        'base':  config.ASSET_BASE,
    }


def main():
    ap = argparse.ArgumentParser(description='Merge a built set into manifest.json.')
    ap.add_argument('--set', required=True, choices=sorted(config.SETS))
    args = ap.parse_args()
    cfg = config.SETS[args.set]

    row = build_row(cfg)
    with open(MANIFEST, encoding='utf-8') as f:
        manifest = json.load(f)

    idx = next((i for i, r in enumerate(manifest) if r['key'] == row['key']), None)
    if idx is None:
        manifest.append(row)
        action = f'appended (now {len(manifest)} rows)'
    else:
        manifest[idx] = row
        action = f'replaced in place at index {idx}'

    with open(MANIFEST, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f'manifest.json: row "{row["key"]}" {action}')
    print(f'   {json.dumps(row)}')

    # --- deploy checklist ---------------------------------------------------
    out_dir = os.path.join(HERE, 'out', cfg['img_dir'])
    print('\n=== DEPLOY CHECKLIST ===')
    print(f'1. Upload {out_dir}\\*.jpg  ->  DigitalOcean Space at {cfg["img_dir"]}/  (Space root, no assets/ prefix)')
    print(f'      (served from {config.ASSET_BASE}{cfg["img_dir"]}/<n>.jpg; manifest row carries this base)')
    print(f'2. data/{cfg["key"]}.txt  -> already in repo data/ (build.ps1 copies it).')
    if cfg['movies']:
        print('   data/movies_map.json -> already in repo data/ (ensure .gitignore allows it).')
    print('3. manifest.json row -> done (above).')
    if cfg['movies']:
        print('4. js/app.js movies-title change -> one-time; see plan component 12.')
    print(f'{5 if cfg["movies"] else 4}. .\\build.ps1  ->  drag dist/ contents into FileZilla.')


if __name__ == '__main__':
    main()
