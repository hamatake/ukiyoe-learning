import cv2
import gist as pygist
import numpy as np
import os
from scipy import misc
import sys

def gist(image):
    return pygist.extract(image)

def sift(image):
    MAX_KPS = 4000
    gray= cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sift = cv2.xfeatures2d.SIFT_create()
    kp, desc = sift.detectAndCompute(gray, None)

    # Join keypoints and descriptors for output in a single array.
    N = desc.shape[0]
    joined = np.zeros((N, 6 + 128))
    joined[:, 6:] = desc
    for i in range(N):
        p = kp[i]
        joined[i, 0:6] = [p.pt[0], p.pt[1], p.size, p.angle, p.octave, p.response]
    joined_sorted = joined[joined[:, 5].argsort()]
    return joined_sorted[-MAX_KPS:]

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print "Usage: get-desc.py desc_name image_dir manifest output_dir"
        sys.exit(1)
    desc_name = sys.argv[1]
    image_dir = sys.argv[2]
    manifest = sys.argv[3]
    output_dir = sys.argv[4]

    use_whitelist = (manifest != 'None')
    whitelist = {}
    if use_whitelist:
        with open(manifest) as f:
            for line in f:
                whitelist[line.strip()] = True
        print "Whitelist entries: %i" % len(whitelist)

    for image_name in os.listdir(image_dir):
        if use_whitelist and image_name not in whitelist:
            #print 'Skipping ' + image_name
            continue

        key = image_name.split('.')[0]
        output_name = os.path.join(output_dir, key + '.' + desc_name + '.npz')
        if os.path.isfile(output_name):
            print 'Not recomputing ' + image_name
            continue

        print 'Processing ' + image_name

        image = misc.imread(os.path.join(image_dir, image_name))
        desc = globals()[desc_name](image)

        np.savez_compressed(output_name, desc)
