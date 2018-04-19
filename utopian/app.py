from flask import Flask, render_template, request, url_for, redirect
from pymongo import MongoClient
from dateutil.parser import parse
import datetime
import json
import timeago
from bokeh.core.properties import value
from bokeh.io import show, output_file
from bokeh.models import ColumnDataSource, HoverTool, Legend
from bokeh.plotting import figure, output_file, show
from bokeh.embed import components
from collections import Counter

client = MongoClient()
db = client.utopian

app = Flask(__name__)


def get_cms():
    """
    Get a list of all the names of all current supervisors, with the exception
    of Elear.
    """
    moderators = db.moderators
    cms = [moderator["account"] for moderator in
           moderators.find({"supermoderator": True})]

    return cms


@app.route("/")
def index():
    # supervisors = get_supervisors()
    # return render_template("index.html", supervisors=supervisors)
    return redirect(url_for("moderator", username="amosbastian"))


def percentage(moderated, accepted):
    """
    Helper function used to calculate the accepted / rejected percentage.
    """
    if accepted == 0:
        return 0
    elif moderated == accepted:
        return 100
    else:
        return float(accepted) / moderated * 100


def moderator_points(category):
    if category == "ideas":
        return 2.0
    elif category == "development":
        return 4.25
    elif category == "translations":
        return 4.0
    elif category == "graphics":
        return 3.0
    elif category == "documentation":
        return 2.25
    elif category == "copywriting":
        return 2.0
    elif category == "tutorials":
        return 4.0
    elif category == "analysis":
        return 3.25
    elif category == "social":
        return 2.0
    elif category == "blog":
        return 2.25
    elif category == "video-tutorials":
        return 4.0
    elif category == "bug-hunting":
        return 3.25
    elif category == "task-ideas":
        return 1.25
    elif category == "task-development":
        return 1.25
    elif category == "task-bug-huntung":
        return 1.25
    elif category == "task-translations":
        return 1.25
    elif category == "task-graphics":
        return 1.25
    elif category == "task-documentation":
        return 1.25
    elif category == "task-analysis":
        return 1.25
    elif category == "task-social":
        return 1.25
    elif category == "overall":
        return 0


def last_updated():
    """
    Returns the moderation time of the most recently moderated post in the
    database.
    """
    posts = db.posts
    for post in posts.find().sort([("$natural", -1)]).limit(1):
        updated = post["updated"]
    return updated.strftime("%Y-%m-%d %H:%M:%S")


def moderators_list():
    moderator_list = []
    moderators = db.moderators
    for moderator in moderators.find():
        moderator_list.append(moderator["account"])
    return moderator_list


@app.context_processor
def inject_updated():
    moderators = moderators_list()
    categories = sorted([
        "copywriting", "social", "blog", "graphics", "ideas",
        "development", "bug-hunting", "translations", "tutorials",
        "video-tutorials", "analysis", "documentation", "all"])
    return dict(
        updated=last_updated(), categories=categories, moderators=moderators)


def category_plot(dates, accepted, rejected):
    dates = dates
    status = ["Accepted", "Rejected"]
    colours = ["#9975b9", "#3a404d"]

    percentages = ["{:.1f}".format(percentage(x[0] + x[1], x[0]))
                   for x in zip(accepted, rejected)]
    data = {"dates": dates, "Accepted": accepted, "Rejected": rejected,
            "percentages": percentages}

    source = ColumnDataSource(data=data)

    p = figure(
        x_range=dates, plot_height=250, sizing_mode="stretch_both",
        toolbar_location=None, tools="")

    p.vbar_stack(
        status, x="dates", width=0.9, color=colours, source=source,
        legend=[value(x) for x in status])

    p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    p.legend.location = "top_right"
    p.legend.orientation = "horizontal"

    script, div = components(p)
    return script, div


def moderator_leaderboard(moderators, N):
    """
    Return a list of the N most active moderators.
    """
    moderator_list = []
    for key, value in moderators.items():
        value["moderator"] = key
        value["percentage"] = percentage(value["total"], value["accepted"])
        moderator_list.append(value)
    return sorted(moderator_list, key=lambda x: x["total"], reverse=True)[:N]


def leaderboard(users, N, user):
    """
    Return a list containing the best users and a list containing the
    worst users.
    """
    user_list = []
    for key, value in users.items():
        value[user] = key
        value["percentage"] = percentage(value["total"], value["accepted"])
        user_list.append(value)
    best = sorted(user_list, key=lambda x: x["accepted"], reverse=True)[:N]
    worst = sorted(user_list, key=lambda x: x["rejected"], reverse=True)[:N]
    return best, worst


def category_information(posts):
    """
    One big function for collecting all relevant information about the given
    category. Could probably be done better...
    """
    today = datetime.date.today()
    date = today - datetime.timedelta(days=6)
    category = {"pending": 0, "total": 0, "accepted": 0, "rejected": 0}
    authors = {}
    moderators = {}
    dates = {}
    while date <= today:
        dates[str(date)] = {"accepted": 0, "rejected": 0}
        date += datetime.timedelta(days=1)

    for post in posts:
        if post["status"] == "pending":
            category["pending"] += 1
            category["total"] += 1
            continue

        # Get author and moderator and set default is applicable
        author = post["author"]
        authors.setdefault(author, {"total": 0, "accepted": 0, "rejected": 0})
        moderator = post["moderator"]["account"]
        moderators.setdefault(
            moderator, {"total": 0, "accepted": 0, "rejected": 0})

        # Post was rejected
        if post["moderator"]["flagged"]:
            category["rejected"] += 1
            moderators[moderator]["rejected"] += 1
            authors[author]["rejected"] += 1
            dates[str(post["moderator"]["time"].date())]["rejected"] += 1
        # Post was accepted
        else:
            category["accepted"] += 1
            moderators[moderator]["accepted"] += 1
            authors[author]["accepted"] += 1
            dates[str(post["moderator"]["time"].date())]["accepted"] += 1

        # Add to total
        category["total"] += 1
        moderators[moderator]["total"] += 1
        authors[author]["total"] += 1

    # Add moderator leaderboard
    category["moderators"] = moderator_leaderboard(moderators, 10)
    best, worst = leaderboard(authors, 10, "author")
    # Add author leaderboard
    category["best_authors"] = best
    category["worst_authors"] = worst
    # Create plot and script
    accepted = [date["accepted"] for date in dates.values()]
    rejected = [date["rejected"] for date in dates.values()]
    dates = list(dates.keys())
    script, plot = category_plot(dates, accepted, rejected)
    category["plot"] = plot
    category["script"] = script
    # Calculate percentages for progress bar
    total = category["total"]
    category["accepted_percentage"] = percentage(total, category["accepted"])
    category["rejected_percentage"] = percentage(total, category["rejected"])
    category["pending_percentage"] = percentage(total, category["pending"])
    return category


def category_colour(category):
    if category == "ideas":
        return "#54d2a0"
    elif category == "development":
        return "#000000"
    elif category == "translations":
        return "#ffce3d"
    elif category == "graphics":
        return "#f6a623"
    elif category == "documentation":
        return "#b1b1b1"
    elif category == "copywriting":
        return "#008080"
    elif category == "tutorials":
        return "#782c51"
    elif category == "analysis":
        return "#164265"
    elif category == "social":
        return "#7ec2f3"
    elif category == "blog":
        return "#0275d8"
    elif category == "video-tutorials":
        return "#ec3324"
    elif category == "bug-hunting":
        return "#d9534f"
    elif category == "all":
        return "#7954A7"


def category_piechart(categories):
    from numpy import pi, cumsum
    percents = [c["percentage"] for c in categories]
    percents = list(cumsum(percents))
    percents.insert(0, 0)
    starts = [p * 2 * pi for p in percents[:-1]]
    ends = [p * 2 * pi for p in percents[1:]]
    colors = [category_colour(c["category"]) for c in categories]
    total = sum([c["count"] for c in categories])

    p = figure(x_range=(-1, 1), y_range=(-1, 1), sizing_mode="scale_height",
               toolbar_location=None, tools="",
               title="Total pending: {}".format(total))

    p.title.align = "center"

    p.wedge(x=0, y=0, radius=1, start_angle=starts, end_angle=ends,
            color=colors)

    p.axis.visible = False
    p.ygrid.visible = False
    p.xgrid.visible = False

    script, div = components(p)
    return script, div


def all_piechart():
    posts = db.posts
    information = {"all": 0}
    for post in posts.find({"status": "pending"}):
        information.setdefault(post["category"], 0)
        information[post["category"]] += 1
        information["all"] += 1

    categories = []
    for category in information:
        if category == "all":
            continue
        pct = percentage(information["all"], information[category]) / 100.0
        categories.append({"category": category, "percentage": pct,
                           "count": information[category]})

    script, div = category_piechart(categories)
    return script, div


@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for("moderator", username="amosbastian"))


@app.route("/category/<category>")
def categories(category):
    posts = db.posts
    all_piechart()
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1
    limit = 8 * page
    skip = limit - 8

    week_ago = datetime.datetime.now() - datetime.timedelta(days=6)
    week_ago = datetime.datetime.combine(
        week_ago, datetime.datetime.min.time())
    if not category == "all":
        pipeline = [{"$match": {"$or": [{"status": "pending"}, {
            "moderator.time": {"$gt": week_ago}}], "category": category}}]
        post_list = [post for post in posts.find({
                     "category": category,
                     "status": {"$ne": "pending"}}).sort(
                     "moderator.time", -1).skip(skip).limit(10)]
    else:
        pipeline = [{"$match": {"$or": [{"status": "pending"}, {
            "moderator.time": {"$gt": week_ago}}]}}]
        post_list = [post for post in posts.find({
                     "status": {"$ne": "pending"}}).sort(
                     "moderator.time", -1).skip(skip).limit(10)]

    post_weekly = [post for post in posts.aggregate(pipeline)]
    information = category_information(post_weekly)

    post_list = sorted(post_list, key=lambda x: x["moderator"]["time"],
                       reverse=True)

    next_url = url_for("categories", category=category, page=[page + 1])
    previous_url = url_for("categories", category=category, page=[page - 1])
    script, div = all_piechart()

    return render_template(
        "category/reviews.html",
        category=category,
        information=information,
        page=page,
        post_list=post_list[skip:limit],
        next=next_url,
        previous=previous_url,
        script=script,
        div=div)


@app.route("/category/<category>/moderators")
def category_moderators(category):
    posts = db.posts
    all_piechart()

    week_ago = datetime.datetime.now() - datetime.timedelta(days=6)
    week_ago = datetime.datetime.combine(
        week_ago, datetime.datetime.min.time())
    if not category == "all":
        pipeline = [{"$match": {"$or": [{"status": "pending"}, {
            "moderator.time": {"$gt": week_ago}}], "category": category}}]
    else:
        pipeline = [{"$match": {"$or": [{"status": "pending"}, {
            "moderator.time": {"$gt": week_ago}}]}}]

    post_weekly = [post for post in posts.aggregate(pipeline)]
    information = category_information(post_weekly)

    script, div = all_piechart()

    return render_template(
        "category/moderators.html",
        category=category,
        information=information,
        script=script,
        div=div)


@app.route("/category/<category>/contributors")
def category_contributors(category):
    posts = db.posts
    all_piechart()

    week_ago = datetime.datetime.now() - datetime.timedelta(days=6)
    week_ago = datetime.datetime.combine(
        week_ago, datetime.datetime.min.time())
    if not category == "all":
        pipeline = [{"$match": {"$or": [{"status": "pending"}, {
            "moderator.time": {"$gt": week_ago}}], "category": category}}]
    else:
        pipeline = [{"$match": {"$or": [{"status": "pending"}, {
            "moderator.time": {"$gt": week_ago}}]}}]

    post_weekly = [post for post in posts.aggregate(pipeline)]
    information = category_information(post_weekly)

    script, div = all_piechart()

    return render_template(
        "category/contributors.html",
        category=category,
        information=information,
        script=script,
        div=div)


@app.template_filter("timeago")
def time_ago(date):
    return timeago.format(date)


def categories_moderated(posts):
    categories = []
    accepted = 0
    rejected = 0
    for post in posts:
        if post["status"] == "pending":
            continue
        if post["moderator"]["flagged"]:
            rejected += 1
        else:
            accepted += 1
        categories.append(post["category"])
    return Counter(categories).most_common(3), accepted, rejected


def moderator_activity(posts, moderating_since):
    authors = {}
    delta = datetime.datetime.now() - moderating_since
    dates = [str((moderating_since + datetime.timedelta(days=i)).date())
             for i in range(delta.days + 2)]

    data = {"all": [0] * len(dates)}
    for post in posts:
        category = post["category"]
        author = post["author"]
        if "task" in category or "sub" in category:
            continue
        authors.setdefault(author, {"total": 0, "accepted": 0, "rejected": 0})
        date = str(post["moderator"]["time"].date())
        data.setdefault(category, [0] * len(dates))

        index = dates.index(date)

        if post["moderator"]["flagged"]:
            authors[author]["rejected"] += 1
        else:
            authors[author]["accepted"] += 1

        authors[author]["total"] += 1
        data[category][index] += 1
        data["all"][index] += 1

    data["dates"] = [parse(date) for date in dates]
    best, worst = leaderboard(authors, 10, "author")
    return data, best, worst


def activity_plot(activity):
    x = activity["dates"]
    p = figure(plot_width=1100, plot_height=500, x_axis_type="datetime")

    legend = []
    for category, y in activity.items():
        if not category == "dates":
            colour = category_colour(category)
            line = p.line(
                x, y, line_width=2, color=colour, alpha=0.8,
                muted_color=colour, muted_alpha=0.2, name=category)
            legend.append((category.replace("-", " ").title(), [line]))
    legend = Legend(items=legend, location=(0, 0))

    p.add_tools(HoverTool(
        names=["all"],
        tooltips=[
            ("date", "@x{%F}"),
            ("moderated", "@y")
        ],
        formatters={
            "x": "datetime",
        },
        mode="vline"
    ))

    p.add_layout(legend, "right")
    p.legend.click_policy = "mute"
    script, div = components(p)
    return script, div


def moderator_categories(posts):
    categories = {}
    for post in posts:
        category = post["category"]
        categories.setdefault(category, {"accepted": 0, "rejected": 0})

        if post["moderator"]["flagged"]:
            categories[category]["rejected"] += 1
        else:
            categories[category]["accepted"] += 1

    category_list = []
    for key, value in categories.items():
        value["category"] = key
        value["total"] = value["accepted"] + value["rejected"]
        value["percentage"] = percentage(value["total"], value["accepted"])
        category_list.append(value)

    return sorted(category_list, key=lambda x: x["category"])


def information(post_list, is_moderator):
    if is_moderator:
        since = post_list[-1]["moderator"]["time"]
    else:
        since = post_list[-1]["created"]
    categories, accepted, rejected = categories_moderated(post_list)
    categories_formatted = [c[0].replace("-", " ").title() for c in categories]

    return since.date(), categories_formatted, accepted, rejected


def calculate_points(username):
    if username in get_cms():
        cm = True
        total = 100
    else:
        cm = False
        total = 0

    posts = db.posts
    week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    pipeline = [{"$match": {
        "moderator.time": {"$gt": week_ago}, 
        "moderator.account": username
    }}]

    post_list = [post for post in posts.aggregate(pipeline)]

    pts = sum([moderator_points(post["category"]) for post in post_list])
    return round(total + pts)


@app.route("/moderator/<username>")
def moderator(username):
    moderators = db.moderators
    moderator_list = [moderator["account"] for moderator in moderators.find()]
    if username not in moderator_list:
        return redirect(url_for("moderator", username="amosbastian"))
    posts = db.posts
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1
    limit = 10 * page
    skip = limit - 10

    post_list = [post for post in posts.find({"moderator.account": username})]

    # Add empty repository if it doesn't exist
    for post in post_list:
        if post["repository"] is None:
            post["repository"] = {"owner": {"login": "None"}}

    post_list = sorted(post_list, key=lambda x: x["moderator"]["time"],
                       reverse=True)

    next_url = url_for("moderator", username=username, page=[page + 1])
    previous_url = url_for("moderator", username=username, page=[page - 1])

    since, categories, accepted, rejected = information(post_list, True)

    points = calculate_points(username)
    return render_template(
        "moderator/reviews.html",
        username=username,
        post_list=post_list[skip:limit],
        page=page,
        next=next_url,
        previous=previous_url,
        since=since,
        categories=categories,
        accepted=accepted,
        rejected=rejected,
        percentage=percentage(accepted + rejected, accepted),
        points=points
    )


@app.route("/moderator/<username>/activity")
def m_activity(username):
    moderators = db.moderators
    moderator_list = [moderator["account"] for moderator in moderators.find()]
    if username not in moderator_list:
        return redirect(url_for("m_activity", username="amosbastian"))
    posts = db.posts

    post_list = [post for post in posts.find({"moderator.account": username})]
    post_list = sorted(post_list, key=lambda x: x["moderator"]["time"])

    moderating_since = post_list[0]["moderator"]["time"]

    # Calculate moderator's activity and create plot
    activity, _, _ = moderator_activity(post_list, moderating_since)
    script, div = activity_plot(activity)

    since, categories, accepted, rejected = information(post_list, True)
    points = calculate_points(username)
    return render_template(
        "moderator/activity.html",
        div=div,
        script=script,
        username=username,
        since=since,
        categories=categories,
        accepted=accepted,
        rejected=rejected,
        percentage=percentage(accepted + rejected, accepted),
        points=points
    )


@app.route("/moderator/<username>/contributors")
def moderator_contributors(username):
    moderators = db.moderators
    moderator_list = [moderator["account"] for moderator in moderators.find()]
    if username not in moderator_list:
        return redirect(url_for("moderator_contributors",
                                username="amosbastian"))
    posts = db.posts

    post_list = [post for post in posts.find({"moderator.account": username})]
    post_list = sorted(post_list, key=lambda x: x["moderator"]["time"])

    moderating_since = post_list[0]["moderator"]["time"]
    _, best, worst = moderator_activity(post_list, moderating_since)

    since, categories, accepted, rejected = information(post_list, True)
    points = calculate_points(username)
    return render_template(
        "moderator/contributors.html",
        best=best,
        worst=worst,
        username=username,
        since=since,
        categories=categories,
        accepted=accepted,
        rejected=rejected,
        percentage=percentage(accepted + rejected, accepted),
        points=points
    )


def contributor_activity(posts):
    moderators = {}

    for post in posts:
        moderator = post["moderator"]["account"]
        moderators.setdefault(
            moderator, {"total": 0, "accepted": 0, "rejected": 0})

        if post["moderator"]["flagged"]:
            moderators[moderator]["rejected"] += 1
        else:
            moderators[moderator]["accepted"] += 1

        moderators[moderator]["total"] += 1

    best, worst = leaderboard(moderators, 10, "moderator")
    return best, worst


@app.route("/contributor/<username>")
def contributor(username):
    posts = db.posts
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1
    limit = 10 * page
    skip = limit - 10

    post_list = [post for post in posts.find({"author": username}) if
                 not post["status"] == "pending"]

    if post_list == []:
        return redirect(url_for("contributor", username="amosbastian"))

    # Add empty repository if it doesn't exist
    for post in post_list:
        if post["repository"] is None:
            post["repository"] = {"owner": {"login": "None"}}

    post_list = sorted(post_list, key=lambda x: x["created"], reverse=True)

    next_url = url_for("contributor", username=username, page=[page + 1])
    previous_url = url_for("contributor", username=username, page=[page - 1])

    since, categories, accepted, rejected = information(post_list, False)

    return render_template(
        "contributor/reviews.html",
        username=username,
        post_list=post_list[skip:limit],
        page=page,
        next=next_url,
        previous=previous_url,
        since=since,
        categories=categories,
        accepted=accepted,
        rejected=rejected,
        percentage=percentage(accepted + rejected, accepted)
    )


@app.route("/contributor/<username>/moderators")
def contributor_moderators(username):
    posts = db.posts

    post_list = [post for post in posts.find({"author": username}) if
                 not post["status"] == "pending"]

    if post_list == []:
        return redirect(url_for("contributor_moderators",
                                username="amosbastian"))

    # Add empty repository if it doesn't exist
    for post in post_list:
        if post["repository"] is None:
            post["repository"] = {"owner": {"login": "None"}}

    best, worst = contributor_activity(post_list)

    since, categories, accepted, rejected = information(post_list, False)

    return render_template(
        "contributor/moderators.html",
        best=best,
        worst=worst,
        username=username,
        since=since,
        categories=categories,
        accepted=accepted,
        rejected=rejected,
        percentage=percentage(accepted + rejected, accepted)
    )


@app.route("/icon/<name>")
def icon(name):
    print(url_for("static", filename="img"))


def main():
    app.run(host="0.0.0.0")


if __name__ == '__main__':
    main()
