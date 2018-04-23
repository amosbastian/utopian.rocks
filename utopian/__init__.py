"""
Script used to run the Flask application.
"""
import os

from flask import Flask, render_template
from pymongo import MongoClient

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

    return app
