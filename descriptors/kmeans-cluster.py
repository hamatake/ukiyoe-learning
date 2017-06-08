import cv2
import datetime
import numpy as np
import os
import sys

if __name__ == '__main__':
    if len(sys.argv) != 6:
        print ('Usage: kmeans-cluster.py sample_dir file_prefix num_dimensions '
            'num_clusters outfile')
        sys.exit(1)
    print datetime.datetime.now()

    # Directory containing one .npy file for each data sample. Filenames are
    # used as keys throughout the rest of processing.
    sample_dir = sys.argv[1]

    # Only process feature files with this prefix. Allows for easy sharding,
    # since filenames are checksums.
    file_prefix = sys.argv[2]

    # Number of dimensions in each feature.
    num_dimensions = int(sys.argv[3])

    # The "k" in k-means: number of clusters to form.
    num_clusters = int(sys.argv[4])

    # Output file to dump k x F matrix of cluster centroids, where k = num
    # clusters and F = num features (dimensions) per sample.
    outfile = sys.argv[5]

    max_kps = 42

    if os.path.isfile(outfile):
        print 'Not recomputing %s' % outfile
        sys.exit(0)

    # Read samples.
    buf_size = len(os.listdir(sample_dir)) * max_kps
    samples = np.zeros((buf_size, num_dimensions), dtype=np.float32)
    print samples.shape
    i = 0
    j = 0
    for sample_file in os.listdir(sample_dir):
        key = sample_file.split('.')[0]
        if file_prefix != 'None' and not key.startswith(file_prefix):
            continue

        try:
            npz = np.load(os.path.join(sample_dir, sample_file))
            # Ignore the first dimensions, as they're keypoint data, not featues.
            sample = npz['arr_0'][:, -num_dimensions:]
            num_kps = sample.shape[0]
            if num_kps > max_kps:
                # TODO: make this a flag
                np.random.shuffle(sample)

                sample = sample[-max_kps:]
                num_kps = max_kps
            if i + num_kps > buf_size:
                print 'Out of buffer space while processing %s' % key
                break
            samples[i: i + num_kps] = sample
            i += num_kps
            npz.close()
        except:
            print 'Error processing %s' % key
            continue
        #print 'Loaded %i samples' % i
        j += 1
        if j % 100 == 0:
            print 'Read %i files' % j
    N = i
    print 'Loaded %i samples' % N
    print datetime.datetime.now()

    samples = samples[:N]
    print samples.shape

    # (type, max_iter, epsilon)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    num_attempts = 10

    # Apply KMeans
    compactness, labels, centers = cv2.kmeans(
        samples, num_clusters, None,
        criteria, num_attempts, cv2.KMEANS_RANDOM_CENTERS)
    print datetime.datetime.now()

    # Save the centroids.
    np.savez_compressed(outfile, centers)
    print datetime.datetime.now()
