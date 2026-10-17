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
| **Sunlight** | what fraction of a year the Sun is above that patch's own horizon |
| **Permanent shadow** | whether the Sun never reaches it, so water ice can survive |
| **Ground** | the local slope, which decides whether a lander can set down |
| **Earth** | whether Earth is ever in view, which decides if you can talk home directly |

Then it ranks the places that do well on all four at once.

## Why it is not just "look at the elevation"

Near the pole the Sun never climbs more than about 1.5 degrees above the
horizon. At that angle a ridge 50 km away can cast a shadow that never moves.
So the calculation has to trace, from every patch of ground, the skyline in
every direction out to 100 km — and include the Moon's curvature, because over
100 km the surface drops 2.9 km below the local horizontal, which is more than
most of the relief here. That horizon is then compared against the Sun's
position hour by hour for a year.

## Running it

```bash
./fetch_data.sh     # 115 MB from NASA's Planetary Data System
pip install numpy scipy matplotlib pandas
python3 run.py      # about ten minutes
pytest              # the geometry checks, no download needed
```

Outputs land in `results/`: `sites.csv` with the ranked sites, and maps of
sunlight, permanent shadow and terrain.

## Data

- **LOLA LDEM 85S 40M**, Lunar Orbiter Laser Altimeter gridded elevation,
  85–90°S, 40 m per pixel, from the
  [Planetary Data System](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/).
  Collected 2009–2017; heights are relative to a 1737.4 km sphere.

## What this is and is not

It is a first-pass siting study built from real terrain. It is not a landing
site recommendation. Specifically:

- **The Sun is treated as a point**, so the few hundred metres of partial
  shadow around every edge are counted as dark. Real twilight is softer.
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
- **The terrain is averaged to 240 m** for the horizon tracing. Boulders and
  small craters that matter to an actual lander are invisible at that scale.

## What I would do differently

The obvious next step is adding the neutron data from LRO's LEND instrument,
which is the closest thing there is to a direct measurement of buried hydrogen,
and seeing whether the places this picks on geometry alone are also the places
that look wet. After that, a proper thermal model: ice survival depends on
temperature staying below about 110 K, and that is not quite the same question
as whether sunlight ever lands on it.
