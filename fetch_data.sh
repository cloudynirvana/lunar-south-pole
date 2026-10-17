#!/usr/bin/env bash
# NASA's LOLA south-polar elevation map, 40 m per pixel, 85-90 degrees south (115 MB).
set -euo pipefail
B=https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img
mkdir -p data && cd data
for f in ldem_85s_40m.lbl ldem_85s_40m.img; do [ -f $f ] || curl -fL# -O $B/$f; done
