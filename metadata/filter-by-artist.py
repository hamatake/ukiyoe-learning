import io
import json
import operator
import os
import sys

allowed_artists = {
    u'Utagawa Kunisada I (Toyokuni III)': 0,
    u'Utagawa Hiroshige I': 1,
    u'Utagawa Kuniyoshi': 2,
    u'Katsushika Hokusai': 3,
    u'Utagawa Toyokuni I': 4,
    u'Kitagawa Utamaro I': 5,
    u'Katsukawa Shunsh\xf4': 6,
    u'Utagawa Hiroshige II (Shigenobu)': 7,
    u'Toyohara Kunichika': 8,
    u'Torii Kiyonaga': 9,
    u'Utagawa Kunisada II (Kunimasa III, Toyokuni IV)': 10,
    u'Suzuki Harunobu': 11,
    u'Isoda Kory\xfbsai': 12,
    u'Tsukioka Yoshitoshi': 13,
    u'Kawase Hasui': 14,
}


if __name__ == '__main__':
    infile = sys.argv[1]  # json lines
    outfile = sys.argv[2]  # json lines

    with io.open(outfile, 'w', encoding='utf-8') as out:
        with io.open(infile, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                artist = data['artist']
                if artist in allowed_artists:
                    out.write(line)
