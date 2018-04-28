import datetime
import json
import math
import os
import requests

from dateutil.parser import parse
from pymongo import MongoClient
from urllib.parse import urlencode

CLIENT = MongoClient()
DB = CLIENT.utopian
ERROR = "{ERROR}"
UTOPIAN_API = "https://api.utopian.io/api/"

HEADERS = {
    "Origin": "https://utopian.info",
    "Accept": "application/json",
    "x-api-key": os.environ["API_KEY"],
    "x-api-key-id": os.environ["API_KEY_ID"]
}


def generate_url(action, parameters):
    return f"{UTOPIAN_API}{action}/?{urlencode(parameters)}"


def create_post(post, status, update=True):
    week = datetime.datetime.now() - datetime.timedelta(days=7)
    if update and parse(post["created"]) < week:
        return None

    new_post = {
        "moderator": {"account": ""},
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
        "updated": datetime.datetime.now(),
        "reward": float(post["pending_payout_value"].split()[0])
    }

    if not new_post["repository"]:
        new_post["repository"] = {"full_name": ""}

    if new_post["reward"] == 0:
        new_post["reward"] = float(post["total_payout_value"].split()[0])

    if not status == "pending":
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
            if new_post["score"] is None:
                new_post["score"] = 0
        else:
            new_post["score"] = 100

        # Add questionaire's questions
        if "questions" in post["json_metadata"].keys():
            new_post["questions"] = post["json_metadata"]["questions"]
        else:
            new_post["questions"] = "N/A"

    return new_post


def get_posts(status, update=True):
    posts = []
    limit = 1000
    skip = 0
    action = "posts"
    posts = DB.posts

    # Get total amount of posts submitted to Utopian.io
    if not status == "pending":
        r = requests.get(generate_url(action, {"status": status, "limit": 1}),
                         headers=HEADERS)
    else:
        r = requests.get(generate_url(action, {"filterBy": "review",
                         "limit": 1}), headers=HEADERS)

    if r.status_code == 200:
        total = r.json()["total"]
        total = math.ceil(total / 1000)
    else:
        time = datetime.datetime.now()
        print(f"{time} - {ERROR}")
        return

    # Get ALL posts submitted to Utopian.io
    if not update:
        for _ in range(total):
            # Parameters depend on status of the post
            if not status == "pending":
                parameters = {"status": status, "limit": limit, "skip": skip}
            else:
                parameters = {"filterBy": "review", "limit": limit,
                              "skip": skip}

            # Generate URL and send the request to the API
            url = generate_url(action, parameters)
            print(f"{datetime.datetime.now()} - Fetching from {url}")
            r = requests.get(url, headers=HEADERS)

            # If request was okay then replace posts in the database
            if r.status_code == 200:
                post_list = [create_post(post, status, False)
                             for post in r.json()["results"]]

                for post in post_list:
                    if post is not None:
                        posts.replace_one({"_id": post["_id"]}, post, True)
            else:
                time = datetime.datetime.now()
                print(f"{time} - {ERROR}")
                return
            skip += 1000
    # Get posts submitted to Utopian.io within the last week
    else:
        week = datetime.datetime.now() - datetime.timedelta(days=7)
        for _ in range(total):
            # Set parameters and send a request to the API
            parameters = {"status": status, "limit": limit, "skip": skip}
            url = generate_url(action, parameters)
            print(f"{datetime.datetime.now()} - Fetching from {url}")
            r = requests.get(url, headers=HEADERS)

            # If request was okay then replace posts in the database
            if r.status_code == 200:
                post_list = [create_post(post, status, True)
                             for post in r.json()["results"]]
                for post in post_list:
                    if post is None:
                        return
                    posts.replace_one({"_id": post["_id"]}, post, True)
                    if post["created"] < week:
                        print("YES")
                        return
            else:
                time = datetime.datetime.now()
                print(f"{time} - {ERROR}")
                return

            skip += 1000


def get_moderators():
    action = "moderators"
    url = generate_url(action, {})
    r = requests.get(url, headers=HEADERS)

    if r.status_code == 200:
        return r.json()["results"]
    else:
        time = datetime.datetime.now()
        print(f"{time} - {ERROR}")
        return
