"""
Contains all the functions used for searching on Utopian.info.
"""
from flask import Blueprint, render_template, jsonify, request, make_response
from pymongo import MongoClient
from utopian.forms import (
    ManagerForm,
    ModeratorForm,
    ContributorForm,
    ProjectForm,
    SearchForm
)

BP = Blueprint("search", __name__, url_prefix="/")
CLIENT = MongoClient()
DB = CLIENT.utopian


def moderator_search(data, manager=True):
    """
    Returns a list of either managers of moderators that match the given
    query.
    """
    if not data:
        data = "amosbastian"
    moderators = DB.moderators
    search_result = list(moderators.find({
        "account": {"$regex": data},
        "supermoderator": manager
    }).distinct("account"))
    return search_result


@BP.route("/manager", methods=["GET"])
def manager():
    """
    Handles the manager form on the home page.
    """
    manager_form = ManagerForm()
    search_result = moderator_search(manager_form.manager.data)
    if len(search_result) == 1:
        # TODO: Redirect to manager's page
        return "{}'s page...".format(search_result[0])
    return jsonify(search_result)


@BP.route("/moderator", methods=["GET"])
def moderator():
    """
    Handles the moderator form on the home page.
    """
    moderator_form = ModeratorForm()
    search_result = moderator_search(moderator_form.moderator.data, False)
    if len(search_result) == 1:
        # TODO: Redirect to moderator's page
        return "{}'s page...".format(search_result[0])
    return jsonify(search_result)


def contributor_search(data):
    posts = DB.posts
    search_result = posts.find({"author": {"$regex": data}})
    return list(search_result.distinct("author"))


@BP.route("/contributor", methods=["GET"])
def contributor():
    """
    Handles the contributor form on the home page.
    """
    contributor_form = ContributorForm()
    search_result = contributor_search(contributor_form.contributor.data)
    if len(search_result) == 1:
        # TODO: Redirect to contributor's page
        return "{}'s page...".format(search_result[0])
    return jsonify(search_result)


def project_search(data):
    posts = DB.posts
    search_result = posts.find({"repository.full_name": {"$regex": data}})
    return list(search_result.distinct("repository.full_name"))


@BP.route("/project", methods=["GET"])
def project():
    """
    Handles the project form on the home page.
    """
    project_form = ProjectForm()
    search_result = project_search(project_form.project.data)
    if len(search_result) == 1:
        # TODO: Redirect to project's page
        return "{}'s page...".format(search_result[0])
    return jsonify(search_result)


def search(data):
    """
    Returns lists of managers, moderators, contributors and projects that match
    the given data.
    """
    managers = moderator_search(data, manager=True)
    moderators = moderator_search(data, manager=False)
    contributors = contributor_search(data)
    projects = project_search(data)
    return managers, moderators, contributors, projects


@BP.route("/search", methods=["GET"])
def index():
    """
    Handles the search form in the header.
    """
    search_form = SearchForm()
    managers, moderators, contributors, projects = search(search_form.q.data)
    return render_template("search/index.html",
        managers=managers,
        moderators=moderators,
        contributors=contributors,
        projects=projects
    )
