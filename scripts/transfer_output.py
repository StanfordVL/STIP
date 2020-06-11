import os
import json
import shutil
import pickle
import argparse
import numpy as np
import os.path as osp
from glob import glob


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=str,
                    help='Root folder of the dataset')
    ap.add_argument('output', type=str,
                    help='output folder')
    args = ap.parse_args()
    return args


def transfer_data(root_dir, output_dir):
    if not osp.exists(output_dir):
        os.makedirs(output_dir, mode=0o770, exist_ok=True)
    for seq in sorted(glob(osp.join(root_dir, '*'))):
        seq_name = osp.basename(seq)
        print(f"Transferring sequence {seq_name}")
        out_folder = osp.join(output_dir, seq_name)
        os.makedirs(out_folder, exist_ok=True, mode=0o770)
        videos = glob(osp.join(seq, '*.mkv'))
        print(f"Transferring videos")
        for video in videos:
            # print(f"{video} -> {out_folder}")
            shutil.copy(video, out_folder)
        annos = glob(osp.join(seq, "new_*.json"))
        print(f"Transferring annotations")
        for anno in annos:
            # print(f"{anno} -> {out_folder}")
            shutil.copy(anno, out_folder)
        print(f"Transferring processed interpolation")
        final_annos = glob(osp.join(seq, 'processed_interpolations*.json'))
        for anno in final_annos:
            # print(f"{anno} -> {out_folder}")
            shutil.copy(anno, out_folder)
        instance_folder = osp.join(seq, 'instances')
        if osp.exists(instance_folder):
            print(f"Transferring instances")
            # print(f"{instance_folder} -> {out_folder}")
            shutil.copytree(instance_folder, osp.join(out_folder, 'instances'))


if __name__ == "__main__":
    args = parse_args()
    transfer_data(args.root, args.output)
