import os
import glob
import argparse
import shutil
import pdb
from tqdm import tqdm
import time
from multiprocessing import Pool
from functools import partial

ap = argparse.ArgumentParser()
ap.add_argument('-r', '--root', type = str, required = True, help = 'Input folder containing dumped images for 12fps video')
ap.add_argument('-o', '--output_directory', type = str, required = True, help = 'Output directory to save new structure')
ap.add_argument('-v', '--verbose', action = 'store_true', help = 'Verbose output')
args = ap.parse_args()
directories = glob.glob(os.path.join(args.root, '*'))
new_directories = [os.path.join(args.output_directory, os.path.basename(f.rsplit('_', 1)[0]), f.rsplit('_', 1)[-1]) for f in directories]
for new_dir in new_directories:
    os.makedirs(new_dir, exist_ok = True)

def move_image(img, i):
    if args.verbose:
        print("Moving {} to {}".format(img, os.path.join(new_directories[i], os.path.basename(img))))
    shutil.copy(img, os.path.join(new_directories[i], os.path.basename(img)))
pool = Pool(40)

for idx, old_dir in enumerate(tqdm(directories)):
        
    imgs = glob.glob(os.path.join(old_dir, 'front_12fps','*'))
    if args.verbose:
        print("Moving {} Images in {}".format(len(imgs), old_dir))
    # for img in tqdm(imgs[:5], leave = False):
    pool.map(partial(move_image, i=idx), imgs)
pool.close()
pool.join()