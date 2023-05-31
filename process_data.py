from docx import Document
from docx.shared import Pt
import re
import os
import sys
import argparse
import json
from tqdm import tqdm
from pypinyin import pinyin, Style
import ipdb

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--data_dir", type=str, default="./data",
                        help="Directory of data doc")

    return parser.parse_args()

def construct_data(doc):
    
    book_name = None

    character_intro = []
    character_intro_status = False

    chapters = {}
    chapter_status = False

    main_text_status = False
    current_chapter = None
    current_subchapter = ""
    current_subsubchapter = 0
    current_text = ""
    main_texts = []

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()

        # 获取书名
        if book_name is None and re.match(r"^《.*》$", text):
            book_name = text

        # 人物介绍
        if text == "人物介绍":
            character_intro_status = True
            character_text = ""
            continue

        if character_intro_status:
            if text != "":
                character_text += text + "\n"
            else:
                if character_text != "":
                    character_intro.append(character_text)
                    character_text = ""

        # 目  录
        if text == "目  录":
            character_intro_status = False
            chapter_status = True
            continue

        if chapter_status:
            if re.match(r"[零一二三四五六七八九十百千万亿]+、", text):
                re_res = re.match(r"[零一二三四五六七八九十百千万亿]+、", text)
                chapter_num = text[re_res.start(): re_res.end()]
                chapters[chapter_num] = text
            if text == "尾声":
                chapters[text] = text
                chapter_status = False
                main_text_status = True
                continue



        # 正文
        if main_text_status:
            if re.search(r"[零一二三四五六七八九十百千万亿]+、", text):
                re_res = re.search(r"[零一二三四五六七八九十百千万亿]+、", text)
                chapter_num = text[re_res.start(): re_res.end()]
                if chapter_num in chapters.keys():

                    if len(current_text.strip()) > 0:
                        text_obj = {
                                "chapter": current_chapter,
                                "subchapter": current_subchapter,
                                "subsubchapter": current_subsubchapter,
                                "text": current_text
                                }
                        main_texts.append(text_obj)
                        current_text = ""

                    current_chapter = chapters[chapter_num]
                    current_subchapter = ""
                    current_subsubchapter = 0
                    continue
            if text == "尾声":

                if len(current_text.strip()) > 0:
                    text_obj = {
                            "chapter": current_chapter,
                            "subchapter": current_subchapter,
                            "subsubchapter": current_subsubchapter,
                            "text": current_text
                            }
                    main_texts.append(text_obj)
                    current_text = ""

                current_chapter = "尾声"
                current_subchapter = ""
                current_subsubchapter = 0
                continue

            if re.match(r"^[(（].*[)）]$", text):

                if len(current_text.strip()) > 0:
                    text_obj = {
                            "chapter": current_chapter,
                            "subchapter": current_subchapter,
                            "subsubchapter": current_subsubchapter,
                            "text": current_text
                            }
                    main_texts.append(text_obj)
                    current_text = ""

                current_subchapter = text
                current_subsubchapter = 0
                continue

            current_text += text + "\n"
            if len(current_text.strip()) > 500:
                text_obj = {
                        "chapter": current_chapter,
                        "subchapter": current_subchapter,
                        "subsubchapter": current_subsubchapter,
                        "text": current_text
                        }
                main_texts.append(text_obj)
                current_text = ""
                current_subsubchapter += 1
    book_data = {
            "book_name": book_name,
            "character_intro": character_intro,
            "chapters": chapters,
            "texts": main_texts
            }

    book_name_pinyin = pinyin(book_name, style=Style.NORMAL)
    book_name_pinyin = "".join([c[0] for c in book_name_pinyin])
    json_filename = os.path.join("./json_data/raw", re.sub(r'[^a-z]', '', book_name_pinyin) + ".json")
    json.dump(book_data, open(json_filename, "w"), indent=4)

def main(args):

    for parent, dirnames, filenames in os.walk(args.data_dir):
        for filename in filenames:
            if filename.startswith(".~"):
                continue
            file_path = os.path.join(parent, filename)
            doc = Document(file_path)
            construct_data(doc)


if __name__ == "__main__":
    args = parse_args()
    main(args)
