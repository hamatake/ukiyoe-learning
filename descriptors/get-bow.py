import numpy as np
import os
import sys

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print 'Usage: get-bow codeword_dict input_feat_dir file_prefix output_desc_dir'
        sys.exit(1)

    # Location of dictionary file. Should be .npz format, with arr_0 containing
    # and n x m array of n codewords, each with m dimensions.
    codeword_dict_file = sys.argv[1]

    # Directory containing one .npz file per sample. Each sample may consist of
    # many keypoints; initial data before the actual features will be ignored.
    input_feat_dir = sys.argv[2]

    # Skip input files that don't start with this prefix.
    file_prefix = sys.argv[3]

    # Directory to output the bag of words models, one .npy file per sample.
    # The file will contain an uncompressed array of n dimensions, where n is
    # the number of codewords in the dictionary, and array values are counts of
    # occurences of each codeword in the sample.
    output_desc_dir = sys.argv[4]

    # Load codeword dictionary.
    npz = np.load(codeword_dict_file)
    codeword_dict = npz['arr_0']
    npz.close()
    num_codewords = codeword_dict.shape[0]
    num_dimensions = codeword_dict.shape[1]
    print 'Loaded %i codewords, %i dimensions' % (num_codewords, num_dimensions)

    # Process each sample.
    for sample_file in os.listdir(input_feat_dir):
        key = sample_file.split('.')[0]
        if not key.startswith(file_prefix):
            continue
        outfile_name = os.path.join(output_desc_dir, key + '.npy')
        if os.path.isfile(outfile_name):
            print 'Not recomputing %s' % key
            continue

        try:
            npz = np.load(os.path.join(input_feat_dir, sample_file))
            # Ignore the first dimensions, as they're keypoint data, not featues.
            sample = npz['arr_0'][:, -num_dimensions:]
            num_kps = sample.shape[0]
            npz.close()
        except:
            print 'Error processing %s' % key
            continue
        print 'Processing %s' % key

        # Find each keypoint's nearest neighbor in the dictionary, and add
        # contribution to histogram.
        # TODO: experiment with weighting by keypoint attributes.
        histogram = np.zeros((num_codewords))
        for kp in sample:
            diff = codeword_dict - kp
            dist = [0] * num_codewords
            for i in range(num_codewords):
                dist[i] = np.linalg.norm(diff[i])
            closest = np.argsort(dist)[0]
            histogram[closest] += 1

        # Write out the histogram as our descriptor.
        np.save(outfile_name, histogram)
