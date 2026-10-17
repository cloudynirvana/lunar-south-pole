# Where to put a base at the lunar south pole

Run on 17 October 2026 against NASA's LOLA elevation map. Rebuild with
`./fetch_data.sh && python3 run.py`.

Read the headline sunlit areas below as **upper bounds**, not estimates. Which
is a strange thing to open with, so the reason is in
[Does this survive its own settings?](#does-this-survive-its-own-settings) and
it is the most interesting thing this project found.

## The headline

Within 120 km of the south pole there are **45,242 km² of ground**, and of that:

- **6,556 km² (14.5%) never sees the Sun at all** across a full 18.6-year
  cycle. That is where water ice can survive: an area larger than Delaware, in
  permanent darkness, a few kilometres from the pole.
- **Only 2.3 km² is sunlit more than 70% of the time.** A fifth of a square
  kilometre clears 80%. The best single patch on the whole map manages 88.5%.

That contrast is the whole problem in one line. The ice is abundant; the
sunlight is not. The ratio is about **2,800 to 1** by area. The places that have
both are a handful of high points, each smaller than a city block, standing a
kilometre or so above the ground around them and a few kilometres from
permanent shadow.

*Chart: `results/sunlight.png`*

## The best twelve sites

Ranked by sunlight, nearness to permanent shadow, flat ground and a view of
Earth. Longitudes are east. "Sunlit" is the mean fraction of the Sun's disc
visible over the 18.6-year cycle.

| Rank | Latitude | Longitude | Sunlit | Earth in view | Slope | Shadow nearby | Above surroundings |
|---|---|---|---|---|---|---|---|
| 1 | -89.78 | 204.3 | 89% | 58% | 2.5° | 2.7 km | 1,378 m |
| 2 | -88.81 | 123.6 | 86% | 58% | 0.5° | 4.7 km | 1,066 m |
| 3 | -89.31 | 245.9 | 79% | 56% | 1.3° | 1.7 km | 1,128 m |
| 4 | -88.67 | 291.8 | 80% | 58% | 1.2° | 5.7 km | 1,387 m |
| 5 | -89.80 | 54.7 | 76% | 56% | 1.9° | 2.4 km | 1,613 m |
| 6 | -89.45 | 222.7 | 75% | 53% | 0.6° | 2.7 km | 1,017 m |
| 7 | -89.01 | 265.2 | 77% | 56% | 1.9° | 4.8 km | 1,272 m |
| 8 | -86.37 | 336.7 | 70% | 61% | 3.4° | 1.2 km | 1,394 m |
| 9 | -87.98 | 193.7 | 74% | 42% | 0.9° | 1.7 km | 1,836 m |
| 10 | -87.36 | 264.4 | 68% | 61% | 2.7° | 1.2 km | 1,031 m |
| 11 | -87.97 | 147.9 | 70% | 44% | 0.5° | 1.3 km | 644 m |
| 12 | -89.30 | 131.3 | 68% | 56% | 0.3° | 1.8 km | 1,152 m |

Full table with scores: `results/sites.csv`.

What the twelve have in common is height. Every one of them stands between
**0.6 and 1.8 km above the average height of the ground within 20 km of it**.
None of them is on a plain. Sunlight this close to the pole is something you
have to stand on top of.

Five of the twelve lie within 25 km of the pole, on the high ground between the
shadowed basins there. That band is the most valuable real estate in the study
area, because it is the only place where near-constant sunlight and permanent
shadow are a few kilometres apart: those five sites are 1.7 to 2.7 km from
ground that never sees the Sun.

This project does not name the craters. It works from the elevation map alone,
and the gazetteer it would need to attach names to features was not available
offline, so sites are identified by coordinates.

## Three things the numbers say

**Sunlight is a ridge-top resource.** Flat ground at the pole gets sunlight
about half the time, because the Sun spends half of every year on the northern
side of the lunar equator and from here simply never rises. Getting above 70% means standing
on something high enough to see over the local terrain. That is measurable:
every one of the top twelve stands between 644 m and 1,836 m above the mean
height of the ground within 20 km of it. Not one of them is on a plain.

**Permanent shadow is everywhere and sunlight is rare.** The ratio is roughly
2,800 to 1 by area. A mission does not have to search for ice; it has to search
for somewhere to park.

**Earth hangs on the horizon.** Every site in the table can see Earth between
42% and 61% of the time, and no site can see it always. From the south pole,
Earth is only above the horizon while the Moon's libration tips the pole
towards it. Continuous contact with Earth needs a relay satellite no matter
which of these sites is chosen.

## Method

1. **Horizons.** For every patch of ground, trace the skyline in 60 directions
   out to 150 km, including the Moon's curvature, which drops the surface 6.5 km
   over that distance — far more than any of the local relief.
2. **Sunlight.** Step the Sun through the full 18.6-year nodal cycle at one-hour
   intervals: declination swinging ±1.54°, azimuth circling the sky every 29.53
   days. The Sun is a 0.52° disc cut into seven equal-area slices, so a patch
   that can see half of it scores a half.
3. **Permanent shadow.** Ground that never sees any part of the Sun's disc in
   that cycle.
4. **Ranking.** Slope under 10°, sunlit over 50%, permanent shadow within 20 km,
   then scored on sunlight, nearness to shadow and view of Earth.

## Does this survive its own settings?

There are six settings in the model, and `validate.py` turns each one on its own
to find out which of them the answer depends on. The full output, with tables,
is [`results/validation.md`](results/validation.md). The summary:

| setting | does the answer depend on it? |
|---|---|
| how finely the Sun's year is sampled (1 h) | no, not at all |
| how long a stretch of it (18.6 years) | no; one year gets the same answer |
| how many slices the Sun's disc is cut into (7) | no for sunlight, ±2% for shadow |
| treating the Sun as a disc at all | shadow only: a point Sun over-reports it by 9% |
| how many compass directions (60) | a little: doubling it moves the best patch 0.3 points |
| how far the horizon is traced (150 km) | **yes**: 25 km instead of 150 finds 4.9× the area above 70% |
| **how coarsely the terrain is averaged (240 m)** | **yes, more than everything else together** |

The last one is the finding. Run the same 40 km box at 240, 120, 80 and 40 m and
the sunlight falls every time the grid gets finer: the best patch in the box goes
from 88.5% at 240 m to 82.0% at 40 m, and the ground above 70% from 1.0 to
0.1 km². The reason is the Sun's elevation
here: at half a degree, a 2 m bump 200 m away blocks it. Illumination at the
lunar south pole is set by terrain at the metre scale, and a 40 m gridded
product built from altimeter tracks cannot resolve the metre scale. The fine
grids carry real small-scale terrain and gridding noise together and this
calculation cannot tell them apart.

One thing survives that test well: the ranked sites themselves. Read each of
them off all four grids, as the best pixel within 400 m, and at 40 m they still
sit between 69% and 75% sunlit. What a finer map takes away is the extreme tail
— the single spectacular pixel the headline quotes — not the ground the ranking
picked. The siting conclusion is the robust part of this project; the record
sunlit fraction is not.

So the resolution ladder is not a convergence sequence heading for a true
answer. It is the width of the honest uncertainty, and it is wide. Every sunlit
area in this document is reported at 240 m, which is the most generous end of
that range and the grid the published maps use.

## Against published work

| published | they found | we find |
|---|---|---|
| Mazarico et al. 2011 (LOLA, 18.6-year illumination) | about 5 km² above 80% average illumination near the south pole | 0.2 km² within 120 km |
| Gläser et al. 2014 (20 m DTM, Connecting Ridge) | a point 10 m up lit 95.65% of a year | best patch 88.5% |
| LROC (Shackleton–de Gerlache ridge) | lit up to about 90% | best patch 88.5% |

We are at the low end, and against Mazarico et al. we are low by an order of
magnitude — far more than any setting in the table above can explain. It is
worth being plain about what that does and does not mean. It is not the point
Sun, and it is not the sampling of the Sun's motion; those were measured and
they are small. The two settings that do matter both say our figures are *too
generous*, so neither closes the gap. What is left is definitional: what counts
as "near the pole", whether a mast height is assumed, what exactly average
illumination means. Reading those definitions and reproducing them is the next
piece of work.

Until that is done, the honest description of this project is **a lower bound
built from public data, not a replication of the published maps**.

What does hold up, at every setting in every table: permanent shadow is
thousands of square kilometres, near-constant sunlight is single square
kilometres, and the ratio between them is three orders of magnitude. No knob in
the model changes that, and it is the part a mission planner would act on.

## What would change these numbers

- **Terrain at the metre scale**, which is the whole ballgame and which LOLA's
  gridded product does not have. The LROC NAC stereo DTMs of candidate Artemis
  sites do, over small areas, and that is the obvious next dataset.
- **Horizons beyond 151 km**, where this map ends. Beyond the edge the terrain
  is treated as flat, so sunlight in the outer ring of the study area is
  overstated. The sites that matter sit within 40 km of the pole, where the map
  gives at least 110 km in every direction.
- **Scattered light and temperature.** Sunlight here is geometric only. A crater
  floor never directly lit can still be warmed by light off its own walls, and
  ice survival is a question about temperature staying under about 110 K, not
  about photons arriving.
- **Permanent shadow is where ice *can* survive, not where it *is*.** Confirming
  it needs LRO's neutron data, which this project does not use yet.
