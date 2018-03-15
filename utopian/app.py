from flask import Flask, render_template
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

client = MongoClient()
db = client.utopian

app = Flask(__name__)


def moderation_team(supervisor):
    """
    Returns a list containing the names of moderators in a supervisor's team.
    """
    moderators = db.moderators
    team = [moderator["account"] for moderator in
        moderators.find({"referrer": supervisor})]
    team.append(supervisor)
    return team


def get_supervisors():
    """
    Get a list of all the names of all current supervisors, with the exception
    of Elear.
    """
    moderators = db.moderators
    supervisors = [moderator["account"] for moderator in 
        moderators.find({"supermoderator": True})]
    try:
        supervisors.remove("elear")
    except Exception as error:
        print(repr(error))
    
    supervisors = [(supervisor, len(moderation_team(supervisor)))
        for supervisor in supervisors]

    return sorted(supervisors, key=lambda x: x[1], reverse=True)


@app.route("/")
def index():
    supervisors = get_supervisors()
    return render_template("index.html", supervisors=supervisors)


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


def moderator_points(category, reviewed):
    if category == "ideas":
        return reviewed * 0.75
    elif category == "development":
        return reviewed * 2.0
    elif category == "translations":
        return reviewed * 1.25
    elif category == "graphics":
        return reviewed * 1.0
    elif category == "documentation":
        return reviewed * 0.75
    elif category == "copywriting":
        return reviewed * 0.75
    elif category == "tutorials":
        return reviewed * 1.0
    elif category == "analysis":
        return reviewed * 1.25
    elif category == "social":
        return reviewed * 1.0
    elif category == "blog":
        return reviewed * 0.75
    elif category == "video-tutorials":
        return reviewed * 1.25
    elif category == "bug-hunting":
        return reviewed * 1.0
    elif category == "task-ideas":
        return reviewed * 0.5
    elif category == "task-development":
        return reviewed * 0.5
    elif category == "task-bug-huntung":
        return reviewed * 0.5
    elif category == "task-translations":
        return reviewed * 0.5
    elif category == "task-graphics":
        return reviewed * 0.5
    elif category == "task-documentation":
        return reviewed * 0.5
    elif category == "task-analysis":
        return reviewed * 0.5
    elif category == "task-social":
        return reviewed * 0.5
    elif category == "overall":
        return 0

def individual_performance(posts, team):
    performance = {"categories": {"overall": {}}, "overall": []}
    for post in posts:
        category = post["category"]
        if "task" in category:
            continue
        moderator = post["moderator"]["account"]
        performance["categories"].setdefault(category, {})
        performance["categories"][category].setdefault(moderator, {
            "moderated": 0,
            "accepted": 0,
            "rejected": 0
        })
        performance["categories"]["overall"].setdefault(moderator, {
            "moderated": 0,
            "accepted": 0,
            "rejected": 0
        })

        if post["moderator"]["flagged"]:
            performance["categories"][category][moderator]["rejected"] += 1
            performance["categories"]["overall"][moderator]["rejected"] += 1
        else:
            performance["categories"][category][moderator]["accepted"] += 1
            performance["categories"]["overall"][moderator]["accepted"] += 1
        performance["categories"][category][moderator]["moderated"] += 1
        performance["categories"]["overall"][moderator]["moderated"] += 1

    categories = []
    points_dictionary = {}
    for moderator in team:
        points_dictionary[moderator] = 0
    for category in performance["categories"]:
        moderators = []
        for key, value in performance["categories"][category].items():
            points = moderator_points(category, value["moderated"])
            try:
                points_dictionary[key] += points
            except TypeError:
                continue
            moderator = {
                "moderator": key,
                "moderated": value["moderated"],
                "accepted": value["accepted"],
                "rejected": value["rejected"],
                "percentage": percentage(value["moderated"], value["accepted"]),
                "points": points
            }
            moderators.append(moderator)

        moderator_list = [moderator["moderator"] for moderator in moderators]

        # Add performance for each moderator, even if they didn't review
        for moderator in team:
            if not moderator in moderator_list:
                new_moderator = {"moderated": 0, "accepted": 0, "rejected": 0, 
                    "moderator": moderator, "percentage": 0, "points": 0}
                moderators.append(new_moderator)
        moderators = sorted(moderators, key=lambda x: x["moderator"])
        categories.append({"category": category, "moderators": moderators})
        
        total_moderated = sum([m["moderated"] for m in moderators])
        total_accepted = sum([m["accepted"] for m in moderators])
        total_rejected = total_moderated - total_accepted
        total_percentage = percentage(total_moderated, total_accepted)
        total_points = sum([m["points"] for m in moderators])

        performance["overall"].append({
            "category": category,
            "moderated": total_moderated,
            "accepted": total_accepted,
            "rejected": total_rejected,
            "percentage": total_percentage,
            "points": total_points
        })

    categories = sorted(categories, key=lambda x: x["category"])
    overall = sorted(performance["overall"], key=lambda x: x["category"])
    
    for category in categories:
        if category["category"] == "overall":
            for moderator in category["moderators"]:
                moderator["points"] += points_dictionary[moderator["moderator"]]
            categories.insert(0, categories.pop(categories.index(category)))
            
    total_points = sum([c["points"] for c in overall])
    
    for category in overall:
        if category["category"] == "overall":
            category["points"] += total_points
            overall.insert(0, overall.pop(overall.index(category)))
    performance["categories"] = categories
    performance["overall"] = overall

    return performance

def peformance(supervisor):
    posts = db.posts
    team = moderation_team(supervisor)
    week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    pipeline = [{
        "$match": {
            "$and": [{
                "moderator.account": {"$in": team}
            },{
                "moderator.time": {"$gt": week_ago}
            }]
        }
    }]
    team_posts = [post for post in posts.aggregate(pipeline)]
    return individual_performance(team_posts, team)


@app.route("/team/<supervisor>")
def team(supervisor):
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=7)
    team_performance = peformance(supervisor)
    return render_template("team.html", supervisor=supervisor, today=today,
        week_ago=week_ago, team_performance=team_performance)


@app.route("/test")
def test():
    """
    Route used for testing.
    """
    return render_template("test.html")


def last_updated():
    """
    Returns the moderation time of the most recently moderated post in the 
    database.
    """
    posts = db.posts
    for post in posts.find().sort([("$natural", -1)]).limit(1):
        updated = post["updated"]
    return updated.strftime("%Y-%m-%d %H:%M:%S")


@app.context_processor
def inject_updated():
    categories = sorted(["copywriting", "social", "blog", "graphics", "ideas",
        "development", "bug-hunting", "translations", "tutorials",
        "video-tutorials", "analysis", "documentation", "all"])
    return dict(updated=last_updated(), categories=categories)


def category_plot(dates, accepted, rejected):
    dates = dates
    status = ["Accepted", "Rejected"]
    colours = ["#9975b9", "#3a404d"]

    percentages = ["{:.1f}".format(percentage(x[0] + x[1], x[0]))
        for x in zip(accepted, rejected)]
    data = {"dates": dates, "Accepted": accepted, "Rejected": rejected,
        "percentages": percentages}

    source = ColumnDataSource(data=data)

    p = figure(x_range=dates, plot_height=250, sizing_mode="stretch_both",
        toolbar_location=None, tools="")

    p.vbar_stack(status, x="dates", width=0.9, color=colours, source=source,
        legend=[value(x) for x in status])

    p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.axis.minor_tick_line_color = None
    p.outline_line_color = None
    p.legend.location = "top_right"
    p.legend.orientation = "horizontal"
    p.add_tools(HoverTool(tooltips=[("Accepted", "@Accepted"),
        ("Rejected", "@Rejected"), ("%", "@percentages")]))

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


def author_leaderboard(authors, N):
    """
    Return a list containing the best authors and a list containing the
    worst authors.
    """
    author_list = []
    for key, value in authors.items():
        value["author"] = key
        value["percentage"] = percentage(value["total"], value["accepted"])
        author_list.append(value)
    best = sorted(author_list, key=lambda x: x["accepted"], reverse=True)[:N]
    worst = sorted(author_list, key=lambda x: x["rejected"], reverse=True)[:N]
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
        moderators.setdefault(moderator, {"total": 0, "accepted": 0,
            "rejected": 0})
        
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
    category["moderators"] = moderator_leaderboard(moderators, 5)
    best, worst = author_leaderboard(authors, 5)
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


@app.route("/category/<category>")
def categories(category):
    posts = db.posts
    week_ago = datetime.datetime.now() - datetime.timedelta(days=6)
    week_ago = datetime.datetime.combine(week_ago, datetime.datetime.min.time())
    if not category == "all":
        pipeline = [{"$match": {"$or": [{"status": "pending"},{
            "moderator.time": {"$gt": week_ago}}], "category": category}}]
    else:
        pipeline = [{"$match": {"$or": [{"status": "pending"},{
            "moderator.time": {"$gt": week_ago}}]}}]

    post_list = [post for post in posts.aggregate(pipeline)]
    information = category_information(post_list)
    return render_template("category.html", category=category,
        information=information)


@app.template_filter("timeago")
def time_ago(date):
    return timeago.format(date)


def categories_moderated(posts):
    categories = []
    accepted = 0
    rejected = 0
    for post in posts:
        if post["moderator"]["flagged"]:
            rejected += 1
        else:
            accepted += 1
        categories.append(post["category"])
    return list(set(categories)), accepted, rejected


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
    best, worst = author_leaderboard(authors, 10)
    return data, best, worst
    

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


def activity_plot(activity):
    x = activity["dates"]
    p = figure(plot_width=1100, plot_height=500, x_axis_type="datetime")

    legend = []
    for category, y in activity.items():
        if not category == "dates":
            colour = category_colour(category)
            line = p.line(x, y, line_width=2, color=colour, alpha=0.8,
                muted_color=colour, muted_alpha=0.2, name=category)
            legend.append((category.replace("-", " ").title(), [line]))
    legend = Legend(items=legend, location=(0, 0))

    p.add_tools(HoverTool(
        names=["all"],
        tooltips=[
            ( "date", "@x{%F}" ),
            ( "moderated", "@y")
        ],
        formatters={
            "x": "datetime",
        },
        mode="vline"
    ))

    p.add_layout(legend, "right")
    p.legend.click_policy="mute"
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


@app.route("/moderator/<username>")
def user(username):
    posts = db.posts
    moderators = db.moderators
    moderator = moderators.find_one({"account": username})

    post_list = [post for post in posts.find({"moderator.account": username})]
    post_list = sorted(post_list, key=lambda x: x["moderator"]["time"])

    # Add empty repository if it doesn't exist
    for post in post_list:
        if post["repository"] == None:
            post["repository"] = {"owner": {"login": "None"}}

    moderating_since = post_list[0]["moderator"]["time"]
    categories, accepted, rejected = categories_moderated(post_list)

    # Format categories for showing them in template
    categories_formatted = [c.replace("-", " ").title() for c in categories]

    # If too many categories just replace with "All"...
    if len(categories_formatted) > 10:
        categories_formatted = ["All"]
    
    # Calculate moderator's activity and create plot
    activity, best, worst = moderator_activity(post_list, moderating_since)
    script, div = activity_plot(activity)

    category_performance = moderator_categories(post_list)

    return render_template("moderator.html", username=username, 
        post_list=post_list, moderating_since=moderating_since.date(),
        category_list=sorted(categories), accepted=accepted, rejected=rejected,
        percentage=percentage(accepted + rejected, accepted),
        categories_formatted=sorted(categories_formatted), moderator=moderator,
        script=script, div=div, best=best, worst=worst,
        category_performance=category_performance)


def main():
    app.run(host="0.0.0.0", debug=True)


if __name__ == '__main__':
    main()
