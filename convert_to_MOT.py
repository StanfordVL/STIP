import numpy as np
import json
import argparse
import pdb

ap = argparse.ArgumentParser()
ap.add_argument('--input_file', type = str, required = True, help = 'Input JSON labelling file to be converted to MOT format')

args = ap.parse_args()

with open(args.input_file, 'r') as f:
    input_file = json.load(f)

frames = [i for i in input_file['frames'].keys()]
boxes = [[int(k), int(box['boxId']), box['x1'], box['y1'], box['x2'] - box['x1'], box['y2'] - box['y1']] 
            for k,v in input_file['frames'].items() 
                for box in v ]
boxes = np.vstack(boxes)
boxes = boxes[np.argsort(boxes[:,0])]
#Add columns for confidence, and dummy columns to comply with MOT format
boxes = np.hstack([boxes, np.ones((boxes.shape[0], 1)), np.ones((boxes.shape[0], 3))*-1])

np.savetxt(args.input_file[:-9]+'.txt', boxes, delimiter=',', fmt='%d,%d,%.2f,%.2f,%.2f,%.2f,%.4f,%d,%d,%d')

