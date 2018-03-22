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
        account_list = [moderator["account"] for moderator in moderator_list]
        for moderator in moderators.find():
            account = moderator["account"]
            if not account in account_list:
                time = datetime.datetime.now()
                print(f"{time} - Removing moderator: {account}")
                moderators.delete_one(moderator)
                continue
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
        return {"moderator": None}


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
    time = datetime.datetime.now()
    print(f"{time} - {added} posts were added.")


def main():
    update_moderators()
    update_posts("any")
    update_posts("flagged")
    update_posts("pending", True)


def converter(object_):
    if isinstance(object_, datetime.datetime):
        return object_.__str__()

import json
if __name__ == '__main__':
    main()