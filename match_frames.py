import numpy as np
import cv2

from glob import glob
import os
import pickle
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument('--dr_12', type = str, required = True, help = 'Input folder containing dumped images for 12fps video')
ap.add_argument('--dr_20', type = str, required = True, help = 'Input folder containing dumped images for 20fps video')
ap.add_argument('-o', '--output_directory', type = str, required = True, help = 'Output directory to save mapping')

args = ap.parse_args()
os.makedirs(args.output_directory, exist_ok=True)

imgs_12 = sorted(glob(os.path.join(args.dr_12,'*.png')))
imgs_20 = sorted(glob(os.path.join(args.dr_20,'*.png')))

#mapping from 12fps frame number to 20fps frame number
mapping = {}
# l2 distances associated with each frame that has been mapped
l2_distances = {}
last_matched_frame_20fps = 0
for i, f_12 in enumerate(imgs_12):
    img_12 = cv2.imread(f_12)
    best_l2_distance = np.inf
    best_match = 0
    l2_distance_series = []
    for j in range(max(0, last_matched_frame_20fps), last_matched_frame_20fps+20):
        f_20 = imgs_20[j]
        img_20 = cv2.imread(f_20)
        l2_distance = np.mean((img_20 - img_12)**2)
        l2_distance_series.append(l2_distance)
        if l2_distance < best_l2_distance:
            best_l2_distance = l2_distance
            best_match = j
    # if i%100 == 0:
    #     plt.plot(range(max(0, last_matched_frame_20fps-10), last_matched_frame_20fps+40), l2_distance_series)
    #     plt.title("l2 distances for 12fps frame: %d"%i)
    #     plt.savefig(os.path.join(args.output_directory, '%d.png'%i))
    mapping[i] = best_match
    l2_distances[i] = best_l2_distance
    last_matched_frame_20fps = best_match
    if i%1000 == 0:
        output_dict = {}
        output_dict['mapping'] = mapping
        output_dict['l2_distances'] = l2_distances
        with open(os.path.join(args.output_directory, 'tmp_mapping_output_%d.p'%i), 'wb') as f:
            pickle.dump(output_dict, f)

output_dict = {}
output_dict['mapping'] = mapping
output_dict['l2_distances'] = l2_distances
with open(os.path.join(args.output_directory, 'tmp_mapping_output_final.p'), 'wb') as f:
    pickle.dump(output_dict, f)



