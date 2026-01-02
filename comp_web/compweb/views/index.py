import uuid
import hashlib
import pathlib
import arrow
import flask
import compweb

print("compweb.views imported")

@compweb.app.route('/')
def show_index():
    context = {}
    return flask.render_template("home_page.html", **context)
