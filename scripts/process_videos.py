import os
import argparse
import os.path as osp
from glob import glob


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=str,
                    help='Root folder of the dataset')
    ap.add_argument('-f', '--force', action='store_true',
                    help='Overwrite output when set')
    args = ap.parse_args()
    return args


def downsample_videos(root_dir, force=False):
    for seq in sorted(glob(osp.join(root_dir, '*'))):
        video_files = glob(osp.join(seq, '*.mkv'))
        for vid in video_files:
            downsampled_vid = \
                osp.join(osp.dirname(vid),
                         'downsampled_' + osp.splitext(osp.basename(vid))[0]
                         + '.mp4')
            if osp.exists(downsampled_vid) and not force:
                continue
            vid_type = vid[vid.find('idx'):-4]
            log_path = osp.join(osp.dirname(downsampled_vid),
                                f"ffmpeg_log_{vid_type}.txt")
            print(f"Downsampling to {downsampled_vid}"
                  + f" with log in {log_path}")
            os.system(f"ffmpeg -y -i {vid} -r 12 -c:v libx264"
                      + f" -b:v 3M -strict -2 -movflags faststart"
                      + f" {downsampled_vid}  -loglevel"
                      + f" debug 2> {log_path}")


def check_duplicated(root_dir, force=False):
    for seq in sorted(glob(osp.join(root_dir, '*'))):
        video_files = glob(osp.join(seq, 'downsampled_*.mp4'))
        for vid in video_files:
            vid_type = vid[vid.find('idx'):-4]
            log_path = osp.join(osp.dirname(vid),
                                f"duplicate_log_{vid_type}.txt")
            if osp.exists(log_path) and not force:
                continue
            print(f"Checking duplicates in {vid}"
                  + f" with log in {log_path}")
            os.system(f"ffmpeg -i {vid} -vf mpdecimate -loglevel"
                      + f" debug -f null - 2> {log_path}")


if __name__ == "__main__":
    args = parse_args()
    downsample_videos(args.root, args.force)
    check_duplicated(args.root, args.force)
