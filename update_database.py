import datetime
import pprint

from pymongo import MongoClient
from utopian import utopian_client

client = MongoClient()
db = client.utopian


def update_moderators():
    print("Updating moderators...")
    moderators = db.moderators
    moderator_list = utopian_client.get_moderators()

    if not moderator_list:
        print("Something went wrong, please try again.")
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


def update_posts(status):
    posts = db.posts    
    post_status = status_converter(status)
    count = posts.find(status_parameter(status)).count()
    print(f"Updating {post_status} posts...")
    print(f"{count} {post_status} posts in the database...")
    if count == 0:
        posts_list = utopian_client.get_posts(status, update=False)
    else:
        posts_list = utopian_client.get_posts(status, update=True)

    if not posts_list:
        print(f"There currently aren't any {post_status} posts to be added...")
        return
    else:
        for post in posts_list:
            posts.replace_one({"_id": post["_id"]}, post, True)

    added = posts.find(status_parameter(status)).count() - count
    last_week = datetime.datetime.now() - datetime.timedelta(days=7)
    updated = sum([1 for post in posts_list if post["created"] > last_week])
    print(f"{added} posts were added and {updated} posts were updated...")


def main():
    update_moderators()
    update_posts("any")
    update_posts("flagged")
    update_posts("pending")

if __name__ == '__main__':
    main()
    posts = db.posts
    week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    reviewed_posts = posts.aggregate([
        {"$match": {
            "$and": [{
                "moderator.account": "amosbastian"
            },{
                "created": {"$gt": week_ago}
            }]
        }}])