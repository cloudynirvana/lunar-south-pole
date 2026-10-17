"""Export the frames and numbers the film puts on screen, from the real results.

Reads results/lit_fraction.npy (written by run.py) and the LOLA map, and writes
public/*.png and public/data.json. Every figure in the video comes from here,
so nothing on screen is typed by hand.

    python3 export_data.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import lola  # noqa: E402

OUT = Path(__file__).parent / "public"
RES_M = 240.0
STUDY_KM = 120.0


def save(field, cmap, path, vmin=0.0, vmax=1.0):
    """Write a square RGBA image of a field, transparent where it is nan."""
    norm = np.clip((field - vmin) / (vmax - vmin), 0, 1)
    rgba = (mpl.colormaps[cmap](np.nan_to_num(norm)) * 255).astype(np.uint8)
    rgba[..., 3] = np.where(np.isnan(field), 0, 255)
    Image.fromarray(rgba).save(path)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lit = np.load(ROOT / "results" / "lit_fraction.npy")
    n = len(lit)
    area = (RES_M / 1000) ** 2
    inside = np.isfinite(lit)
    shadow = inside & (lit == 0)

    save(lit, "magma", OUT / "sunlight.png")
    save(np.where(shadow, 1.0, np.nan), "Blues", OUT / "shadow.png", 0, 1.4)

    h, res = lola.load(6)
    edge = (len(h) - n) // 2
    hc = h[edge:edge + n, edge:edge + n] / 1000
    save(np.where(inside, hc, np.nan), "cividis", OUT / "terrain.png",
         float(np.nanmin(hc[inside])), float(np.nanmax(hc[inside])))

    sites = pd.read_csv(ROOT / "results" / "sites.csv")
    # polar stereographic position of each site, in km from the pole, the same
    # projection the map images are in
    colat = np.radians(90 + sites.latitude)
    r = 2 * lola.R_MOON * np.tan(colat / 2) / 1000
    sites["x_km"] = (r * np.sin(np.radians(sites.east_longitude))).round(2)
    sites["y_km"] = (r * np.cos(np.radians(sites.east_longitude))).round(2)

    data = {
        "study_km": STUDY_KM,
        "image_half_km": n * RES_M / 2000,
        "mapped_km2": round(float(inside.sum() * area)),
        "shadow_km2": round(float(shadow.sum() * area)),
        "shadow_pct": round(100 * float(shadow.sum()) / float(inside.sum()), 1),
        "best_lit_pct": round(float(np.nanmax(lit)) * 100, 1),
        "lit_area": [{"over_pct": int(c * 100),
                      "km2": round(float(np.nansum(lit > c) * area), 1)}
                     for c in (0.5, 0.6, 0.7, 0.8, 0.9)],
        "shadow_to_sun_ratio": round(float(shadow.sum()) / max(float(np.nansum(lit > 0.7)), 1)),
        "earth_min_pct": round(float(sites.earth_in_view_fraction.min()) * 100),
        "earth_max_pct": round(float(sites.earth_in_view_fraction.max()) * 100),
        "sites": [
            {"rank": int(s.rank), "lat": float(s.latitude), "lon": float(s.east_longitude),
             "lit": round(float(s.sunlit_fraction_of_year) * 100),
             "earth": round(float(s.earth_in_view_fraction) * 100),
             "slope": float(s.slope_deg), "ice_km": float(s.km_to_permanent_shadow),
             "relief_m": int(s.metres_above_surroundings),
             "from_pole_km": round(float(rk), 1),
             "x_km": float(s.x_km), "y_km": float(s.y_km)}
            for s, rk in zip(sites.itertuples(), r)
        ],
        "relief_min_m": int(sites.metres_above_surroundings.min()),
        "relief_max_m": int(sites.metres_above_surroundings.max()),
        "near_pole_km": 25,
        "near_pole_count": int((r <= 25).sum()),
        # how much of the mapped ground is lit, as a curve
        "curve": [{"pct": int(c), "km2": round(float(np.nansum(lit > c / 100) * area), 1)}
                  for c in range(0, 100, 5)],
    }
    (OUT / "data.json").write_text(json.dumps(data, indent=1))
    print(f"{data['mapped_km2']:,} km2 mapped, {data['shadow_km2']:,} km2 shadowed, "
          f"best patch {data['best_lit_pct']}% -> {OUT}")


if __name__ == "__main__":
    main()
