# Is this result about the Moon, or about our settings?

Baseline, the settings `run.py` uses: terrain averaged to 240 m, horizons in 60 directions out to 150 km, the Sun stepped hourly through the whole 18.6-year nodal cycle, its disc cut into 7 equal-area slices, everything reported over the 120 km disc around the pole. One knob moves at a time.

## 1. Cutting the Sun's disc into slices

The Sun is 0.52° across and at this latitude never climbs more than 1.54°,
so a patch near the pole spends a long time with the Sun half risen.
Treating the Sun as a point calls all of that darkness. `disc=1` *is* that
point-Sun model, which is what the first pass of this project shipped, so
the first row is the old answer and the gap below it is the size of the error.

| Sun's disc | never lit (km²) | >50% (km²) | >70% (km²) | >80% (km²) | best patch | mean |
|---|---|---|---|---|---|---|
| 1 slice (a point) | 7,151 | 153 | 2.2 | 0.17 | 88.61% | 17.44% |
| 3 slices | 6,710 | 152 | 2.3 | 0.17 | 88.49% | 17.45% |
| 7 slices | 6,556 | 152 | 2.3 | 0.17 | 88.47% | 17.45% |
| 15 slices | 6,483 | 152 | 2.3 | 0.17 | 88.45% | 17.45% |
| 31 slices | 6,441 | 152 | 2.3 | 0.17 | 88.45% | 17.45% |

One pixel is 0.06 km², so the >80% column is three or four pixels and moves in
steps of a third. Read the >50%, mean and best-patch columns for whether a
setting matters; >80% is in the table because it is what the write-up quotes,
not because three pixels are a measurement.

The point Sun was wrong, but not where it was expected to be wrong. The sunlit
ground barely moves: above 70% goes from 2.2 to 2.3 km², above 50% from 153 to
152 km², the best patch from 88.61% to 88.47%. A crest lit nearly 90% of the
time is nowhere near the edge of being lit at all, so smearing the Sun out over
half a degree does nothing for it. What moves is the darkness: 7,151 km² of permanent
shadow becomes 6,556, because 595 km² of it does catch a sliver of Sun. A disc
and a point only disagree about marginal ground, and permanent shadow is made
entirely of marginal ground.

Seven slices is enough for the sunlight: going to 31 moves the mean sunlit
fraction by 0.0% and the best patch by 0.02 points. The shadow area is the
slow one, still drifting 1.8% from 7 slices to 31, so it is good to a couple of per
cent and no better.

## 2. How many compass directions the horizon is traced in

60 directions is one every 6°. Each one is a single ray, and whatever it
finds is applied to the whole sector, so a ridge narrower than a sector is
either missed or over-applied.

| azimuth bins | never lit (km²) | >50% (km²) | >70% (km²) | >80% (km²) | best patch | mean |
|---|---|---|---|---|---|---|
| 30 directions | 6,848 | 156 | 2.4 | 0.17 | 87.86% | 17.48% |
| 60 directions | 6,556 | 152 | 2.3 | 0.17 | 88.47% | 17.45% |
| 120 directions | 6,379 | 152 | 2.4 | 0.17 | 88.80% | 17.45% |

A single ray can invent blocking and miss it in equal measure, so this knob has
no guaranteed direction and measuring beats reasoning about it. Doubling to 120
directions moves the best patch up 0.33 points, the mean sunlit fraction by
0.0%, and the permanent shadow by 2.7%. Halving it to 30 is
distinctly worse: 0.61 points on the best patch, the other way. Not
converged, then, but what is left is a fraction of a point, which is small next
to section 6.

## 3. How finely the Sun's motion is sampled

The Sun crosses the sky at 0.5° an hour, which is about one solar diameter,
so an hourly step and a half-degree Sun are matched to each other.

| time step | never lit (km²) | >50% (km²) | >70% (km²) | >80% (km²) | best patch | mean |
|---|---|---|---|---|---|---|
| 2 hours | 6,556 | 152 | 2.3 | 0.17 | 88.47% | 17.45% |
| 1 hour | 6,556 | 152 | 2.3 | 0.17 | 88.47% | 17.45% |
| 0.5 hour | 6,556 | 152 | 2.3 | 0.17 | 88.47% | 17.45% |
| 0.25 hour | 6,556 | 152 | 2.3 | 0.17 | 88.47% | 17.45% |

This knob does nothing. Eight times the samples changes no area at all and
the best patch by 0.00 points, which is the quantisation of the disc slices
rather than the time step. Hourly it is.

## 4. How long a stretch of the Sun's motion

A year holds only 12.37 synodic months, so in one year each compass direction
is visited about twelve times and the Sun's declination takes only a couple of
dozen distinct values while it is in any one direction. That sounded like it
ought to quantise the answer in steps of several per cent, and the published
maps use the 18.6-year nodal cycle, so this is worth checking rather than
assuming. It costs almost nothing: more time samples only lengthen the sorted
array each pixel is searched against.

| window | never lit (km²) | >50% (km²) | >70% (km²) | >80% (km²) | best patch | mean |
|---|---|---|---|---|---|---|
| 1 lunar year | 6,603 | 157 | 2.4 | 0.17 | 88.57% | 17.59% |
| 1 year | 6,603 | 165 | 2.4 | 0.17 | 88.91% | 17.46% |
| 18.6 years | 6,556 | 152 | 2.3 | 0.17 | 88.47% | 17.45% |

Checked, and it does not matter: a single year gets the areas right to a few
per cent and the best patch to a fraction of a point. The quantisation is
there, but it averages out over a map this size. The 18.6-year cycle stays
the default anyway, because it is what the published maps use and it is free.

## 5. How far out the horizon is traced

The Moon's surface drops 2.9 km below the local horizontal over 100 km and
6.5 km over 150, so there is a distance past which terrain cannot block the
Sun however tall it is. The map itself stops 151 km from the pole.

| horizon range | never lit (km²) | >50% (km²) | >70% (km²) | >80% (km²) | best patch | mean |
|---|---|---|---|---|---|---|
| 25 km | 4,020 | 478 | 11.2 | 1.56 | 94.27% | 23.04% |
| 50 km | 6,528 | 247 | 4.5 | 0.58 | 91.63% | 18.86% |
| 100 km | 6,578 | 167 | 3.2 | 0.46 | 91.21% | 17.59% |
| 150 km | 6,556 | 152 | 2.3 | 0.17 | 88.47% | 17.45% |

This one matters. Stopping at 25 km finds 4.9 times as much ground above 70% as
tracing the full 150 km, and a best patch 5.8 points higher, because distant massifs
really do block the Sun here. The sequence is still falling at the end of it,
which is a limit of the data and not of the method: 150 km is as far as the
map reaches. Beyond the edge the terrain is treated as flat, so sunlight in the
outer ring of the study area is overstated; the ranked sites that matter sit
within 40 km of the pole, where the map gives at least 110 km in every direction.

## 6. How coarsely the terrain is averaged

The map is 40 m per pixel and we average it to 240 m, because a horizon
array for the whole map at 40 m would be fourteen gigabytes. To find out what
that costs, here is the same 40 km box around the pole at four grid sizes,
tracing rays through the whole map each time and computing horizons only
inside the box. The areas are over the box alone, so they are not comparable
with the tables above, only with each other.

| terrain grid | never lit (km²) | >50% (km²) | >70% (km²) | >80% (km²) | best patch | mean |
|---|---|---|---|---|---|---|
| 240 m | 312 | 20 | 1.0 | 0.12 | 88.47% | 17.29% |
| 120 m | 316 | 10 | 0.3 | 0.01 | 86.93% | 16.76% |
| 80 m | 319 | 7 | 0.2 | 0.01 | 82.29% | 16.53% |
| 40 m | 327 | 3 | 0.1 | 0.00 | 82.02% | 16.14% |

This is the one that matters, and it goes the way that costs us: the finer the
terrain, the *less* sunlight there is. The best patch in the box falls from 88.5%
at 240 m to 82.0% at 40 m, the ground above 70% from 1.0 to 0.1 km², and the mean
sunlit fraction from 17.3% to 16.1%.

The same thing at the ranked sites that fall inside the box - the best pixel
within 400 m of each one, sunlit %, read off each grid:

| grid | site 1 | site 3 | site 5 | site 6 | site 12 |
|---|---|---|---|---|---|
| 240 m | 88.5 | 79.4 | 76.0 | 75.4 | 68.3 |
| 120 m | 80.0 | 79.7 | 78.3 | 74.1 | 70.0 |
| 80 m | 77.8 | 69.0 | 78.7 | 82.3 | 71.0 |
| 40 m | 75.1 | 74.3 | 75.4 | 75.2 | 69.2 |

The ranked sites hold up far better than the single best pixel does. 4 of the 5
fall between 240 m and 40 m and the rest do not; at 40 m they read 69% to 75%,
against 68% to 88% at 240 m. What a finer grid takes away is the extreme
tail - the one spectacular pixel the headline quotes - rather than the ground
the ranking actually picked. The siting conclusion is the robust part; the
record sunlit fraction is not.

Two things are going on and they pull the same way. Averaging to 240 m shaves
the tops off the ridges that do the standing, which should *lower* a crest's
own sunlight, and it also erases small nearby terrain, which raises it. The
second effect wins, and it wins for a reason worth stating: at 0.5° of solar
elevation, a 2 m bump 200 m away is enough to block the Sun. Illumination here
is set by terrain at the metre scale, and a 40 m gridded product built from
altimeter tracks does not resolve the metre scale - the fine grids carry real
small-scale terrain and gridding noise together, and this calculation cannot
tell them apart. So the resolution ladder is not a convergence sequence
heading for the truth. It is the width of the honest uncertainty.

## 7. Against published work

| published | they found | we find | |
|---|---|---|---|
| Mazarico et al. 2011, LOLA, 18.6-year illumination | about 5 km² above 80% average illumination near the south pole | 0.17 km² within 120 km | we are low |
| Gläser et al. 2014, a 20 m DTM of the Connecting Ridge | a point 10 m up lit 95.65% of a year | best patch 88.5% | we are low |
| LROC, the Shackleton–de Gerlache ridge | lit up to about 90% | 0.00 km² above 90%, best 88.5% | agrees |

We are at the low end, and the disagreement with Mazarico et al. is an order of
magnitude - far larger than any knob in sections 1 to 5. It is worth being
plain about what that does and does not mean.

It is not the point Sun: fixing that moved the sunlit areas by a few per cent
(section 1). It is not the sampling of the Sun's motion (sections 3 and 4). The
two settings that do move the answer, horizon range and terrain resolution,
both say our figures are *too generous* rather than too stingy, so neither
closes the gap. What is left is definitional - what counts as 'near the pole',
whether a mast height is assumed, exactly what average illumination means - and
those are the things a table of headline numbers cannot reconcile. Reading the
paper's own definitions and reproducing them is the next piece of work, and
until that is done the right description of this project is a lower bound built
from public data, not a replication.

What does hold up, at every setting in every table above: permanent shadow is
thousands of square kilometres, near-constant sunlight is single square
kilometres, and the ratio between them is three orders of magnitude. That
conclusion survives every knob in this file.

*Generated by `validate.py` in 984 s.*
