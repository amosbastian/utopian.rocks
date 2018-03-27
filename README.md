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

### [Supervisor team overview](https://utopian.info/team/amosbastian)
Shows a supervisor's team's performance in the last week.
### [Moderator overview](https://utopian.info/moderator/amosbastian)
Shows a moderator's performance, like recent reviews, activity and more.
### [Contributor overview](https://utopian.info/moderator/amosbastian)
Shows a contributor's performance, like recent contributions, who they were moderated by and more.

Roadmap
-------

Currently I have the following plans, but this could all change in the future

* Add a way to change the static time frame of 7 days to e.g. 1 day, 12 hours etc.
* Add a page for projects that show statistics about contributions made to it (e.g. best contributor, overall acceptance rate etc.)
* Improve overall look and feel, making everything more consistent.

