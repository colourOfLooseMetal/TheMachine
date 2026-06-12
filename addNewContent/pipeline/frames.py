"""Frame grabbing + sharpness selection + downscale-to-box.

The old createMapFromVideo grabbed exactly one frame at 60% of the cue window
and DEFINED detect_blur but never called it. Here the blur check actually runs:
we try the 60% frame first, and if it's blurry (hard cut / motion blur) we try
the alternates and keep the sharpest. Then downscale to fit the 960x540 box,
preserving aspect, shrink-only.
"""

import cv2

from . import config
from .subtitles import frame_time_ms


def detect_blur(image_bgr):
    """Variance of the Laplacian: higher = sharper. Ported from
    createMapFromVideo's detect_blur (the Laplacian one that was never wired in)."""
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def downscale_to_box(image_bgr, box_w=config.BOX_W, box_h=config.BOX_H):
    """Fit within box_w x box_h, preserving aspect ratio, shrinking only
    (never upscale small sources). INTER_AREA is best for downscaling."""
    h, w = image_bgr.shape[:2]
    scale = min(box_w / w, box_h / h, 1.0)
    if scale >= 1.0:
        return image_bgr
    new_w = max(1, round(w * scale))
    new_h = max(1, round(h * scale))
    return cv2.resize(image_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)


class FrameGrabber:
    """Wraps one cv2.VideoCapture so the whole video is opened once and seeked
    per cue (matches the old per-video loop). Use as a context manager."""

    def __init__(self, video_path):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise RuntimeError(f'cannot open video: {video_path}')

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.release()

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def _read_at(self, ms):
        self.cap.set(cv2.CAP_PROP_POS_MSEC, ms)
        ok, frame = self.cap.read()
        return frame if ok and frame is not None else None

    def grab_best_frame(self, sub):
        """Grab the sharpest non-blurry frame within this cue's display window.
        Tries PRIMARY_FRAME_FRAC first; only falls back to the alternates if it
        is below BLUR_THRESHOLD. Returns a downscaled BGR frame, or None if no
        frame could be read at all."""
        fracs = (config.PRIMARY_FRAME_FRAC,) + config.ALT_FRAME_FRACS
        best_frame, best_score = None, -1.0
        for frac in fracs:
            frame = self._read_at(frame_time_ms(sub, frac))
            if frame is None:
                continue
            score = detect_blur(frame)
            if score > best_score:
                best_frame, best_score = frame, score
            # The primary frame is good enough on its own if it clears the bar.
            if frac == config.PRIMARY_FRAME_FRAC and score >= config.BLUR_THRESHOLD:
                break
        if best_frame is None:
            return None
        return downscale_to_box(best_frame)
