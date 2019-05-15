import numpy as np
import cv2

from glob import glob
import os
import pickle
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tqdm import tqdm

ap = argparse.ArgumentParser()
ap.add_argument('--dr_12', type = str, required = True, help = 'Input folder containing segment folders with dumped images for 12fps video')
ap.add_argument('--dr_20', type = str, required = True, help = 'Input folder containing segment folders with dumped images for 20fps video')
ap.add_argument('-o', '--output_directory', type = str, required = True, help = 'Output directory to save mapping')

args = ap.parse_args()

if os.path.basename(args.dr_12) in ['0926-2017_downtown_ann_1', '0927-2017_downtown_ann_1', '0927-2017_downtown_ann_2', '0927-2017_downtown_ann_3',
                    '0928-2017_downtown_ann_1', '0928-2017_downtown_ann_2', '0928-2017_downtown_ann_3', 'ANN_conor1', 'ANN_conor2',
                    'ANN_hanh1', 'ANN_hanh2', 'downtown_palo_alto_1', 'downtown_palo_alto_2', 'downtown_palo_alto_4', 'downtown_palo_alto_6',
                    'dt_palo_alto_1', 'dt_palo_alto_2', 'dt_palo_alto_3']:
    exit(1)
os.makedirs(args.output_directory, exist_ok=True)

imgs_12 = sorted(glob(os.path.join(args.dr_12,'*', '*.png')))
imgs_20 = sorted(glob(os.path.join(args.dr_20,'*', '*.png')))

#mapping from 12fps frame number to 20fps frame number
mapping = {}
# l2 distances associated with each frame that has been mapped
l2_distances = {}
last_matched_frame_20fps = 0
for i, f_12 in enumerate(tqdm(imgs_12)):
    img_12 = cv2.imread(f_12)
    best_l2_distance = np.inf
    best_match = -1
    l2_distance_series = []
    for j in range(last_matched_frame_20fps, min(len(imgs_20), last_matched_frame_20fps+20)):
        f_20 = imgs_20[j]
        img_20 = cv2.imread(f_20)
        l2_distance = np.mean((img_20 - img_12)**2)
        l2_distance_series.append(l2_distance)
        if l2_distance < best_l2_distance:
            best_l2_distance = l2_distance
            best_match = int(os.path.basename(f_20)[:-4])
            last_matched_frame_20fps = j

    # if i%100 == 0:
    #     plt.plot(range(max(0, last_matched_frame_20fps-10), last_matched_frame_20fps+40), l2_distance_series)
    #     plt.title("l2 distances for 12fps frame: %d"%i)
    #     plt.savefig(os.path.join(args.output_directory, '%d.png'%i))
    mapping[os.path.basename(f_12)[:-4]] = best_match
    l2_distances[os.path.basename(f_12)[:-4]] = best_l2_distance
    if i%1000 == 0:
        output_dict = {}
        output_dict['mapping'] = mapping
        output_dict['l2_distances'] = l2_distances
        with open(os.path.join(args.output_directory, os.path.basename(args.dr_20)+'_tmp_mapping_output_%d.p'%i), 'wb') as f:
            pickle.dump(output_dict, f)

output_dict = {}
output_dict['mapping'] = mapping
output_dict['l2_distances'] = l2_distances
with open(os.path.join(args.output_directory, os.path.basename(args.dr_20.rstrip(os.path.sep)))+'.p', 'wb') as f:
    pickle.dump(output_dict, f)
cleanup_files = glob(os.path.join(args.output_directory, os.path.basename(args.dr_20.rstrip(os.path.sep)), 'tmp_mapping_output*.p'))
for file in cleanup_files:
    os.remove(file)