import re
import os
import sys
import argparse
import json
import openai
import random
from tqdm import tqdm
import ipdb

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--data_dir", type=str, default="./json_data/creation",
                        help="Directory of json data")
    parser.add_argument("--prefix", type=str, default="",
                        help="prefix of the novel files")
    parser.add_argument("--output", type=str, default="output.txt",
                        help="output file name")

    return parser.parse_args()

def main(args):

    chapter_outlines_filename = os.path.join(args.data_dir, "{}chapter_outlines.json".format(args.prefix))
    subchapters_filename = os.path.join(args.data_dir, "{}subchapters.json".format(args.prefix))
    subsubchapters_filename = os.path.join(args.data_dir, "{}subsubchapters.json".format(args.prefix))
    writing_texts_filename = os.path.join(args.data_dir, "{}writing_texts.json".format(args.prefix))

    output_filename = os.path.join(args.data_dir, "{}{}".format(args.prefix, args.output))

    chapter_outlines = json.load(open(chapter_outlines_filename, "r"))
    subchapters = json.load(open(subchapters_filename, "r"))
    subsubchapters = json.load(open(subsubchapters_filename, "r"))
    writing_texts = json.load(open(writing_texts_filename, "r"))

    with open(output_filename, "w") as f:
        # 目录
        f.write("大纲\n")
        for chapter_outline in chapter_outlines:
            f.write(chapter_outline + "\n")
        f.write("\n")
        # 内容
        for i_chapter, chapter_outline in enumerate(chapter_outlines):
            f.write("\n")
            f.write("{}. ".format(i_chapter + 1))
            f.write("\n")
            if not chapter_outline in subchapters.keys():
                continue
            for i_subchapter, subchapter_outline in enumerate(subchapters[chapter_outline]):
                f.write("\n")
                f.write("({})".format(i_subchapter + 1))
                f.write("\n\n")
                key = chapter_outline + subchapter_outline
                if not key in subsubchapters.keys():
                    continue
                for subsubchapter_outline in subsubchapters[key]:
                    text_key = key + subsubchapter_outline
                    if not text_key in writing_texts.keys():
                        continue
                    text = writing_texts[text_key]
                    if re.search(r"续写上一段落", text):
                        text = text.strip()[7:]
                    f.write(text)
                    f.write("\n")

if __name__ == "__main__":
    args = parse_args()
    main(args)
