# Utopian.info

A web application showing additional information about Utopian.io. It was created using Flask and MongoDB. Visit https://utopian.info/ to see it in action!

Note: this is the `develop` branch and is completely separate to the `master` branch. On this branch I am converting the application structure to something much better. Because of this I am remaking most of the application from scratch, while reusing snippets of code. My aim is to make the website much more aesthetically pleasing, but more importantly quicker and easier to use.

### Prerequisites

To run Utopian.info locally you need to have Python installed - you can find more information and instructions on https://www.python.org/. Nutmega also uses MongoDB - tutorials on installation of MongoDB can be found on https://docs.mongodb.com/manual/installation/.

### Installing

Once you have Python and MongoDB installed the first step is cloning the repository and setting up a virtual environment

```bash
git clone https://github.com/amosbastian/utopian.git
cd utopian
python3 -m venv venv
. venv/bin/activate
```

Utopian.info currently requires the version of Flask that is only available on GitHub, so install this and the other requires packages with the following commands

```
$ pip install git+https://github.com/pallets/flask.git
$ python setup.py install
```

Once you have a MongoDB instance running you can use the following script to populate the database

```
$ python update_database.py
```

Finally, you need to set the environment variables `FLASK_APP` and `FLASK_ENV` like this

```
$ export FLASK_APP=nutmega
$ export FLASK_env=development
```

or 

```
$ gunicorn wsgi:app
```

### Usage

After installing everything all that's left is to run the application with the following command

```
flask run
```

However, since Utopian.info uses SCSS I use node.js to compile my `.scss` files into the final `style.css` file. If you want to do the same, then you must first install node.js and use the following command in the Utopian.info folder to install all the dependencies

```
npm install
```

I have also added a script that *should* run the Flask application and recompile the SCSS files every time you make a change to them. You can run this using the following command

```
npm start
```

## Built with

Nutmega was built with

* [Flask](http://flask.pocoo.org/docs/0.12/) - a micro webdevelopment framework for Python.
* [MongoDB](https://www.mongodb.com/) - a free and open-source cross-platform document-oriented database program.


## Contributing

Please read [CONTRIBUTING.md](https://github.com/amosbastian/utopian/blob/master/CONTRIBUTING.md) for details on how to contribute to Utopian.info and what the best way to go about this is!

## Roadmap

Currently remaking the website to make it more dynamic and usable

* Finish homepage
* Remake page for moderators
* Remake page for contributors
* Remake page for categories
* Create page for projects
* Create page for task requests

## Authors

* **Amos Bastian** - *Initial work* - [@amosbastian](https://github.com/amosbastian)

See also the list of [contributors](https://github.com/amosbastian/utopian/graphs/contributors) who participated in this project.

## License

This project is licensed under the MIT license - see the [LICENSE](https://github.com/amosbastian/utopian/blob/master/LICENSE) file for details.
