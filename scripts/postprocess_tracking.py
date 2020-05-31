import os
import json
import scipy
import argparse
import numpy as np
import os.path as osp
from glob import glob
from tqdm import tqdm
from collections import defaultdict
from scipy.optimize import linear_sum_assignment as lsa


def iou(a, b):
    x_min = max(a[0], b[0])
    y_min = max(a[1], b[1])
    x_max = min(a[0]+a[2], b[0]+b[2])
    y_max = min(a[1]+a[3], b[1]+b[3])
    if x_max < x_min or y_max < y_min:
        return 0
    intersect = (x_max-x_min)*(y_max-y_min)
    union = min(a[2]*a[3], b[2]*b[3])
    # union = a[2]*a[3] + b[2]*b[3] - intersect
    return intersect/union


def parse_args():
    ap = argparse.ArgumentParser()
    '''
    Note: The sequence folder must only contain one txt file: Tracking results,
    two .json files: original annotations (*_annotation.json)
    and id_map (*_id_map.json) of new annotations,
    one gt folder containing gt.txt
    one det folder containing det.txt
    one imgs folder containing all images
    '''
    ap.add_argument('dataset_folder',
                    type=str,
                    help='folder containing STIP dataset')
    ap.add_argument('mot_folder',
                    type=str,
                    help='folder containing MOT format of STIP, with tracking output')
    args = ap.parse_args()
    return args


def clean_tracking_results(mot_sequence_folder, dataset_root_folder):
    for seq in sorted(glob(osp.join(dataset_root_folder, '*'))):
        seq_name = osp.basename(seq)
        print(f"Processing sequences {seq_name}")
        segments = sorted(glob(osp.join(mot_sequence_folder, seq_name + '_idx00*')))
        # Only for center video
        annotation_file = osp.join(seq, 'new_' + seq_name + '_idx00.mkv.json')
        if not osp.exists(annotation_file):
            print(f"Annotation file does not exist. Skipping")
            continue
        with open(annotation_file) as f:
            old_anno = json.load(f)
        processed_results = []
        annotated_frames = set([int(k) for k in old_anno['frames'].keys()])
        latest_frame = max(annotated_frames)
        for segment in segments:
            seg_name = osp.basename(segment)
            print(f"Processing segment {seg_name}")
            # if seg_name == "mountain-view-2_idx00.mkv_segments_29:47_29:56":
            #     import pdb; pdb.set_trace()
            results_file = \
                osp.join(segment, 'tracker_output', f"{seg_name}.txt")
            if not osp.exists(results_file):
                print(f"No tracking output found, skipping")
                continue
            with open(results_file) as f:
                results = np.loadtxt(f, delimiter=',')
            gt_file = osp.join(segment, 'gt', 'gt.txt')
            with open(gt_file) as f:
                gt = np.loadtxt(f, delimiter=',')
            # Get mapping from integer gt ID to original ID
            with open(os.path.join(segment, 'id_map.json')) as f:
                id_map = json.load(f)
            id_map = {v: k for k, v in id_map.items()}

            new_anno = {'frames': {}}
            tp_matches = {}
            fp = []
            unannotated_list = []
            img_frames = \
                sorted([int(os.path.basename(f)[:-4])
                        for f in glob(os.path.join(segment, 'imgs', '*'))])
            if len(set(img_frames) & annotated_frames) == 0:
                print(f"No GT annotation at all for this segment!")
                continue
            # Match each track in every GT frame with annotation
            for frame in img_frames:
                if frame not in annotated_frames:
                    continue
                det_frame = results[results[:, 0] == frame]
                gt_frame = gt[gt[:, 0] == frame]
                if not len(det_frame):
                    continue
                iou_mat = np.zeros((len(gt_frame), len(det_frame)))
                for i, gt_ in enumerate(gt_frame):
                    for j, det_ in enumerate(det_frame):
                        iou_mat[i, j] = iou(gt_[2:], det_[2:])
                matches = lsa(1 - iou_mat)
                for row_idx, col_idx in zip(*matches):
                    if iou_mat[row_idx, col_idx] >= 0.6:
                        if det_frame[col_idx][1] not in tp_matches:
                            tp_matches[det_frame[col_idx][1]] = \
                                gt_frame[row_idx][1]
                for det in det_frame:
                    if det[1] not in tp_matches:
                        fp.append(det[1])
            for row_idx in range(len(results)):
                new = results[row_idx]
                if new[1] in tp_matches:
                    new[1] = tp_matches[new[1]]
                    processed_results.append(new)
                else:
                    unannotated_list.append(new[1])
        if not processed_results:
            print(f"Could not find any matches for {seq_name}"
                  + f" between tracker output and GT")
            processed_results = np.array([[-1, -1]])
        else:
            processed_results = np.vstack(processed_results)

        last_gt_frame = -1
        for frame in range(latest_frame):
            if frame in annotated_frames:
                new_anno['frames'][str(frame)] = old_anno['frames'][str(frame)]
                last_gt_frame = frame
            else:
                frame_tracks = \
                    processed_results[processed_results[:, 0] == frame]
                box_list = []
                for i, box in enumerate(frame_tracks):
                    obj_id = box[1]
                    x1 = max(0, box[2])
                    y1 = max(0, box[3])
                    x2 = box[2] + box[4]
                    y2 = box[3] + box[5]
                    box_dict = \
                        {'box': {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2},
                         'matchIds': id_map[obj_id],
                         'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                         'tags': ['pedestrian'], 'type': 'Rectangle',
                         'width': 1936, 'height': 1216,
                         'id': i+1, 'boxId': i + 1, 'name': i+1,
                         'locked': False, 'UID': '-1'}
                    if last_gt_frame != -1:
                        gt_ids = \
                            [f['matchIds'] for f in old_anno['frames'][str(last_gt_frame)]]
                        if id_map[obj_id] in gt_ids:
                            idx = gt_ids.index(id_map[obj_id])
                            box_dict['crossed'] = \
                                old_anno['frames'][str(last_gt_frame)][idx]['crossed']
                            box_dict['UID'] = \
                                old_anno['frames'][str(last_gt_frame)][idx]['UID']
                            box_dict['id'] = \
                                old_anno['frames'][str(last_gt_frame)][idx]['id']
                            box_dict['boxId'] = \
                                old_anno['frames'][str(last_gt_frame)][idx]['boxId']
                    if 'crossed' not in box_dict:
                        box_dict['crossed'] = False
                    box_list.append(box_dict)
                new_anno['frames'][str(frame)] = box_list
        new_anno["framerate"] = "20"
        new_anno["inputTags"] = "pedestrian"
        new_anno["suggestiontype"] = "copy"
        new_anno["scd"] = True
        new_anno["tag_colors"] = ["#ffa20c"]
        out_filename = \
            'processed_interpolations_' + os.path.basename(annotation_file)

        out_file = os.path.join(seq, out_filename)
        with open(out_file, 'w') as f:
            json.dump(new_anno, f)


if __name__ == "__main__":
    args = parse_args()
    clean_tracking_results(args.mot_folder, args.dataset_folder)
