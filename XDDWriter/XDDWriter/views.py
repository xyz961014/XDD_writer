from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.db.models import F, Q
import os
import sys
import re
import json
import time

def index(request):
    html_data = {}
    return render(request, "index.html", html_data)


