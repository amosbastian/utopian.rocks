from flask import Flask, render_template
from pymongo import MongoClient
import datetime

client = MongoClient()
db = client.utopian

app = Flask(__name__)


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
    
    return supervisors


@app.route("/")
def index():
    supervisors = get_supervisors()
    return render_template("index.html", supervisors=supervisors)


def moderation_team(supervisor):
    moderators = db.moderators
    team = [moderator["account"] for moderator in
        moderators.find({"referrer": supervisor})]
    return team


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

    total_moderated = 0
    total_accepted = 0
    for category in performance["categories"]:
        moderated = performance["categories"][category]["moderated"]
        accepted = performance["categories"][category]["accepted"]
        total_moderated += moderated
        total_accepted += accepted
        performance["categories"][category]["percentage"] = percentage(moderated, accepted)

    total_rejected = total_moderated - total_accepted
    total_percentage = percentage(total_moderated, total_accepted)
    performance["overall"] = {
        "moderated": total_accepted,
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
        total_moderated = 0
        total_accepted = 0
        for moderator in performance["moderators"][category]:
            moderated = performance["moderators"][category][moderator]["moderated"]
            accepted = performance["moderators"][category][moderator]["accepted"]
            total_moderated += moderated
            total_accepted += accepted
            performance["moderators"][category][moderator]["percentage"] = percentage(
                moderated, accepted)
        
        total_rejected = total_moderated - total_accepted
        total_percentage = percentage(total_moderated, total_accepted)
        performance["overall"].setdefault(category, {
            "moderated": total_accepted,
            "accepted": total_accepted,
            "rejected": total_rejected,
            "percentage": total_percentage
        })
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
    team_performance, category_performance = peformance(supervisor)
    return  render_template("team.html", supervisor=supervisor,
        team_performance=team_performance,
        category_performance=category_performance)


def main():
    app.run(debug=True)


if __name__ == '__main__':
    main()