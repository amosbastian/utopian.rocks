Utopian
-------

Utopian.rocks is a flask application that includes a table showing the contributions that are currently in the unreviewed worksheet, so users can check if their contribution was added succesfully. It also includes some endpoints to retrieve contributions, statistics and a weekly template for one of Utopian's posts.

Usage
-----

To run this locally you must have MongoDB and Python3.6 installed. After this you can clone this repository with

```
$ git clone https://github.com/amosbastian/utopian.git
```

and install all the Python packages using

```
$ cd utopian
$ pip install requirements.txt
```

Once you have a MongoDB instance running you can use the following script to populate the database

```
$ python update_database.py
```

Finally, you can run the web application with either of the following commands

```
$ python utopian/app.py
```

or 

```
$ gunicorn wsgi:app
```

Features
--------

The script `update_database.py` updates a MongoDB with all contributions made in the spreadsheet. While doing this it also adds some additional information that isn't available in the spreadsheet, like the total payout of the post, the number of comments it has and more. An example of a post in the database is shown below

```json
{
  "_id": {
    "$oid": "5b05d3229d6f5d7215a2b826"
  }, 
  "author": "amosbastian", 
  "category": "development", 
  "moderator": "helo", 
  "picked_by": "", 
  "repository": "https://github.com/amosbastian/utopian-spreadsheet", 
  "review_date": {
    "$date": 1526947200000
  }, 
  "staff_picked": false, 
  "status": "reviewed", 
  "total_comments": 4, 
  "total_payout": 165.864, 
  "total_votes": 25, 
  "url": "https://steemit.com/utopian-io/@amosbastian/utopian-spreadsheet-management-bot", 
  "utopian_vote": 163.62548043223717, 
  "voted_on": true
}
```

### Homepage

Showing all currently unreviewed contributions in a table, as seen [here](https://utopian.rocks/). Made specifically for contributors to see if their contribution was added to the spreadsheet.

### Posts endpoint

Retrieves posts from the database and returns them. Multiple query parameters can be used for this, as will be described in the usage section below. This was implemented using [webargs](https://github.com/sloria/webargs) to parse the arguments and [Flask-RESTful](https://flask-restful.readthedocs.io/en/latest/) to create the actual endpoint, as seen in the code snippet below

```
from flask import Flask, jsonify, render_template
from flask_restful import Resource, Api
from webargs import fields, validate
from webargs.flaskparser import use_args, use_kwargs, parser, abort

app = Flask(__name__)
api = Api(app)

class ContributionResource(Resource):
    """
    Endpoint for contributions in the spreadsheet.
    """
    query_parameters = {
        "category": fields.Str(),
        "status": fields.Str(),
        "author": fields.Str(),
        "moderator": fields.Str(),
        "staff_picked": fields.Bool()
    }

    @use_args(query_parameters)
    def get(self, query_parameters):
        """
        Uses the given query parameters to search for contributions in the
        database.
        """
        contributions = [json.loads(json_util.dumps(without_score(c)))
                         for c in DB.contributions.find(query_parameters)]
        return jsonify(contributions)
```

As you can see it's pretty straightforward to implement!

## Statistics endpoint

Retrieves contributions made in the last 7 days from the given date and calculates some statistics about it, as seen [here](https://utopian.rocks/api/statistics/today). This includes e.g. the average score a moderator gave that week, the average payout for contributions in a specific category, the staff picks about that week etc.

An example of statistics given for the development category is shown below

```json
{
  "average_payout": 101.59276712328769, 
  "average_score": 47.71917808219178, 
  "average_utopian_vote": 126.23418697612053, 
  "category": "development", 
  "moderators": [
    [
      "amosbastian", 
      26
    ], 
    [
      "codingdefined", 
      19
    ], 
    [
      "gregory.latinier", 
      11
    ], 
    ...
  ], 
  "not_voted": 16, 
  "pct_voted": 78.08219178082192, 
  "reviewed": 73, 
  "rewarded_contributors": [
    [
      "dumar022", 
      2
    ], 
    [
      "bflanagin", 
      2
    ], 
    [
      "semasping", 
      2
    ],
    ...
  ], 
  "total_payout": 7416.272000000001, 
  "unvoted": 1, 
  "utopian_total": 7195.3486576388705, 
  "voted": 57
}
```

## Weekly overview

Generates a template that can be used for the Weekly Top of Utopian posts (e.g. [this one](https://steemit.com/utopian-io/@utopian-io/weekly-top-of-utopian-io-may-17-24)), as seen [here](https://utopian.rocks/weekly). This includes all staff picks in the given week and a short overview of post statistics as seen below

```markdown
# Utopian.io Post Statistics

The staff picked contributions are only a small (but exceptional) example of the mass of contributions reviewed and rewarded by Utopian.io.

* Overall, the last week saw a total of 717 posts, with 267 of them rewarded through an upvote by @utopian-io.
* In total, Utopian.io distributed an approximate of 17259.87 SBD to contributors.
* The highest payout seen on any Utopian.io contribution this week was 1120.537 SBD, with a total of 1263 votes received from the community.
* The contribution that attracted the most engagement was <a href='https://steemit.com/utopian-io/@asbear/steempay-0-3-0-release-supporting-seven-more-currencies-usd-eur-gbp-jpy-cny-php-myr'>SteemPay 0.3.0 Release - Supporting seven more currencies (USD, EUR, GBP, JPY, CNY, PHP, MYR)</a>, with no less than 344 comments in its comment threads.
* The average vote given by Utopian.io was worth 64.64 SBD.

# Category Statistics

|Category|Reviewed|Rewarded|Total rewards|Top contributor|
|:-|:-|:-|-:|:-|
|graphics|47|31|3366.65 SBD|@nunojesus|
|bug-hunting|487|128|3350.78 SBD|@neupanedipen|
|development|73|57|7195.35 SBD|@dumar022|
|tutorials|53|22|1496.95 SBD|@edetebenezer|
|analysis|11|6|665.93 SBD|@abh12345|
|ideas|16|3|66.67 SBD|@jubreal|
|video-tutorials|13|9|862.52 SBD|@omersurer|
|blog|4|3|184.31 SBD|@moisesmcardona|
```

Usage
-----

## /api/post?category=&status=&author=&moderator=&staff_picked=

|Parameter|Description|Value|
|:-|:-|:-|
|category|Retrieve posts from a specific category|Any category (see [here](https://steemit.com/utopian-io/@utopian-io/utopian-now-contributions-are-welcome))|
|status|Status to filter contributions by|unreviewed,reviewed,pending,unvoted|
|author|Retrieve posts by a specific author|Steem username|
|moderator|Retrieve posts reviewed by a specific moderator|Moderator username|
|staff_picked|Retrieve posts that were or weren't staff picked|True/False|

## /api/statistics/<string:date>

Simply send a GET request to e.g. https://utopian.rocks/api/statistics/2018-05-24 or https://utopian.rocks/api/statistics/today and you will get the statistics from 2018-05-17 to 2018-05-24 back. It uses `dateutil.parser` to parse the date, so the date can be in whatever format it recognises.

## /weekly

Same as above, except you currently can't specify a specific date.

Roadmap
-------

Not sure, as the sheet will hopefully not be used for that long. I will probably want to add the following

* More query parameters
* Add date range to /api/statistics
* Add user statistics
* Add date range to /weekly
* Think of more statistics that could be interesting
* ...

Technology stack
----------------
 
* Python
* Flask
* MongoDB

Contributing
------------

If you want to contribute, then please read [CONTRIBUTING.md](https://github.com/amosbastian/utopian/blob/master/CONTRIBUTING.md) for more information.
