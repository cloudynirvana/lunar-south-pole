# Where to put a base at the lunar south pole

NASA plans to land crew near the Moon's south pole, because that is where the
water is. Water means drinking water, breathable oxygen and rocket fuel that
nobody has to lift off Earth. But the water only survives in craters the Sun
has never touched, and a base in permanent darkness has no power. So the real
question is a siting problem: **which patches of ground are sunlit almost all
the time, flat enough to land on, and close enough to permanent shadow to drive
to the ice?**

This answers it from NASA's own measurements rather than from a map someone
else drew.

There is also a short narrated film of the result:
[`video/lunar_south_pole.mp4`](video/lunar_south_pole.mp4).

## What it does

It reads the LOLA elevation map of the south pole (40 m per pixel, real laser
altimetry from Lunar Reconnaissance Orbiter) and works out, for every patch of
ground in the 300 km square around the pole:

| | |
|---|---|
| **Sunlight** | what fraction of the Sun's disc that patch can see, averaged over the 18.6-year cycle |
| **Permanent shadow** | whether the Sun never reaches it, so water ice can survive |
| **Ground** | the local slope, which decides whether a lander can set down |
| **Earth** | whether Earth is ever in view, which decides if you can talk home directly |

Then it ranks the places that do well on all four at once.

## Why it is not just "look at the elevation"

Near the pole the Sun never climbs more than about 1.5 degrees above the
horizon. At that angle a ridge 50 km away can cast a shadow that never moves.
So the calculation has to trace, from every patch of ground, the skyline in
every direction out to 150 km, which is as far as the map reaches — and include
the Moon's curvature, because over that distance the surface drops 6.5 km below
the local horizontal, far more than any of the local relief. That horizon is then compared against the Sun's
position hour by hour for a year.

And the Sun has to be a disc, not a point. It is half a degree wide and never
climbs more than one and a half, so a patch near the pole spends a long time
with the Sun half risen. Treating it as a point calls all of that darkness,
which is wrong in one direction only: it always reports too little sunlight.
`illumination.disc_levels` cuts the disc into seven equal-area slices, and a
patch scores the fraction of the disc it can see. The first pass of this project
got this wrong; `results/validation.md` measures what it cost, which turned out
to be a tenth of the permanent shadow and almost none of the sunlight.

## Running it

```bash
./fetch_data.sh     # 115 MB from NASA's Planetary Data System
pip install numpy scipy matplotlib pandas
python3 run.py      # about ten minutes
python3 validate.py # about fifteen; the convergence study
pytest              # the geometry checks, no download needed
```

Outputs land in `results/`: `sites.csv` with the ranked sites, maps of
sunlight, permanent shadow and terrain, and `validation.md`.

## Is the answer about the Moon, or about the settings?

There are six knobs in the model: how coarsely the terrain is averaged, how many
compass directions the horizon is traced in, how far out, how long a stretch of
the Sun's motion is sampled, how finely, and how many slices the Sun's disc is
cut into. A result that moves when you turn a knob is a result about the knob.

Four of them turn out not to matter. Two do: how far the horizon is traced, and
above all how coarsely the terrain is averaged. Illumination at this latitude is
set by terrain at the metre scale — at half a degree of solar elevation, a 2 m
bump 200 m away blocks the Sun — and a 40 m gridded product cannot resolve the
metre scale. **So every sunlit area in this project is an upper bound rather
than an estimate**, and the resolution ladder in the validation study is the
width of the honest uncertainty.

`validate.py` turns each one on its own and prints what the headline numbers do,
then sets them beside three published figures for the same ground. The output is
[`results/validation.md`](results/validation.md), and the short version is in
[`RESULTS.md`](RESULTS.md#does-this-survive-its-own-settings).

## Data

- **LOLA LDEM 85S 40M**, Lunar Orbiter Laser Altimeter gridded elevation,
  85–90°S, 40 m per pixel, from the
  [Planetary Data System](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/).
  Collected 2009–2017; heights are relative to a 1737.4 km sphere.

## What this is and is not

It is a siting study built from real terrain, and a lower bound rather than a
replication of the published illumination maps — the comparison, and why we come
out low, is in [`RESULTS.md`](RESULTS.md#against-published-work). It is not a
landing site recommendation. Specifically:

- **The terrain is averaged to 240 m**, the grid the published illumination maps
  also use, and that is the setting the answer really depends on. Redoing a
  40 km box at 120, 80 and 40 m finds less sunlight every time, so these areas
  are upper bounds. See `results/validation.md`.
- **Sunlight is geometric only.** No scattered light, no thermal modelling. A
  crater floor that is never directly lit can still be warmed by light bouncing
  off its own walls, which is one of the things that decides whether ice
  actually survives there.
- **Permanent shadow is a necessary condition for ice, not a sufficient one.**
  This map shows where ice *could* last. Whether it is there, and in what
  concentration, needs neutron and radar data this project does not use yet.
- **Earth visibility assumes the standard longitude convention** for this
  projection (zero longitude up the map, longitude increasing east). Sunlight
  results do not depend on that, because the Sun sweeps every direction each
  month, but the Earth-link numbers would mirror if the convention were flipped.
- **Boulders and small craters are invisible** at 240 m, and they matter to an
  actual lander.

## What I would do differently

The obvious next step is adding the neutron data from LRO's LEND instrument,
which is the closest thing there is to a direct measurement of buried hydrogen,
and seeing whether the places this picks on geometry alone are also the places
that look wet. After that, a proper thermal model: ice survival depends on
temperature staying below about 110 K, and that is not quite the same question
as whether sunlight ever lands on it.
