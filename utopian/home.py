"""
Blueprint for the homepage.
"""
import datetime

from collections import Counter
from flask import Blueprint, render_template
from pymongo import MongoClient

BP = Blueprint("home", __name__, url_prefix="/")
CLIENT = MongoClient()
DB = CLIENT.utopian


def converter(object_):
    if isinstance(object_, datetime.datetime):
        return object_.__str__()


def category_converter(category):
    if category == "social":
        return "visibility"
    elif category == "ideas":
        return "suggestions"
    return category


def moderator_points(category):
    if category == "ideas":
        return 2.0
    elif category == "development":
        return 4.25
    elif category == "translations":
        return 4.0
    elif category == "graphics":
        return 3.0
    elif category == "documentation":
        return 2.25
    elif category == "copywriting":
        return 2.0
    elif category == "tutorials":
        return 4.0
    elif category == "analysis":
        return 3.25
    elif category == "social":
        return 2.0
    elif category == "blog":
        return 2.25
    elif category == "video-tutorials":
        return 4.0
    elif category == "bug-hunting":
        return 3.25
    elif "task" in category:
        return 1.25


def get_moderators():
    """
    Returns a list containing the names of all community managers and a list
    containing the names of all moderators.
    """
    moderators = DB.moderators
    moderator_list = []
    manager_list = []

    for moderator in moderators.find():
        if moderator["supermoderator"]:
            manager_list.append(moderator["account"])
        else:
            moderator_list.append(moderator["account"])

    return manager_list, moderator_list


def contributor_performance(post_list):
    contributors = {}
    for post in post_list:
        contributor = post["author"]
        contributors.setdefault(contributor, {
            "accepted": 0, "rejected": 0, "rewards": 0, "category": []
        })

        if post["moderator"]["flagged"]:
            contributors[contributor]["rejected"] += 1
        else:
            contributors[contributor]["accepted"] += 1

        # TODO: Add post rewards to the database and sum them here.
        category = post["category"]
        contributors[contributor]["category"].append(category)

    contributor_list = []
    for key, value in contributors.items():
        category = Counter(value["category"]).most_common(1)[0][0]
        if "task" in category:
            category = category.split("-")[1]
        value["category"] = category_converter(category)
        value["account"] = key
        contributor_list.append(value)

    return sorted(
        contributor_list,
        key=lambda x: x["accepted"] + x["rejected"],
        reverse=True)[:5]


def moderator_performance(moderator_list, post_list, manager=True):
    moderators = {}

    if manager:
        points = 100
    else:
        points = 0

    for post in post_list:
        moderator = post["moderator"]["account"]
        if moderator in moderator_list:
            moderators.setdefault(moderator, {
                "accepted": 0, "rejected": 0, "points": points, "category": []
            })
            if post["moderator"]["flagged"]:
                moderators[moderator]["rejected"] += 1
            else:
                moderators[moderator]["accepted"] += 1

            category = post["category"]
            moderators[moderator]["points"] += moderator_points(category)
            moderators[moderator]["category"].append(category)

    moderator_list = []
    for key, value in moderators.items():
        category = Counter(value["category"]).most_common(1)[0][0]
        if "task" in category:
            category = category.split("-")[1]
        value["category"] = category_converter(category)
        value["account"] = key
        moderator_list.append(value)

    return sorted(
        moderator_list,
        key=lambda x: x["accepted"] + x["rejected"],
        reverse=True)[:5]


@BP.route("/")
def index():
    """
    Returns the homepage's template.
    """
    posts = DB.posts

    manager_list, moderator_list = get_moderators()

    time_frame = datetime.datetime.now() - datetime.timedelta(days=7)
    post_list = [post for post in posts.find(
        {"moderator.time": {"$gt": time_frame}}
    )]

    manager_info = moderator_performance(manager_list, post_list)
    moderator_info = moderator_performance(moderator_list, post_list, False)
    contributor_info = contributor_performance(post_list)
    return render_template(
        "index.html",
        manager_info=manager_info,
        moderator_info=moderator_info,
        contributor_info=contributor_info
    )
