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


def overall_performance(posts):
    performance = {"categories": {}, "overall": {}}
    for post in posts:
        category = post["category"]
        performance["categories"].setdefault(category, {
            "moderated": 0,
            "accepted": 0,
            "rejected": 0
        })

        if post["moderator"]["flagged"]:
            performance["categories"][category]["rejected"] += 1
        else:
            performance["categories"][category]["accepted"] += 1
        performance["categories"][category]["moderated"] += 1

    categories = []
    for key, value in performance["categories"].items():
        category = {
            "category": key,
            "moderated": value["moderated"],
            "accepted": value["accepted"],
            "rejected": value["rejected"],
            "percentage": percentage(value["moderated"], value["accepted"])
        }
        categories.append(category)
    categories = sorted(categories, key=lambda x: x["moderated"], reverse=True)
    performance["categories"] = categories
    total_moderated = sum([category["moderated"] for category in categories])
    total_accepted = sum([category["accepted"] for category in categories])
    total_rejected = total_moderated - total_accepted
    total_percentage = percentage(total_moderated, total_accepted)

    performance["overall"] = {
        "moderated": total_moderated,
        "accepted": total_accepted,
        "rejected": total_rejected,
        "percentage": total_percentage
    }

    return performance


def individual_performance(posts):
    performance = {"moderators": {}, "overall": {}}
    for post in posts:
        category = post["category"]
        moderator = post["moderator"]["account"]
        performance["moderators"].setdefault(category, {})
        performance["moderators"][category].setdefault(moderator, {
            "moderated": 0,
            "accepted": 0,
            "rejected": 0
        })

        if post["moderator"]["flagged"]:
            performance["moderators"][category][moderator]["rejected"] += 1
        else:
            performance["moderators"][category][moderator]["accepted"] += 1
        performance["moderators"][category][moderator]["moderated"] += 1

    for category in performance["moderators"]:
        moderators = []
        for key, value in performance["moderators"][category].items():
            moderator = {
                "moderator": key,
                "moderated": value["moderated"],
                "accepted": value["accepted"],
                "rejected": value["rejected"],
                "percentage": percentage(value["moderated"], value["accepted"])
            }
            moderators.append(moderator)
        moderators = sorted(moderators, key=lambda x: x["moderated"], reverse=True)
        performance["moderators"][category] = moderators

        total_moderated = sum([m["moderated"] for m in moderators])
        total_accepted = sum([m["accepted"] for m in moderators])
        total_rejected = total_moderated - total_accepted
        total_percentage = percentage(total_moderated, total_accepted)

        performance["overall"][category] = {
            "moderated": total_moderated,
            "accepted": total_accepted,
            "rejected": total_rejected,
            "percentage": total_percentage
        }
    
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
    return overall_performance(team_posts), individual_performance(team_posts)


@app.route("/team/<supervisor>")
def team(supervisor):
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=7)
    team_performance, category_performance = peformance(supervisor)
    return  render_template("team.html", supervisor=supervisor,
        team_performance=team_performance, today=today, week_ago=week_ago,
        category_performance=category_performance)


@app.route("/test")
def test():
    return render_template("test.html")


def last_updated():
    posts = db.posts
    for post in posts.find().sort([("$natural", -1)]).limit(1):
        updated = post["moderator"]["time"]
    return updated


@app.context_processor
def inject_updated():
    return dict(updated=last_updated())


def main():
    app.run(host="0.0.0.0", debug=True)


if __name__ == '__main__':
    main()
