from datetime import date, timedelta
from oauth2client.service_account import ServiceAccountCredentials
from pymongo import MongoClient
import gspread
import os

CLIENT = MongoClient()
DB = CLIENT.utempian

DIR_PATH = os.path.dirname(os.path.realpath(__file__))
SCOPE = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
CREDENTIALS = ServiceAccountCredentials.from_json_keyfile_name(
    f"{DIR_PATH}/client_secret.json", SCOPE)
GSPREAD_CLIENT = gspread.authorize(CREDENTIALS)
SHEET = GSPREAD_CLIENT.open("Copy of Utopian Reviews")

# Get date of current, next and previous Thursday
TODAY = date.today()
OFFSET = (TODAY.weekday() - 3) % 7
THIS_WEEK = TODAY - timedelta(days=OFFSET)
LAST_WEEK = THIS_WEEK - timedelta(days=7)
NEXT_WEEK = THIS_WEEK + timedelta(days=7)

# Reviewed
TITLE_PREVIOUS = f"Reviewed - {LAST_WEEK:%b %-d} - {THIS_WEEK:%b %-d}"
TITLE_CURRENT = f"Reviewed - {THIS_WEEK:%b %-d} - {NEXT_WEEK:%b %-d}"
PREVIOUS_REVIEWED = SHEET.worksheet(TITLE_PREVIOUS)
CURRENT_REVIEWED = SHEET.worksheet(TITLE_CURRENT)

# Unreviewed
TITLE_UNREVIEWED = f"Unreviewed - {THIS_WEEK:%b %-d} - {NEXT_WEEK:%b %-d}"
UNREVIEWED = SHEET.worksheet(TITLE_UNREVIEWED)
