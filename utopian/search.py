"""
Contains all the functions used for full text search on Utopian.info. Also used
for the /search route.
"""
from flask import Blueprint, render_template, jsonify
from pymongo import MongoClient
from utopian.forms import SearchForm

BP = Blueprint("search", __name__, url_prefix="/search")
CLIENT = MongoClient()
DB = CLIENT.utopian


def text_index():
    """
    Creates text index for author, moderator and repository name.
    """
    posts = DB.posts
    posts.drop_indexes()
    posts.create_index([
        ("author", "text"),
        ("moderator.account", "text"),
        ("repository.full_name", "text")
    ],
        language_override="en"
    )

    moderators = DB.moderators
    moderators.drop_indexes()
    moderators.create_index([
        ("account", "text")
    ])


def search(data):
    moderators = DB.moderators
    search_results = list(moderators.find({"$text": {"$search": data}}))
    for moderator in search_results:
        print(moderator)
    return jsonify(list(search_results))


@BP.route("/", methods=["GET"])
def index():
    search_form = SearchForm()
    return search(search_form.q.data)
