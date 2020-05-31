# STIP

This repository is meant to host common functionalities of the STIP dataset. This includes, but is not limited to, preprocessing, annotation reading, visualisation, and any other miscellaneous functions.

All code requires python 3.6+

There are 3 main bash scripts found here, which are used to perform different functions.

* process_dataset.sh - Used to copy the original raw data from TRI into standard STIP_dataset format, downsample videos, generate mappings from 2fps - 20fps and finally map the original annotations into 20fps annotations.

* generate_interpolations.sh - Used to dump segment images to disk, convert the STIP_dataset into STIP_MOT format (required for input to the tracker), run the JRMOT 2D tracker, and then postprocess the tracking to map back into the GT annotation format (plus some ID mapping)

* visualise_final_annotations.sh - Used to visualise the final interpolated annotations and generate videos for every sequence

* visualize_tracking.sh - Utility file to visualise the raw tracking results from STIP_MOT format

There are several python scripts that can be found in the scripts folder, each used for various functions. They are provided with comments and some high level descriptions. To see examples of usage, please take a look at the above bash scripts.

Note, the tracker is not perfect, and the postprocessing is quite limited.
Future work to improve the tracking should be targeted towards
1. Improving instance segmentation recall
2. Better global optimization based postprocessing - current postprocessing is frame-by-frame optimization

Remaining issues:

1. Some sequences have videos, but do not have the annotations
2. Some segements did not have any instance segmentation output

Final output can be found under ```/vision/group/STIP/STIP_dataset```
Please verify that the output processed_interpolations_new* is present in each folder. If it is not available, it is due to one of the issues listed above.

Dependencies:

For the above scripts to all work, you will need access to:
1. JRMOT tracker, which can be found internally in StanfordVL/depth_tracking on github, or ```/cvgl2/u/ashenoi/depth_tracking```.
2. Data in raw form from TRI ```/vision/group/STIP/raw_data```
3. Annotations in raw form from TRI, mapped to the final names ```/vision/group/STIP/annotations
4. Instance segmentation results at 20fps for the segments of interest (and after dumping box results using Bingbin's script data_proc.py) ```/vision/group/STIP/instances_20fps```
