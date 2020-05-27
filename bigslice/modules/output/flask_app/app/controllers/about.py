#!/usr/bin/env python3

import sqlite3
from flask import render_template

# import global config
from ..config import conf

# set blueprint object
from flask import Blueprint
blueprint = Blueprint('about', __name__)


@blueprint.route("/about")
def page_about():

    # todo: implements

    # page title
    page_title = "About BiG-SLiCE"
    page_subtitle = (
        "under construction"
    )

    # render view
    return render_template(
        "about/main.html.j2",
        page_title=page_title,
        page_subtitle=page_subtitle
    )
