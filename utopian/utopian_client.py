import datetime
import json
import math
import requests
import threading
from dateutil.parser import parse
from pymongo import MongoClient
from steem.post import Post

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
    posts = db.posts
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
        # Add moderator to post
        moderator = post["json_metadata"]["moderator"]
        try:
            moderator["time"] = parse(moderator.get("time"))
        except TypeError:
            moderator["time"] = new_post["created"]
        new_post["moderator"] = moderator

        # Add post's score
        try:
            new_post["score"] = post["json_metadata"]["score"]
        except KeyError:
            new_post["score"] = 100

        # Add moderator's comment to post
        # author = new_post["author"]
        # permlink = new_post["permlink"]
        # steemit_post = Post(f"@{author}/{permlink}")
        # print(f"@{author}/{permlink}")
        # for post in Post.get_all_replies(steemit_post):
        #     if post["author"] == moderator["account"]:
        #         if "[[utopian-moderator]]" in post["body"]:
        #             new_post["comment"] = post["body"]
        #         else:
        #             new_post["comment"] = None
        #         break

        database_post = posts.find_one({"_id": new_post["_id"]})
        if database_post and "flagged" in database_post:
            if (not database_post["flagged"] == new_post["flagged"]
                or database_post["modified"]):
                new_post["modified"] = True
    posts.replace_one({"_id": new_post["_id"]}, new_post, True)

def get_posts(status, update=True):
    limit = 1000
    skip = 0
    action = "posts"
    number_threads = 5

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
                posts =  r.json()["results"]
                for i in range(0, len(posts), number_threads):
                    threads = []
                    for j in range(number_threads):
                        try:
                            t = threading.Thread(target=create_post,
                                name=j, args=(posts[i + j], status))
                            threads.append(t)
                            t.start()
                        except IndexError:
                            pass
                    for t in threads:
                        t.join()
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
                posts = r.json()["results"]
                for i in range(0, len(posts), number_threads):
                    threads = []
                    for j in range(number_threads):
                        t = threading.Thread(target=create_post,
                            name=j, args=(posts[i + j], status))
                        threads.append(t)
                        t.start()
                    for t in threads:
                        t.join()
                    
                    if parse(posts[i]["created"]) < week:
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