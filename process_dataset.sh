#!/bin/bash
set -e
FINAL_OUTPUT=${1:-/vision/group/STIP/STIP_dataset}
# Rename files and copy dataset to output directory. Also transfer annotations (if last argument uncommented)
# python3 scripts/process_raw_dataset.py /vision/group/STIP/raw_data $FINAL_OUTPUT \
# --anno /vision/group/STIP/annotations --instances /vision/group/STIP/instances_20fps

# Downsample videos and check downsampled videos for duplicates
python3 scripts/process_videos.py $FINAL_OUTPUT

# Inspect ffmpeg logs to create mappings
for SEQ in $FINAL_OUTPUT/*;
do 
    echo $SEQ
    python3 scripts/check_ffmpeg_log.py $SEQ
done

# Map annotations
python3 scripts/transfer_annotations.py $FINAL_OUTPUT

