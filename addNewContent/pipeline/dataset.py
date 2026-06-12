"""Write the pipeline output: numbered screenshots + data/<key>.txt + (for
movies) data/movies_map.json, plus a manifest.json row helper.

Output contract (must match the existing 12 shows exactly):
  * out/<dir>/<n>.jpg          — 0-based, one image per caption cue, in order.
  * data/<key>.txt             — one clean_caption() per line, trailing '\n'
                                 (byte-identical to getKeyFromJson's output).
  * data/movies_map.json       — [{title,start,lines}, ...] ascending by start
                                 (movies only; gives per-film attribution).
  * manifest row               — {key,dir,name,lines,bytes,file:"data/<key>.txt"}.

Image numbering is GLOBAL across the whole set and continues on --append
(movies), so films added later keep incrementing the count + the map.
"""

import json
import os

import cv2

from . import config


class DatasetWriter:
    def __init__(self, key, img_dir, repo_root, out_root, movies=False, append=False):
        self.key = key
        self.img_dir = img_dir
        self.movies = movies
        self.repo_root = repo_root

        self.out_dir = os.path.join(out_root, img_dir)
        self.txt_path = os.path.join(repo_root, 'data', key + '.txt')
        self.map_path = os.path.join(repo_root, 'data', 'movies_map.json')
        os.makedirs(self.out_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.txt_path), exist_ok=True)

        self.films = []  # [{title,start,lines}] for movies
        if append:
            # Numbering resumes from the corpus line count (the source of truth for
            # global image numbers). out/ is gitignored and easily cleared between
            # sessions, so warn loudly if the images on disk don't match — otherwise
            # we'd keep numbering from N while images 0..N-1 are silently absent.
            self.count = self._existing_line_count()
            self._warn_if_images_missing()
            if movies and os.path.exists(self.map_path):
                with open(self.map_path, encoding='utf-8') as f:
                    self.films = json.load(f)
            mode = 'a'
        else:
            self.count = 0
            mode = 'w'

        # newline='\n' so we never emit CRLF on Windows (matches getKeyFromJson).
        self._txt = open(self.txt_path, mode, encoding='utf-8', newline='\n')

    def _existing_line_count(self):
        if not os.path.exists(self.txt_path):
            return 0
        with open(self.txt_path, encoding='utf-8') as f:
            return sum(1 for _ in f)

    def _warn_if_images_missing(self):
        """On --append, sanity-check that out/<dir>/ holds the 0..count-1 images the
        corpus expects. A mismatch means out/ was cleared/partial — the new run will
        keep numbering from `count` and NOT regenerate the earlier images, so the
        upload would have gaps. Warn rather than silently produce a broken set."""
        if self.count == 0:
            return
        on_disk = sum(1 for f in os.listdir(self.out_dir)
                      if f.endswith('.jpg')) if os.path.isdir(self.out_dir) else 0
        if on_disk != self.count:
            print(f'   !! WARNING: appending from corpus line {self.count}, but '
                  f'{self.out_dir} has {on_disk} image(s).')
            print(f'      Images 0..{self.count - 1} will NOT be regenerated this run; '
                  f'the uploaded set may have gaps.')
            print(f'      If out/ was cleared, rebuild from scratch (drop --append) '
                  f'so all images are produced.')

    @property
    def next_index(self):
        return self.count

    def start_film(self, title):
        """Movies only: begin a new film's run of images at the current count."""
        self.films.append({'title': title, 'start': self.count, 'lines': 0})

    def write_frame(self, frame_bgr, corpus_caption):
        """Save the burned frame as <count>.jpg and append its cleaned caption.
        Returns the image number used."""
        n = self.count
        path = os.path.join(self.out_dir, f'{n}.jpg')
        ok = cv2.imwrite(path, frame_bgr,
                         [int(cv2.IMWRITE_JPEG_QUALITY), config.JPEG_QUALITY])
        if not ok:
            raise RuntimeError(f'cv2.imwrite failed: {path}')
        self._txt.write(corpus_caption + '\n')
        if self.movies and self.films:
            self.films[-1]['lines'] += 1
        self.count = n + 1
        return n

    def close(self):
        self._txt.close()
        if self.movies:
            self.films.sort(key=lambda f: f['start'])
            with open(self.map_path, 'w', encoding='utf-8', newline='\n') as f:
                json.dump(self.films, f, indent=2, ensure_ascii=False)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # -- manifest row ---------------------------------------------------------
    def manifest_row(self, display_name):
        """Build the manifest.json row for this set (call after close())."""
        return {
            'key':   self.key,
            'dir':   self.img_dir,
            'name':  display_name,
            'lines': self.count,
            'bytes': os.path.getsize(self.txt_path),
            'file':  'data/' + self.key + '.txt',
        }
