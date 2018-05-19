import datetime
import json
import os
from flask import Flask, jsonify, redirect, render_template, request, url_for
from pymongo import MongoClient

CLIENT = MongoClient()
DB = CLIENT.utempian
app = Flask(__name__)


@app.route("/json/<json_file>")
def rewards(json_file):
    filename = os.path.join(app.static_folder, "{}.json".format(json_file))
    try:
        with open(filename) as fp:
            data = json.load(fp)
        return jsonify(data)
    except:
        return jsonify("")


@app.route("/")
def index():
    contributions = DB.contributions
    unreviewed = contributions.find({"status": "unreviewed"})
    return render_template("index.html", contributions=unreviewed)


def main():
    app.run(host="0.0.0.0")


if __name__ == '__main__':
    main()
