"""Compact perceptual regression fingerprints, not a substitute for source values."""
import base64
import zlib

import numpy as np
from PIL import Image


def signature(im):
    # Area averaging retains ink and color while tolerating subpixel AA differences.
    tile = im.resize((48, 32), Image.Resampling.BOX)
    return [round(im.width / im.height, 6), base64.b64encode(zlib.compress(tile.tobytes(), 9)).decode("ascii")]


def signature_delta(a, b):
    def decode(item):
        return np.frombuffer(zlib.decompress(base64.b64decode(item[1])), dtype=np.uint8).astype(np.int16).reshape(-1, 3)
    error = np.abs(decode(a) - decode(b))
    return {"mae": round(float(error.mean() / 255), 6),
            "changed_tiles": round(float((error.max(axis=1) > 24).mean()), 6),
            "aspect": round(abs(b[0] / a[0] - 1), 6)}
