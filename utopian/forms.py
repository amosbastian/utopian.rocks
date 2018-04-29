"""
File to store all the forms used across the application.
"""
from flask import request
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class ManagerForm(FlaskForm):
    """
    Form for handling the community manager search on the home page.
    """
    manager = StringField(
        "Username",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Community manager",
            "id": "community-manager"
        }
    )


class ModeratorForm(FlaskForm):
    """
    Form for handling the moderator search on the home page.
    """
    moderator = StringField(
        "Username",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Moderator",
            "id": "moderator"
        }
    )


class ContributorForm(FlaskForm):
    """
    Form for handling the contributor search on the home page.
    """
    contributor = StringField(
        "Username",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Contributor",
            "id": "contributor"
        }
    )


class ProjectForm(FlaskForm):
    """
    Form for handling the project search on the home page.
    """
    project = StringField(
        "Project",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Project",
            "id": "project"
        }
    )


class SearchForm(FlaskForm):
    """
    Form for handling the overall search on Utopian.info.
    """
    q = StringField(
        "Search",
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Search Utopian.info"
        }
    )

    def __init__(self, *args, **kwargs):
        if "formdata" not in kwargs:
            kwargs["formdata"] = request.args
        if "csrf_enabled" not in kwargs:
            kwargs["csrf_enabled"] = False
        super(SearchForm, self).__init__(*args, **kwargs)