"""How much sunlight each patch of the lunar south pole gets, and for how long.

Near the pole the Sun never climbs more than about 1.5 degrees above the
horizon, so what matters is not the time of day but what the terrain does: a
ridge 50 km away that stands 2 km tall can put a crater floor in shadow
forever. So the calculation comes in two halves.

1. The horizon. For every pixel and every compass direction, the highest
   elevation angle the terrain reaches. The Moon's curvature is included: at
   100 km the surface has already dropped 2.9 km below the local horizontal,
   which is more than most of the relief here.
2. The Sun. Its elevation through a full year, sampled finely enough to catch
   every circuit of its azimuth around the sky. A pixel is lit whenever the
   Sun stands higher than its horizon in the direction the Sun is in.

A place that is never lit is a permanently shadowed region, and those are
where water ice can survive. A place that is nearly always lit can run on
solar power without hauling a huge battery. The useful landing sites are the
ones next to both.

Angles are radians inside this module. Azimuth is measured clockwise from the
map's +y axis, which is the zero-longitude meridian, so a body sitting over
longitude L is seen in map azimuth L from anywhere near the pole.
"""
from __future__ import annotations

import numpy as np

from lola import R_MOON

SYNODIC_DAY = 29.530588  # days for the Sun to go once round the lunar sky
YEAR = 365.25
SOLAR_INCLINATION = 1.54  # degrees; the Moon's spin axis tilt to the ecliptic
SOLAR_RADIUS_DEG = 0.26  # the Sun is a disc, not a point


def horizon(h: np.ndarray, res: float, n_azimuth: int = 60, max_km: float = 100.0,
            n_steps: int = 60) -> np.ndarray:
    """Highest terrain elevation angle per pixel per compass direction.

    Returns (n_azimuth, rows, cols); bin i is the direction i * 360/n_azimuth
    degrees clockwise from +y.

    Distances are log-spaced: a close ridge needs fine steps, a far massif does
    not. A ray that runs off the edge of the map is clamped to the last pixel
    it had, so the edge is treated as flat continuation rather than wrapping
    round to terrain on the opposite side of the pole. Horizons within max_km
    of the edge are therefore only as good as the map is wide.
    """
    max_px = int(max_km * 1000 / res)
    steps = np.unique(np.round(np.geomspace(1, max_px, n_steps)).astype(int))
    rows, cols = np.arange(h.shape[0]), np.arange(h.shape[1])
    out = np.full((n_azimuth, *h.shape), -np.pi / 2, np.float32)
    for i in range(n_azimuth):
        az = 2 * np.pi * i / n_azimuth
        best = out[i]
        for d in steps:
            dx, dy = int(round(d * np.sin(az))), int(round(d * np.cos(az)))
            if dx == 0 and dy == 0:
                continue
            dist = np.hypot(dx, dy) * res
            # terrain dx pixels right and dy pixels up (rows run down the image)
            far = h[np.clip(rows - dy, 0, h.shape[0] - 1)][:, np.clip(cols + dx, 0, h.shape[1] - 1)]
            drop = dist * dist / (2 * R_MOON)  # the Moon curving away underneath
            np.maximum(best, np.arctan((far - h - drop) / dist), out=best)
    return out


def sun_track(days: float = YEAR, step_hours: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Solar elevation as seen from the pole itself, and solar azimuth, over time.

    The Sun's declination swings +/-1.54 degrees over a year while its azimuth
    goes right round the sky every synodic month. At the south pole the Sun is
    above the horizon exactly when its declination is southern.
    """
    t = np.arange(0, days, step_hours / 24)
    dec = np.radians(SOLAR_INCLINATION) * np.sin(2 * np.pi * t / YEAR)
    return -dec, (2 * np.pi * t / SYNODIC_DAY) % (2 * np.pi)


def local_offset(lat: np.ndarray, lon: np.ndarray, azimuth: float) -> np.ndarray:
    """How much higher a body in `azimuth` looks from a pixel than from the pole.

    A patch 100 km from the pole on the side facing the body sees it 3.3
    degrees higher, because its own horizontal plane is tilted by that much.
    """
    return np.radians(90 + lat) * np.cos(azimuth - np.radians(lon))


def lit_fraction(hor: np.ndarray, lat: np.ndarray, lon: np.ndarray,
                 step_hours: float = 1.0) -> np.ndarray:
    """Fraction of a year each pixel sees the centre of the Sun above its horizon."""
    n_az = hor.shape[0]
    elev, az = sun_track(step_hours=step_hours)
    bins = np.round(az / (2 * np.pi) * n_az).astype(int) % n_az
    total = np.zeros(hor.shape[1:], np.float32)
    for i in range(n_az):
        here = np.sort(elev[bins == i])
        if not len(here):
            continue
        # Lit when the Sun's elevation at the pole clears the horizon less the
        # tilt of this pixel's own horizontal plane. Count with one search.
        need = hor[i] - local_offset(lat, lon, 2 * np.pi * i / n_az)
        total += len(here) - np.searchsorted(here, need.ravel(), "right").reshape(need.shape)
    return total / len(elev)


def earth_fraction(hor: np.ndarray, lat: np.ndarray, lon: np.ndarray,
                   n_libration: int = 36) -> np.ndarray:
    """Fraction of the time Earth is above the horizon: can the site talk home?

    Earth hangs almost still in the lunar sky, wobbling about +/-7 degrees as
    the Moon librates. Near the south pole it sits close to the horizon, so a
    ridge in the way is the difference between a direct link and none.
    """
    n_az = hor.shape[0]
    phase = np.linspace(0, 2 * np.pi, n_libration, endpoint=False)
    total = np.zeros(hor.shape[1:], np.float32)
    for sub_lat, sub_lon in zip(6.7 * np.sin(phase), 8.2 * np.cos(phase)):
        az = np.radians(sub_lon) % (2 * np.pi)
        elev = local_offset(lat, lon, az) - np.radians(sub_lat)
        total += elev > hor[int(round(az / (2 * np.pi) * n_az)) % n_az]
    return total / n_libration
