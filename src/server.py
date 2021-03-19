#!/usr/bin/env python3

import os
import json
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from flask import Flask, render_template, Markup

import conf

class State:
    observer = Observer()
    feed = []
    categories = set()
    
class FeedFileObserver(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        try:
            self.read_feed()
        except FileNotFoundError:
            pass
    
    def on_modified(self, event):
        time.sleep(1)
        self.read_feed()
        
    def read_feed(self):
        with open(conf.FEED_FILE) as f:
            State.feed = json.load(f)
        
        cats = set()
            
        for item in State.feed:
            item["content"] = Markup(item["content"])
            
            if item["category"] is None:
                item["category"] = "Sonstiges"
                
            cats.add(item["category"])
            
        State.categories = sorted(cats)

app = Flask(
    __name__,
    static_folder=os.path.abspath(conf.STATIC_FOLDER),
    template_folder=os.path.abspath(conf.TEMPLATE_FOLDER)
)

@app.route("/")
def index():
    return render_template("index.html", feed=State.feed, cats=list(enumerate(State.categories)))

def main():
    while not os.path.isfile(conf.FEED_FILE):
        time.sleep(1)

    State.observer.schedule(FeedFileObserver(), conf.FEED_FILE)
    State.observer.start()
    app.run(host=conf.SERVER_HOST, port=conf.SERVER_PORT)

if __name__ == "__main__":
    main()
