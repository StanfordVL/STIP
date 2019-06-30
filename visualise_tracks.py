import cv2
import json
import numpy as np
import optparse
import os
import time
from glob import glob
from multiprocessing import Pool

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

def create_writer(capture):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_count = int(capture.get(cv2.CAP_PROP_FPS))

    writer = cv2.VideoWriter('original_annotation_videos/ANN_hanh1.mp4',
                             fourcc,
                             2,
                             (width, height), isColor=True)

    return writer



def parse_options():
    parser = optparse.OptionParser()
    parser.add_option('-v', '--video',
                      dest='video_path',
                      default=None)
    parser.add_option('-j', '--json',
                      dest='json_path',
                      default=None)
    parser.add_option('-u', '--until',
                      type='int',
                      default=None)
    parser.add_option('-w', '--write',
                      dest='write',
                      action='store_true',
                      default=False)
    parser.add_option('-m', '--mask',
                      dest='mask',
                      action='store_true',
                      default=False)
    parser.add_option('-d', '--dump_images',
                      dest='dump_images',
                      action='store_true',
                      default=False)
    parser.add_option('-o', '--output_folder',
                      dest='output_folder',
                      default=None)
    parser.add_option('-i', '--from_image',
                      default='')
    options, _ = parser.parse_args()

    # Check for errors.
    if options.video_path is None and not options.from_image:
        raise Exception('Undefined video or image path')
    if options.json_path is None:
        raise Exception('Undefined json_file')

    return options


def Main():
    options = parse_options()
    if options.dump_images:
        os.makedirs(options.output_folder, exist_ok = True)
    if options.dump_images:
        pool = Pool(20)
    if options.from_image:
        img_list = sorted(glob(os.path.join(options.from_image, 'imgs','*')), key = lambda x:int(os.path.basename(x)[:-4]))
    # Open VideoCapture.
    cap = cv2.VideoCapture(options.video_path)

    # Load json file with annotations.
    with open(options.json_path, 'r') as f:
        data = json.load(f)['frames']

    if options.write:
        writer = create_writer(cap)

    font = cv2.FONT_HERSHEY_SIMPLEX
    if options.from_image:
        frame_no = 0
    else:
        frame_no = 1
    while True:
        if options.from_image and frame_no >= len(img_list):
            break
        wait_key = 25
        if options.from_image:
            img = cv2.imread(img_list[frame_no])
            flag = True
        else:
            flag, img = cap.read()

        if img is None:
          break
        if options.dump_images:
            # pool.apply_async(cv2.imwrite, (os.path.join('redumped_images_12fps', 'ANN_hanh2_12fps_images', str(frame_no)+'.png'), img))
            cv2.imwrite(os.path.join(options.output_folder, str(frame_no-1)+'.png'), img)
        # Create black image.
        black_img = np.zeros(img.shape, dtype=np.uint8)

        if frame_no % 120 == 0:
            print('Processed {0} frames'.format(frame_no))

        if not options.from_image:
            key = str(int(frame_no / 6 + 1))
            # key = str(frame_no-1)
            # if frame_no % 6 != 0:
            #     frame_no += 1
            #     continue
        else:
            # if int(os.path.basename(img_list[frame_no])[:-4]) % 6 != 0:
            #     frame_no += 1
            #     continue
            key = str(int(os.path.basename(img_list[frame_no])[:-4]))
            # key = frame_no
            # frame_no += 1
        boxes = data.get(key)

        if boxes == None:
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
        if options.from_image:
            cv2.putText(img, os.path.basename(img_list[frame_no])[:-4], (200,200), font, 5, (0,0,1), 5)
        else:
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
