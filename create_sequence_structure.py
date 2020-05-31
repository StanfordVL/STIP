import os
from glob import glob
import shutil
import argparse
import pdb
from tqdm import tqdm

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('-i', '--input_folder', type = str, required = True, help = '20fps image folder with all sequences (need absolute path)')
    ap.add_argument('-a', '--annotation_folder', type = str, default = '', help = 'Prepared detections')
    args = ap.parse_args()
    return args

def create_sequence_structure(args):
    img_folders = glob(os.path.join(args.input_folder, '*', '*'))
    out_folders = [os.path.join('sequences',os.path.basename(os.path.dirname(f))+'_'+os.path.basename(f), 'imgs') for f in img_folders]
    detections = [f for f in glob(os.path.join(args.annotation_folder, '*.txt')) if '_gt.txt' not in f]
    gts = [f for f in glob(os.path.join(args.annotation_folder, '*.txt')) if f.endswith('_gt.txt')]
    id_maps = [f for f in glob(os.path.join(args.annotation_folder, '*.json')) if f.endswith('_id_map.json')]
    annotations = [f for f in glob(os.path.join(args.annotation_folder, '*.json')) if not f.endswith('_id_map.json')]
    for input_folder, output_folder in tqdm(zip(img_folders, out_folders), total = len(img_folders)):
        sequence_name = os.path.basename(os.path.dirname(input_folder))
        det_file = [f for f in detections if sequence_name in f]
        gt_file = [f for f in gts if sequence_name in f]
        id_map = [f for f in id_maps if sequence_name in f]
        annotation_file = [f for f in annotations if sequence_name in f]
        if not det_file:
            continue
        
        os.makedirs(os.path.dirname(output_folder), exist_ok = True)
        os.system('cd {} && ln -s {} imgs && cd ../..'.format(os.path.dirname(output_folder), os.path.abspath(input_folder)))
        out_det_file = os.path.join(os.path.dirname(output_folder), 'det', 'det.txt')
        out_gt_file = os.path.join(os.path.dirname(output_folder), 'gt', 'gt.txt')
        out_id_map = os.path.join(os.path.dirname(output_folder), sequence_name+'_id_map.json')

        os.makedirs(os.path.dirname(out_det_file), exist_ok = True)
        os.makedirs(os.path.dirname(out_gt_file), exist_ok = True)

        shutil.copy(det_file[0], out_det_file)
        shutil.copy(gt_file[0], out_gt_file)
        
        shutil.copy(id_map[0], out_id_map)
        shutil.copy(annotation_file[0], os.path.join(os.path.dirname(output_folder), sequence_name+'_annotation.json'))
    
if __name__ == "__main__":
    args = parse_args()
    create_sequence_structure(args)