from flask import Flask, render_template
from pymongo import MongoClient
import datetime
import json

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
    return dict(updated=last_updated())


def categories_information(posts):
    post_dictionary = {"total": {"moderated": 0, "accepted": 0,
        "rejected": 0, "moderators": []}}
    for post in posts:
        category = post["category"]
        moderator = post["moderator"]["account"]
        post_dictionary.setdefault(category, {
            "moderated": 0,
            "accepted": 0,
            "rejected": 0,
            "moderators": []
        })

        if post["moderator"]["flagged"]:
            post_dictionary[category]["rejected"] += 1
            post_dictionary["total"]["rejected"] += 1
        else:
            post_dictionary[category]["accepted"] += 1
            post_dictionary["total"]["accepted"] += 1
        post_dictionary[category]["moderated"] += 1
        post_dictionary["total"]["moderated"] += 1
        post_dictionary[category]["moderators"].append(moderator)
        post_dictionary["total"]["moderators"].append(moderator)

    post_list = []

    # Create list with average amount of contributions per category
    for key, value in post_dictionary.items():
        value["moderators"] = list(set(value["moderators"]))
        value["average"] = float(value["moderated"]) / len(value["moderators"])
        value["percentage"] = percentage(value["moderated"], value["accepted"])
        post_list.append({"category": key, "statistics": value})

    # Sort alphabetically and move "total" to the end of the list
    post_list = sorted(post_list, key=lambda x: x["category"])
    for category in post_list:
        if category["category"] == "total":
            post_list.append(category)
            post_list.remove(category)
    return post_list

from collections import Counter

def category_ratio(posts):
    categories = {"total": {"moderated": 0, "pending": 0, "total": 0, "accepted": 0, "rejected": 0}}
    authors = {"total": {}}
    moderators = {"total": {}}
    for post in posts:
        category = post["category"]
        if "task" in category:
            continue
        if post["status"] == "pending":
            categories[category]["pending"] += 1
            categories["total"]["pending"] += 1
            continue
        author = post["author"]
        moderator = post["moderator"]["account"]
        categories.setdefault(category, {"moderated": 0, "pending": 0, "total": 0, "accepted": 0, "rejected": 0})
        
        authors.setdefault(category, {})
        authors["total"].setdefault(author, {"total": 0, "accepted": 0, "rejected": 0})
        authors[category].setdefault(author, {"total": 0, "accepted": 0, "rejected": 0})

        moderators.setdefault(category, {})
        moderators["total"].setdefault(moderator, {"total": 0, "accepted": 0, "rejected": 0})
        moderators[category].setdefault(moderator, {"total": 0, "accepted": 0, "rejected": 0})
        if post["moderator"]["flagged"]:
            moderators[category][moderator]["rejected"] += 1
            moderators["total"][moderator]["rejected"] += 1
            authors[category][author]["rejected"] += 1
            authors["total"][author]["rejected"] += 1
            categories[category]["rejected"] += 1
            categories["total"]["rejected"] += 1
        else:
            moderators[category][moderator]["accepted"] += 1
            moderators["total"][moderator]["accepted"] += 1
            authors[category][author]["accepted"] += 1
            authors["total"][author]["accepted"] += 1
            categories[category]["accepted"] += 1
            categories["total"]["accepted"] += 1

        moderators["total"][moderator]["total"] += 1
        moderators[category][moderator]["total"] += 1
        authors["total"][author]["total"] += 1
        authors[category][author]["total"] += 1
        categories[category]["moderated"] += 1
        categories["total"]["moderated"] += 1

    for category in moderators:
        moderator_list = []
        for key, value in moderators[category].items():
            total = value["total"]
            value["accepted_percentage"] = percentage(total, value["accepted"])
            value["rejected_percentage"] = percentage(total, value["rejected"])
            value["moderator"] = key
            moderator_list.append(value)
        most_active = sorted(moderator_list, key=lambda x: x["total"], reverse=True)[:5]
        moderators[category].clear()
        moderators[category] = most_active

    for category in authors:
        author_list = []
        for key, value in authors[category].items():
            total = value["total"]
            contributed = value["accepted"] + value["rejected"]
            value["total_percentage"] = percentage(total, contributed)
            value["accepted_percentage"] = percentage(total, value["accepted"])
            value["rejected_percentage"] = percentage(total, value["rejected"])
            value["author"] = key
            author_list.append(value)
        best = sorted(author_list, key=lambda x: x["accepted"], reverse=True)[:5]
        worst = sorted(author_list, key=lambda x: x["rejected"], reverse=True)[:5]
        authors[category].clear()
        authors[category]["best"] = best
        authors[category]["worst"] = worst

    category_list = []
    for key, value in categories.items():
        value["total"] = value["pending"] + value["moderated"]
        value["total_percentage"] = percentage(value["total"], value["moderated"])
        value["accepted_percentage"] = percentage(value["total"], value["accepted"])
        value["rejected_percentage"] = percentage(value["total"], value["rejected"])
        value["pending_percentage"] = percentage(value["total"], value["pending"])
        category_list.append({"category": key, "statistics": value})

    categories = sorted(category_list, key=lambda x: x["statistics"]["total_percentage"])
    for category in categories:
        if category["category"] == "total":
            categories.append(category)
            categories.remove(category)
    
    return categories, authors, moderators


@app.route("/categories")
def categories():
    posts = db.posts
    week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    pipeline = [{
        "$match": {
            "$or": [{
                "status": "pending"
            },{
                "moderator.time": {"$gt": week_ago}
            }]
        }
    }]
    post_list = [post for post in posts.aggregate(pipeline)]
    information, authors, moderators = category_ratio(post_list)
    return render_template("categories.html", information=information,
        authors=authors, moderators=moderators)


def main():
    app.run(host="0.0.0.0", debug=True)


if __name__ == '__main__':
    main()
