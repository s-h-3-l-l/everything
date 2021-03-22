#!/usr/bin/env python3

import os
import sys
import queue
import json
import threading
import time
import logging
import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from flask import Markup

import conf
import server

class State:
    timer_interval = conf.DEFAULT_TIMER_INTERVAL
    feed = []
    events = queue.Queue()
    modules = {}
    subscriptions = []
    categories = []
    observer = Observer()
    logger = logging.getLogger("everything")

class ConfigFileObserver(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        c = None
        with open(conf.CONFIG_FILE) as f:
            c = json.load(f)
        State.subscriptions = c["subs"]
        State.categories = c["cats"]
        if c["timer"] is not None:
            State.timer_interval = c["timer"]
        State.logger.info(f"Observing: {conf.CONFIG_FILE}")
        State.events.put({"event" : "reload", "data" : None})
    
    def on_modified(self, event):
        c = None
        with open(conf.CONFIG_FILE) as f:
            c = json.load(f)
        State.events.put({"event" : "config", "data" : c})

class TimerThread(threading.Thread):
    def run(self):
        State.logger.info("Started timer")
        
        while True:
            time.sleep(State.timer_interval)
            State.events.put({"event" : "reload", "data" : None})

def remove_feed_items(sub):
    i = 0
    while i < len(State.feed):
        if State.feed[i]["sub"] == sub["url"]:
            State.feed.pop(i)
        else:
            i += 1

def remove_feed_category(cat):
    for item in State.feed:
        if item["category"] == cat:
            item["category"] = conf.UNCATEGORIZED_NAME

def config_changed(new_config):
    if new_config is None:
        return
    
    fetch = []
    
    for new_sub in new_config["subs"]:
        if new_sub not in State.subscriptions:
            fetch.append(new_sub)
            State.logger.debug(f"Found new subscription: {new_sub}")
    
    for old_sub in State.subscriptions:
        if old_sub not in new_config["subs"]:
            remove_feed_items(old_sub)
            State.logger.debug(f"Removed old subscription: {old_sub}")
        
    State.subscriptions = new_config["subs"]
    
    if new_config["cats"] != State.categories:
        for cat in State.categories:
            if cat not in new_config["cats"]:
                remove_feed_category(cat)
                State.logger.debug(f"Removed category: {cat}")
    
    State.categories = new_config["cats"]
    
    if new_config["timer"] is not None:
        State.timer_interval = new_config["timer"]
        State.logger.debug(f"Set timer: {State.timer_interval}")
    
    n = 0
    for sub in fetch:
        for item in State.modules[sub["module"]].update(sub):
            State.feed.append(prepare_item(item))
            n += 1
    State.logger.debug(f"Added {n} new items to feed")

def prepare_item(item):
    if item["category"] is None:
        item["category"] = UNCATEGORIZED_NAME
    item["content"] = Markup(item["content"])
    return item

def fetch_subs():
    n = 0
    for sub in State.subscriptions:
        for item in State.modules[sub["module"]].update(sub):
            State.feed.append(prepare_item(item))
            n += 1
    State.logger.debug(f"Added {n} new items to feed")

def read_modules():
    sys.path.append(conf.MODULE_DIR)
    
    for module in os.listdir(conf.MODULE_DIR):
        if module.endswith(".py"):
            name, _ = module.split(".")
            mod = __import__(name)
            State.logger.debug(f"Imported module: {name}")
            State.modules[name] = mod

def event_thread():
    while True:
        event = State.events.get()
        
        if event["event"] == "config":
            State.logger.info("Event: config changed")
            config_changed(event["data"])
        elif event["event"] == "reload":
            State.logger.info("Event: timer reload")
            fetch_subs()

        State.feed = sorted(State.feed, key=lambda x: x["timestamp"], reverse=True)
        State.categories = sorted(State.categories)
        server.update(State.feed, State.categories)

def main():
    State.logger.setLevel(logging.DEBUG)
    State.logger.addHandler(logging.StreamHandler(sys.stdout))
    
    read_modules()
    
    State.observer.schedule(ConfigFileObserver(), conf.CONFIG_FILE)
    State.observer.start()
    threading.Thread(target=event_thread).start()
    TimerThread().start()

    server.main()

if __name__ == "__main__":
    main()
