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
        "under construction"
    )

    # render view
    return render_template(
        "about/main.html.j2",
        page_title=page_title,
        page_subtitle=page_subtitle
    )
