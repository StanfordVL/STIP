import numpy as np
import cv2

from glob import glob
import os
import pickle
import json
import argparse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tqdm import tqdm

ap = argparse.ArgumentParser()
ap.add_argument('-a', '--annotation_directory', type = str, required = True, help = 'Input folder containing annotations at 2fps for the 12fps video')
ap.add_argument('-m', '--mapping_directory', type = str, required = True, help = 'Input folder containing generated mapping files')
args = ap.parse_args()

old_annotations = glob(os.path.join(args.annotation_directory, '*idx00*'))
mapping_files = glob(os.path.join(args.mapping_directory, '*'))
#assumed that mapping file is <name of sequence>.p, and annotation file has name of sequence within it
for annotation_path in tqdm(old_annotations):
    annotation = None
    for mapping_path in mapping_files:
        mapping_filename = os.path.basename(mapping_path)[:-2] # strip .p from end
        if mapping_filename in annotation_path and 'tmp' not in mapping_filename:
            with open (mapping_path, 'rb') as f:
                mapping = pickle.load(f)['mapping']
            with open(annotation_path, 'r') as f:
                annotation = json.load(f)
            new_anno = {}
            for k,v in annotation['frames'].items():
                try:
                    new_anno[str(mapping["{:010d}".format((int(k)-1)*6)])] = v
                except:
                    # print("Missing frame: %d"%((int(k)-1)*6))
                    continue
            annotation['frames'] = new_anno
            break
    # if annotation is not None:
    #     with open(os.path.join('annotations_20fps', 'new_'+os.path.basename(annotation_path)), 'w') as f:
    #         json.dump(annotation, f)