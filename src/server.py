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
subscriptions = []
modules = []
timer = None

app = Flask(
    __name__,
    static_folder=os.path.abspath(conf.STATIC_FOLDER),
    template_folder=os.path.abspath(conf.TEMPLATE_FOLDER)
)

@app.route("/settings")
def settings():
    return render_template("settings.html", categories=categories, subscriptions=list(enumerate(subscriptions)), modules=modules, timer=timer)

@app.route("/")
def index():
    global feed, categories
    return render_template("index.html", feed=feed, cats=list(enumerate(categories + [conf.UNCATEGORIZED_NAME])))

### API ###

def update(f, c, s, t, m):
    global feed, categories, subscriptions, timer, modules
    feed = f
    categories = c
    subscriptions = s
    timer = t
    modules = m

def main():
    app.run(host=conf.SERVER_HOST, port=conf.SERVER_PORT)
