#!/bin/bash
set -e
MOT_STRUCTURE_PATH=${1-/vision/group/STIP/STIP_MOT}

# Visualize tracking results
cd /cvgl2/u/ashenoi/depth_tracking
source /cvgl2/u/ashenoi/env/bin/activate
export PYTHONPATH=$PYTHONPATH:/cvgl2/u/ashenoi/depth_tracking/utils
for SEQ in $MOT_STRUCTURE_PATH/*
do
    echo "Visualizing $SEQ"
    if [ "$(ls -A $DIR)" ]; then
        python visualise.py -i $SEQ/imgs -o $SEQ/tracker_output -t $SEQ/tracker_output/${SEQ##*/}.txt
    else
        echo "No tracking output, skipping"
        continue
    fi
done

