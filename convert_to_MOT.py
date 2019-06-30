import numpy as np
import json
import argparse
import os
from glob import glob
import pdb
from collections import defaultdict
from multiprocessing import Pool


def read_box_file(file):
    boxes = np.load(file)[4]
    if len(boxes) == 0:
        return
    frame_num = int(os.path.basename(file).split('_')[0])
    boxes[:,2] -= boxes[:, 0]
    boxes[:,3] -= boxes[:, 1]
    frames = np.ones((boxes.shape[0], 1))*frame_num
    ids = np.ones((boxes.shape[0], 1))*-1
    boxes = np.hstack([frames, ids, boxes])
    # print("File %s done"%file)
    return boxes

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', '--input_file', type = str, required = True, help = 'Input JSON labelling file to be converted to MOT format')
    ap.add_argument('-d', '--detections', type = str, default = '', help = 'Detection folder with _box files')
    args = ap.parse_args()
    return args

def convert_format(args):
    #assumes annotations have already been mapped to 20fps
    with open(args.input_file, 'r') as f:
        input_file = json.load(f)
    id_set = set([box['matchIds'] for k,v in input_file['frames'].items() for box in v ])
    id_map = {}
    count = 0
    for idx in id_set:
        id_map[idx] = count
        count += 1
    with open(args.input_file[:-9]+'_id_map.json', 'w') as f:
        json.dump(id_map, f)
    boxes = [[int(k), id_map[box['matchIds']], box['x1'], box['y1'], box['x2'] - box['x1'], box['y2'] - box['y1']] 
                for k,v in input_file['frames'].items() 
                    for box in v ]
    new_boxes = []
    if args.detections:
        detection_files = glob(os.path.join(args.detections, '*', '*_box.npy'))
        pool = Pool(40)
        segments = pool.map(read_box_file, detection_files)
        segments = [seg for seg in segments if seg is not None]
        new_boxes = boxes+segments
    boxes = np.vstack(boxes)
    boxes = boxes[np.argsort(boxes[:,0])]
    new_boxes = np.vstack(new_boxes)
    new_boxes = new_boxes[np.argsort(new_boxes[:,0])]
    #Add columns for confidence, and dummy columns to comply with MOT format
    boxes = np.hstack([boxes, np.ones((boxes.shape[0], 1)), np.ones((boxes.shape[0], 3))*-1])
    new_boxes = np.hstack([new_boxes, np.ones((new_boxes.shape[0], 1)), np.ones((new_boxes.shape[0], 3))*-1])
    if args.detections:
        np.savetxt(args.input_file[:-9]+'_gt.txt', boxes, delimiter=',', fmt='%d,%d,%.2f,%.2f,%.2f,%.2f,%.4f,%d,%d,%d')
        np.savetxt(args.input_file[:-9]+'.txt', new_boxes, delimiter=',', fmt='%d,%d,%.2f,%.2f,%.2f,%.2f,%.4f,%d,%d,%d')
    else:
        np.savetxt(args.input_file[:-9]+'_gt.txt', boxes, delimiter=',', fmt='%d,%d,%.2f,%.2f,%.2f,%.2f,%.4f,%d,%d,%d')

if __name__=='__main__':
    args = parse_args()
    convert_format(args)