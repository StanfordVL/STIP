import cv2
import json
import numpy as np
import argparse
import os
import time
import pdb
from glob import glob


def check_color(crossed):
    if crossed:
        return (0, 0, 255)
    return (0, 255, 0)


def create_rect(box):
    x1, y1 = int(box['x1']), int(box['y1'])
    x2, y2 = int(box['x2']), int(box['y2'])

    return x1, y1, x2, y2

def get_params(frame_data):
    boxes = [f['box'] for f in frame_data]
    ids = [f['matchIds'] for f in frame_data]
    crossed = [f['crossed'] for f in frame_data]

    return boxes, ids, crossed

def get_params(frame_data):
    boxes = []
    ids = []
    crossed = []
    for f in frame_data:
        if 'matchIds' in f and 'crossed' in f:
            if 'box' in f:
                boxes.append(f['box'])
            else:
                continue
            #     boxes.append(f)
            ids.append(f['matchIds'])
            crossed.append(f['crossed'])

    return boxes, ids, crossed


def create_writer(capture, output_path):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_count = int(capture.get(cv2.CAP_PROP_FPS))

    writer = cv2.VideoWriter(output_path,
                             fourcc,
                             20,
                             (width, height), isColor=True)

    return writer


def parse_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--video',
                        dest='video_path',
                        required=True)
    parser.add_argument('-j', '--json',
                        required=True,
                        dest='json_path')
    parser.add_argument('-u', '--until',
                        type=int,
                        default=None)
    parser.add_argument('-w', '--write',
                        dest='write',
                        action='store_true',
                        default=False)
    parser.add_argument('-m', '--mask',
                        dest='mask',
                        action='store_true',
                        default=False)
    parser.add_argument('-o', '--output_path',
                        dest='output_path',
                        default=None)
    options = parser.parse_args()

    return options


def Main():
    options = parse_options()
    # Open VideoCapture.
    cap = cv2.VideoCapture(options.video_path)

    # Load json file with annotations.
    with open(options.json_path, 'r') as f:
        data = json.load(f)['frames']

    if options.write:
        writer = create_writer(cap, options.output_path)

    font = cv2.FONT_HERSHEY_SIMPLEX
    frame_no = 0

    while True:
        wait_key = 25
        if options.from_image:
            img = cv2.imread(img_list[frame_no])
            flag = True
        else:
            flag, img = cap.read()

        if img is None:
            break
        # Create black image.
        black_img = np.zeros(img.shape, dtype=np.uint8)

        if frame_no % 120 == 0:
            print('Processed {0} frames'.format(frame_no))

        key = str(frame_no)
        boxes = data.get(key)

        if boxes is None:
            boxes = []

        # Create list of trackers each 60 frames.
        boxes, ids, crossed = get_params(boxes)

        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = create_rect(box)

            if options.mask:
                roi = img[y1:y2, x1:x2].copy()
                black_img[y1:y2, x1:x2] = roi

            if not options.mask:
                crossed_color = check_color(crossed[i])
                cv2.rectangle(img, (x1, y1), (x2, y2), crossed_color, 2, 1)
                cv2.putText(img, ids[i], (x1, y1 - 10), font, 0.6,
                            (0, 0, 0), 5, cv2.LINE_AA)
                cv2.putText(img, ids[i], (x1, y1 - 10), font, 0.6,
                            crossed_color, 1, cv2.LINE_AA)
            cv2.putText(img, str(frame_no), (200,200), font, 5, (0,0,1), 5)

        if options.write:
            if options.mask:
                writer.write(black_img)
            else:
                writer.write(img)
        else:
            if options.mask:
                cv2.imshow('frame', black_img)
            else:
                cv2.imshow('frame', img)

            if cv2.waitKey(wait_key) & 0xFF == ord('q'):
                break
        if frame_no == options.until:
            break

        if flag is False:
            break
        frame_no += 1

    if options.dump_images:
        pool.close()
        pool.join()
    cap.release()
    if options.write:
        writer.release()


if __name__ == '__main__':
    Main()
