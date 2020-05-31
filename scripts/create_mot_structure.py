import os
import cv2
import json
import psutil
import shutil
import argparse
import numpy as np
import os.path as osp
from glob import glob
from multiprocessing import Pool


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=str,
                    help='Root folder of the dataset with mapped annotations')
    ap.add_argument('mot', type=str,
                    help='Output folder')
    args = ap.parse_args()
    return args


def read_box_file(file_name):
    with open(file_name, 'rb') as f:
        boxes = np.load(f, allow_pickle=True)[4].tolist()
    new_boxes = np.array(boxes)
    del boxes
    if len(new_boxes) == 0:
        return
    # -1 is very important! All annotations, videos etc are 0 based
    # But instances are 1 based!
    frame_num = int(os.path.basename(file_name).split('_')[0]) - 1
    new_boxes[:, 2] -= new_boxes[:, 0]
    new_boxes[:, 3] -= new_boxes[:, 1]
    new_boxes[new_boxes < 0] = 0
    frames = np.ones((new_boxes.shape[0], 1))*frame_num
    ids = np.ones((new_boxes.shape[0], 1))*-1
    new_boxes = np.hstack([frames, ids, new_boxes])
    return new_boxes


def create_img_symlink(mot_output, seq, times, seq_name):
    # Currently only need to create for 00 video
    # No instance segmentation available for other videos
    for vid in ['00']:  # , '98', '99']:
        mot_base_folder = \
            osp.join(mot_output,
                     seq_name + f"_idx{vid}.mkv_segments_"
                     + '_'.join(times))
        os.makedirs(mot_base_folder, exist_ok=True)
        src_img_folder = \
            osp.join(seq,
                     f"{seq_name}_idx{vid}.mkv_segments",
                     '_'.join(times))
        if osp.lexists(osp.join(mot_base_folder, 'imgs')):
            os.remove(osp.join(mot_base_folder, 'imgs'))
        os.symlink(src_img_folder, osp.join(mot_base_folder, 'imgs'))


def create_det(seq_path, mot_output, times):
    seq_name = osp.basename(seq_path)
    mot_base_folder = \
        osp.join(mot_output, seq_name + f"_idx00.mkv_segments_"
                 + '_'.join(times))
    mot_gt_folder = osp.join(mot_base_folder, 'gt')
    os.makedirs(mot_gt_folder, exist_ok=True)
    mot_det_folder = osp.join(mot_base_folder, 'det')
    os.makedirs(mot_det_folder, exist_ok=True)

    seg_instances = \
        osp.join(seq_path,
                 'instances',
                 seq_name + f"_idx00.mkv", '--'.join(times))
    annotation = osp.join(seq_path, f"new_{seq_name}_idx00.mkv.json")
    with open(annotation) as f:
        annotation = json.load(f)
    # Move annotations into MOT format
    id_set = \
        set([box['matchIds']
             for k, v in annotation['frames'].items()
             for box in v])
    id_map = {}
    count = 0
    for idx in id_set:
        id_map[idx] = count
        count += 1
    with open(osp.join(mot_base_folder, 'id_map.json'), 'w') as f:
        json.dump(id_map, f)
    boxes = \
        [[int(k), id_map[box['matchIds']],
          box['x1'], box['y1'],
          box['x2'] - box['x1'],
          box['y2'] - box['y1']]
         for k, v in annotation['frames'].items()
         for box in v]
    detection_files = glob(os.path.join(seg_instances, '*_box.npy'))
    if not detection_files:
        print(f"Sequence {seq_name} does not have instances for {times}")
    pool = Pool(8)
    segments = pool.map(read_box_file, detection_files)
    pool.close()
    pool.join()
    segments = [seg for seg in segments if seg is not None]
    new_boxes = boxes + segments
    new_boxes = np.vstack(new_boxes)
    new_boxes = new_boxes[np.argsort(new_boxes[:, 0])]
    boxes = np.vstack(boxes)
    boxes = boxes[np.argsort(boxes[:, 0])]
    # Add columns for confidence, and dummy columns to comply with MOT format
    boxes = \
        np.hstack([boxes,
                   np.ones((boxes.shape[0], 1)),
                   np.ones((boxes.shape[0], 3)) * -1])
    new_boxes = \
        np.hstack([new_boxes,
                   np.ones((new_boxes.shape[0], 1)),
                   np.ones((new_boxes.shape[0], 3)) * -1])

    with open(osp.join(mot_gt_folder, 'gt.txt'), 'wb') as f:
        np.savetxt(f, boxes, delimiter=',',
                   fmt='%d,%d,%.2f,%.2f,%.2f,%.2f,%.4f,%d,%d,%d')
    with open(osp.join(mot_det_folder, 'det.txt'), 'wb') as f:
        np.savetxt(f, new_boxes,
                   delimiter=',',
                   fmt='%d,%d,%.2f,%.2f,%.2f,%.2f,%.4f,%d,%d,%d')
    del boxes
    del new_boxes


def create_MOT_structure(root_folder, mot_output):
    os.makedirs(mot_output, exist_ok=True)
    for seq in sorted(glob(osp.join(root_folder, '*'))):
        seq_name = osp.basename(seq)
        print(f"Processing sequence {seq_name}")
        annotation = osp.join(seq, f"new_{seq_name}_idx00.mkv.json")
        if not osp.exists(annotation):
            print(f"Sequence {seq_name} does not have annotations!")
            continue
        segment_file = osp.join(seq, seq_name + '.txt')
        with open(segment_file) as f:
            segment_lines = f.readlines()
        # get times for segments of interest
        for l in segment_lines:
            times = l.split('"')[0].split("--")
            times = [t.strip() for t in times if t.strip()]
            if times:
                create_img_symlink(mot_output, seq, times, seq_name)
                create_det(seq, mot_output, times)


if __name__ == "__main__":
    args = parse_args()
    create_MOT_structure(args.root, args.mot)
