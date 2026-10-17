# The film

A 2 minute 18 second narrated film about where a base can actually go at the
lunar south pole, and why the answer depends on how sharp your map is:
`lunar_south_pole.mp4`.

The maps in it are the real output of `run.py`, not illustrations.
`export_data.py` turns `results/lit_fraction.npy`, `results/validation.json` and
the LOLA elevation map into the images and the numbers the film draws from, so
nothing on screen is typed in by hand. Run `validate.py` before it, or the last
scene has no bars to draw.

```bash
./fetch_data.sh && python3 run.py   # the study itself; writes results/
cd video
python3 export_data.py              # -> public/*.png and public/data.json
npm install
npm run sound                       # voiceover, then the music mixed under it
npm run render
```

| | |
|---|---|
| `export_data.py` | renders the sunlight, shadow and terrain maps, and the numbers |
| `src/Film.jsx` | the ten scenes; `SCENES` at the bottom sets their lengths |
| `vo/lines.txt` | the narration, one line per scene |
| `voiceover.py` | reads it with Piper, an offline neural voice |
| `soundtrack.py` | synthesizes the music in numpy and ducks it under the voice |

The voice needs `pip install piper-tts` and the `en_US-ryan-high` voice from
[rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) in `voice/`.
The music is generated from sines and filtered noise, so there are no samples
and nothing to license.

Scene timings live in `SCENES` at the bottom of `src/Film.jsx`, and the
`VO_START` list in `soundtrack.py` has to match them. Generate the voice first,
check each line fits its scene, then render.
