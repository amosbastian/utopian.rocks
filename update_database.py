import json
from datetime import date, datetime, timedelta

import requests
from beem.account import Account
from beem.amount import Amount
from beem.comment import Comment
from beem.vote import Vote
from dateutil.parser import parse

import constants
from contribution import Contribution


VIPO_LIST = [vipo["account"] for vipo in constants.DB.vipo.find()]


class User():
    def __init__(self, row):
        self.name = row[0].replace("\n", "").rstrip()
        self.ban_length = float(row[1])
        self.ban_start = parse(row[2])
        self.banned = row[3]


def beneficiary_set(post):
    for beneficiary in post.json()["beneficiaries"]:
        if beneficiary["account"] == "utopian.pay":
            weight = beneficiary["weight"]
            if weight >= 500:
                return True
    return False


def valid_age(post):
    """Checks if post is within last twelve hours before payout."""
    account = constants.DB.accounts.find_one({"account": "utopian-io"})
    recharge_time = account["recharge_time"]
    hours, minutes, seconds = [int(x) for x in recharge_time.split(":")]
    recharging = timedelta(hours=hours, minutes=minutes, seconds=seconds)

    if post.time_elapsed() + recharging > timedelta(days=6, hours=12):
        return False
    return True


def contribution(row, status):
    """Convert row to dictionary, only selecting values we want."""
    contribution = Contribution(row)
    url = contribution.url

    if url == "":
        return

    database_contribution = constants.DB.contributions.find_one({"url": url})

    if contribution.staff_pick.lower() == "yes":
        staff_picked = True
    else:
        staff_picked = False

    try:
        review_date = parse(contribution.review_date)
    except Exception:
        review_date = datetime(1970, 1, 1)

    if ((datetime.now() - review_date).seconds > 561600 and
            status != "unreviewed"):
        return

    total_payout = 0

    # Check if post deleted
    try:
        comment = Comment(url)
    except Exception:
        return

    if database_contribution["comment_url"] != "":
        comment_url = database_contribution["comment_url"]
    elif (contribution.moderator != ""):
        for reply in comment.get_replies():
            if reply.author == contribution.moderator:
                review_date = reply["created"]
                comment_url = reply.permlink
                break
        else:
            review_date = datetime(1970, 1, 1)
            comment_url = ""
    else:
        comment_url = ""

    # Calculate total (pending) payout of contribution
    if comment.time_elapsed() > timedelta(days=7):
        total_payout = Amount(comment.json()["total_payout_value"]).amount
    else:
        total_payout = Amount(comment.json()["pending_payout_value"]).amount

    # Get votes, comments and author
    votes = comment.json()["net_votes"]
    comments = comment.json()["children"]
    author = comment.author

    # Add status for unvoted and pending
    if contribution.vote_status == "Unvoted":
        status = "unvoted"
    elif contribution.vote_status == "Pending":
        status = "pending"

    try:
        utopian_vote = Vote(f"{comment.authorperm}|utopian-io").sbd
    except Exception:
        voted_on = False
        utopian_vote = 0

    if utopian_vote:
        voted_on = True
    else:
        voted_on = False

    # Check for when contribution not reviewed
    if contribution.score == "":
        score = None
    else:
        try:
            score = float(contribution.score)
        except Exception:
            score = None

    # Create contribution dictionary and return it
    new_contribution = {
        "moderator": contribution.moderator.strip(),
        "author": author,
        "review_date": review_date,
        "url": url,
        "repository": contribution.repository,
        "category": contribution.category,
        "staff_picked": staff_picked,
        "picked_by": contribution.picked_by,
        "status": status,
        "score": score,
        "voted_on": voted_on,
        "total_payout": total_payout,
        "total_votes": votes,
        "total_comments": comments,
        "utopian_vote": utopian_vote,
        "created": comment["created"],
        "title": comment.title,
        "review_status": contribution.review_status.lower(),
        "comment_url": comment_url,
        "beneficiaries_set": beneficiary_set(comment),
        "is_vipo": author in VIPO_LIST,
        "valid_age": valid_age(comment)
    }

    return new_contribution


def get_reviewed():
    """Return all the rows in the most recent two review worksheets."""
    previous = constants.PREVIOUS_REVIEWED.get_all_values()
    current = constants.CURRENT_REVIEWED.get_all_values()
    reviewed = previous[1:] + current[1:]
    return reviewed


def get_unreviewed():
    """Return all the rows in the unreviewed worksheet."""
    unreviewed = constants.UNREVIEWED.get_all_values()
    return unreviewed[1:]


def update_posts(local=False):
    """Adds all reviewed and unreviewed contributions to the database."""
    contributions = constants.DB.contributions
    if local:
        with open(f"{constants.DIR_PATH}/contributions.json") as json_data:
            posts = json.load(json_data)

        for post in posts:
            if "created" in post.keys():
                post["created"] = parse(post["created"])
            if "review_date" in post.keys():
                post["review_date"] = parse(post["review_date"])
    else:
        reviewed = get_reviewed()
        unreviewed = get_unreviewed()
        reviewed = [contribution(x, "reviewed") for x in reviewed]
        unreviewed = [contribution(x, "unreviewed") for x in unreviewed]
        posts = reviewed + unreviewed

    for post in posts:
        if post:
            contributions.replace_one({"url": post["url"]}, post, True)


def update_banned():
    """Updates banned users."""
    users = constants.DB.users

    for user in constants.BANNED_USERS.get_all_values()[1:]:
        try:
            user = User(user)
        except ValueError:
            continue

        banned_until = user.ban_start + timedelta(days=user.ban_length)
        user.banned_until = banned_until

        if user.banned == "Yes":
            user.banned = True
        else:
            user.banned = False

        users.update({"name": user.name}, user.__dict__, upsert=True)


def update_account():
    """Updates utopian-io account data."""
    account = Account("utopian-io")
    current_vp = account.get_voting_power()
    recharge_time = account.get_recharge_time_str(constants.VOTE_THRESHOLD)
    recharge_timedelta = account.get_recharge_timedelta(
        constants.VOTE_THRESHOLD)

    if recharge_time == 0 or recharge_timedelta == 0:
        recharge_class = "recharge--low"
    elif recharge_timedelta > timedelta(hours=1):
        recharge_class = "recharge--high"
    elif (recharge_timedelta < timedelta(hours=1) and
          recharge_timedelta > timedelta(minutes=30)):
        recharge_class = "recharge--average"
    else:
        recharge_class = "recharge--low"

    accounts = constants.DB.accounts
    accounts.update(
        {"account": "utopian-io"},
        {
            "account": "utopian-io",
            "current_vp": current_vp,
            "recharge_time": recharge_time,
            "recharge_class": recharge_class,
            "updated": datetime.now()
        },
        upsert=True
    )


def update_moderators():
    """Update moderators who reviewed something in the last 2 weeks."""
    reviewed = get_reviewed()
    accounts = set([row[0] for row in reviewed])
    moderators = constants.DB.moderators

    for account in accounts:
        if account.upper() not in ["BANNED", "IGNORED", "IGNORE",
                                   "IRRELEVANT"]:
            moderators.update(
                {"account": account.lower()},
                {"account": account.lower()}, upsert=True)


def get_vipo():
    """Return all VIPO."""
    return constants.VIPO.col_values(1)[1:]


def update_vipo():
    """Update VIPO."""
    vipo_list = get_vipo()
    vipo = constants.DB.vipo

    for account in vipo_list:
        vipo.update(
            {"account": account.lower().strip()},
            {"account": account.lower().strip()}, upsert=True)


def main():
    if constants.CONTRIBUTING:
        update_posts(True)
        update_account()
    else:
        update_posts()
        update_account()
        update_banned()
        update_moderators()
        update_vipo()

if __name__ == '__main__':
    main()
