#!/usr/bin/env python3

import os
import sys
import queue
import json
import threading
import time
import logging
import datetime
import requests

from flask import Markup

import conf
import server

class LimitedList(list):
    def __init__(self, size):
        super().__init__()
        self._max_size = size
    
    def append(self, item):
        if len(self) >= self._max_size:
            self.pop(0)
        super().append(item)

class State:
    timer_interval = conf.DEFAULT_TIMER_INTERVAL
    feed = LimitedList(conf.FEED_SIZE)
    events = queue.Queue()
    modules = {}
    subscriptions = []
    categories = []
    logger = logging.getLogger("everything")

def timer_thread():
    State.logger.info("Started timer")
    
    while True:
        time.sleep(State.timer_interval)
        State.events.put({"event" : "reload", "data" : None})

def load_config():
    c = None
    
    if os.path.isfile(conf.CONFIG_FILE):
        with open(conf.CONFIG_FILE) as f:
            c = json.load(f)
    else:
        c = {
            "subs" : [],
            "cats" : [],
            "timer" : None
        }
        
    State.subscriptions = c["subs"]
    State.categories = c["cats"]
    if c["timer"] is not None:
        State.timer_interval = c["timer"]
    State.events.put({"event" : "reload", "data" : None})

def save_config():
    config = {
        "subs" : State.subscriptions,
        "cats" : State.categories,
        "timer" : None if State.timer_interval == conf.DEFAULT_TIMER_INTERVAL else State.timer_interval
    }
    with open(conf.CONFIG_FILE, "w") as f:
        f.write(json.dumps(config))

def _verify_url(url):
    try:
        return requests.head(url, allow_redirects=True).status_code not in range(400, 500)
    except requests.exceptions.BaseHTTPError:
        return False

def change_category(url, cat):
    if cat not in State.categories + [conf.UNCATEGORIZED_NAME]:
        return
    
    for sub in State.subscriptions:
        if sub["url"] == url:
            sub["category"] = cat
            break
    else:
        return
    
    for item in State.feed:
        if item["sub"] == url:
            item["category"] = cat
    
def change_module(url, mod):
    if mod not in State.modules:
        return
        
    for sub in State.subscriptions:
        if sub["url"] == url:
            sub["module"] = mod
            break
    else:
        return
    
    i = 0
    while i < len(State.feed):
        if State.feed[i]["sub"] == url:
            State.feed.pop(i)
        else:
            i += 1
    
    fetch_subs(filter=url)

def subscription_add(url, module, category):
    if _verify_url(url) and module in State.modules and category in State.categories + [conf.UNCATEGORIZED_NAME]:
        for sub in State.subscriptions:
            if sub["url"] == url:
                return
        
        State.subscriptions.append({
            "module" : module,
            "category" : category,
            "url" : url
        })
        
        fetch_subs(filter=url)

def subscription_delete(url):
    for i in range(len(State.subscriptions)):
        if State.subscriptions[i]["url"] == url:
            State.subscriptions.pop(i)
            break
    else:
        return
        
    i = 0
    while i < len(State.feed):
        if State.feed[i]["sub"] == url:
            State.feed.pop(i)
        else:
            i += 1

def category_add(cat):
    if cat not in State.categories:
        State.categories.append(cat)

def category_delete(cat):
    if cat in State.categories:
        State.categories.remove(cat)
        
        for sub in State.subscriptions:
            if sub["category"] == cat:
                sub["category"] = conf.UNCATEGORIZED_NAME
                
        for item in State.feed:
            if item["category"] == cat:
                item["category"] = conf.UNCATEGORIZED_NAME

def change_timer(t):
    try:
        t = int(t)
    except ValueError:
        return
    
    if t > 0:
        State.timer_interval = t

def prepare_item(item):
    if item["category"] is None:
        item["category"] = conf.UNCATEGORIZED_NAME
    item["content"] = Markup(item["content"])
    return item

def fetch_subs(filter=None):
    n = 0
    for sub in State.subscriptions:
        if filter is not None and sub["url"] != filter:
            continue
        
        try:
            new_items = State.modules[sub["module"]].update(sub)
            for item in new_items:
                State.feed.append(prepare_item(item))
                n += 1
        except:
            pass
            
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
        
        if event["event"] == "reload":
            State.logger.info("Event: timer reload")
            fetch_subs()
        elif event["event"] == "subscription_change_category":
            State.logger.info("Event: change category")
            change_category(*event["data"])
            save_config()
        elif event["event"] == "subscription_change_module":
            State.logger.info("Event: change module")
            change_module(*event["data"])
            save_config()
        elif event["event"] == "subscription_add":
            State.logger.info("Event: add subscription")
            subscription_add(*event["data"])
            save_config()
        elif event["event"] == "subscription_delete":
            State.logger.info("Event: delete subscription")
            subscription_delete(*event["data"])
            save_config()
        elif event["event"] == "category_add":
            State.logger.info("Event: Add category")
            category_add(*event["data"])
            save_config()
        elif event["event"] == "category_delete":
            State.logger.info("Event: Delete category")
            category_delete(*event["data"])
            save_config()
        elif event["event"] == "timer":
            State.logger.info("Event: Change timer")
            change_timer(*event["data"])
            save_config()
        else:
            State.logger.error(f"Unknown event: {event}")

        State.feed = sorted(State.feed, key=lambda x: x["timestamp"], reverse=True)
        State.categories = sorted(State.categories)

def test_config():
    if not os.path.isdir(conf.MODULE_DIR):
        State.logger.error("Module dir doesn't exist")
        return False
        
    if not os.path.isdir(conf.STATIC_FOLDER):
        State.logger.error("Static folder doesn't exist")
        return False
        
    if not os.path.isdir(conf.TEMPLATE_FOLDER):
        State.logger.error("Template folder does not exist")
        return False
    
    #TODO: double subscriptions, double categories, etc.
    
    return True

def main():
    State.logger.setLevel(logging.ERROR)
    State.logger.addHandler(logging.StreamHandler(sys.stderr))
    
    load_config()
    
    if not test_config():
        exit(1)
    
    read_modules()
    
    threading.Thread(target=event_thread).start()
    threading.Thread(target=timer_thread).start()
    server.main(State)

if __name__ == "__main__":
    main()
