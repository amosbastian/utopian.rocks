import datetime
import pprint

from pymongo import MongoClient
from utopian import utopian_client

client = MongoClient()
db = client.utopian


def update_moderators():
    print(f"{datetime.datetime.now()} - Updating moderators.")
    moderators = db.moderators
    moderator_list = utopian_client.get_moderators()

    if not moderator_list:
        time = datetime.datetime.now()
        print(f"{time} - Could not update moderators.")
        return

    if moderators.count() == 0:
        moderators.insert_many(moderator_list)
    else:
        for moderator in moderator_list:
            moderators.replace_one({"_id": moderator["_id"]}, moderator, True)


def status_converter(status):
    if status == "any":
        return "approved"
    else:
        return status


def status_parameter(status):
    if status == "any":
        return {"moderator.flagged": False}
    elif status == "flagged":
        return {"moderator.flagged": True}
    elif status == "pending":
        return {"moderator.pending": True}


def update_posts(status, force_complete=False):
    posts = db.posts
    post_status = status_converter(status)
    count = posts.find(status_parameter(status)).count()
    time = datetime.datetime.now()
    print(f"{time} - Updating {post_status} posts.")
    time = datetime.datetime.now()
    print(f"{time} - {count} {post_status} posts in the database.")
    if count == 0 or force_complete:
        utopian_client.get_posts(status, update=False)
    else:
        utopian_client.get_posts(status, update=True)

    added = posts.find(status_parameter(status)).count() - count
    last_week = datetime.datetime.now() - datetime.timedelta(days=7)
    # updated = sum([1 for post in posts_list if post["created"] > last_week])
    time = datetime.datetime.now()
    print(f"{time} - {added} posts were added.")


def main():
    update_moderators()
    update_posts("any")
    update_posts("flagged")
    update_posts("pending")


def converter(object_):
    if isinstance(object_, datetime.datetime):
        return object_.__str__()


if __name__ == '__main__':
    main()
    # moderators = db.moderators
    # posts = db.posts
    # mod_list = [moderator["account"] for moderator in 
    #     moderators.find({"referrer": "jestemkioskiem"})]
    # week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    # pipeline = [{
    #     "$match": {
    #         "$and": [{
    #             "moderator.account": {"$in": mod_list}
    #         },{
    #             "moderator.time": {"$gt": week_ago}
    #         }]
    #     }
    # }]
    # import json
    # post_list = [post for post in posts.aggregate(pipeline)]
    # for post in post_list:
    #     print(json.dumps(post, default=converter))
    #     break