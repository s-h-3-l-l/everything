#!/usr/bin/env python3

import os
import sys
import queue
import json
import threading
import time
import logging

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import conf

class LimitedList(list):
    def __init__(self, maxsize):
        self._maxsize = maxsize
        
    def append(self, item):
        if len(self) == self._maxsize:
            self.pop(0)
        super().append(item)

class State:
    timer_interval = conf.DEFAULT_TIMER_INTERVAL
    feed = LimitedList(conf.FEED_SIZE)
    events = queue.Queue()
    modules = {}
    subscriptions = []
    categories = []
    observer = Observer()
    logger = logging.getLogger("everything.update_daemon")

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
            item["category"] = None

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
    
    for sub in fetch:
        State.feed.extend(State.modules[sub["module"]].update(sub))

def fetch_subs():
    for sub in State.subscriptions:
        State.feed.extend(State.modules[sub["module"]].update(sub))

def save_feed_file():
    with open(conf.FEED_FILE, "w") as f:
        f.write(json.dumps(sorted(State.feed, key=lambda x: x["timestamp"], reverse=True)))
    State.logger.debug("Updated feed file")

def read_modules():
    sys.path.append(conf.MODULE_DIR)
    
    for module in os.listdir(conf.MODULE_DIR):
        if module.endswith(".py"):
            name, _ = module.split(".")
            mod = __import__(name)
            State.logger.debug(f"Added module: {name}")
            State.modules[mod.MODULE_NAME] = mod

def main():
    State.logger.setLevel(logging.DEBUG)
    State.logger.addHandler(logging.StreamHandler(sys.stdout))
    
    read_modules()
    
    State.observer.schedule(ConfigFileObserver(), conf.CONFIG_FILE)
    State.observer.start()
    TimerThread().start()
    
    while True:
        event = State.events.get()
        
        if event["event"] == "config":
            State.logger.info("Event: config changed")
            config_changed(event["data"])
        elif event["event"] == "reload":
            State.logger.info("Event: timer reload")
            fetch_subs()
        
        save_feed_file()

if __name__ == "__main__":
    main()
