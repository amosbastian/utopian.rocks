import json
import logging
import os
from beem.comment import Comment
from bson import json_util
from collections import Counter
from datetime import datetime, timedelta
from dateutil.parser import parse
from flask import Flask, jsonify, render_template, abort
from flask_restful import Resource, Api
from pymongo import MongoClient
from statistics import mean
from webargs import fields, validate
from webargs.flaskparser import use_args, use_kwargs, parser, abort

# Score needed for a vote
MIN_SCORE = 10

# Logging
DIR_PATH = os.path.dirname(os.path.realpath(__file__))
LOGGER = logging.getLogger("utopian-io")
LOGGER.setLevel(logging.INFO)
FH = logging.FileHandler(f"{DIR_PATH}/test.log")
FH.setLevel(logging.DEBUG)
FORMATTER = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
FH.setFormatter(FORMATTER)
LOGGER.addHandler(FH)

# Mongo and Flask
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
        abort(404)


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


def average(score):
    """
    Returns the average score of the given list of scores.
    """
    try:
        return mean(score)
    except Exception:
        return 0


def percentage(reviewed, voted):
    """
    Returns the percentage of voted contributions.
    """
    try:
        return 100.0 * voted / reviewed
    except ZeroDivisionError:
        return 100.0


def moderator_statistics(contributions):
    """
    Returns a dictionary containing statistics about all moderators.
    """
    moderators = {}
    for contribution in contributions:
        if contribution["status"] == "unreviewed":
            continue
        moderator = contribution["moderator"]

        # If contribution was submitted by banned user skip it
        if moderator == "BANNED":
            continue

        # Set default in case moderator doesn't exist
        moderators.setdefault(
            moderator, {
                "moderator": moderator,
                "category": [],
                "average_score": []
            }
        )

        # Append scores and categories
        moderators[moderator]["average_score"].append(contribution["score"])
        moderators[moderator]["category"].append(contribution["category"])

    moderator_list = []
    for moderator, value in moderators.items():
        # Set new keys and append value to list
        value["category"] = Counter(value["category"]).most_common()
        value["average_score"] = average(value["average_score"])
        moderator_list.append(value)

    return {"moderators": moderator_list}


def category_statistics(contributions):
    """
    Returns a dictionary containing statistics about all categories.
    """
    categories = {}
    categories.setdefault(
        "all", {
            "category": "all",
            "average_score": [],
            "voted": 0,
            "not_voted": 0,
            "unvoted": 0,
            "task-requests": 0,
            "moderators": [],
            "rewarded_contributors": [],
            "total_payout": 0,
            "utopian_total": []
        }
    )
    for contribution in contributions:
        # Don't count unreviewed contributions
        if contribution["status"] == "unreviewed":
            continue
        category = contribution["category"]
        moderator = contribution["moderator"]
        author = contribution["author"]
        score = contribution["score"]
        total_payout = contribution["total_payout"]
        utopian_vote = contribution["utopian_vote"]

        # Set default in case category doesn't exist
        categories.setdefault(
            category, {
                "category": category,
                "average_score": [],
                "voted": 0,
                "not_voted": 0,
                "unvoted": 0,
                "moderators": [],
                "rewarded_contributors": [],
                "total_payout": 0,
                "utopian_total": []
            }
        )

        # Check if contribution was voted on or unvoted
        for category in [category, "all"]:
            if contribution["status"] == "unvoted":
                categories[category]["unvoted"] += 1
                categories[category]["not_voted"] += 1
            elif contribution["voted_on"]:
                categories[category]["voted"] += 1
            else:
                categories[category]["not_voted"] += 1

            # Add moderator, score and total payout in SBD
            categories[category]["moderators"].append(moderator)
            categories[category]["average_score"].append(score)
            categories[category]["total_payout"] += total_payout
            categories[category]["utopian_total"].append(utopian_vote)

            if score > 0:
                categories[category]["rewarded_contributors"].append(author)

    category_list = []
    for category, value in categories.items():
        # Set new keys and append value to list
        value["reviewed"] = value["voted"] + value["not_voted"]
        value["average_score"] = average(value["average_score"])
        value["moderators"] = Counter(value["moderators"]).most_common()
        value["rewarded_contributors"] = Counter(
            value["rewarded_contributors"]).most_common()
        value["average_payout"] = value["total_payout"] / value["reviewed"]
        value["pct_voted"] = percentage(value["reviewed"], value["voted"])

        # Add Utopian.io's vote statistics
        value["utopian_total"] = [vote for vote in value["utopian_total"]
                                  if vote != 0]
        value["average_utopian_vote"] = average(value["utopian_total"])
        value["utopian_total"] = sum(value["utopian_total"])
        category_list.append(value)

    return {"categories": category_list}


def project_statistics(contributions):
    """
    Returns a dictionary containing statistics about all projects.
    """
    projects = {}
    for contribution in contributions:
        # Don't count unreviewed contributions
        if contribution["status"] == "unreviewed":
            continue
        project = contribution["repository"]
        utopian_vote = contribution["utopian_vote"]

        # Set default in case category doesn't exist
        projects.setdefault(
            project, {
                "project": project,
                "average_score": [],
                "voted": 0,
                "not_voted": 0,
                "unvoted": 0,
                "task-requests": 0,
                "moderators": [],
                "average_payout": [],
                "total_payout": 0,
                "utopian_total": []
            }
        )

        # Check if contribution was voted on or unvoted
        if contribution["status"] == "unvoted":
            projects[project]["unvoted"] += 1
            projects[project]["not_voted"] += 1
        elif contribution["voted_on"]:
            projects[project]["voted"] += 1
        else:
            projects[project]["not_voted"] += 1

        # If contribution was a task request count this
        if "task" in contribution["category"]:
            projects[project]["task-requests"] += 1

        # Add moderator and score
        projects[project]["moderators"].append(contribution["moderator"])
        projects[project]["average_score"].append(contribution["score"])
        projects[project]["total_payout"] += contribution["total_payout"]
        projects[project]["utopian_total"].append(utopian_vote)

    project_list = []
    for project, value in projects.items():
        # Set new keys and append value to list
        value["reviewed"] = value["voted"] + value["not_voted"]
        value["average_score"] = average(value["average_score"])
        value["average_payout"] = value["total_payout"] / value["reviewed"]
        value["moderators"] = Counter(value["moderators"]).most_common()
        value["pct_voted"] = percentage(value["reviewed"], value["voted"])

        # Add Utopian.io's vote statistics
        value["utopian_total"] = [vote for vote in value["utopian_total"]
                                  if vote != 0]
        value["average_utopian_vote"] = average(value["utopian_total"])
        value["utopian_total"] = sum(value["utopian_total"])
        project_list.append(value)

    return {"projects": project_list}


def staff_pick_statistics(contributions):
    """
    Returns a list of contributions that were staff picked.
    """
    staff_picks = []
    for contribution in contributions:
        # If contribution wasn't staff picked skip it
        if not contribution["staff_picked"]:
            continue

        staff_picks.append(contribution)

    return {"staff_picks": staff_picks}


def task_request_statistics(contributions):
    """
    Returns a list of task requests.
    """
    task_requests = []
    for contribution in contributions:
        # If contribution wasn't staff picked skip it
        if "task" in contribution["category"]:
            task_requests.append(contribution)

    return {"task_requests": task_requests}


class WeeklyResource(Resource):
    """
    Endpoint for weekly contribution data (requested).
    """
    def get(self, date):
        LOGGER.info(f"Retrieving for {date}")
        try:
            # Get date for retrieving posts
            date = string_to_date(date)
            week_ago = date - timedelta(days=7)

            # Retrieve contributions made in week before the given date
            contributions = DB.contributions
            print(week_ago, date)
            pipeline = [
                {"$match": {"review_date": {"$gte": week_ago, "$lt": date}}}]
            contributions = [json.loads(json_util.dumps(c))
                             for c in contributions.aggregate(pipeline)]

            moderators = moderator_statistics(contributions)
            categories = category_statistics(contributions)
            projects = project_statistics(contributions)
            staff_picks = staff_pick_statistics(contributions)
            task_requests = task_request_statistics(contributions)

            return jsonify(
                [moderators, categories, projects, staff_picks, task_requests])
        except Exception as error:
            LOGGER.error(error)


api.add_resource(WeeklyResource, "/api/statistics/<string:date>")
api.add_resource(ContributionResource, "/api/posts")


def staff_pick_section(staff_picks):
    """
    Creates the staff pick section for the Utopian weekly post.
    """
    LOGGER.info("Generating staff pick statistics section...")
    section = ""
    for staff_pick in staff_picks["staff_picks"]:
        url = staff_pick["url"]
        post = Comment(url)
        title = post.json()["title"]

        # If title can't be retrieved set it to the post's URL
        if not title:
            title = url
        author = staff_pick['author']
        category = staff_pick['category']

        # Add staff pick to the string
        section += (
            f"&lt;a href='{url}'&gt;{title}&lt;/a&gt; by @{author} "
            f"[{category}]<br>[Image (contributor profile image / image from "
            "the post)]<br><br>[Paragraph: Background info on project etc.]"
            "<br><br>[Paragraph: CM review, including etc.]<br><br>"
            f"Total payout: {staff_pick['total_payout']:.2f} STU<br>"
            f"Number of votes: {staff_pick['total_votes']}<br><br>"
        )

    return section


def post_statistics_section(categories, contributions):
    """
    Creates the post statistics part for the Utopian weekly post.
    """
    LOGGER.info("Generating post statistics section...")
    section = (
        "<br><br># Utopian.io Post Statistics<br><br>"
        "The staff picked contributions are only a small (but exceptional) "
        "example of the mass of contributions reviewed and rewarded by "
        "Utopian.io.<br><br>"
    )

    # Get some statistics needed
    for category in categories["categories"]:
        reviewed = category["reviewed"]
        voted = category["voted"]
        utopian_total = category["utopian_total"]
        average_vote = category["average_utopian_vote"]
        if category["category"] == "all":
            break

    # Get contributions with highest payout and engagement
    highest_payout = sorted(
        contributions, key=lambda x: x["total_payout"], reverse=True)[0]
    most_engagement = sorted(
        contributions, key=lambda x: x["total_votes"], reverse=True)[0]
    title = Comment(most_engagement["url"]).title

    # Create the section with the above statistics
    section += (
        f"* Overall, the last week saw a total of {reviewed} posts, with "
        f"{voted} of them rewarded through an upvote by @utopian-io.<br>"
        "* In total, Utopian.io distributed an approximate of "
        f"{utopian_total:.2f} STU to contributors.<br>"
        "* The highest payout seen on any Utopian.io contribution this week "
        f"was {highest_payout['total_payout']} STU, with a total of "
        f"{highest_payout['total_votes']} votes received from the community."
        "<br>* The contribution that attracted the most engagement was "
        f"&lt;a href='{most_engagement['url']}'&gt;{title}&lt;/a&gt;, with no "
        f"less than {most_engagement['total_comments']} comments in its "
        "comment threads.<br>"
        f"* The average vote given by Utopian.io was worth {average_vote:.2f} "
        "STU.<br><br># Category Statistics<br><br>"
        "|Category|Reviewed|Rewarded|Total rewards|Top contributor|<br>"
        "|:-|:-|:-|-:|:-|<br>"
    )

    # Create the table with category statistics
    for category in categories["categories"]:
        # Skip if category is 'all' or is task
        if category["category"] == "all" or "task" in category["category"]:
            continue

        # Don't include category is no contributions were rewarded
        rewarded = category["voted"]
        if rewarded == 0:
            continue

        # Get all the data needed
        reviewed = category["reviewed"]
        rewards = f"{category['utopian_total']:.2f}"
        author = f"@{category['rewarded_contributors'][0][0]}"
        category = category["category"]

        # Add the row
        section += (
            f"|{category}|{reviewed}|{rewarded}|{rewards} STU|{author}|<br>")

    return section


@app.route("/weekly")
def weekly():
    """
    Returns weekly statistics in a format that can be posted on Steemit.
    """
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    contributions = DB.contributions
    pipeline = [
        {"$match": {"review_date": {"$gte": week_ago, "$lt": today}}}]
    contributions = [json.loads(json_util.dumps(c))
                     for c in contributions.aggregate(pipeline)]

    # Get the data needed for all statistics
    categories = category_statistics(contributions)
    staff_picks = staff_pick_statistics(contributions)

    # Get each section of the post
    try:
        staff_section = staff_pick_section(staff_picks)
        post_section = post_statistics_section(categories, contributions)
        LOGGER.info((staff_section + post_section))
    except Exception as error:
        LOGGER.error(error)
    return render_template("weekly.html", body=(staff_section + post_section))


def main():
    app.run(host="0.0.0.0")


if __name__ == '__main__':
    print(DIR_PATH)
    main()
