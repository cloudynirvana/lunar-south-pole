# Where to put a base at the lunar south pole

Run on 16 October 2026 against NASA's LOLA elevation map. Rebuild with
`./fetch_data.sh && python3 run.py`.

## The headline

Within 120 km of the south pole there are **45,242 km² of ground**, and of that:

- **7,222 km² (16%) never sees the Sun at all.** That is where water ice can
  survive, and it is a lot of it: an area the size of Puerto Rico, in permanent
  darkness, a few kilometres from the pole.
- **Only 3.7 km² is sunlit more than 70% of the year.** Less than 0.5 km²
  clears 80%. The best single patch on the whole map manages 91.6%.

That contrast is the whole problem in one line. The ice is abundant; the
sunlight is not. The places that have both are a handful of ridge crests, each
smaller than a city block, perched on crater rims within a few kilometres of
permanent shadow.

*Chart: `results/sunlight.png`*

## The best twelve sites

Ranked by sunlight, nearness to permanent shadow, flat ground and a view of
Earth. Longitudes are east.

| Rank | Latitude | Longitude | Sunlit | Earth in view | Slope | Shadow nearby |
|---|---|---|---|---|---|---|
| 1 | −89.78 | 204.3 | 92% | 58% | 2.5° | 2.6 km |
| 2 | −88.81 | 123.6 | 91% | 58% | 0.5° | 4.6 km |
| 3 | −89.31 | 245.9 | 81% | 61% | 1.3° | 1.7 km |
| 4 | −89.80 | 54.7 | 81% | 58% | 1.9° | 2.4 km |
| 5 | −88.59 | 292.2 | 80% | 61% | 2.4° | 3.8 km |
| 6 | −89.01 | 265.2 | 79% | 56% | 1.9° | 4.8 km |
| 7 | −89.49 | 221.2 | 78% | 53% | 3.1° | 4.1 km |
| 8 | −86.37 | 336.7 | 72% | 61% | 3.4° | 1.2 km |
| 9 | −86.95 | 335.9 | 71% | 58% | 1.9° | 1.2 km |
| 10 | −89.38 | 104.5 | 70% | 61% | 3.1° | 1.4 km |
| 11 | −87.98 | 193.7 | 72% | 44% | 0.9° | 1.7 km |
| 12 | −89.30 | 123.4 | 71% | 53% | 5.3° | 1.6 km |

Full table with scores: `results/sites.csv`.

Sites 1, 3, 4, 7, 10 and 12 all sit on the rim of the large crater centred
almost exactly on the pole, which the map shows as the dark disc at the middle
of `results/sunlight.png`. That ring of rim is the single most valuable
real estate in the study area: it is the high ground, so it catches light that
never reaches the floor a kilometre below, and the permanently shadowed floor
is a short drive away.

## Three things the numbers say

**Sunlight is a ridge-top resource.** Flat ground at the pole gets sunlight
about half the year, because the Sun spends half the year on the northern side
of the lunar equator and simply never rises. Getting above 70% means standing
on something high enough to see over the local terrain — which is why the good
sites are crater rims and ridge crests, not plains.

**Permanent shadow is everywhere and sunlight is rare.** The ratio is roughly
2,000 to 1 by area. A mission does not have to search for ice; it has to search
for somewhere to park.

**Earth hangs on the horizon.** Every site in the table can see Earth between
44% and 61% of the time, and no site can see it always. From the south pole,
Earth is only above the horizon while the Moon's libration tips the pole
towards it. Continuous contact with Earth needs a relay satellite no matter
which of these sites is chosen.

## Method

1. **Horizons.** For every patch of ground, trace the skyline in 60 directions
   out to 100 km, including the Moon's curvature, which drops the surface 2.9 km
   over that distance — more than most of the local relief.
2. **Sunlight.** Step the Sun through a year at one-hour intervals: declination
   swinging ±1.54°, azimuth circling the sky every 29.53 days. A patch is lit
   when the Sun stands above its own horizon in the Sun's direction.
3. **Permanent shadow.** Ground that is never lit in that year.
4. **Ranking.** Slope under 10°, sunlit over 50%, permanent shadow within 20 km,
   then scored on sunlight, nearness to shadow and view of Earth.

## What would change these numbers

- The Sun is treated as a point, not a half-degree disc, so partial shadow at
  every edge is counted as dark. Real sites do slightly better than this says.
- Terrain is averaged to 240 m for the horizon tracing. Small ridges that help,
  and small craters that hurt, are invisible at that scale.
- Permanent shadow is where ice *can* survive, not where it *is*. Confirming
  that needs LRO's neutron data, which this project does not use yet.
- The map runs out at 151 km from the pole, so the study is cut at 120 km to
  keep every horizon inside real data.
