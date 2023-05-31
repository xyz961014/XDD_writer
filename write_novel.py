import re
import os
import sys
import argparse
import json
import openai
import random
from tqdm import tqdm
import ipdb
openai.api_key = os.getenv("OPENAI_API_KEY")

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--data_dir", type=str, default="./json_data/with_summary",
                        help="Directory of json data")
    parser.add_argument("--idea", type=str, default="",
                        help="Idea of the novel")

    return parser.parse_args()

def get_chapter_prompts(num_prompts=4):
    assert num_prompts <= len(books)
    chosen_books = random.sample(books, num_prompts)

    prompts = []
    for book in chosen_books:
        chapters = list(book["chapter_summary"].values())
        prompt = {
                "prompt": book["book_summary"]["summary"],
                "completion": [chapter["summary"] for chapter in chapters]
                }
        prompts.append(prompt)

    return prompts

#def get_book_outline_prompts(num_prompts=4):
#    assert num_prompts <= len(books)
#    chosen_books = random.sample(books, num_prompts)
#
#    prompts = []
#    for book in chosen_books:
#        chapters = list(book["chapter_summary"].values())
#        prompt = {
#                "prompt": [chapter["summary"] for chapter in chapters],
#                "completion": book["book_summary"]["text"]
#                }
#        prompts.append(prompt)
#
#    return prompts

def plan_chapters(idea, character_intro, num_chapters=12):
    """
    Input: 
        idea: General idea of the novel
        character_intro: Introduction to characters (500)
        num_chapters: Number of chapters requested

    Few Shot Prompt:
        (
            Book Summary (50)
            chapter Summary (~ 50 * 12)
        ) (~ 650 * 2)

    Output: 
        Outline of each chapter (50 * N)
    """

    chapter_prompts = get_chapter_prompts(1)

    prompt = \
    f"""
    请根据提供的想法构思主人公为许多多的小说的大纲。
    以下是小说的人物介绍: 
{character_intro}

    以下是一个生成的大纲的例子。
    """
    for i_example, chapter_prompt in enumerate(chapter_prompts):
        prompt += \
    f"""
    例{i_example + 1}
        想法: {chapter_prompt["prompt"]}
        输出:
            """
        for i_chapter, chapter_summary in enumerate(chapter_prompt["completion"]):
            prompt += \
            """{}. {}
            """.format(i_chapter + 1, chapter_summary)

    prompt += \
    f"""
    请严格填写以下格式输出{num_chapters}个章节的章节概要, 每段<章节概要>不能超过50字:
    
    大纲:"""
    for i_chapter in range(1, num_chapters + 1):
        prompt += \
    f"""
        {i_chapter}. <章节概要>"""

    prompt += \
    f"""

    请扩展以下想法生成小说的大纲: 
        想法: {idea}
    """

    print(prompt)

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
              "role": "user", 
              "content": prompt
            },
        ]
    )
    response = completion["choices"][0]["message"]["content"]
    print(response)

    chapter_outlines = []
    for content in response.split("\n"):
        if re.search(r"[0-9]+\.", content):
            chapter_outlines.append(content.strip())

    return chapter_outlines


#def plan_book_outline(chapter_outlines):
#    """
#    Input: 
#        chapter_outlines: Outline of the chapters (~ 50 * 12)
#
#    Few Shot Prompt:
#        (
#            Chapter Summary (~ 50 * 12)
#            Book Summary text (~ 600)
#        ) (~ 1200)
#
#    Output: 
#        Outline of each chapter (50 * N)
#        Outline of the book (500)
#    """
#
#    book_outline_prompts = get_book_outline_prompts(1)
#
#    prompt = \
#    f"""
#    请根据提供的大纲生成主人公为许多多的小说的情节概要。
#    """
#    #prompt += \
#    #"""
#    #以下是一个生成的情节概要的例子。
#    #"""
#    #for i_example, book_outline_prompt in enumerate(book_outline_prompts):
#    #    prompt += \
#    #f"""
#    #例{i_example + 1}
#    #    大纲: 
#    #        """
#    #    for i_chapter, chapter_summary in enumerate(book_outline_prompt["prompt"]):
#    #        prompt += \
#    #        """{}. {}
#    #        """.format(i_chapter + 1, chapter_summary)
#    #    prompt += \
#    #    f"""
#    #    输出: 
#    #        {book_outline_prompt["completion"]}
#    #        """
#
#    prompt += \
#    f"""
#    请严格填写以下格式输出小说的情节概要, <小说概要>约500字:
#    """
#    prompt += \
#    """
#    小说概要: 
#        <小说概要>
#    """
#
#    prompt += \
#    f"""
#    请扩展以下大纲生成小说的情节概要: 
#    """
#    for chapter_outline in chapter_outlines:
#        prompt += \
#    f"""
#        {chapter_outline}"""
#
#
#    print(prompt)
#    print(len(prompt))
#
#    completion = openai.ChatCompletion.create(
#        model="gpt-3.5-turbo",
#        messages=[
#            {
#              "role": "user", 
#              "content": prompt
#            },
#        ]
#    )
#    response = completion["choices"][0]["message"]["content"]
#    print(response)
#
#    book_outline = ""
#    book_outline_status = False
#    for content in response.split("\n"):
#        if re.search(r"小说概要", content):
#            book_outline_status = True
#            continue
#        if book_outline_status:
#            book_outline += content.strip()
#
#    return book_outline



def plan_subchapters(chapter_outlines, chapter_outline, recap, num_subchapters=3):
    """
    Input: 
        chapter_outlines: Outline of the all chapters (50 * N)
        chapter_outline: Outline of the chapter to plan (50)
        recap: A long-term memory block summarizing content already planned/written (500)
        num_subchapters: Number of subchapters requested

    Few Shot Prompt:
        (
            Chapter Summary (50)
            Subchapter Summary (~ 50 * 4)
        ) (~ 250 * 4)

    Output: 
        Outline of each subchapter (50)
        Recap of planned content (500)
    """
    pass

def plan_subsubchapters(chapter_outlines, chapter_outline, subchapter_outline, recap, num_subsubchapters=3):
    """
    Input: 
        chapter_outlines: Outline of the all chapters (50 * N)
        chapter_outline: Outline of the chapter (200)
        subchapter_outline: Outline of the subchapter to plan (50)
        recap: A long-term memory block summarizing content already planned/written (500)
        num_subsubchapters: Number of subsubchapters requested

    Few Shot Prompt:
        (
            Subchapter Summary (50)
            Subsubchapter Summary (~ 50 * 4)
        ) (~ 250 * 4)

    Output: 
        Outline of each subsubchapter (50)
        Recap of planned content (500)
    """
    pass

def write_subsubchapter(chapter_outlines, character_intro, recap, last_paragraph, subsubchapter_outline):
    """
    Input: 
        chapter_outlines: Outline of the all chapters (50 * N)
        character_intro: Introduction to characters (500)
        recap: A long-term memory block summarizing content already planned/written (500)
        last_paragraph: Last subsubchapter to continue writing on (500)
        subchapter_outline: Outline of the subsubchapter to write (50)

    Few Shot Prompt:
        (
            Subsubchapter Summary (50)
            Subsubchapter Content (500)
        ) (~ 550 * 2)

    Output: 
        Content of the subsubchapter (500)
        Recap of written content (500)
    """
    pass

def main(args):

    character_intro = "".join(books[3]["character_intro"])

    # Plan chapters
    args.idea = "许多多开始玩动物森友会游戏，他一开始赚了很多钱，但是他逐渐发现并不是所有事情都可以靠钱来解决，单单有钱并没有什么用。"
    #chapter_outlines = plan_chapters(args.idea, character_intro)
    #json.dump(chapter_outlines, open(os.path.join("./json_data/creation", "chapter_outlines.json"), "w"))

    chapter_outlines = json.load(open(os.path.join("./json_data/creation", "chapter_outlines.json"), "r"))

    # Plan subchapters
    recap = "尚未创作任何内容。"
    for chapter_outline in chapter_outlines:
        subchapter_outlines, recap = plan_subchapters(chapter_outlines, chapter_outline, recap)
    ipdb.set_trace()
    pass


if __name__ == "__main__":
    args = parse_args()

    # Load data
    books = []
    for parent, dirnames, filenames in os.walk(args.data_dir):
        for filename in filenames:
            file_path = os.path.join(parent, filename)
            book_data = json.load(open(file_path, "r"))
            books.append(book_data)

    main(args)
