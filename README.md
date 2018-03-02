Utopian
-------

A web application created using Flask and MongoDB.

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
