# -*- coding: utf-8 -*-

import csv
import datetime
import numpy as np
import os
from sklearn import svm
from sklearn.decomposition import PCA
from sklearn.externals import joblib
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import cross_val_predict
from sklearn.model_selection import train_test_split
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import StratifiedKFold
import sys

# TODO: try different scoring fuction

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

artist_count = {}

max_features = 3000

if __name__ == '__main__':
    if len(sys.argv) != 8:
        print ('Usage: two-artist-svm.py FIT|TEST feature_dir label_file '
              'num_pca_features train_percent model_file feature_labels')
        sys.exit(1)

    # If FIT, we still test as well, then write model to file. If TEST, we read
    # model from file then test instead of fitting.
    command = sys.argv[1]
    if command != 'FIT' and command != 'LOAD':
        print 'Command must be FIT or LOAD'
        sys.exit(1)

    # Directory containing one .npy file for each data sample. Filenames are
    # used as keys throughout the rest of processing.
    feature_dir = sys.argv[2]

    # File mapping sample keys (.npy filenames without extension) to labels.
    # Format of each line: "key::label"
    label_file = sys.argv[3]

    # Number of features desired after PCA.
    num_pca_features = int(sys.argv[4])

    # Percentage of data to use for training. The rest will be used for testing.
    train_percent = float(sys.argv[5])

    # Persist the trained model to this pickle file.
    model_file = sys.argv[6]

    # Optional file containing human-readable names for each feature (descriptor
    # dimension). Will be used to prettify output. Doesn't work with PCA.
    feature_name_file = sys.argv[7]

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
    labels = [0] * N
    i = 0
    # TODO: rename features to samples
    for feature_file in os.listdir(feature_dir):
        key = feature_file.split('.')[0]
        if key not in label_map:
            continue
        label = label_map[key]

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
        i += 1
        #if i > 1000:
        #    break
    N = i
    print 'After discarding uninteresting samples, %i remain' % N
    features = features[0:N]
    labels = labels[0:N]

    # Reduce dimensionality via PCA.
    feature_names = None
    if num_pca_features < features.shape[1]:
        pca = PCA(n_components=num_pca_features)
        features = pca.fit_transform(features)
    else:
        with open(feature_name_file) as infile:
            feature_names = []
            for row in infile:
                feature_names.append(row.split('\t')[0])
    print features.shape

    # Compute train / test boundary.
    features_train, features_test, labels_train, labels_test = train_test_split(
        features, labels, test_size=(1-train_percent), random_state=0)
    num_train = features_train.shape[0]
    num_test = features_test.shape[0]
    print 'Using %i training, %i testing points' % (num_train, num_test)

    classifier = None
    if command == 'FIT':
        print datetime.datetime.now()

        # Tune C hyperparam via 3-fold cross-validation.
        C_range = np.logspace(-2, 10, 13)
        param_grid = dict(C=C_range)
        grid = GridSearchCV(svm.LinearSVC(class_weight='balanced'), param_grid=param_grid)
        grid.fit(features_train, labels_train)
        print 'Learned C: '
        print grid.best_params_
        classifier = grid.best_estimator_

        # Learn svm from training samples.
        #manual_C = 1.0
        #print 'Using C=%f' % manual_C
        #classifier = svm.LinearSVC(C=manual_C, class_weight='balanced')
        #classifier.fit(features_train, labels_train)
        #print 'Learned classifier'

        print datetime.datetime.now()
        joblib.dump(classifier, model_file)
    else:
        classifier = joblib.load(model_file)

    # Evaluate on test data.
    results = classifier.predict(features_test)
    confusion = confusion_matrix(labels_test, results)
    num_correct = np.diagonal(confusion).sum()
    confusion = confusion.astype(float)
    for i in range(confusion.shape[0]):
        if np.count_nonzero(confusion[i]):
            confusion[i] /= confusion[i].sum()
    print 'Got %i correct (%f)' % (num_correct, float(num_correct) / num_test)
    print 'Confusion:'
    print confusion
    print 'Accuracy: %f' % np.diagonal(confusion).mean()

    # Extract highest-weighted (positive & negative) features in descriptor.
    for weights in classifier.coef_:
        magnitudes = np.abs(weights)
        max_idx = np.argsort(magnitudes)[::-1][0:5]
        output = []
        for idx in max_idx:
            output.append('%i (%s): %f' % (idx, feature_names[idx], weights[idx]))
        print output
