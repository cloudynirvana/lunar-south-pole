"""Read NASA's LOLA south-polar elevation map and work out where each pixel is.

The map is LDEM_85S_40M: a 7584 x 7584 grid of 16-bit heights, 40 m per pixel,
covering 85 to 90 degrees south in a polar stereographic projection centred on
the south pole. Heights are metres relative to a 1737.4 km sphere.

Download (115 MB) with ./fetch_data.sh.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

R_MOON = 1_737_400.0  # m, the reference sphere the heights are measured from
DATA = Path(__file__).parent / "data"
IMG, SIZE, SCALE, CENTRE = DATA / "ldem_85s_40m.img", 7584, 40.0, 3791.5


def load(downsample: int = 1) -> tuple[np.ndarray, float]:
    """Heights in metres, and the metres-per-pixel of what is returned.

    downsample=6 averages 6x6 blocks, giving a 240 m grid. Averaging rather
    than sampling keeps the blocky ridgelines from aliasing into false horizons.
    """
    h = np.memmap(IMG, dtype="<i2", mode="r").reshape(SIZE, SIZE).astype(np.float32) * 0.5
    if downsample > 1:
        n = (SIZE // downsample) * downsample
        h = h[:n, :n].reshape(n // downsample, downsample, n // downsample, downsample).mean((1, 3))
    return np.ascontiguousarray(h), SCALE * downsample


def grid(n: int, res: float) -> tuple[np.ndarray, np.ndarray]:
    """Latitude and east longitude (degrees) of every pixel of an n x n map.

    Polar stereographic, south pole at the centre, 0 degrees longitude pointing
    along +y (up the image), longitude increasing east. The convention matters
    only for naming a place and for where Earth sits; sunlight sweeps every
    azimuth each month, so illumination does not depend on it.
    """
    half = (n - 1) / 2
    x = (np.arange(n) - half) * res  # +x is to the right
    y = (half - np.arange(n)) * res  # +y is up the image
    xx, yy = np.meshgrid(x, y)
    r = np.hypot(xx, yy)
    colat = 2 * np.arctan(r / (2 * R_MOON))  # inverse polar stereographic
    return np.degrees(colat) - 90, np.degrees(np.arctan2(xx, yy)) % 360


def slope_deg(h: np.ndarray, res: float) -> np.ndarray:
    """Steepest slope at each pixel, in degrees, from the local gradient."""
    gy, gx = np.gradient(h, res)
    return np.degrees(np.arctan(np.hypot(gx, gy)))
