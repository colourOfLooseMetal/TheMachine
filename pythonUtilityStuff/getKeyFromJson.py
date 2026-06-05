import os
import json
import re

# Show table: (source json under ./showMapData, asset dir key, image folder name, display name).
# ORDER MATTERS — it determines the global-index ordering the engine uses, which must
# match the image folders on the server. Add new shows by appending a row here.
SHOWS = [
    ('sm.json',    'sm',       'sm',           'Sailor Moon'),
    ('cw.json',    'cw2003',   'cw2003',       'Clone Wars 2003'),
    ('sw.json',    'swPrequel','swPrequel',     'Star Wars Prequels'),
    ('rc.json',    'recess',   'recess',        'Recess'),
    ('dispix.json','DisPix',   'DisPix',        'Disney Pixar'),
    ('jb.json',    'JohnnyBravo','JohnnyBravo', 'Johnny Bravo'),
    ('gib.json',   'ghibli',   'ghibli',        'Ghibli'),
    ('lt.json',    'looneyTunes','looneyTunes', 'Looney Tunes'),
    ('db.json',    'db',       'db',            'Dragon Ball'),
    ('dbz.json',   'dbz',      'dbz',           'Dragon Ball Z'),
    ('dbzm.json',  'dbzMov',   'dbzMov',        'Dragon Ball Z Movies'),
    ('jojo.json',  'jojo',     'jojo',          'JoJo\'s Bizarre Adventure'),
]

SHOW_MAP_DIR = './showMapData'
OUT_DIR      = '../data'   # relative to this script: repo-root/data/

def remove_non_ascii(text):
    return re.sub(r'[^\x00-\x7F]', ' ', text)

def clean_line(raw):
    line = remove_non_ascii(raw).lower().replace('\n', ' ')
    line = re.sub(r'\s*\{.*?\}\s*', ' ', line)
    line = re.sub(r'\s+', ' ', line)
    line = line.replace('</b>', ' ').replace('<b>', ' ')
    line = line.replace('</i>', ' ').replace('<i>', ' ')
    line = line.replace('\\"', '"')
    return remove_non_ascii(line)

os.makedirs(OUT_DIR, exist_ok=True)

manifest = []
cumulative = 0

for src_file, key, img_dir, display_name in SHOWS:
    path = os.path.join(SHOW_MAP_DIR, src_file)
    with open(path, encoding='utf-8') as f:
        data = json.load(f)

    lines = [clean_line(entry['text']) for entry in data]

    # Write one line per caption, trailing '\n' so the last line is null-terminated
    # by commitShow in wams.cpp (which replaces '\n' with '\0' in-place).
    out_path = os.path.join(OUT_DIR, key + '.txt')
    content = '\n'.join(lines) + '\n'
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

    byte_size = os.path.getsize(out_path)

    manifest.append({
        'key':   key,
        'dir':   img_dir,
        'name':  display_name,
        'lines': len(lines),
        'bytes': byte_size,
        'file':  'data/' + key + '.txt',
    })

    print(f'{display_name:30s}  lines={len(lines):6d}  offset={cumulative:7d}  bytes={byte_size:8d}  -> {out_path}')
    cumulative += len(lines)

print(f'\nTotal lines: {cumulative}')

manifest_path = os.path.join(OUT_DIR, '..', 'manifest.json')
with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)
print(f'Written: {manifest_path}')
