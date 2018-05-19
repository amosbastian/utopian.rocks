import gspread
import json
import os
from beem.comment import Comment
from datetime import datetime, date
from dateutil.parser import parse
from oauth2client.service_account import ServiceAccountCredentials
from pymongo import MongoClient


CLIENT = MongoClient()
DB = CLIENT.utempian

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
SCOPE = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
CREDENTIALS = ServiceAccountCredentials.from_json_keyfile_name(
    f"{DIR_PATH}/client_secret.json", SCOPE)
GSPREAD_CLIENT = gspread.authorize(CREDENTIALS)
SHEET = GSPREAD_CLIENT.open("Utopian Reviews")


def contribution(row, status):
    if row[6] == "Yes":
        staff_picked = True
    else:
        staff_picked = False

    try:
        review_date = parse(row[1])
    except Exception:
        review_date = datetime(1970, 1, 1)

    url = row[2]
    # hehe
    author = url.split("/")[4][1:]

    new_contribution = {
        "moderator": row[0],
        "author": author,
        "review_date": review_date,
        "url": url,
        "repository": row[3],
        "category": row[4],
        "staff_picked": staff_picked,
        "picked_by": row[8],
        "status": status
    }
    return new_contribution


def converter(object_):
    if isinstance(object_, datetime):
        return object_.__str__()


def update_posts():
    reviewed = []
    unreviewed = []
    for worksheet in SHEET.worksheets():
        if worksheet.title.startswith("Reviewed"):
            reviewed += worksheet.get_all_values()[1:]
    for worksheet in SHEET.worksheets():
        if worksheet.title.startswith("Unreviewed"):
            unreviewed += worksheet.get_all_values()[1:]
    reviewed = [contribution(x, "reviewed") for x in reviewed]
    unreviewed = [contribution(x, "unreviewed") for x in unreviewed]

    contributions = DB.contributions
    DB.contributions.drop()
    contributions.insert_many(reviewed)
    contributions.insert_many(unreviewed)


def main():
    update_posts()

if __name__ == '__main__':
    main()
    contributions = DB.contributions
    print(contributions.count())
