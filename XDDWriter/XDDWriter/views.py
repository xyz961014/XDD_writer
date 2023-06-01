from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db.models import F, Q
import os
import sys
import re
import json
import time


curr_path = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(os.path.join(curr_path, "../.."))
import write_novel
#from write_novel import plan_chapters, plan_subchapters, plan_subsubchapters, write_subsubchapter, get_character_intro

def index(request):
    html_data = {
            "character_intro": write_novel.get_character_intro(),
            "idea": "许多多开始玩动物森友会游戏，他一开始赚了很多钱，但是他逐渐发现并不是所有事情都可以靠钱来解决，单单有钱并没有什么用。",
            }
    return render(request, "index.html", html_data)


def plan_chapters(request):
    idea = request.POST.get("idea", "无")
    character_intro = request.POST.get("character_intro", "无")
    num_chapters = request.POST.get("num_chapters", 12)
    if not type(num_chapters) == int:
        num_chapters = int(num_chapters)
    chapter_outlines = write_novel.plan_chapters(idea, character_intro, num_chapters)
    return JsonResponse({'chapter_outlines': chapter_outlines})


def plan_subchapters(request):
    chapter_outlines = request.POST.get("chapter_outlines", "无")
    chapter_outlines = json.loads(chapter_outlines)
    chapter_outline = request.POST.get("chapter_outline", "无")
    recap = request.POST.get("recap", "无")
    num_subchapters = request.POST.get("num_subchapters", 3)
    if not type(num_subchapters) == int:
        num_subchapters = int(num_subchapters)
    subchapter_outlines, recap = write_novel.plan_subchapters(chapter_outlines, 
                                                              chapter_outline, 
                                                              recap,
                                                              num_subchapters)
    return JsonResponse({'subchapter_outlines': subchapter_outlines, "recap": recap})


def plan_subsubchapters(request):
    chapter_outlines = request.POST.get("chapter_outlines", "无")
    chapter_outlines = json.loads(chapter_outlines)
    subchapter_outlines = request.POST.get("subchapter_outlines", "无")
    subchapter_outlines = json.loads(subchapter_outlines)
    subchapter_outline = request.POST.get("subchapter_outline", "无")
    recap = request.POST.get("recap", "无")
    num_subsubchapters = request.POST.get("num_subsubchapters", 3)
    if not type(num_subsubchapters) == int:
        num_subsubchapters = int(num_subsubchapters)
    subsubchapter_outlines, recap = write_novel.plan_subsubchapters(chapter_outlines,
                                                                    subchapter_outlines,
                                                                    subchapter_outline,
                                                                    recap,
                                                                    num_subsubchapters)
    return JsonResponse({'subsubchapter_outlines': subsubchapter_outlines, "recap": recap})


def write_subsubchapter(request):
    chapter_outlines = request.POST.get("chapter_outlines", "无")
    chapter_outlines = json.loads(chapter_outlines)
    character_intro = request.POST.get("character_intro", "无")
    recap = request.POST.get("recap", "无")
    last_paragraph = request.POST.get("last_paragraph", "无")
    subsubchapter_outline = request.POST.get("subsubchapter_outline", "无")

    text, recap = write_novel.write_subsubchapter(chapter_outlines, 
                                                  character_intro,
                                                  recap,
                                                  last_paragraph,
                                                  subsubchapter_outline)
    return JsonResponse({'text': text, "recap": recap})
