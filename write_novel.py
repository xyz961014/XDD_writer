import re
import os
import sys
import argparse
import json
import openai
import random
import jieba
from tqdm import tqdm
import ipdb

curr_path = os.path.split(os.path.realpath(__file__))[0]
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load data
data_dir = os.path.join(curr_path, "json_data", "with_summary")
books = []
for parent, dirnames, filenames in os.walk(data_dir):
    for filename in filenames:
        file_path = os.path.join(parent, filename)
        book_data = json.load(open(file_path, "r"))
        books.append(book_data)

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--data_dir", type=str, default="./json_data/with_summary",
                        help="Directory of json data")
    parser.add_argument("--idea", type=str, default="",
                        help="Idea of the novel")
    parser.add_argument("--prefix", type=str, default="xdd",
                        help="prefix of the novel files")

    return parser.parse_args()


def split_sentences(text):
    # 使用jieba分词将文本切分成单词
    words = jieba.cut(text, cut_all=False)

    # 根据标点符号将单词划分为句子
    sentences = []
    current_sentence = []
    for word in words:
        current_sentence.append(word)
        if word in ['。', '！', '？', '；', '……']:
            sentences.append(''.join(current_sentence))
            current_sentence = []

    # 处理最后一个句子
    if current_sentence:
        sentences.append(''.join(current_sentence))

    return sentences

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

def get_subchapter_prompts(num_prompts=4):
    subchapter_prompts = []
    for book in books:
        for title, chapter in book["chapter_summary"].items():
            subchapters = [subchapter for subchapter in book["subchapter_summary"].values() 
                           if subchapter["chapter"] == title]
            prompt = {
                    "prompt": chapter["summary"],
                    "completion": [subchapter["summary"] for subchapter in subchapters]
                    }
            subchapter_prompts.append(prompt)

    assert num_prompts <= len(subchapter_prompts)
    prompts = random.sample(subchapter_prompts, num_prompts)

    return prompts

def get_subsubchapter_prompts(num_prompts=4):
    subsubchapter_prompts = []
    for book in books:
        for title, subchapter in book["subchapter_summary"].items():
            subsubchapters = [subsubchapter for subsubchapter in book["texts"]
                              if subsubchapter["chapter"] + " " + subsubchapter["subchapter"] == title]
            prompt = {
                    "prompt": subchapter["summary"],
                    "completion": [subsubchapter["summary"] for subsubchapter in subsubchapters]
                    }
            subsubchapter_prompts.append(prompt)

    assert num_prompts <= len(subsubchapter_prompts)
    prompts = random.sample(subsubchapter_prompts, num_prompts)

    return prompts


def get_writing_prompts(num_prompts=4):
    writing_prompts = []
    for book in books:
        for text in book["texts"]:
            prompt = {
                    "prompt": text["summary"],
                    "completion": text["text"]
                    }
            if len(text["text"]) > 300:
                writing_prompts.append(prompt)

    assert num_prompts <= len(writing_prompts)
    prompts = random.sample(writing_prompts, num_prompts)

    return prompts


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
    请根据提供的想法构思主人公为许多多的小说的大纲, 尽可能设计生动有趣的情节。
    在创作时, 重要的是小说情节的发展, 不要进行说理和总结。
    """
    prompt += \
    f"""
    以下是小说的人物介绍: 
{character_intro}
    """
    prompt += \
    f"""

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

    subchapter_prompts = get_subchapter_prompts(3)

    prompt = \
    f"""
    请根据小说大纲和提供的章节概要扩展章节的子章节的内容概要, 子章节的内容概要需要包括更加丰富的情节, 请尽可能设计生动有趣的情节。
    请参考当前已创作的内容概要, 确保新创作的小说情节和之前已创作的情节之间的发展符合逻辑。
    在创作时, 重要的是小说情节的发展, 不要进行说理和总结。
    """
    prompt += \
    f"""
    以下是一些扩展章节概要输出子章节的内容概要的例子。
    """
    for i_example, subchapter_prompt in enumerate(subchapter_prompts):
        prompt += \
    f"""
    例{i_example + 1}
        章节概要: {subchapter_prompt["prompt"]}
        扩展章节概要:
            """
        for i_subchapter, subchapter_summary in enumerate(subchapter_prompt["completion"]):
            prompt += \
            """{}. {}
            """.format(i_subchapter + 1, subchapter_summary)
    prompt += \
    f"""
    请参考以下信息进行输出: 
    """

    prompt += \
    """
    小说大纲:"""
    for outline in chapter_outlines:
        prompt += \
    f"""
        {outline}"""

    prompt += \
    f"""

    当前已创作的内容概要:
        {recap}
    """

    prompt += \
    f"""
    请严格填写以下格式输出{num_subchapters}个子章节的子章节概要: 每段<子章节概要>约50字;
    
    扩展章节概要:"""
    for i_subchapter in range(1, num_subchapters + 1):
        prompt += \
    f"""
        {i_subchapter}. <子章节概要>"""

    prompt += \
    f"""

    请扩展以下章节概要生成{num_subchapters}个子章节概要: 
        章节概要:
            {chapter_outline}
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

    subchapter_outlines = []
    for content in response.split("\n"):
        if re.search(r"[0-9\.]+", content):
            subchapter_outlines.append(content.strip())

    prompt = \
    f"""
    请用一段文本概括当前已创作的内容概要和新扩展的章节概要, 生成新的当前已创作的内容概要, 请包含尽可能多的情节,  不超过500字。
    请严格按照以下输出格式输出: <内容概要>严格不超过500字;

    输出格式:
        新的当前已创作的内容概要:
            <内容概要>

    输入如下:
        当前已创作的内容概要:
            {recap}
        新扩展的章节概要:"""
    for subchapter_outline in subchapter_outlines:
        prompt += \
    f"""
            {subchapter_outline}"""

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

    new_recap = ""
    for content in response.split("\n"):
        if re.search(r"新的当前已创作的内容概要", content):
            new_recap += content.strip()[13:]
            continue

        new_recap += content.strip()
        if len(new_recap) > 500:
            break

    return subchapter_outlines, new_recap


def plan_subsubchapters(chapter_outlines, subchapter_outlines, subchapter_outline, recap, num_subsubchapters=3):
    """
    Input: 
        chapter_outlines: Outline of the all chapters (50 * N)
        subchapter_outlines: Outline of all subchapter in the chapter (50 * M)
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

    subsubchapter_prompts = get_subsubchapter_prompts(2)

    prompt = \
    f"""
    请根据小说的子章节概要和提供的其他信息扩展子章节的各个段落的段落概要, 段落概要需要包括更加具体的情节, 请尽可能设计生动有趣的情节。
    请参考当前已创作的内容概要, 确保新创作的小说情节和之前已创作的情节之间的发展符合逻辑。
    在创作时, 重要的是推动小说情节的发展, 不要说理和总结, 不要描述人物的感想和收获。
    """
    prompt += \
    f"""
    以下是一些扩展子章节概要输出子章节段落的内容概要的例子。
    """
    for i_example, subsubchapter_prompt in enumerate(subsubchapter_prompts):
        prompt += \
    f"""
    例{i_example + 1}
        子章节概要: {subsubchapter_prompt["prompt"]}
        段落概要:
            """
        for i_subsubchapter, subsubchapter_summary in enumerate(subsubchapter_prompt["completion"]):
            prompt += \
            """{}. {}
            """.format(i_subsubchapter + 1, subsubchapter_summary)
    prompt += \
    f"""
    请参考以下信息进行输出: 
    """
    prompt += \
    """
    小说大纲:"""
    for outline in chapter_outlines:
        prompt += \
    f"""
        {outline}"""
    prompt += \
    """

    当前章节概要:"""
    for outline in subchapter_outlines:
        prompt += \
    f"""
        {outline}"""
    prompt += \
    f"""

    当前已创作的内容概要:
        {recap}
    """

    prompt += \
    f"""
    请严格按照以下格式输出子章节的{num_subsubchapters}个段落的段落概要: 每段<段落概要>约50字;
    
    段落概要:"""
    for i_subsubchapter in range(1, num_subsubchapters + 1):
        prompt += \
    f"""
        {i_subsubchapter}. <段落概要>"""

    prompt += \
    f"""
    请扩展以下子章节概要生成子章节段落概要, 注意使用给定的格式进行输出: 
        子章节概要:
            {subchapter_outline}
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

    subsubchapter_outlines = []
    for content in response.split("\n"):
        if re.search(r"[0-9\.]+", content):
            subsubchapter_outlines.append(content.strip())

    prompt = \
    f"""
    请用一段文本合并概括当前已创作的内容概要和新扩展的段落概要, 生成新的当前已创作的内容概要, 请包含尽可能多的情节, 不超过500字。
    请严格按照以下输出格式输出: <内容概要>严格不超过500字;

    输出格式:
        新的当前已创作的内容概要:
            <内容概要>

    输入如下:
        当前已创作的内容概要:
            {recap}
        新扩展的段落概要:"""
    for subsubchapter_outline in subsubchapter_outlines:
        prompt += \
    f"""
            {subsubchapter_outline}"""

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

    new_recap = ""
    for content in response.split("\n"):
        if re.search(r"新的当前已创作的内容概要", content):
            new_recap += content.strip()[13:]
            continue

        new_recap += content.strip()
        if len(new_recap) > 500:
            break

    return subsubchapter_outlines, new_recap


def write_subsubchapter(chapter_outlines, character_intro, recap, last_paragraph, subsubchapter_outline):
    """
    Input: 
        chapter_outlines: Outline of the all chapters (50 * N)
        character_intro: Introduction to characters (500)
        recap: A long-term memory block summarizing content already planned/written (500)
        last_paragraph: Last subsubchapter to continue writing on (500)
        subsubchapter_outline: Outline of the subsubchapter to write (50)

    Few Shot Prompt:
        (
            Subsubchapter Summary (50)
            Subsubchapter Content (500)
        ) (~ 550 * 1)

    Output: 
        Content of the subsubchapter (500)
        Recap of written content (500)
    """

    writing_prompts = get_writing_prompts(1)

    if len(last_paragraph) > 500:
        sentences = split_sentences(last_paragraph)

        shorter_text = ""
        for i in range(len(sentences) - 1, -1, -1):
            sentence = sentences[i]
            if len(shorter_text) + len(sentence) < 500:
                shorter_text = sentence + shorter_text
        last_paragraph = shorter_text

    prompt = \
    f"""
    请创作主人公为小学生许多多的小说。
    请根据小说的段落概要和提供的其他信息使用生动的文字完成段落的创作, 创作时不用拘泥于段落概要的内容, 尽可能创造生动有趣的情节。
    在创作时请接着创作段落的上一段落续写, 保证段落之间的流畅性。在小说创作时, 重要的是推动小说情节的发展, 不要说理和总结, 不要描述人物的感想和收获。
    请参考当前已创作的内容概要, 在保证段落之间流畅性的同时，确保全文情节发展符合逻辑。
    """
    prompt += \
    f"""
    以下是根据段落概要创作段落内容的例子, 请模仿语言风格并参考人物性格。
    """
    for i_example, writing_prompt in enumerate(writing_prompts):
        prompt += \
    f"""
    例子
        段落概要: 
            {writing_prompt["prompt"]}
        段落内容:
            {writing_prompt["completion"]}
    """
    prompt += \
    f"""
    请参考以下信息进行输出: 
    """
    #prompt += \
    #"""
    #小说大纲:"""
    #for outline in chapter_outlines:
    #    prompt += \
    #f"""
    #    {outline}"""

    prompt += \
    f"""

    小说的人物介绍: 
        {character_intro}
    """

    prompt += \
    f"""
    当前已创作的内容概要:
        {recap}
    """

    prompt += \
    f"""
    请严格按照以下输出格式输出段落内容和当前已创作的内容概要: <段落内容>严格不超过500字;
   
    输出格式:
        段落内容:
            <段落内容>
    """

    prompt += \
    f"""
    请根据段落概要在上一段落后续写创作情节丰富的小说段落内容, 请直接在<段落内容>中生成新的情节内容，不要拷贝上一段落。
    段落内容的语言风格必须完全模仿之前给出的例子, 请通过对话等方式发展小说情节, 不描述人物的感想和收获, 不描述事件造成的影响, 不对情节进行总结和升华。
    输入如下, 请严格使用以上给定的输出格式进行输出: 
        续写上一段落: 
            {last_paragraph}
        段落概要: 
            {subsubchapter_outline}
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

    new_text = ""
    for content in response.split("\n"):
        if re.search(r"段落内容", content):
            new_text += content[5:]
            continue

        if re.search(r"续写上一段落", content):
            new_text += content[7:]
            continue

        new_text += content
        if len(new_text) > 500:
            break

    prompt = \
    f"""
    请概括当前已创作的内容概要, 上一段落和当前段落生成新的当前已创作的内容概要, 请包含尽可能多的情节, 不超过500字。
    请严格按照以下输出格式输出: <内容概要>严格不超过500字;

    输出格式:
        新的当前已创作的内容概要:
            <内容概要>

    输入如下:
        当前已创作的内容概要:
            {recap}
        上一段落:
            {last_paragraph}
        当前段落:
            {new_text}
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

    new_recap = ""
    for content in response.split("\n"):
        if re.search(r"新的当前已创作的内容概要", content):
            new_recap += content.strip()[13:]
            continue

        new_recap += content.strip()
        if len(new_recap) > 500:
            break

    if len(new_recap) > 500:
        prompt = \
        f"""
        请用不超过500字概括出新的当前已创作的内容概要，包含尽可能多的情节。
        请严格按照以下输出格式输出: <内容概要>严格不超过500字;

        输出格式:
            新的当前已创作的内容概要:
                <内容概要>

        输入如下:
            当前已创作的内容概要:
                {new_recap}
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

        new_recap = ""
        for content in response.split("\n"):
            if re.search(r"新的当前已创作的内容概要", content):
                new_recap += content.strip()[13:]
                continue

            new_recap += content.strip()
            if len(new_recap) > 500:
                break

    return new_text, new_recap


def get_character_intro():
    character_intro = "".join(books[3]["character_intro"])
    return character_intro

def main(args):

    character_intro = get_character_intro()

    #####################################################
    # Plan chapters
    #####################################################
    args.idea = "许多多开始玩动物森友会游戏，他一开始赚了很多钱，但是他逐渐发现并不是所有事情都可以靠钱来解决，单单有钱并没有什么用。"
    chapter_outlines_filename = os.path.join("./json_data/creation", "{}_chapter_outlines.json".format(args.prefix))
    if os.path.exists(chapter_outlines_filename):
        chapter_outlines = json.load(open(chapter_outlines_filename, "r"))
    else:
        chapter_outlines = plan_chapters(args.idea, character_intro)
        json.dump(chapter_outlines, open(chapter_outlines_filename, "w"))


    #####################################################
    # Plan subchapters
    #####################################################
    subchapters_filename = os.path.join("./json_data/creation", "{}_subchapters.json".format(args.prefix))
    if os.path.exists(subchapters_filename):
        subchapters = json.load(open(subchapters_filename, "r"))
        recap = subchapters["recap"]
    else:
        subchapters = {}
        recap = "无内容。"
    for chapter_outline in chapter_outlines:
        if not chapter_outline in subchapters.keys():
            subchapter_outlines, recap = plan_subchapters(chapter_outlines, chapter_outline, recap)
            subchapters[chapter_outline] = subchapter_outlines
            subchapters["recap"] = recap
            json.dump(subchapters, open(subchapters_filename, "w"))

    #####################################################
    # Plan subsubchapters
    #####################################################
    subsubchapters_filename = os.path.join("./json_data/creation", "{}_subsubchapters.json".format(args.prefix))
    if os.path.exists(subsubchapters_filename):
        subsubchapters = json.load(open(subsubchapters_filename, "r"))
        recap = subsubchapters["recap"]
    else:
        subsubchapters = {}
        recap = "无内容。"
    for chapter_outline in chapter_outlines:
        for subchapter_outline in subchapters[chapter_outline]:
            key = chapter_outline + subchapter_outline
            if not key in subsubchapters.keys():
                subsubchapter_outlines, recap = plan_subsubchapters(chapter_outlines, 
                                                                    subchapters[chapter_outline], 
                                                                    subchapter_outline,
                                                                    recap)
                subsubchapters[key] = subsubchapter_outlines
                subsubchapters["recap"] = recap
                json.dump(subsubchapters, open(subsubchapters_filename, "w"))

    #####################################################
    # Final writing
    #####################################################
    writing_texts_filename = os.path.join("./json_data/creation", "{}_writing_texts.json".format(args.prefix))
    if os.path.exists(writing_texts_filename):
        writing_texts = json.load(open(writing_texts_filename, "r"))
        recap = writing_texts["recap"]
        last_paragraph = writing_texts["last_paragraph"]
    else:
        writing_texts = {}
        recap = "无内容。"
        last_paragraph = "无内容。"
    for chapter_outline in chapter_outlines:
        for subchapter_outline in subchapters[chapter_outline]:
            key = chapter_outline + subchapter_outline
            for subsubchapter_outline in subsubchapters[key]:
                text_key = key + subsubchapter_outline
                if not text_key in writing_texts.keys():
                    text, recap = write_subsubchapter(chapter_outlines, 
                                                      character_intro,
                                                      recap,
                                                      last_paragraph,
                                                      subsubchapter_outline)
                    last_paragraph = text
                    writing_texts[text_key] = text
                    writing_texts["last_paragraph"] = last_paragraph
                    writing_texts["recap"] = recap
                    json.dump(writing_texts, open(writing_texts_filename, "w"))


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
