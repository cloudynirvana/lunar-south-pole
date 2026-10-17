"""Rank places to put a base at the lunar south pole, from NASA's LOLA map.

A good site needs three things at once, and they pull against each other:

  sunlight  - near-constant sun means solar power and no two-week freeze
  ice       - a permanently shadowed crater floor nearby, within driving range
  ground    - flat enough to land on and build on
  Earth     - a line of sight home, or you need a relay satellite

This script computes all four over the 300 km square around the pole, then
picks the pixels that do best on all of them.

    ./fetch_data.sh && python3 run.py

Writes results/sites.csv and three charts. Takes about ten minutes.

How much of this answer is really about the Moon and how much is about the
settings at the top of this file is a fair question, and `validate.py` answers
it by turning each one on its own: see results/validation.md. The short version
is that the terrain resolution matters more than everything else together, and
it biases every sunlit area here upwards, so read them as upper bounds.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import ndimage

import illumination as il
import lola

RES_M = 240.0  # the 40 m map averaged 6x6, the grid the published maps use too
DOWNSAMPLE = 6
AZIMUTHS = 60  # compass directions the horizon is traced in
HORIZON_KM = 150.0  # how far away terrain can still block the Sun; the map's limit
STUDY_KM = 120.0  # how far from the pole to report; the map itself stops at 151 km
MAX_SLOPE = 10.0  # degrees; steeper than a lander should touch down on
DRIVE_KM = 20.0  # how far a rover might reasonably go for ice
OUT = Path(__file__).parent / "results"


def relief_m(h, res, radius_km=20.0):
    """How far each patch stands above the average height around it.

    The reason the good sites are where they are: sunlight this close to the
    pole goes to whatever is standing highest, because the Sun never climbs far
    enough to clear the local terrain. This measures that directly.
    """
    return h - ndimage.uniform_filter(h, size=int(radius_km * 1000 / res))


def ranked_sites(lit, earth, slope, ice_km, relief, lat, lon, n=12, apart_km=5.0):
    """The best-scoring pixels, thinned so two sites are never neighbours."""
    ok = (slope < MAX_SLOPE) & (lit > 0.5) & (ice_km < DRIVE_KM) & np.isfinite(lit)
    score = np.where(ok, np.nan_to_num(lit) * (1 - ice_km / DRIVE_KM / 4) * (0.8 + 0.2 * np.nan_to_num(earth)), 0)
    apart = int(apart_km * 1000 / RES_M)
    peaks = score == ndimage.maximum_filter(score, 2 * apart + 1)
    rows, cols = np.nonzero(peaks & ok)
    order = np.argsort(score[rows, cols])[::-1][:n]
    rows, cols = rows[order], cols[order]
    return pd.DataFrame({
        "latitude": lat[rows, cols].round(3),
        "east_longitude": lon[rows, cols].round(2),
        "sunlit_fraction": lit[rows, cols].round(3),
        "earth_in_view_fraction": earth[rows, cols].round(3),
        "slope_deg": slope[rows, cols].round(1),
        "km_to_permanent_shadow": ice_km[rows, cols].round(1),
        "metres_above_surroundings": relief[rows, cols].round(0),
        "score": score[rows, cols].round(3),
    })


def map_chart(field, title, label, path, sites=None, cmap="magma", vmax=None):
    fig, ax = plt.subplots(figsize=(7.4, 7))
    n = field.shape[0]
    extent = [-n * RES_M / 2000, n * RES_M / 2000] * 2  # km from the pole
    im = ax.imshow(field, cmap=cmap, extent=extent, vmin=0, vmax=vmax, origin="upper")
    ax.plot(0, 0, "+", color="#00e5ff", ms=12, mew=2)
    ax.annotate("south pole", (0, 0), (9, 9), textcoords="offset points",
                color="#00e5ff", fontsize=8)
    if sites is not None:
        for i, s in enumerate(sites.itertuples(), 1):
            colat = np.radians(90 + s.latitude)
            r = 2 * lola.R_MOON * np.tan(colat / 2) / 1000
            x, y = r * np.sin(np.radians(s.east_longitude)), r * np.cos(np.radians(s.east_longitude))
            ax.plot(x, y, "o", mfc="none", mec="#7CFC00", ms=9, mew=1.6)
            ax.annotate(str(i), (x, y), (7, -3), textcoords="offset points",
                        color="#7CFC00", fontsize=9, weight="bold")
    ax.set_xlabel("km from the pole (towards 90 east)")
    ax.set_ylabel("km from the pole (towards 0 longitude)")
    ax.set_title(title, fontsize=11)
    fig.colorbar(im, ax=ax, shrink=0.8, label=label)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    print("reading the LOLA map...", flush=True)
    h, res = lola.load(DOWNSAMPLE)
    assert res == RES_M
    lat, lon = lola.grid(len(h), res)

    print(f"horizons in {AZIMUTHS} directions out to {HORIZON_KM:.0f} km...", flush=True)
    hor = il.horizon(h, res, n_azimuth=AZIMUTHS, max_km=HORIZON_KM)

    print(f"sunlight over {il.NODAL_CYCLE / 365.25:.1f} years...", flush=True)
    lit = il.lit_fraction(hor, lat, lon)
    earth = il.earth_fraction(hor, lat, lon)
    del hor

    slope = lola.slope_deg(h, res)
    relief = relief_m(h, res)
    shadow = lit == 0
    ice_km = ndimage.distance_transform_edt(~shadow, sampling=res) / 1000

    # Report only within STUDY_KM of the pole: further out, a site's horizon
    # would depend on terrain beyond the edge of the map, which we do not have.
    edge = int((len(h) * RES_M / 2 - STUDY_KM * 1000) / RES_M)
    crop = (slice(edge, -edge), slice(edge, -edge))
    lit, earth, slope, shadow, ice_km, relief = (a[crop] for a in (lit, earth, slope, shadow, ice_km, relief))
    lat_c, lon_c, h_c = lat[crop], lon[crop], h[crop]
    inside = np.hypot(*np.meshgrid(*[(np.arange(len(h_c)) - (len(h_c) - 1) / 2) * RES_M] * 2)) <= STUDY_KM * 1000
    lit, earth, slope = (np.where(inside, a, np.nan) for a in (lit, earth, slope))
    shadow &= inside

    sites = ranked_sites(lit, earth, slope, ice_km, relief, lat_c, lon_c)
    sites.index = np.arange(1, len(sites) + 1)
    sites.to_csv(OUT / "sites.csv", index_label="rank")
    np.save(OUT / "lit_fraction.npy", lit)

    area = (RES_M / 1000) ** 2
    print(f"\nmapped {inside.sum() * area:,.0f} km2 within {STUDY_KM:.0f} km of the pole")
    print(f"permanently shadowed: {shadow.sum() * area:,.0f} km2 "
          f"({100 * shadow.sum() / inside.sum():.1f}% of it)")
    for cut in (0.7, 0.8, 0.9):
        print(f"lit more than {cut:.0%} of the time: {np.nansum(lit > cut) * area:,.1f} km2")
    print(f"best single patch: {np.nanmax(lit) * 100:.1f}% of the time in sunlight")
    r = sites.metres_above_surroundings
    print(f"every one of the top {len(sites)} stands {r.min():,.0f} to {r.max():,.0f} m "
          f"above the mean height within 20 km of it")
    from_pole = 2 * lola.R_MOON * np.tan(np.radians(90 + sites.latitude) / 2) / 1000
    print(f"{(from_pole <= 25).sum()} of them are within 25 km of the pole "
          f"(they range {from_pole.min():.0f} to {from_pole.max():.0f} km out)")
    print(f"\n{sites.to_string()}")

    map_chart(lit, "Sunlight at the lunar south pole (LOLA terrain, an 18.6-year cycle)",
              "fraction of the time in sunlight", OUT / "sunlight.png", sites, vmax=1)
    map_chart(np.where(shadow, 1.0, np.nan), "Permanently shadowed ground: where ice can survive",
              "never sunlit", OUT / "permanent_shadow.png", sites, cmap="Blues", vmax=1)
    map_chart(h_c / 1000, "Terrain", "km above a 1737.4 km sphere",
              OUT / "terrain.png", sites, cmap="cividis", vmax=None)
    print(f"\ncharts and sites.csv written to {OUT}")
