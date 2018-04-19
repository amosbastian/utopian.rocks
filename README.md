Utopian
-------

A web application showing additional information about Utopian.io. It was created using Flask and MongoDB. Visit https://utopian.info/ to see it in action!

Usage
-----

To run this locally you must have MongoDB and Python3.6 installed. After this you can clone this repository with

```
$ https://github.com/amosbastian/utopian.git
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

### [Moderator profile page](https://utopian.info/contributor/amosbastian)
Shows a moderator's recent reviews, their activity and their most accepted and rejected contributors.
### [Contributor profile page](https://utopian.info/moderator/amosbastian)
Shows a contributor's recent contributions and the moderators who have accepted and rejected their contributions the most.
### [Category overview](https://utopian.rocks/category/all)
Shows a category's review feed, the amount of moderated posts in the last week, a pie chart of the pending posts' categories. It also shows the most active moderators for that category and the most accepted and rejected contributors for that category in the last week.

Roadmap
-------

Currently I have the following plans, but this could all change in the future

* Add a way to change the static time frame of 7 days to e.g. 1 day, 12 hours etc.
* Add a page for projects that show statistics about contributions made to it (e.g. best contributor, overall acceptance rate etc.)
* Add the ability to search for moderators, contributors, projects etc.

Contributing
------------

If you want to contribute, then please read [CONTRIBUTING.md](https://github.com/amosbastian/utopian/blob/master/CONTRIBUTING.md) for more information.
