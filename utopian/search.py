from pymongo import MongoClient

CLIENT = MongoClient()
DB = CLIENT.utopian


def main():
    posts = DB.posts
    posts.drop_indexes()
    posts.create_index([
        ("author", "text"),
        ("moderator.account", "text"),
        ("repository.full_name", "text")
    ])

if __name__ == '__main__':
    # main()
    posts = DB.posts
    for post in posts.find({"$text": {"$search": "amosbastian/nutmega"}}):
        print(post["title"])
