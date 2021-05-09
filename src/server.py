#!/usr/bin/env python3

import os
import json
import time

from flask import Flask, render_template, Markup, request, redirect

import conf

state = None

app = Flask(
    __name__,
    static_folder=os.path.abspath(conf.STATIC_FOLDER),
    template_folder=os.path.abspath(conf.TEMPLATE_FOLDER)
)

@app.route("/settings")
def settings():
    return render_template("settings.html", categories=state.categories + [conf.UNCATEGORIZED_NAME], subscriptions=list(enumerate(state.subscriptions)), modules=list(state.modules), timer=state.timer_interval)

@app.route("/")
def index():
    return render_template("index.html", feed=state.feed, cats=list(enumerate(state.categories + [conf.UNCATEGORIZED_NAME])))

### API ###

@app.route("/subscription/change_category", methods=["POST"])
def subscription_change_category():
    url = request.form["url"]
    cat = request.form["cat"]
    state.events.put({"event" : "subscription_change_category", "data" : (url, cat)})
    return redirect("/settings")
    
@app.route("/subscription/change_module", methods=["POST"])
def subscription_change_module():
    url = request.form["url"]
    mod = request.form["mod"]
    state.events.put({"event" : "subscription_change_module", "data" : (url, mod)})
    return redirect("/settings")
    
@app.route("/subscription/add", methods=["POST"])
def subscription_add():
    url = request.form["url"]
    module = request.form["module"]
    category = request.form["category"]
    state.events.put({"event" : "subscription_add", "data" : (url, module, category)})
    return redirect("/settings")
    
@app.route("/subscription/delete", methods=["POST"])
def subscription_delete():
    url = request.form["url"]
    state.events.put({"event" : "subscription_delete", "data" : (url,)})
    return redirect("/settings")
    
@app.route("/category/add", methods=["POST"])
def category_add():
    cat = request.form["cat"]
    state.events.put({"event" : "category_add", "data" : (cat,)})
    return redirect("/settings")
    
@app.route("/category/delete", methods=["POST"])
def category_delete():
    cat = request.form["cat"]
    state.events.put({"event" : "category_delete", "data" : (cat,)})
    return redirect("/settings")
    
@app.route("/timer", methods=["POST"])
def timer():
    t = request.form["t"]
    state.events.put({"event" : "timer", "data" : (t,)})
    return redirect("/settings")

### END OF API ###

def main(s):
    global state
    state = s
    app.run(host=conf.SERVER_HOST, port=conf.SERVER_PORT)
