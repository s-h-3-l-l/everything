#!/usr/bin/env python3

import os
import json
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from flask import Flask, render_template, Markup

import conf

feed = []
categories = []

app = Flask(
    __name__,
    static_folder=os.path.abspath(conf.STATIC_FOLDER),
    template_folder=os.path.abspath(conf.TEMPLATE_FOLDER)
)

@app.route("/")
def index():
    global feed, categories
    return render_template("index.html", feed=feed, cats=list(enumerate(categories + [conf.UNCATEGORIZED_NAME])))

def update(f, c):
    global feed, categories
    feed = f
    categories = c

def main():
    app.run(host=conf.SERVER_HOST, port=conf.SERVER_PORT)
