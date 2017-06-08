# -*- coding: utf-8 -*-

import datetime
import numpy as np
import os
from sklearn.decomposition import PCA
import sys

# TODO: move to common lib
allowed_artists = {
    u'Utagawa Kunisada I (Toyokuni III)': 0,
    u'Utagawa Hiroshige I': 1,
    u'Utagawa Kuniyoshi': 2,
    u'Katsushika Hokusai': 3,
    u'Utagawa Toyokuni I': 4,
    u'Kitagawa Utamaro I': 5,
    'Katsukawa Shunshô': 6,
    u'Utagawa Hiroshige II (Shigenobu)': 7,
    u'Toyohara Kunichika': 8,
    u'Torii Kiyonaga': 9,
    u'Utagawa Kunisada II (Kunimasa III, Toyokuni IV)': 10,
    u'Suzuki Harunobu': 11,
    'Isoda Koryûsai': 12,
    u'Tsukioka Yoshitoshi': 13,
    u'Kawase Hasui': 14,
}

# The most features there will ever be for a single sample.
max_features = 3000

def process_single_image(features, labels, keys, query_idx):
    N = features.shape[0]
    # Sort samples by proximity to query image.
    if not query_idx:
        print 'Key not found: %s' % query_key
        exit(1)
    query_desc = features[query_idx]
    diff = features - query_desc
    dist = np.ones((N))
    for i in range(N):
        dist[i] = np.linalg.norm(diff[i])
    sorted_idx = np.argsort(dist)
    sorted_features = features[sorted_idx]

    # Get closest image of each class.
    closest_by_class = {}
    query_rank = -1
    i = 0
    top_found = 0
    for idx in sorted_idx:
        if top_found < 10:
            print keys[idx]
            top_found += 1
        if labels[idx] not in closest_by_class:
            closest_by_class[labels[idx]] = keys[idx]
            if len(closest_by_class) >= len(allowed_artists) and query_rank > -1:
                break
        if keys[idx] == query_key:
            query_rank = i
        i += 1
    print closest_by_class
    print query_rank

def compute_class_stats(features, labels, keys):
    N = features.shape[0]
    num_dimensions = features.shape[1]
    num_classes = len(allowed_artists)
    means = np.zeros((num_classes + 1, num_dimensions))
    variances = np.zeros((num_classes))

    for class_key in allowed_artists:
        class_label = allowed_artists[class_key]
        class_features = features[labels == class_label]
        class_keys = keys[labels == class_label]
        assert class_features.shape[0] == class_keys.shape[0]
        class_N = class_features.shape[0]
        print "Class %s has %i samples" % (class_label, class_N)

        # Compute centroid and sort the class by distance from the centroid.
        mean = np.mean(class_features, axis=0)
        means[class_label] = mean
        diff = class_features - mean
        dist = np.ones((class_N))
        for i in range(class_N):
            dist[i] = np.linalg.norm(diff[i])
        sorted_idx = np.argsort(dist)
        sorted_features = class_features[sorted_idx]
        sorted_keys = class_keys[sorted_idx]

        variance = np.var(dist)
        variances[class_label] = variance

        # Compute "representative sample", the sample closest to the mean.
        print 'Closest to mean:'
        print sorted_keys[0:5]

        # Compute greatest outliers.
        print 'Outliers:'
        print sorted_keys[-5:]

    # Global centroid.
    means[-1] = np.mean(features, axis=0)

    # Compute inter-class distances.
    inter_class_dist = np.zeros((num_classes + 1, num_classes + 1))
    for i in range(num_classes + 1):
        for j in range(num_classes + 1):
            inter_class_dist[i, j] = np.linalg.norm(means[i] - means[j])
    print inter_class_dist
    print variances


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print ('Usage: data-characteristics.py feature_dir num_pca_features '
               'label_file query_key')
        sys.exit(1)

    # Directory containing one .npy file for each data sample. Filenames are
    # used as keys throughout the rest of processing.
    feature_dir = sys.argv[1]

    # If less than the number of features in the descriptor, we will apply PCA
    # to reduce the dimensionality.
    num_pca_features = int(sys.argv[2])

    # File mapping sample keys (.npy filenames without extension) to labels.
    # Format of each line: "key::label"
    label_file = sys.argv[3]

    # Key for an image that we'd like to know more about.
    query_key = sys.argv[4]
    if query_key == "None":
        query_key = None
    query_idx = None  # Index into sample matrix of the desired query image.

    # Read lables.
    label_map = {}
    with open(label_file) as f:
        for line in f:
            parts = line.strip().split('::')
            if len(parts) != 2:
                print 'Bad label entry: ' + line
                continue
            key = parts[0]
            artist = parts[1]
            if artist not in allowed_artists:
                print 'Unrecognized artist: %s' % artist
                continue
            label_map[key] = allowed_artists[artist]
    print 'Read labels of %i samples' % len(label_map)

    # Read samples.
    N = len(os.listdir(feature_dir))
    print 'Reading descriptors for %i samples' % N
    features = np.zeros((N, max_features))
    labels = np.zeros((N))
    keys = np.full(N, "", dtype=np.object_)
    i = 0
    # TODO: rename features to samples
    for feature_file in os.listdir(feature_dir):
        key = feature_file.split('.')[0]
        if key not in label_map:
            continue
        label = label_map[key]
        keys[i] = key

        feature = None
        ext = feature_file.split('.')[-1]
        if ext == 'ascii':
            feature = np.loadtxt(os.path.join(feature_dir, feature_file))
        else:
            feature = np.load(os.path.join(feature_dir, feature_file))
        if i == 0:
            features = features[:, :feature.shape[0]]
        features[i] = feature
        labels[i] = label
        if key == query_key:
            query_idx = i
        i += 1
        #if i > 5000:
        #    break
    N = i
    print 'After discarding uninteresting samples, %i remain' % N
    features = features[0:N]
    labels = labels[0:N]
    keys = keys[0:N]

    # Apply PCA if requested.
    if num_pca_features < features.shape[1]:
        pca = PCA(n_components=num_pca_features)
        features = pca.fit_transform(features)

    if query_key:
        process_single_image(features, labels, keys, query_idx)
    else:
        compute_class_stats(features, labels, keys)
