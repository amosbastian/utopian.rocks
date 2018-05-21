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
    """
    Convert row to dictionary, only selecting values we want.
    """
    # Check if contribution was staff picked
    if row[6] == "Yes":
        staff_picked = True
    else:
        staff_picked = False

    # Try and get date, since some people don't enter it correctly
    try:
        review_date = parse(row[1])
    except Exception:
        review_date = datetime(1970, 1, 1)

    url = row[2]
    author = url.split("/")[4][1:]

    # Create contribution dictionary and return it
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


def update_posts():
    """
    Adds all reviewed and unreviewed contributions to the database.
    """
    reviewed = []
    unreviewed = []

    # Iterate over all worksheets in the spreadsheet
    for worksheet in SHEET.worksheets():
        if worksheet.title.startswith("Reviewed"):
            reviewed += worksheet.get_all_values()[1:]
        elif worksheet.title.startswith("Unreviewed"):
            unreviewed += worksheet.get_all_values()[1:]

    # Convert row to dictionary
    reviewed = [contribution(x, "reviewed") for x in reviewed]
    unreviewed = [contribution(x, "unreviewed") for x in unreviewed]

    # Lazy so drop database and replace
    contributions = DB.contributions

    for post in reviewed + unreviewed:
        contributions.replace_one({"url": post["url"]}, post, True)


def main():
    update_posts()

if __name__ == '__main__':
    main()
    contributions = DB.contributions
