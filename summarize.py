import re
import os
import sys
import argparse
import json
import openai
from tqdm import tqdm
import ipdb
openai.api_key = os.getenv("OPENAI_API_KEY")


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--data_dir", type=str, default="./json_data/with_summary",
                        help="Directory of json data")
    parser.add_argument("--func", type=str, default="summarize",
                        choices=["summarize", "summarize_subchapter", "summarize_chapter", "summarize_book"],
                        help="Function to choose")

    return parser.parse_args()

def summarize(book_data, filename):
    json_filename = os.path.join("./json_data/with_summary", filename)

    for i, text in enumerate(tqdm(book_data["texts"])):
        if not "summary" in text.keys():
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                      "role": "user", 
                      "content": text["text"]
                    },
                    {
                      "role": "user", 
                      "content": "总结以上段落, 50字左右"
                    },
                ]
            )
            book_data["texts"][i]["summary"] = completion["choices"][0]["message"]["content"]
            tqdm.write(completion["choices"][0]["message"]["content"])
            json.dump(book_data, open(json_filename, "w"), indent=4)


def summarize_subchapter(book_data, filename):
    json_filename = os.path.join("./json_data/with_summary", filename)

    if not "subchapter_summary" in book_data.keys():
        book_data["subchapter_summary"] = {}
        for text in book_data["texts"]:
            subchapter_title = "{} {}".format(text["chapter"], text["subchapter"])
            if subchapter_title not in book_data["subchapter_summary"].keys():
                book_data["subchapter_summary"][subchapter_title] = {
                        "chapter": text["chapter"],
                        "subchapter": text["subchapter"],
                        "text": "",
                        "raw_text": ""
                        }
            book_data["subchapter_summary"][subchapter_title]["text"] += text["summary"]
            book_data["subchapter_summary"][subchapter_title]["raw_text"] += text["text"]

    for i, (title, subchapter) in enumerate(tqdm(book_data["subchapter_summary"].items())):
        if not "summary" in subchapter.keys():
            if len(subchapter["raw_text"]) > 4000:
                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                          "role": "user", 
                          "content": subchapter["text"]
                        },
                        {
                          "role": "user", 
                          "content": "将上文改得更为流畅"
                        },
                    ]
                )
                book_data["subchapter_summary"][title]["text"] = completion["choices"][0]["message"]["content"]
                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                          "role": "user", 
                          "content": completion["choices"][0]["message"]["content"]
                        },
                        {
                          "role": "user", 
                          "content": "总结以上段落, 50字左右"
                        },
                    ]
                )
            else:
                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                          "role": "user", 
                          "content": subchapter["raw_text"]
                        },
                        {
                          "role": "user", 
                          "content": "总结以上段落, 50字左右"
                        },
                    ]
                )
            book_data["subchapter_summary"][title]["summary"] = completion["choices"][0]["message"]["content"]
            tqdm.write(completion["choices"][0]["message"]["content"])
            json.dump(book_data, open(json_filename, "w"), indent=4)


def summarize_chapter(book_data, filename):
    json_filename = os.path.join("./json_data/with_summary", filename)

    if not "chapter_summary" in book_data.keys():
        book_data["chapter_summary"] = {}
        for text in book_data["texts"]:
            if text["chapter"] not in book_data["chapter_summary"].keys():
                book_data["chapter_summary"][text["chapter"]] = {
                        "chapter": text["chapter"],
                        "text": ""
                        }
            book_data["chapter_summary"][text["chapter"]]["text"] += text["summary"]

    for i, (title, chapter) in enumerate(tqdm(book_data["chapter_summary"].items())):
        if not "summary" in chapter.keys():
            #completion = openai.ChatCompletion.create(
            #    model="gpt-3.5-turbo",
            #    messages=[
            #        {
            #          "role": "user", 
            #          "content": chapter["text"]
            #        },
            #        {
            #          "role": "user", 
            #          "content": "将上文改得更为流畅"
            #        },
            #    ]
            #)
            #book_data["chapter_summary"][title]["text"] = completion["choices"][0]["message"]["content"]
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                      "role": "user", 
                      "content": chapter["text"]
                    },
                    {
                      "role": "user", 
                      "content": "总结以上小说段落的情节, 50字左右"
                    },
                ]
            )
            book_data["chapter_summary"][title]["summary"] = completion["choices"][0]["message"]["content"]
            tqdm.write(completion["choices"][0]["message"]["content"])
            json.dump(book_data, open(json_filename, "w"), indent=4)



def summarize_book(book_data, filename):
    json_filename = os.path.join("./json_data/with_summary", filename)

    if not "book_summary" in book_data.keys():
        book_data["book_summary"] = {
                "text": ""
                }
        for i, (title, chapter) in enumerate(book_data["chapter_summary"].items()):
            book_data["book_summary"]["text"] += chapter["summary"]

    if not "summary" in book_data["book_summary"].keys() or True:
        #completion = openai.ChatCompletion.create(
        #    model="gpt-3.5-turbo",
        #    messages=[
        #        {
        #          "role": "user", 
        #          "content": book_data["book_summary"]["text"]
        #        },
        #        {
        #          "role": "user", 
        #          "content": "将上文改得更为流畅"
        #        },
        #    ]
        #)
        #print(completion["choices"][0]["message"]["content"])
        #book_data["book_summary"]["text"] = completion["choices"][0]["message"]["content"]
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                  "role": "user", 
                  "content": book_data["book_summary"]["text"]
                },
                {
                  "role": "user", 
                  "content": "描述小说的情节发展, 100字左右"
                },
            ]
        )
        book_data["book_summary"]["summary"] = completion["choices"][0]["message"]["content"]
        print(completion["choices"][0]["message"]["content"])
        json.dump(book_data, open(json_filename, "w"), indent=4)



def main(args):
    for parent, dirnames, filenames in os.walk(args.data_dir):
        for filename in filenames:
            file_path = os.path.join(parent, filename)
            book_data = json.load(open(file_path, "r"))
            if args.func == "summarize":
                summarize(book_data, filename)
            elif args.func == "summarize_subchapter":
                summarize_subchapter(book_data, filename)
            elif args.func == "summarize_chapter":
                summarize_chapter(book_data, filename)
            elif args.func == "summarize_book":
                summarize_book(book_data, filename)


if __name__ == "__main__":
    args = parse_args()
    main(args)
