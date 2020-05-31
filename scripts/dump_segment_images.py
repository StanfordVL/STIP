import os
import cv2
import shutil
import argparse
import os.path as osp
from glob import glob

FRAME_RATE = 20


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=str,
                    help='Root folder of the dataset with mapped annotations')
    ap.add_argument('-f', '--force', action='store_true',
                    help='Force overwrite output')
    args = ap.parse_args()
    return args


def dump_imgs(vid_path, segment_times, vid_segment_output):
    os.makedirs(vid_segment_output, exist_ok=True)
    segment_frames = []
    segment_outputs = []
    for times in segment_times:
        frames = []
        stime, etime = times
        segment_output = osp.join(vid_segment_output, f"{stime}_{etime}")
        os.makedirs(segment_output, exist_ok=True)
        segment_outputs.append(segment_output)
        mm, ss = stime.split(':')
        frames.append((60 * int(mm) + int(ss)) * FRAME_RATE)
        mm, ss = etime.split(':')
        frames.append((60 * int(mm) + int(ss)) * FRAME_RATE)
        segment_frames.append(frames)

    cap = cv2.VideoCapture(vid_path)
    cur_seg_idx = 0
    frame_idx = 0
    while cap.grab():
        if frame_idx > segment_frames[cur_seg_idx][1]:
            print(f"Completed segment {segment_times[cur_seg_idx]}")
            # move to next segment
            cur_seg_idx += 1
            if cur_seg_idx == len(segment_frames):
                break
        if frame_idx >= segment_frames[cur_seg_idx][0]:
            # save image if within segment
            _, img = cap.retrieve()
            cv2.imwrite(osp.join(segment_outputs[cur_seg_idx],
                                 f"{frame_idx:06d}.jpg"), img)
        frame_idx += 1


def dump_segment_imgs(root, force):
    for seq in sorted(glob(osp.join(root, '*'))):
        seq_name = osp.basename(seq)
        print(f"Processing sequence {seq_name}")
        segment_file = osp.join(seq, seq_name + '.txt')
        with open(segment_file) as f:
            segment_lines = f.readlines()
        # get times for segments of interest
        segment_times = []
        for l in segment_lines:
            times = l.split('"')[0].split("--")
            times = [t.strip() for t in times if t.strip()]
            if times:
                segment_times.append(times)
        # Only for idx00 required now
        video_paths = [osp.join(seq, seq_name + '_idx00.mkv')]#,
                    #    osp.join(seq, seq_name + '_idx98.mkv'),
                    #    osp.join(seq, seq_name + '_idx99.mkv')]
        output_segment_paths = \
            [osp.join(seq, seq_name + '_idx00.mkv_segments')]#,
            #  osp.join(seq, seq_name + '_idx98.mkv_segments'),
            #  osp.join(seq, seq_name + '_idx99.mkv_segments')]
        # dump images for each segment
        for vid, output in zip(video_paths, output_segment_paths):
            if not args.force and osp.exists(output):
                continue
            elif args.force and osp.exists(output):
                shutil.rmtree(output)
            print(f"Processing video {osp.basename(vid)}")
            print(f"Dumping output in {output}")
            dump_imgs(vid, segment_times, output)


if __name__ == "__main__":
    args = parse_args()
    dump_segment_imgs(args.root, args.force)
