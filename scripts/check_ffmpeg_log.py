import argparse
import os
import pickle
import copy
import os.path as osp


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('root', type=str,
                    help='Root folder of the sequence')
    args = ap.parse_args()
    return args


def parse_log(root):
    for vid in ['idx00', 'idx97', 'idx98']:
        log_file = osp.join(root, f"ffmpeg_log_{vid}.txt")
        dup_file = osp.join(root, f"duplicate_log_{vid}.txt")
        print(f"Inspecting {log_file}")
        with open(log_file) as f:
            # Select only lines corresponding to frame drop
            log = f.readlines()
        new_log = []
        for line in log:
            lines = [line.split(r'\r')[-1]]
            new_log.extend(lines)
        log = new_log
        with open(dup_file) as f:
            dup = f.readlines()
        new_dup = []
        for line in log:
            lines = [line.split(r'\r')[-1]]
            new_dup.extend(lines)
        dup = new_dup
        # Find all duplicated 12fps frames
        dup_idx = [idx for idx, i in enumerate(dup) if 'drop pts' in i]
        dup_frames = []
        for i in dup_idx:
            delta = 1
            line = dup[i - 1]
            if line[1:5] == 'null':
                delta += 1
            dup_frames.append(-int(dup[i - delta].split(':')[-1]))
        for idx in range(len(dup_frames)):
            if idx:
                dup_frames[idx] += dup_frames[idx - 1] + 1
        # Find all dropped 20fps frames
        dropped_frames = \
            [int(i.rstrip().split(' ')[3]) for i in log
             if i[0] == '*' and len(i.split(' ')) == 10]
        # Find total length of video in frames from ffmpeg log
        tot_frames_20fps = \
            int([i.split(' ')[0] for i in log
                if ' '.join(i.split(' ')[1:4])
                == 'frames successfully decoded,'][0])
        tot_frames_12fps = \
            int([i.split(':')[2].lstrip().split(' ')[0] for i in log
                if 'Output stream #0:0 (video):' in i][0])
        # Keep all 20fps frame indices which have not been dropped
        num_dropped = 0
        frames_20fps = []
        # Simulates ffmpeg output buffer, where frames are dropped
        for i in range(tot_frames_20fps):
            if i - num_dropped in dropped_frames:
                dropped_frames.remove(i - num_dropped)
                num_dropped += 1
            else:
                frames_20fps.append(i)

        # Duplicate all 20fps frames which correspond to duplicate 12fps frames
        num_dups = 0
        final_frames_20fps = []
        remaining_20fps_frames = len(frames_20fps)
        for idx in range(remaining_20fps_frames):
            final_frames_20fps.append(frames_20fps[idx])
            # if next 12fps frame is a duplicate, repeat current 20fps frame
            if idx + num_dups + 1 in dup_frames:
                num_dups += 1
                final_frames_20fps.append(frames_20fps[idx])
        # Remaining 20fps frames correspond to 12fps frames
        mapping = {frame_12: frame_20
                   for frame_12, frame_20 in enumerate(final_frames_20fps)}
        with open(osp.join(root, f"mapping_{vid}.pkl"), 'wb') as f:
            pickle.dump(mapping, f)


if __name__ == "__main__":
    args = parse_args()
    parse_log(args.root)
