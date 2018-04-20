"""
Script used to run the Flask application.
"""
import os

from flask import Flask, render_template


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

    @app.route("/")
    def index():
        """
        Returns the homepage's template.
        """
        return render_template("index.html")

    return app
