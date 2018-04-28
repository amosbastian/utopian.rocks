"""
Blueprint for the homepage.
"""
import datetime
import json
import os
import requests

from collections import Counter
from flask import Blueprint, render_template, flash, redirect
from pymongo import MongoClient
from utopian.forms import (
    ManagerForm,
    ModeratorForm,
    ContributorForm,
    ProjectForm
)

BP = Blueprint("home", __name__, url_prefix="/")
CLIENT = MongoClient()
DB = CLIENT.utopian
GITHUB = "https://api.github.com/"
HEADERS = {
    "Authorization": "token {}".format(os.environ["GITHUB_TOKEN"]),
    "Accept": "application/vnd.github.v3+json"
}
N = 7


def category_converter(category):
    """
    Convert category to its actual name.
    """
    if category == "social":
        return "visibility"
    elif category == "ideas":
        return "suggestions"
    return category


def moderator_points(category):
    """
    Return the amount of points received for reviewing a contribution in the
    given category.
    """
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

    # Sort moderators and managers into own list
    for moderator in moderators.find():
        if moderator["supermoderator"]:
            manager_list.append(moderator["account"])
        else:
            moderator_list.append(moderator["account"])

    return manager_list, moderator_list


def moderator_performance(moderator_list, post_list, manager=True):
    """
    Returns a list of the N most active moderators/managers in the last week,
    with their name, amount of accepted and rejected contributions and points.
    """
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

            # Add category to list and count points
            category = post["category"]
            moderators[moderator]["points"] += moderator_points(category)
            moderators[moderator]["category"].append(category)

    moderator_list = []
    for key, value in moderators.items():
        category = Counter(value["category"]).most_common(1)[0][0]
        # Replace task request with actual category
        if "task" in category:
            category = category.split("-")[1]

        value["category"] = category_converter(category)
        value["account"] = key
        moderator_list.append(value)

    return sorted(
        moderator_list,
        key=lambda x: x["accepted"] + x["rejected"],
        reverse=True)[:N]


def contributor_performance(post_list):
    """
    Returns a list of the N most rewarded contributors in the last week, with
    their name, amount of accepted and rejected contributions and amount of
    pending rewards on those contributions.
    """
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

        # Add category to list and count points
        category = post["category"]
        contributors[contributor]["category"].append(category)
        contributors[contributor]["rewards"] += post["reward"]

    contributor_list = []
    for key, value in contributors.items():
        category = Counter(value["category"]).most_common(1)[0][0]
        # Replace task request with actual category
        if "task" in category:
            category = category.split("-")[1]

        value["category"] = category_converter(category)
        value["account"] = key
        contributor_list.append(value)

    return sorted(
        contributor_list,
        key=lambda x: x["rewards"],
        reverse=True)[:N]


def project_performance(post_list):
    """
    Returns a list of the N most rewarded projects in the last week. This list
    contains each project's name, avatar URL, repository URL, amount of
    accepted and rejected contributions made to it and the amount of pending
    rewards on those contributions.
    """
    projects = {}
    for post in post_list:
        project = str(post["repository"]["id"])
        projects.setdefault(project, {
            "accepted": 0, "rejected": 0, "rewards": 0
        })

        if post["moderator"]["flagged"]:
            projects[project]["rejected"] += 1
        else:
            projects[project]["accepted"] += 1

        projects[project]["rewards"] += post["reward"]

    project_list = []
    for key, value in projects.items():
        value["id"] = key
        project_list.append(value)

    # Get IDs of N most rewarded projects
    project_list = sorted(project_list,
                          key=lambda x: x["rewards"],
                          reverse=True)[:N]

    # Use GitHub API to get additional information
    # for project in project_list:
    #     project_id = project["id"]
    #     request = requests.get(f"{GITHUB}repositories/{project_id}").json()
    #     project["full_name"] = request["full_name"]
    #     project["avatar_url"] = request["owner"]["avatar_url"]
    #     project["html_url"] = request["html_url"]

    return project_list


@BP.route("/")
def index():
    """
    Returns the homepage's template.
    """
    posts = DB.posts

    # Get lists for use in autocompletion
    manager_list, moderator_list = get_moderators()

    # Set time frame and retrieve posts
    time_frame = datetime.datetime.now() - datetime.timedelta(days=7)
    post_list = [post for post in posts.find(
        {"moderator.time": {"$gt": time_frame}}
    )]

    # Get all information needed for homepage
    manager_info = moderator_performance(manager_list, post_list)
    moderator_info = moderator_performance(moderator_list, post_list, False)
    contributor_info = contributor_performance(post_list)
    project_info = project_performance(post_list)

    return render_template(
        "index.html",
        manager_info=manager_info,
        moderator_info=moderator_info,
        contributor_info=contributor_info,
        project_info=project_info,
        manager_form=ManagerForm(),
        moderator_form=ModeratorForm(),
        contributor_form=ContributorForm(),
        project_form=ProjectForm()
    )
