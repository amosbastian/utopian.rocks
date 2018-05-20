import datetime
import json
import os
from flask import Flask, jsonify, render_template
from pymongo import MongoClient

CLIENT = MongoClient()
DB = CLIENT.utempian
app = Flask(__name__)


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


def main():
    app.run(host="0.0.0.0")


if __name__ == '__main__':
    main()
