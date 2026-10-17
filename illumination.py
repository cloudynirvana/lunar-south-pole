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
            n_steps: int = 60, window: tuple[slice, slice] | None = None) -> np.ndarray:
    """Highest terrain elevation angle per pixel per compass direction.

    Returns (n_azimuth, rows, cols); bin i is the direction i * 360/n_azimuth
    degrees clockwise from +y.

    Distances are log-spaced: a close ridge needs fine steps, a far massif does
    not. A ray that runs off the edge of the map is clamped to the last pixel
    it had, so the edge is treated as flat continuation rather than wrapping
    round to terrain on the opposite side of the pole. Horizons within max_km
    of the edge are therefore only as good as the map is wide.

    `window` restricts the pixels we compute horizons *for*, while still
    ray-tracing into the whole of `h`. That is what makes a fine-resolution
    convergence check affordable: the full map at 120 m would need gigabytes of
    horizon array, but a 30 km box out of it costs almost nothing.
    """
    max_px = int(max_km * 1000 / res)
    steps = np.unique(np.round(np.geomspace(1, max_px, n_steps)).astype(int))
    rs, cs = window if window is not None else (slice(None), slice(None))
    rows = np.arange(h.shape[0])[rs]
    cols = np.arange(h.shape[1])[cs]
    here = h[rs, cs]
    out = np.full((n_azimuth, *here.shape), -np.pi / 2, np.float32)
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
            np.maximum(best, np.arctan((far - here - drop) / dist), out=best)
    return out


NODAL_CYCLE = 6793.48  # days; the 18.6-year wobble of the Moon's orbit plane


def sun_track(days: float = NODAL_CYCLE, step_hours: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Solar elevation as seen from the pole itself, and solar azimuth, over time.

    The Sun's declination swings +/-1.54 degrees over a year while its azimuth
    goes right round the sky every synodic month. At the south pole the Sun is
    above the horizon exactly when its declination is southern.

    The default run is 18.6 years, not one, and that is not thoroughness for
    its own sake. A year holds only 12.37 synodic months, so each compass
    direction is visited about twelve times, and the Sun's declination takes
    only about two dozen distinct values while it is in any one direction. A
    lit fraction built from that is quantised in steps of several per cent.
    Over the 18.6-year nodal cycle each direction is visited 230 times, the
    declination fills in, and it is the window the published illumination maps
    use, which makes the comparison a fair one.
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


def disc_levels(n: int = 7) -> np.ndarray:
    """Heights that split the Sun's disc into `n` equal-area horizontal slices.

    The Sun is half a degree across, which is not nothing when it never rises
    more than three. Treating it as a point counts every partially lit pixel as
    dark, and near the pole almost every lit pixel spends a long time partly
    lit, so the error is one-sided and large.

    The fix is quadrature. The fraction of the disc above a horizon `d` radians
    below its centre is P(d > s*v) for a point v drawn uniformly over the disc,
    so averaging the indicator over the equal-probability quantiles of v gives
    that fraction, and each quantile costs one more sorted search. Returned in
    units of the solar radius; heights are symmetric about zero, and n = 1
    gives back the old point-Sun model exactly.
    """
    # CDF of a point's height over a unit disc: F(v) = 1 - (acos v - v*sqrt(1-v^2))/pi
    q = (np.arange(n) + 0.5) / n
    v = np.linspace(-1, 1, 200001)
    cdf = 1 - (np.arccos(v) - v * np.sqrt(np.maximum(1 - v * v, 0))) / np.pi
    return np.interp(q, cdf, v)


def lit_fraction(hor: np.ndarray, lat: np.ndarray, lon: np.ndarray,
                 step_hours: float = 1.0, disc: int = 7,
                 days: float = NODAL_CYCLE) -> np.ndarray:
    """Mean fraction of the Sun's disc visible from each pixel over `days`.

    This is the quantity that matters for a solar array: the share of full
    sunlight it would collect, averaged over the year. `disc=1` reduces to the
    older, harsher definition, the fraction of the time the Sun's *centre*
    clears the horizon. Lengthening `days` costs almost nothing: the work is
    one sorted search per pixel per direction per disc slice, and more time
    samples only make the sorted array longer.
    """
    n_az = hor.shape[0]
    elev, az = sun_track(days=days, step_hours=step_hours)
    bins = np.round(az / (2 * np.pi) * n_az).astype(int) % n_az
    levels = disc_levels(disc) * np.radians(SOLAR_RADIUS_DEG)
    total = np.zeros(hor.shape[1:], np.float32)
    for i in range(n_az):
        here = np.sort(elev[bins == i])
        if not len(here):
            continue
        # Lit when the Sun's elevation at the pole clears the horizon less the
        # tilt of this pixel's own horizontal plane. Count with one search per
        # slice of the disc, then average the slices.
        need = hor[i] - local_offset(lat, lon, 2 * np.pi * i / n_az)
        for v in levels:
            edge = (need + v).ravel()
            total += (len(here) - np.searchsorted(here, edge, "right").reshape(need.shape)) / len(levels)
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
