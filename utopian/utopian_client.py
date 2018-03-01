import datetime
import json
import math
import requests
from dateutil.parser import parse

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

UTOPIAN_API = "https://api.utopian.io/api/"


def generate_url(action, parameters):
    return f"{UTOPIAN_API}{action}/?{urlencode(parameters)}"


def create_post(post):
    moderator = post["json_metadata"]["moderator"]
    try:
        moderator["time"] = parse(moderator.get("time"))
    except TypeError:
        moderator["time"] = datetime.datetime(2010, 10, 10, 10, 10)

    new_post = {
        "moderator": moderator,
        "author": post["author"],
        "permlink": post["permlink"],
        "title": post["title"],
        "repository": post.get("json_metadata").get("repository"),
        "last_update": parse(post["last_update"]),
        "created": parse(post["created"]),
        "active": parse(post["active"]),
        "_id": post["_id"],
        "category": post.get("json_metadata").get("type"),
        "modified": False
    }
    return new_post


def get_posts(status, update=True):
    posts = []
    limit = 1000
    skip = 0
    action = "posts"

    # Get total amount of posts submitted to Utopian.io
    r = requests.get(generate_url(action, {"status": status, "limit": 1}))
    if r.status_code == 200:
        total = r.json()["total"]
        total = math.ceil(total / 1000)
    else:
        time = datetime.datetime.now()
        print(f"{time} - Something went wrong, please try again later.")
        return

    # Get ALL posts submitted to Utopian.io
    if not update:
        for _ in range(total):
            parameters = {"status": status, "limit": limit, "skip": skip}
            url = generate_url(action, parameters)
            print(f"{datetime.datetime.now()} - Fetching from {url}")
            r = requests.get(url)
            if r.status_code == 200:
                post_list = [create_post(post) for post in r.json()["results"]]
                posts.extend(post_list)
            else:
                time = datetime.datetime.now()
                print(f"{time} - Something went wrong, please try again later.")
                return
            skip += 1000
        return posts
    # Get posts submitted to Utopian.io within the last week
    else:
        week = datetime.datetime.now() - datetime.timedelta(days=7)
        for _ in range(total):
            parameters = {"status": status, "limit": limit, "skip": skip}
            url = generate_url(action, parameters)
            print(f"{datetime.datetime.now()} - Fetching from {url}")
            r = requests.get(url)
            if r.status_code == 200:
                post_list = [create_post(post) for post in r.json()["results"]]
                posts.extend(post_list)
            else:
                time = datetime.datetime.now()
                print(f"{time} - Something went wrong, please try again later.")
                return
            
            if posts[-1]["created"] < week:
                return posts
            
            skip += 1000


def get_moderators():
    action = "moderators"
    url = generate_url(action, {})
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()["results"]
    else:
        time = datetime.datetime.now()
        print(f"{time} - Something went wrong, please try again later.")
        return