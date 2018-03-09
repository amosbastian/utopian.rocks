import datetime
import json
import math
import requests
from dateutil.parser import parse
from pymongo import MongoClient

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

client = MongoClient()
db = client.utopian

UTOPIAN_API = "https://api.utopian.io/api/"


def generate_url(action, parameters):
    return f"{UTOPIAN_API}{action}/?{urlencode(parameters)}"


def create_post(post, status):
    new_post = {
        "moderator": None,
        "author": post["author"],
        "permlink": post["permlink"],
        "title": post["title"],
        "repository": post.get("json_metadata").get("repository"),
        "last_update": parse(post["last_update"]),
        "created": parse(post["created"]),
        "active": parse(post["active"]),
        "_id": post["_id"],
        "category": post.get("json_metadata").get("type"),
        "modified": False,
        "status": status,
        "updated": datetime.datetime.now()
    }
    if not status == "pending":
        moderator = post["json_metadata"]["moderator"]
        try:
            moderator["time"] = parse(moderator.get("time"))
        except TypeError:
            moderator["time"] = datetime.datetime(2010, 10, 10, 10, 10)
        new_post["moderator"] = moderator
        
    return new_post


def get_posts(status, update=True):
    posts = []
    limit = 1000
    skip = 0
    action = "posts"
    posts = db.posts

    # Get total amount of posts submitted to Utopian.io
    if not status == "pending":
        r = requests.get(generate_url(action, {"status": status, "limit": 1}))
    else:
        r = requests.get(generate_url(action, {"filterBy": "review", "limit": 1}))
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
            if not status == "pending":
                parameters = {"status": status, "limit": limit, "skip": skip}
            else:
                parameters = {"filterBy": "review", "limit": limit, "skip": skip}
            url = generate_url(action, parameters)
            print(f"{datetime.datetime.now()} - Fetching from {url}")
            r = requests.get(url)
            if r.status_code == 200:
                post_list = [create_post(post, status) for post in r.json()["results"]]
                for post in post_list:
                    posts.replace_one({"_id": post["_id"]}, post, True)
            else:
                time = datetime.datetime.now()
                print(f"{time} - Something went wrong, please try again later.")
                return
            skip += 1000
    # Get posts submitted to Utopian.io within the last week
    else:
        week = datetime.datetime.now() - datetime.timedelta(days=7)
        for _ in range(total):
            parameters = {"status": status, "limit": limit, "skip": skip}
            url = generate_url(action, parameters)
            print(f"{datetime.datetime.now()} - Fetching from {url}")
            r = requests.get(url)
            if r.status_code == 200:
                post_list = [create_post(post, status) for post in r.json()["results"]]
                for post in post_list:
                    database_post = posts.find_one({"_id": post["_id"]})
                    if database_post and "flagged" in database_post:
                        if (not database_post["flagged"] == post["flagged"]
                            or database_post["modified"]):
                            post["modified"] = True
                    posts.replace_one({"_id": post["_id"]}, post, True)
                    if post["created"] < week:
                        return posts
            else:
                time = datetime.datetime.now()
                print(f"{time} - Something went wrong, please try again later.")
                return
            
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