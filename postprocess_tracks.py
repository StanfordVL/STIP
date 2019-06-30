import argparse
import numpy as np
from collections import defaultdict
from glob import glob
import os
import json
from tqdm import tqdm

def iou(a, b):
    x_min = max(a[0], b[0])
    y_min = max(a[1], b[1])
    x_max = min(a[0]+a[2], b[0]+b[2])
    y_max = min(a[1]+a[3], b[1]+b[3])
    intersect = (x_max-x_min)*(y_max-y_min)
    union = min(a[2]*a[3],b[2]*b[3])
    # union = a[2]*a[3] + b[2]*b[3] - intersect
    return intersect/union

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('-s', '--sequence_folder', type = str, required = True, help = 'Sequence folder in MOT format containing tracking results')
    '''
    Note: The sequence folder must only contain one txt file: Tracking results,
    two .json files: original annotations (*_annotation.json) and id_map (*_id_map.json) of new annotations,
    one gt folder containing gt.txt
    one det folder containing det.txt
    one imgs folder containing all images
    '''
    # ap.add_argument('-g', '--ground_truth', type = str, default = '', help = 'Ground truth .txt file')
    # ap.add_argument('-d', '--data_path', type = str, default = '', help = 'Sequence directory to check for images')
    # ap.add_argument('-j', '--json_path', type = str, default = '', help = 'JSON file with original 2fps annotations (upsampled to 20fps)')
    # Assumed that in same directory is the id_mapping file for ID's
    args = ap.parse_args()
    return args

def clean_tracking_results(args):

    results = np.loadtxt(glob(os.path.join(args.sequence_folder, '*.txt'))[0], delimiter = ',')
    gt = np.loadtxt(os.path.join(args.sequence_folder, 'gt', 'gt.txt'), delimiter = ',')
    new_anno = {'frames':{}}
    annotation_file = [f for f in glob(os.path.join(args.sequence_folder, '*_annotation.json')) if not os.path.basename(f).startswith('final_')][0]
    with open(annotation_file) as f:
        old_anno = json.load(f)
    with open(glob(os.path.join(args.sequence_folder, '*_id_map.json'))[0]) as f:
        id_map = json.load(f)
    id_map = {v:k for k,v in id_map.items()}
    tp_matches = {}
    fp = []
    unannotated_list = []
    img_frames = sorted([int(os.path.basename(f)[:-4]) for f in glob(os.path.join(args.sequence_folder,'imgs','*'))])
    for frame in tqdm(np.unique(gt[:,0])):
        if frame not in img_frames:
            continue
        det_frame = results[results[:,0]==frame]
        gt_frame = gt[gt[:, 0] == frame]
        if not len(det_frame):
            continue
        for gt_ in gt_frame:
            ious = [iou(gt_[2:], det_frame[idx, 2:]) for idx in range(len(det_frame))]
            det_idx = np.argmax(ious)
            if ious[det_idx] > 0.8:
                if det_frame[det_idx][1] not in tp_matches:
                    tp_matches[det_frame[det_idx][1]] = gt_[1]
        for det in det_frame:
            if det[1] not in tp_matches:
                fp.append(det[1])
    processed_results = []
    for row_idx in range(len(results)):
        new = results[row_idx]
        if new[1] in tp_matches:
            new[1] = tp_matches[new[1]]
            processed_results.append(new)
        else:
            unannotated_list.append(new[1])
            continue

    processed_results = np.vstack(processed_results)
    # processed_results.extend(gt)
    
    annotated_frames = sorted([int(k) for k in old_anno['frames'].keys()])
    last_gt_frame = -1
    for frame in img_frames:
        if frame in annotated_frames:
            new_anno['frames'][str(frame+2)] = old_anno['frames'][str(frame)]
            last_gt_frame  = frame
        else:
            frame_tracks = processed_results[processed_results[:,0] == frame]
            box_list = []
            for i, box in enumerate(frame_tracks):
                obj_id = box[1]
                x1 = max(0, box[2])
                y1 = max(0, box[3])
                x2 = box[2] + box[4] #+ .25*box[4]
                y2 = box[3] + box[5] #+ .25*box[5]
                box_dict= {'box':{'x1': x1, 'y1':y1, 'x2':x2, 'y2':y2}, 'matchIds': id_map[obj_id], 
                            'x1': x1, 'y1':y1, 'x2':x2, 'y2':y2, 'tags': ['pedestrian'], 'type':'Rectangle',
                            'width': 1936, 'height':1216, 'id': i+1, 'boxId': i+1, 'name': i+1,
                            'locked': False, 'UID': '-1'}
                if last_gt_frame != -1:
                    gt_ids = [f['matchIds'] for f in old_anno['frames'][str(last_gt_frame)]]
                    if id_map[obj_id] in gt_ids:
                        idx = gt_ids.index(id_map[obj_id])
                        box_dict['crossed'] = old_anno['frames'][str(last_gt_frame)][idx]['crossed']
                        box_dict['UID'] = old_anno['frames'][str(last_gt_frame)][idx]['UID']
                        box_dict['id'] = old_anno['frames'][str(last_gt_frame)][idx]['id']
                        box_dict['boxId'] = old_anno['frames'][str(last_gt_frame)][idx]['boxId']
                if 'crossed' not in box_dict:
                    box_dict['crossed'] = False
                box_list.append(box_dict)
            new_anno['frames'][str(frame+2)] = box_list
    new_anno["framerate"] = "20"
    new_anno["inputTags"] = "pedestrian"
    new_anno["suggestiontype"] = "copy"
    new_anno["scd"] = True
    new_anno["tag_colors"] = [ "#ffa20c"]
    out_filename = 'final_'+os.path.basename(annotation_file)

    out_file = os.path.join(args.sequence_folder, out_filename)
    with open(out_file, 'w') as f:
        json.dump(new_anno, f)
    # np.savetxt(out_file, processed_results, delimiter = ',')
        

if __name__ == "__main__":
    args = parse_args()
    clean_tracking_results(args)