import logging
import time
import datetime
from urllib.parse import urlparse

import feedparser

MODULE_LOGO = "/static/News.jpg"

class State:
    logger = logging.getLogger("everything.update_daemon")
    feeds = {}

def update(sub):
    State.logger.debug(f"Doing modules.News.update: {sub}")
    feed = feedparser.parse(sub["url"])
    
    if sub["url"] not in State.feeds:
        State.feeds[sub["url"]] = datetime.datetime(1970, 1, 1)
    
    for entry in feed.entries:
        year, month, day, hour, minute, second, *_ = entry.published_parsed
        date = datetime.datetime(year, month, day, hour, minute, second)
        
        content = ""
        if "description" in entry and entry.description.count(". ") < 10 and "<img" not in entry.description:
            content = entry.description.replace("...", ". ").replace(". ", ".<br/>").strip()
        
        source = urlparse(sub["url"]).netloc
        
        if source.startswith("www."):
            source = source[4:]
            
        link = "#"
        if "link" in entry:
            link = entry.link
        elif "enclosures" in entry and entry.enclosures:
            link = entry.enclosures[0].href
        
        if date >= State.feeds[sub["url"]]:
            yield {
                "module" : sub["module"],
                "headline" : entry.title,
                "thumbnail" : MODULE_LOGO,
                "content" : content,
                "category" : sub["category"],
                "sub" : sub["url"],
                "timestamp" : date.timestamp(),
                "link" : link,
                "source" : source
            }
    
    State.feeds[sub["url"]] = datetime.datetime.utcnow()
