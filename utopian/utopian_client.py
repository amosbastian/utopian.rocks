import datetime
import json
import math
import requests
import threading
from multiprocessing import Pool
from functools import partial
from dateutil.parser import parse
from pymongo import MongoClient
from steem import Steem

steem = Steem()

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

client = MongoClient()
db = client.utopian

UTOPIAN_API = "https://api.utopian.io/api/"


def generate_url(action, parameters):
    return f"{UTOPIAN_API}{action}/?{urlencode(parameters)}"


def create_post(post, status, update=True):
    week = datetime.datetime.now() - datetime.timedelta(days=7)
    if update and parse(post["created"]) < week:
        return None
    
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
        # print(post["permlink"])
        # Add moderator to post
        moderator = post["json_metadata"]["moderator"]
        try:
            moderator["time"] = parse(moderator.get("time"))
        except TypeError:
            moderator["time"] = new_post["created"]
        new_post["moderator"] = moderator

        # Add post's score
        if "score" in post["json_metadata"].keys():
            new_post["score"] = post["json_metadata"]["score"]
        else:
            new_post["score"] = 100

        # Add questionaire's questions
        if "questions" in post["json_metadata"].keys():
            new_post["questions"] = post["json_metadata"]["questions"]
        else:
            new_post["questions"] = "N/A"

        # Add moderator's comment to post
        # author = new_post["author"]
        # permlink = new_post["permlink"]
        # new_post["comment"] = "N/A"
        # steemit_post = Post(f"@{author}/{permlink}")
        # replies = steem.get_content_replies(author, permlink)
        # if replies:
        #     for post in replies:
        #         if (post["author"] == moderator["account"] and
        #             "[[utopian-moderator]]" in post["body"]):
        #             new_post["comment"] = post["body"]
        #             return new_post
        # else:
        #     return new_post
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
                pool = Pool()
                x = partial(create_post, status=status, update=False)
                post_list = pool.map(x, r.json()["results"])
                pool.close()
                pool.join()
                for post in post_list:
                    if not post == None:
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
                pool = Pool()
                x = partial(create_post, status=status, update=True)
                post_list = pool.map(x, r.json()["results"])
                pool.close()
                pool.join()
                for post in post_list:
                    if post == None:
                        return
                    database_post = posts.find_one({"_id": post["_id"]})
                    if database_post and "flagged" in database_post:
                        if (not database_post["flagged"] == post["flagged"]
                            or database_post["modified"]):
                            post["modified"] = True
                    posts.replace_one({"_id": post["_id"]}, post, True)
                    if post["created"] < week:
                        return
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