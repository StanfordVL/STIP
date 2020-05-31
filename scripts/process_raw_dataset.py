import os
import shutil
import argparse
import os.path as osp
from glob import glob


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=str,
                    help='Root folder of the original raw dataset')
    ap.add_argument('output', type=str,
                    help='Output folder for renamed data')
    ap.add_argument('--anno', type=str, default=None,
                    help='Folder containing annotations')
    ap.add_argument('--instances', type=str, default=None,
                    help='Folder containing instance segmentation results')
    args = ap.parse_args()
    return args


def rename_sequences(root_dir, out_dir):
    sequences = glob(osp.join(root_dir, '*'))
    for seq in sorted(sequences):
        out_seq = osp.join(out_dir, osp.basename(seq))
        print(f"Copying {seq} -> {out_seq}")
        shutil.copytree(seq, out_seq)


def rename_files(root_dir):
    sequences = glob(osp.join(root_dir, '*'))
    for seq in sorted(sequences):
        files_to_rename = glob(osp.join(seq, '*idx*'))
        for file in files_to_rename:
            out_name = \
                osp.basename(seq) + '_' + file[file.find('idx'):]
            out_name = osp.join(root_dir, osp.basename(seq), out_name)
            print(f"Moving {file} -> {out_name}")
            shutil.move(file, out_name)
        txt_file = glob(osp.join(seq, '*.txt'))
        txt_file = [i for i in txt_file
                    if 'cam' not in i and 'timestamp' not in i][0]
        out_name = \
            osp.join(root_dir, osp.basename(seq),
                     osp.basename(seq)+'.txt')
        print(f"Moving {txt_file} -> {out_name}")
        shutil.move(txt_file, out_name)


def copy_annotations(annotation_dir, root_dir):
    video_files = glob(osp.join(root_dir, '*', '*.mkv'))
    annotation_files = glob(osp.join(annotation_dir, '*'))
    for vid in video_files:
        seq = osp.dirname(vid)
        for anno in annotation_files:
            if osp.basename(vid) in osp.basename(anno):
                out_path = \
                    osp.join(seq, osp.basename(seq) + '_'
                             + vid[vid.find('idx'):] + '.json')
                print(f"Copying {anno} -> {out_path}")
                shutil.copy(anno, out_path)


def copy_instances(instance_dir, root_dir):
    video_files = glob(osp.join(root_dir, '*', '*idx00.mkv'))
    for vid in sorted(video_files):
        seq = osp.dirname(vid)
        seq_name = osp.basename(seq)
        print(f"Moving instances of {seq_name}")
        instance_folder = osp.join(seq, 'instances')
        if osp.exists(instance_folder):
            shutil.rmtree(instance_folder)
        os.makedirs(instance_folder)
        src_instances = osp.join(instance_dir, seq_name, 'inference')
        shutil.copytree(src_instances, osp.join(instance_folder,
                                                osp.basename(vid)))


if __name__ == "__main__":
    args = parse_args()
    if args.anno is not None:
        copy_annotations(args.anno, args.root)
    rename_sequences(args.root, args.output)
    rename_files(args.output)
    if args.instances is not None:
        copy_instances(args.instances, args.output)
