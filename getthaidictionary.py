import os
from pathlib import Path

from pythainlp.corpus import download, get_corpus_path

source_file_name = "/pythainlp-data/thai_dictionary_v1.0.csv"
destinationfile = "/opt/pycharmProjects/PythonProject/Thai/thai_dictionary_v1.0.csv"


def fetchthai_dictionary():
    print(get_corpus_path('thai_dict'))
    # output: None

    download('thai_dict')
    # output:
    # Download: wiki_lm_lstm
    # wiki_lm_lstm 0.32
    # thwiki_lm.pth?dl=1: 1.05GB [00:25, 41.5MB/s]
    # /root/pythainlp-data/thwiki_model_lstm.pth

    print(get_corpus_path('thai_dict'))

    # Define source file path and target directory
    home_dir = str(Path.home())
    source_file = home_dir + source_file_name

    # 1. Ensure the destination directory exists

    if os.path.exists(destinationfile):
        os.remove(destinationfile)
    # 2. Move the file
    os.replace(source_file, destinationfile)


def fetchthai_words():
    thaiwords = []
    fetchthai_dictionary()

    with open(destinationfile, 'r+t', encoding='utf-8') as fh:
        lines = fh.readlines()
        fh.seek(0)
        ct = 0
        first = True
        for line in lines:
            if first:
                first = False
                continue
            word, definition = line.split(',', 1)
            # print("WORD:", word)
            thaiwords.append(word)
            ct += 1

        print("Total Count of words:", ct)
    return thaiwords


if __name__ == '__main__':
    fetchthai_words()
