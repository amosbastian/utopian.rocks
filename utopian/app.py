from flask import Flask, render_template
from pymongo import MongoClient
import datetime

client = MongoClient()
db = client.utopian

app = Flask(__name__)


def moderation_team(supervisor):
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
    if moderated == accepted:
        return 100
    elif accepted == 0:
        return 0
    else:
        return round(float(accepted) / moderated * 100)


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
            points_dictionary[key] += points
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
    return render_template("test.html")


def last_updated():
    posts = db.posts
    for post in posts.find().sort([("$natural", -1)]).limit(1):
        updated = post["moderator"]["time"]
    return updated.strftime("%Y-%m-%d %H:%M:%S")


@app.context_processor
def inject_updated():
    return dict(updated=last_updated())


def main():
    app.run(host="0.0.0.0", debug=True)


if __name__ == '__main__':
    main()
