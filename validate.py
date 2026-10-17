"""Does the answer depend on the choices we made? And does it match published work?

Every number in RESULTS.md comes out of a model with six knobs in it: how
coarsely the terrain is averaged, how many compass directions the horizon is
traced in, how far out it is traced, how long a stretch of the Sun's motion is
sampled, how finely, and how many slices the Sun's disc is cut into. A result
that moves when you turn a knob is a result about the knob, not about the Moon.

So this script turns each knob on its own, holding the rest at the settings
run.py uses, and prints what the headline numbers do. Then it puts them beside
three published figures for the same ground.

    python3 validate.py            # about half an hour, writes results/validation.md

Three of the six turn out not to matter at all, two matter a little, and one -
the resolution of the terrain - matters more than everything else put together.
That last one is the honest headline of this project.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import illumination as il
import lola
from run import AZIMUTHS, DOWNSAMPLE, HORIZON_KM, RES_M, STUDY_KM

OUT = Path(__file__).parent / "results"
AREA = (RES_M / 1000) ** 2  # km2 per pixel at the baseline resolution
BOX_KM = 20.0  # half-width of the box used for the resolution ladder
SITE_RADIUS_M = 400.0  # how near a pixel has to be to count as "at" a site
report: list[str] = []
knobs: dict[str, list] = {}  # the same tables as data, for the film to read
t0 = time.time()


def say(line: str = "") -> None:
    print(line, flush=True)
    report.append(line)


def tick(what: str) -> None:
    print(f"  [{time.time() - t0:5.0f} s] {what}", flush=True)


def headline(lit: np.ndarray, area: float = AREA) -> dict[str, float]:
    """The numbers the write-up quotes, from a lit-fraction map with nan outside."""
    return {
        "shadow": float((lit == 0).sum() * area),
        "over_50": float(np.nansum(lit > 0.5) * area),
        "over_70": float(np.nansum(lit > 0.7) * area),
        "over_80": float(np.nansum(lit > 0.8) * area),
        "over_90": float(np.nansum(lit > 0.9) * area),
        "best": float(np.nanmax(lit) * 100),
        "mean": float(np.nanmean(lit) * 100),
    }


def table(rows: list[tuple[str, dict]], knob: str) -> None:
    knobs[knob] = [{"setting": name, **{k: round(v, 3) for k, v in vals.items()}}
                   for name, vals in rows]
    say(f"| {knob} | never lit (km²) | >50% (km²) | >70% (km²) | >80% (km²) | best patch | mean |")
    say("|---|---|---|---|---|---|---|")
    for name, v in rows:
        say(f"| {name} | {v['shadow']:,.0f} | {v['over_50']:,.0f} | {v['over_70']:.1f} "
            f"| {v['over_80']:.2f} | {v['best']:.2f}% | {v['mean']:.2f}% |")
    say()
    if knob == "Sun's disc":
        say("One pixel is 0.06 km², so the >80% column is three or four pixels and moves in")
        say("steps of a third. Read the >50%, mean and best-patch columns for whether a")
        say("setting matters; >80% is in the table because it is what the write-up quotes,")
        say("not because three pixels are a measurement.")
        say()


if __name__ == "__main__":
    say("# Is this result about the Moon, or about our settings?")
    say()
    say(f"Baseline, the settings `run.py` uses: terrain averaged to {RES_M:.0f} m, "
        f"horizons in {AZIMUTHS} directions out to {HORIZON_KM:.0f} km, the Sun "
        f"stepped hourly through the whole {il.NODAL_CYCLE / 365.25:.1f}-year nodal "
        f"cycle, its disc cut into 7 equal-area slices, everything reported over the "
        f"{STUDY_KM:.0f} km disc around the pole. One knob moves at a time.")
    say()

    h, res = lola.load(DOWNSAMPLE)
    lat, lon = lola.grid(len(h), res)
    edge = int((len(h) * RES_M / 2 - STUDY_KM * 1000) / RES_M)
    sl = (slice(edge, -edge), slice(edge, -edge))
    m = len(h) - 2 * edge
    r = np.hypot(*np.meshgrid(*[(np.arange(m) - (m - 1) / 2) * RES_M] * 2))
    inside = r <= STUDY_KM * 1000
    crop = lambda lit: np.where(inside, lit[sl], np.nan)
    tick(f"LOLA map read: {len(h)} x {len(h)} at {res:.0f} m")

    hor = il.horizon(h, res, n_azimuth=AZIMUTHS, max_km=HORIZON_KM)
    tick("baseline horizons")

    # --- 1. The Sun is a disc, not a point ------------------------------------
    say("## 1. Cutting the Sun's disc into slices")
    say()
    say("The Sun is 0.52° across and at this latitude never climbs more than 1.54°,")
    say("so a patch near the pole spends a long time with the Sun half risen.")
    say("Treating the Sun as a point calls all of that darkness. `disc=1` *is* that")
    say("point-Sun model, which is what the first pass of this project shipped, so")
    say("the first row is the old answer and the gap below it is the size of the error.")
    say()
    disc_rows = []
    for d in (1, 3, 7, 15, 31):
        lit = crop(il.lit_fraction(hor, lat, lon, disc=d))
        disc_rows.append((f"{d} slice{'s' if d > 1 else ' (a point)'}", headline(lit)))
        if d == 7:
            base = disc_rows[-1][1]
        tick(f"disc = {d}")
    table(disc_rows, "Sun's disc")
    point, fine = disc_rows[0][1], disc_rows[4][1]
    say("The point Sun was wrong, but not where it was expected to be wrong. The sunlit")
    say(f"ground barely moves: above 70% goes from {point['over_70']:.1f} to "
        f"{base['over_70']:.1f} km², above 50% from {point['over_50']:,.0f} to")
    say(f"{base['over_50']:,.0f} km², the best patch from {point['best']:.2f}% to "
        f"{base['best']:.2f}%. A crest lit nearly 90% of the")
    say("time is nowhere near the edge of being lit at all, so smearing the Sun out over")
    say(f"half a degree does nothing for it. What moves is the darkness: "
        f"{point['shadow']:,.0f} km² of permanent")
    say(f"shadow becomes {base['shadow']:,.0f}, because "
        f"{point['shadow'] - base['shadow']:,.0f} km² of it does catch a sliver of Sun. A disc")
    say("and a point only disagree about marginal ground, and permanent shadow is made")
    say("entirely of marginal ground.")
    say()
    say("Seven slices is enough for the sunlight: going to 31 moves the mean sunlit")
    say(f"fraction by {abs(fine['mean'] - base['mean']) / base['mean'] * 100:.1f}% and the best "
        f"patch by {abs(fine['best'] - base['best']):.2f} points. The shadow area is the")
    say(f"slow one, still drifting "
        f"{(base['shadow'] - fine['shadow']) / base['shadow'] * 100:.1f}% from 7 slices to 31, so "
        f"it is good to a couple of per")
    say("cent and no better.")
    say()

    # --- 2. How many compass directions --------------------------------------
    say("## 2. How many compass directions the horizon is traced in")
    say()
    say(f"{AZIMUTHS} directions is one every {360 / AZIMUTHS:.0f}°. Each one is a single ray, "
        "and whatever it")
    say("finds is applied to the whole sector, so a ridge narrower than a sector is")
    say("either missed or over-applied.")
    say()
    az_rows = [(f"{AZIMUTHS} directions", base)]
    for n_az in (30, 120):
        hor_n = il.horizon(h, res, n_azimuth=n_az, max_km=HORIZON_KM)
        az_rows.append((f"{n_az} directions", headline(crop(il.lit_fraction(hor_n, lat, lon)))))
        del hor_n
        tick(f"{n_az} directions")
    az_rows.sort(key=lambda row: int(row[0].split()[0]))
    table(az_rows, "azimuth bins")
    coarse_az, fine_az = az_rows[0][1], az_rows[2][1]
    moved = "up" if fine_az["best"] > base["best"] else "down"
    say("A single ray can invent blocking and miss it in equal measure, so this knob has")
    say("no guaranteed direction and measuring beats reasoning about it. Doubling to 120")
    say(f"directions moves the best patch {moved} {abs(fine_az['best'] - base['best']):.2f} points, "
        f"the mean sunlit fraction by")
    say(f"{abs(fine_az['mean'] - base['mean']) / base['mean'] * 100:.1f}%, and the permanent shadow "
        f"by {abs(fine_az['shadow'] - base['shadow']) / base['shadow'] * 100:.1f}%. Halving it to 30 is")
    say(f"distinctly worse: {abs(coarse_az['best'] - base['best']):.2f} points on the best patch, "
        f"the other way. Not")
    say("converged, then, but what is left is a fraction of a point, which is small next")
    say("to section 6.")
    say()

    # --- 3. How finely the Sun's motion is sampled ---------------------------
    say("## 3. How finely the Sun's motion is sampled")
    say()
    say("The Sun crosses the sky at 0.5° an hour, which is about one solar diameter,")
    say("so an hourly step and a half-degree Sun are matched to each other.")
    say()
    step_rows = [("1 hour", base)]
    for step in (2.0, 0.5, 0.25):
        step_rows.append((f"{step:g} hour{'s' if step > 1 else ''}",
                          headline(crop(il.lit_fraction(hor, lat, lon, step_hours=step)))))
        tick(f"step = {step} h")
    step_rows.sort(key=lambda row: -float(row[0].split()[0]))
    table(step_rows, "time step")
    say("This knob does nothing. Eight times the samples changes no area at all and")
    say(f"the best patch by {max(abs(r[1]['best'] - base['best']) for r in step_rows):.2f} "
        "points, which is the quantisation of the disc slices")
    say("rather than the time step. Hourly it is.")
    say()

    # --- 4. How long a stretch of the Sun's motion ---------------------------
    say("## 4. How long a stretch of the Sun's motion")
    say()
    say("A year holds only 12.37 synodic months, so in one year each compass direction")
    say("is visited about twelve times and the Sun's declination takes only a couple of")
    say("dozen distinct values while it is in any one direction. That sounded like it")
    say("ought to quantise the answer in steps of several per cent, and the published")
    say("maps use the 18.6-year nodal cycle, so this is worth checking rather than")
    say("assuming. It costs almost nothing: more time samples only lengthen the sorted")
    say("array each pixel is searched against.")
    say()
    win_rows = [(f"{il.NODAL_CYCLE / 365.25:.1f} years", base)]
    for days, label in ((il.YEAR, "1 year"), (il.SYNODIC_DAY * 12, "1 lunar year")):
        win_rows.append((label, headline(crop(il.lit_fraction(hor, lat, lon, days=days)))))
        tick(f"window = {label}")
    win_rows.reverse()
    table(win_rows, "window")
    say("Checked, and it does not matter: a single year gets the areas right to a few")
    say("per cent and the best patch to a fraction of a point. The quantisation is")
    say("there, but it averages out over a map this size. The 18.6-year cycle stays")
    say("the default anyway, because it is what the published maps use and it is free.")
    say()

    # --- 5. How far out the horizon is traced --------------------------------
    say("## 5. How far out the horizon is traced")
    say()
    say("The Moon's surface drops 2.9 km below the local horizontal over 100 km and")
    say("6.5 km over 150, so there is a distance past which terrain cannot block the")
    say("Sun however tall it is. The map itself stops 151 km from the pole.")
    say()
    range_rows = [(f"{HORIZON_KM:.0f} km", base)]
    for km in (25.0, 50.0, 100.0):
        hor_n = il.horizon(h, res, n_azimuth=AZIMUTHS, max_km=km)
        range_rows.append((f"{km:.0f} km", headline(crop(il.lit_fraction(hor_n, lat, lon)))))
        del hor_n
        tick(f"horizon to {km:.0f} km")
    range_rows.sort(key=lambda row: float(row[0].split()[0]))
    table(range_rows, "horizon range")
    near, far = dict(range_rows)["25 km"], dict(range_rows)[f"{HORIZON_KM:.0f} km"]
    say(f"This one matters. Stopping at 25 km finds {near['over_70'] / max(far['over_70'], 1e-9):.1f} "
        f"times as much ground above 70% as")
    say(f"tracing the full {HORIZON_KM:.0f} km, and a best patch {near['best'] - far['best']:.1f} points "
        "higher, because distant massifs")
    say("really do block the Sun here. The sequence is still falling at the end of it,")
    say(f"which is a limit of the data and not of the method: {HORIZON_KM:.0f} km is as far as the")
    say("map reaches. Beyond the edge the terrain is treated as flat, so sunlight in the")
    say("outer ring of the study area is overstated; the ranked sites that matter sit")
    say("within 40 km of the pole, where the map gives at least 110 km in every direction.")
    say()
    del hor

    # --- 6. How coarsely the terrain is averaged -----------------------------
    say("## 6. How coarsely the terrain is averaged")
    say()
    say(f"The map is 40 m per pixel and we average it to {RES_M:.0f} m, because a horizon")
    say("array for the whole map at 40 m would be fourteen gigabytes. To find out what")
    say(f"that costs, here is the same {2 * BOX_KM:.0f} km box around the pole at four grid sizes,")
    say("tracing rays through the whole map each time and computing horizons only")
    say("inside the box. The areas are over the box alone, so they are not comparable")
    say("with the tables above, only with each other.")
    say()
    sites = pd.read_csv(OUT / "sites.csv") if (OUT / "sites.csv").exists() else None
    res_rows, at_sites = [], {}
    for ds in (6, 3, 2, 1):
        hh, rr = lola.load(ds)
        n = len(hh)
        half, c = int(BOX_KM * 1000 / rr), len(hh) // 2
        win = (slice(c - half, c + half), slice(c - half, c + half))
        la, lo = lola.grid(n, rr)
        hor_w = il.horizon(hh, rr, n_azimuth=AZIMUTHS, max_km=HORIZON_KM, window=win)
        lit = il.lit_fraction(hor_w, la[win], lo[win])
        res_rows.append((f"{rr:.0f} m", headline(lit, (rr / 1000) ** 2)))
        if sites is not None:
            # The same places on the ground, read off each grid: do the ranked
            # sites survive a finer map, or are they artefacts of a coarse one?
            # Read as the best pixel within SITE_RADIUS_M, not the single nearest
            # one: a lit crest is a few pixels wide and a site's position is only
            # known to a pixel of the grid that found it, so the nearest pixel
            # measures registration rather than sunlight. It does favour the fine
            # grids slightly, since they offer more pixels to pick from.
            colat = np.radians(90 + sites.latitude)
            rad = 2 * lola.R_MOON * np.tan(colat / 2)
            x = rad * np.sin(np.radians(sites.east_longitude))
            y = rad * np.cos(np.radians(sites.east_longitude))
            row = (half - y / rr).round().astype(int)
            col = (half + x / rr).round().astype(int)
            k = max(1, int(round(SITE_RADIUS_M / rr)))
            ok = (np.abs(x) < (BOX_KM * 1000 - SITE_RADIUS_M - rr)) & \
                 (np.abs(y) < (BOX_KM * 1000 - SITE_RADIUS_M - rr))
            at_sites[f"{rr:.0f} m"] = {
                int(s.rank): round(float(lit[row[i] - k:row[i] + k + 1,
                                             col[i] - k:col[i] + k + 1].max()) * 100, 1)
                for i, s in enumerate(sites.itertuples()) if ok[i]}
        del hor_w, hh, la, lo
        tick(f"box at {rr:.0f} m")
    table(res_rows, "terrain grid")
    coarse, native = res_rows[0][1], res_rows[-1][1]
    say(f"This is the one that matters, and it goes the way that costs us: the finer the")
    say(f"terrain, the *less* sunlight there is. The best patch in the box falls from "
        f"{coarse['best']:.1f}%")
    say(f"at {RES_M:.0f} m to {native['best']:.1f}% at 40 m, the ground above 70% from "
        f"{coarse['over_70']:.1f} to {native['over_70']:.1f} km², and the mean")
    say(f"sunlit fraction from {coarse['mean']:.1f}% to {native['mean']:.1f}%.")
    say()
    if at_sites:
        ranks = sorted(set().union(*(set(v) for v in at_sites.values())))
        say(f"The same thing at the ranked sites that fall inside the box - the best pixel")
        say(f"within {SITE_RADIUS_M:.0f} m of each one, sunlit %, read off each grid:")
        say()
        say("| grid | " + " | ".join(f"site {k}" for k in ranks) + " |")
        say("|---" * (len(ranks) + 1) + "|")
        for g, v in at_sites.items():
            say(f"| {g} | " + " | ".join(f"{v[k]:.1f}" if k in v else "-" for k in ranks) + " |")
        say()
    if "40 m" in at_sites and f"{RES_M:.0f} m" in at_sites:
        a, b = at_sites[f"{RES_M:.0f} m"], at_sites["40 m"]
        both = sorted(set(a) & set(b))
        down = sum(b[k] < a[k] for k in both)
        say(f"The ranked sites hold up far better than the single best pixel does. "
            f"{down} of the {len(both)}")
        say(f"fall between {RES_M:.0f} m and 40 m and the rest do not; at 40 m they read "
            f"{min(b[k] for k in both):.0f}% to {max(b[k] for k in both):.0f}%,")
        say(f"against {min(a[k] for k in both):.0f}% to {max(a[k] for k in both):.0f}% at "
            f"{RES_M:.0f} m. What a finer grid takes away is the extreme")
        say("tail - the one spectacular pixel the headline quotes - rather than the ground")
        say("the ranking actually picked. The siting conclusion is the robust part; the")
        say("record sunlit fraction is not.")
        say()
    say("Two things are going on and they pull the same way. Averaging to 240 m shaves")
    say("the tops off the ridges that do the standing, which should *lower* a crest's")
    say("own sunlight, and it also erases small nearby terrain, which raises it. The")
    say("second effect wins, and it wins for a reason worth stating: at 0.5° of solar")
    say("elevation, a 2 m bump 200 m away is enough to block the Sun. Illumination here")
    say("is set by terrain at the metre scale, and a 40 m gridded product built from")
    say("altimeter tracks does not resolve the metre scale - the fine grids carry real")
    say("small-scale terrain and gridding noise together, and this calculation cannot")
    say("tell them apart. So the resolution ladder is not a convergence sequence")
    say("heading for the truth. It is the width of the honest uncertainty.")
    say()

    # --- 7. Against published work -------------------------------------------
    say("## 7. Against published work")
    say()
    say("| published | they found | we find | |")
    say("|---|---|---|---|")
    say(f"| Mazarico et al. 2011, LOLA, 18.6-year illumination | about 5 km² above 80% "
        f"average illumination near the south pole | {base['over_80']:.2f} km² within "
        f"{STUDY_KM:.0f} km | we are low |")
    say(f"| Gläser et al. 2014, a 20 m DTM of the Connecting Ridge | a point 10 m up lit "
        f"95.65% of a year | best patch {base['best']:.1f}% | we are low |")
    say(f"| LROC, the Shackleton–de Gerlache ridge | lit up to about 90% | "
        f"{base['over_90']:.2f} km² above 90%, best {base['best']:.1f}% | agrees |")
    say()
    say("We are at the low end, and the disagreement with Mazarico et al. is an order of")
    say("magnitude - far larger than any knob in sections 1 to 5. It is worth being")
    say("plain about what that does and does not mean.")
    say()
    say("It is not the point Sun: fixing that moved the sunlit areas by a few per cent")
    say("(section 1). It is not the sampling of the Sun's motion (sections 3 and 4). The")
    say("two settings that do move the answer, horizon range and terrain resolution,")
    say("both say our figures are *too generous* rather than too stingy, so neither")
    say("closes the gap. What is left is definitional - what counts as 'near the pole',")
    say("whether a mast height is assumed, exactly what average illumination means - and")
    say("those are the things a table of headline numbers cannot reconcile. Reading the")
    say("paper's own definitions and reproducing them is the next piece of work, and")
    say("until that is done the right description of this project is a lower bound built")
    say("from public data, not a replication.")
    say()
    say("What does hold up, at every setting in every table above: permanent shadow is")
    say("thousands of square kilometres, near-constant sunlight is single square")
    say("kilometres, and the ratio between them is three orders of magnitude. That")
    say("conclusion survives every knob in this file.")
    say()
    say(f"*Generated by `validate.py` in {time.time() - t0:.0f} s.*")

    OUT.mkdir(exist_ok=True)
    (OUT / "validation.md").write_text("\n".join(report) + "\n")
    (OUT / "validation.json").write_text(json.dumps(
        {"baseline": {"res_m": RES_M, "azimuths": AZIMUTHS, "horizon_km": HORIZON_KM,
                      "disc": 7, "step_hours": 1.0, "years": round(il.NODAL_CYCLE / 365.25, 1),
                      "study_km": STUDY_KM, "box_km": BOX_KM},
         "knobs": knobs, "at_sites": at_sites}, indent=1))
    print(f"\nwritten to {OUT / 'validation.md'}")
