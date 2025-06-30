#!/bin/bash
source /home/photometers/.bash_conda
conda activate py3sqm
python /home/photometers/photometers/ephemeris/ctio_remove_data.py
python /home/photometers/photometers/ephemeris/soar_remove_data.py
conda deactivate