#!/bin/bash
set -e
DATASET_ROOT=${1-/vision/group/STIP/STIP_dataset}

# Visualize tracking results
for SEQ in $DATASET_ROOT/*
do
    if [ -f $SEQ/processed_interpolations_new_${SEQ##*/}_idx00.mkv.json ];
    then
        echo "Visualizing $SEQ"
        python3 scripts/visualise_final_annotations.py -v $SEQ/${SEQ##*/}_idx00.mkv \
        -j $SEQ/processed_interpolations_new_${SEQ##*/}_idx00.mkv.json \
        -o $SEQ/final_processed_annotations.mp4 -w
    fi
done