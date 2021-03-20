"""
https://developers.google.com/youtube/v3/docs
"""

import logging
import requests
import datetime
from urllib.parse import urlparse

from secrets import YOUTUBE_API_KEY as API_KEY

BASE_URL = "https://www.googleapis.com/youtube/v3"

class YouTubeException(Exception):
    pass

def get_videos(id, n=5):
    r = requests.get(BASE_URL + "/playlistItems", params={
        "part" : "snippet",
        "maxResults" : f"{n}",
        "playlistId" : id,
        "key" : API_KEY
    })
    r.raise_for_status()
    
    for item in r.json()["items"]:
        date = datetime.datetime.strptime(item["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%SZ")
        title = item["snippet"]["title"]
        thumbnail = item["snippet"]["thumbnails"]["medium"]["url"]
        id = item["snippet"]["resourceId"]["videoId"]
        yield date, title, thumbnail, id
    
def get_channel(name=None, id=None):
    params = {
        "part" : "id,contentDetails,snippet",
        "maxResults" : "1",
        "key" : API_KEY
    }
    
    if name is not None:
        params["forUsername"] = name
    elif id is not None:
        params["id"] = id
    else:
        raise YouTubeException(f"Invalid get_channel call")
        
    r = requests.get(BASE_URL + "/channels", params=params)
    r.raise_for_status()
    r = r.json()
    
    if r["pageInfo"]["totalResults"] != 1:
        raise YouTubeException(f"No channel results for username: {name}")
    
    return r["items"][0]["id"], r["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"], r["items"][0]["snippet"]["title"]

class State:
    logger = logging.getLogger("everything.update_daemon")
    name_mapping = {}
    timestamps = {}
    
def parse_channel_url(url):
    """
    /user/<name>
    /channel/<id>
    """
    url = urlparse(url)
    
    if url.netloc != "www.youtube.com":
        raise YouTubeException(f"Invalid domain: {url.netloc}")
        
    if url.path.startswith("/user/"):
        username = url.path.split("/")[-1]
        return get_channel(name=username)
    elif url.path.startswith("/channel/"):
        id = url.path.split("/")[-1]
        return get_channel(id=id)
    else:
        raise YouTubeException(f"Unknown url: {url.path}")
    
def update(sub):
    State.logger.debug(f"Doing modules.YouTube.update: {sub}")
    
    if sub["url"] not in State.name_mapping:
        id, uploads, title = parse_channel_url(sub["url"])
        State.name_mapping[sub["url"]] = {
            "id" : id,
            "uploads" : uploads,
            "title" : title
        }
        State.timestamps[sub["url"]] = datetime.datetime(1970, 1, 1)
    
    for date, title, thumbnail, id in get_videos(State.name_mapping[sub["url"]]["uploads"]):
        if date >= State.timestamps[sub["url"]]:
            yield {
                "module" : sub["module"],
                "headline" : title,
                "thumbnail" : thumbnail,
                "content" : "",
                "category" : sub["category"],
                "sub" : sub["url"],
                "timestamp" : date.timestamp(),
                "link" : "https://www.youtube-nocookie.com/embed/" + id + "?autoplay=true",
                "source" : State.name_mapping[sub["url"]]["title"]
            }
    
    State.timestamps[sub["url"]] = datetime.datetime.utcnow()
