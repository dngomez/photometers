#!/bin/bash
source /home/photometers/.bash_conda
conda activate py3sqm
NOW=$(date -u '+%Y-%m-%dT%H:%M:00.00')
python /home/photometers/ephemeris/ctio_ephemeris.py ${NOW}
python /home/photometers/ephemeris/soar_ephemeris.py ${NOW}
conda deactivate