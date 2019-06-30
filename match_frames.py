import numpy as np
import cv2
import pdb
from glob import glob
import os
import pickle
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tqdm import tqdm
import multiprocessing
from functools import partial
import bisect
import time

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dr_12', type = str, required = True, help = 'Input folder containing segment folders with dumped images for 12fps video')
    ap.add_argument('--dr_20', type = str, required = True, help = 'Input folder containing segment folders with dumped images for 20fps video')
    ap.add_argument('-o', '--output_directory', type = str, required = True, help = 'Output directory to save mapping')

    args = ap.parse_args()

    # if os.path.basename(args.dr_12) in ['0926-2017_downtown_ann_1', '0927-2017_downtown_ann_1', '0927-2017_downtown_ann_2', '0927-2017_downtown_ann_3',
    #                     '0928-2017_downtown_ann_1', '0928-2017_downtown_ann_2', '0928-2017_downtown_ann_3', 'ANN_conor1', 'ANN_conor2',
    #                     'ANN_hanh1', 'ANN_hanh2', 'downtown_palo_alto_1', 'downtown_palo_alto_2', 'downtown_palo_alto_4', 'downtown_palo_alto_6',
    #                     'dt_palo_alto_1', 'dt_palo_alto_2', 'dt_palo_alto_3']:
    #     exit(1)
    os.makedirs(args.output_directory, exist_ok=True)
    return args

def match_image(img_12fps, imgs_20, frame_list_20):
        best_l2_distance = np.inf
        img_12 = cv2.imread(img_12fps)
        approx_20fps_frame = (int(os.path.basename(img_12fps)[:-4])*5)//3
        idx_20_fps_imgs = bisect.bisect_left(frame_list_20, approx_20fps_frame) + 1
        for j in range(max(0, idx_20_fps_imgs - 5), min(len(imgs_20), idx_20_fps_imgs + 5)):
            img_20 = cv2.imread(imgs_20[j])
            l2_distance = np.mean((img_20 - img_12)**2)
            if l2_distance < best_l2_distance:
                best_l2_distance = l2_distance
                best_match = int(os.path.basename(imgs_20[j])[:-4])
        return best_match, best_l2_distance

def match_frames(args):

    imgs_12 = sorted(glob(os.path.join(args.dr_12, '*.png')), key = lambda x: int(os.path.basename(x)[:-4]))
    # imgs_12 = imgs_12[168:325]#+imgs_12[2868:3040]+imgs_12[3768:3882]+imgs_12[4032:4158]+imgs_12[4320:4680]+imgs_12[5028:5094]
    imgs_20 = sorted(glob(os.path.join(args.dr_20, '*.png')), key = lambda x: int(os.path.basename(x)[:-4]))
    frame_list_20 = [int(os.path.basename(x)[:-4]) for x in imgs_20]
    
    start = time.time()
    pool = multiprocessing.Pool(40)
    mappings = list(tqdm(pool.imap(partial(match_image, imgs_20 = imgs_20, frame_list_20 = frame_list_20), imgs_12), 
                total = len(imgs_12)))
    print("Total time taken: {}".format(time.time()-start))
    matches, l2_distances = zip(*mappings)
    mapping = {os.path.basename(k)[:-4]:v for k,v in zip(imgs_12, matches)}
    output_dict = {}
    output_dict['mapping'] = mapping
    output_dict['l2_distances'] = l2_distances
    with open(os.path.join(args.output_directory, os.path.basename(args.dr_20.rstrip(os.path.sep)))+'.p', 'wb') as f:
        pickle.dump(output_dict, f)
    # cleanup_files = glob(os.path.join(args.output_directory, os.path.basename(args.dr_20.rstrip(os.path.sep)), '_tmp_mapping_output*.p'))
    # for file in cleanup_files:
    #     os.remove(file)
if __name__ == "__main__":
    args = parse_args()
    match_frames(args)