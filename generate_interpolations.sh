#!/bin/bash
set -e
DATASET_ROOT=${1-/vision/group/STIP/STIP_dataset}
MOT_STRUCTURE_PATH=${2-/vision/group/STIP/STIP_MOT}

# Get images of segments dumped. Run with -f to overwrite existing images
python3 scripts/dump_segment_images.py $DATASET_ROOT -f

# Create MOT directory structure
python3 scripts/create_mot_structure.py $DATASET_ROOT $MOT_STRUCTURE_PATH

# Generate tracking results
cd /cvgl2/u/ashenoi/depth_tracking
source /cvgl2/u/ashenoi/env/bin/activate
export GRB_LICENSE_FILE=/cvgl2/u/ashenoi/gurobi810/license/$HOSTNAME/gurobi.lic

if [[ $GRB_LICENSE_FILE == *".stanford.edu"* ]]; then
  export GRB_LICENSE_FILE=/cvgl2/u/ashenoi/gurobi810/license/$HOSTNAME/gurobi.lic
else
  export GRB_LICENSE_FILE=/cvgl2/u/ashenoi/gurobi810/license/$HOSTNAME.stanford.edu/gurobi.lic
fi

for SEQ in $MOT_STRUCTURE_PATH/*
do
    echo "Tracking $SEQ"
    if [ -z "$(ls -A $SEQ/tracker_output)" ]; then
        python track.py -p --sequence_folder $SEQ --ref_det det --output_folder $SEQ/tracker_output
    else
        echo "Found files $files"
        echo "Skipping";
        continue
    fi
done

deactivate
cd /cvgl2/u/ashenoi/STIP
# Postprocess tracking results
python3 scripts/postprocess_tracking.py /vision/group/STIP/STIP_dataset/ /vision/group/STIP/STIP_MOT/
