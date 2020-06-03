#!/usr/bin/env python3

import sqlite3
from flask import render_template

# import global config
from ..config import conf

# set blueprint object
from flask import Blueprint
blueprint = Blueprint('feedback', __name__)


@blueprint.route("/feedback")
def page_feedback():

    # todo: implements

    # page title
    page_title = "Feedback"
    page_subtitle = (
        "Found <strong>bugs/errors</strong> in the software?"
        " Got some ideas on how to improve BiG-SLiCE? Please"
        " send us your feedback via our GitHub's"
        " <a href='https://github.com/medema-group/bigslice/issues'"
        ">'Issues' page</a>."
        "<br />Want to contribute code to BiG-SLiCE?"
        " feel free to <a href='mailto:satria.kautsar@wur.nl,"
        "marnix.medema@wur.nl?subject=[BiG-SLiCE contribution]'>send us"
        " an e-mail</a> or "
        "<a href='https://github.com/medema-group/bigslice/pulls'>"
        "do a pull request</a> at our GitHub page."
    )

    # render view
    return render_template(
        "feedback/main.html.j2",
        page_title=page_title,
        page_subtitle=page_subtitle
    )
