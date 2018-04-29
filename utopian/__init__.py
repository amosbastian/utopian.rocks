"""
Script used to run the Flask application.
"""
import os

from flask import Flask, render_template
from pymongo import MongoClient
from utopian.forms import SearchForm

CLIENT = MongoClient()
DB = CLIENT.utopian


def create_app(test_config=None):
    """
    Factory for Utopian.info.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import home
    app.register_blueprint(home.BP)

    from . import search
    app.register_blueprint(search.BP)

    @app.context_processor
    def inject_autocompletion():
        moderators = DB.moderators
        posts = DB.posts
        manager_list = [moderator["account"] for moderator in
                        moderators.find({"supermoderator": True})]
        moderator_list = [moderator["account"] for moderator in
                          moderators.find({"supermoderator": False})]
        contributor_list = posts.find().distinct("author")
        project_list = posts.find().distinct("repository.full_name")
        search_form = SearchForm()
        return dict(
            manager_list=manager_list,
            moderator_list=moderator_list,
            contributor_list=contributor_list,
            project_list=project_list,
            search_form=search_form
        )

    return app
