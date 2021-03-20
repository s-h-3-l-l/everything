#!/usr/bin/env python3

import os
import json
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from flask import Flask, render_template, Markup

import conf

State = None

app = Flask(
    __name__,
    static_folder=os.path.abspath(conf.STATIC_FOLDER),
    template_folder=os.path.abspath(conf.TEMPLATE_FOLDER)
)

@app.route("/")
def index():
    return render_template("index.html", feed=State.feed, cats=list(enumerate(State.categories)))

def main(s):
    global State
    State = s
    app.run(host=conf.SERVER_HOST, port=conf.SERVER_PORT)
