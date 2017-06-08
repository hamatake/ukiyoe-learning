import io
import json
import operator
import os
import sys

if __name__ == '__main__':
    infile = sys.argv[1]
    outfile = sys.argv[2]

    with io.open(outfile, 'w', encoding='utf-8') as out:
        with io.open(infile, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                artist = data['artist']

                img = data['images']
                if img:
                    img = img[0]['path']
                if not img:
                    continue

                checksum = os.path.basename(img).split('.')[0]
                out.write('%s::%s\n' % (checksum, artist))
