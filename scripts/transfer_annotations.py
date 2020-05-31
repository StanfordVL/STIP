import argparse
import os
import pickle
import json
import numpy as np
import os.path as osp
from glob import glob


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=str,
                    help='Root folder of the dataset')
    ap.add_argument('-d', '--debug', action='store_true',
                    help='Verbose print statements')
    args = ap.parse_args()
    return args


def transfer_annotations(root_dir, debug=False):
    for seq in sorted(glob(osp.join(root_dir, '*'))):
        old_annotations = glob(osp.join(seq, '*idx*.json'))
        for anno in old_annotations:
            if anno.startswith('new'):
                continue
            print(f"Transferring {anno}")
            vid_type = anno[anno.find('idx'): anno.find('idx') + 5]
            mapping_file = osp.join(seq, f"mapping_{vid_type}.pkl")
            with open(mapping_file, 'rb') as f:
                mapping = pickle.load(f)
            with open(anno, 'r') as f:
                annotation = json.load(f)
            new_anno = {}
            for k, v in annotation['frames'].items():
                try:
                    new_anno[str(mapping[(int(k)-1)*6 - 1])] = v
                except KeyError:
                    if debug:
                        print(f"Missing frame: {(int(k)-1)*6 - 1}")
                    continue
            annotation['frames'] = new_anno
            with open(osp.join(seq, 'new_'+osp.basename(anno)), 'w') as f:
                json.dump(annotation, f, indent=2)
            # os.remove(anno)
            # os.rename(osp.join(seq, 'new_'+osp.basename(anno)), anno)


if __name__ == "__main__":
    args = parse_args()
    transfer_annotations(args.root, args.debug)
