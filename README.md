Utopian
-------

A web application showing additional information about Utopian.io. It was created using Flask and MongoDB.

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

Currently the homepage shows all of Utopian.io's supervisors with a link to a page that shows their team's overall performance, and the performance of each moderator per category.

Roadmap
-------

Currently I have the following plans, but this could all change in the future

* Add a way to change the static time frame of 7 days to e.g. 1 day, 12 hours etc.
* Add a page that shows some statistics about the total number of submitted contributions (overall and per category) for a given time frame
* Add a page for each moderator showing their individual performance, a feed of their most recently reviewed posts, other statistics (e.g. who they have reviewed the most) etc.
* Add a page for projects that show statistics about contributions made to it (e.g. best contributor, overall acceptance rate etc.)
* Add a page for contributors to see their individual performance (e.g acceptance rate, who has reviewed their posts the most etc.)

