from flask import Flask, render_template
from pymongo import MongoClient
import datetime
import json
from bokeh.core.properties import value
from bokeh.io import show, output_file
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
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
        return reviewed * 0.5
    elif category == "development":
        return reviewed * 1.25
    elif category == "translations":
        return reviewed * 1.0
    elif category == "graphics":
        return reviewed * 0.75
    elif category == "copywriting":
        return reviewed * 0.5
    elif category == "tutorials":
        return reviewed * 0.75
    elif category == "analysis":
        return reviewed * 0.75
    elif category == "social":
        return reviewed * 0.5
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
    colours = ["#551a8b", "#9975b9"]

    data = {"dates": dates, "Accepted": accepted, "Rejected": rejected}

    source = ColumnDataSource(data=data)

    p = figure(x_range=dates, plot_height=250, sizing_mode="stretch_both")

    p.vbar_stack(status, x="dates", width=0.9, color=colours, source=source,
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
    date = today - datetime.timedelta(days=7)
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
    accepted = [date["accepted"] for date in dates.values()][1:]
    rejected = [date["rejected"] for date in dates.values()][1:]
    dates = list(dates.keys())[1:]
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
    week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
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


def main():
    app.run(host="0.0.0.0", debug=True)


if __name__ == '__main__':
    main()
