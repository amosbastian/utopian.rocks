import json
import os
from bson import json_util
from datetime import datetime, timedelta
from dateutil.parser import parse
from flask import Flask, jsonify, render_template
from flask_restful import Resource, Api
from pymongo import MongoClient
from webargs import fields, validate
from webargs.flaskparser import use_args, use_kwargs, parser, abort

CLIENT = MongoClient()
DB = CLIENT.utempian
app = Flask(__name__)
api = Api(app)


@app.route("/json/<json_file>")
def rewards(json_file):
    """
    Return all moderator's points for the given week.
    """
    filename = os.path.join(app.static_folder, "{}.json".format(json_file))
    try:
        with open(filename) as fp:
            data = json.load(fp)
        return jsonify(data)
    except:
        return jsonify("")


@app.route("/")
def index():
    """
    Sends all unreviewed contributions to index.html.
    """
    contributions = DB.contributions
    unreviewed = contributions.find({"status": "unreviewed"})
    return render_template("index.html", contributions=unreviewed)


def without_score(contribution):
    """
    Returns a contribution without the score.
    """
    return {x: contribution[x] for x in contribution if x != "score"}


class ContributionResource(Resource):
    """
    Endpoint for contributions in the spreadsheet.
    """
    query_parameters = {
        "category": fields.Str(),
        "status": fields.Str(),
        "author": fields.Str(),
        "moderator": fields.Str(),
        "staff_picked": fields.Bool()
    }

    @use_args(query_parameters)
    def get(self, query_parameters):
        """
        Uses the given query parameters to search for contributions in the
        database.
        """
        contributions = [json.loads(json_util.dumps(without_score(c)))
                         for c in DB.contributions.find(query_parameters)]
        return jsonify(contributions)


def string_to_date(input):
    """
    Converts a given string to a date.
    """
    if input == "today":
        return datetime.now()
    try:
        date = parse(input)
        return date
    except Exception as error:
        abort(422, errors=str(error))


class WeeklyResource(Resource):
    """
    Endpoint for weekly contribution data (requested).
    """
    def get(self, date):
        # Get date for retrieving posts
        date = string_to_date(date)
        week_ago = date - timedelta(days=7)

        # Retrieve contributions made in week before the given date
        contributions = DB.contributions
        pipeline = [{"$match": {"review_date": {"$gt": week_ago}}}]
        contribution_weekly = [json.loads(json_util.dumps(c))
                               for c in contributions.aggregate(pipeline)]

        return jsonify(contribution_weekly)


api.add_resource(WeeklyResource, "/api/weekly/<string:date>")
api.add_resource(ContributionResource, "/api/posts")


def main():
    app.run(host="0.0.0.0")


if __name__ == '__main__':
    main()
