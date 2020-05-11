#!/usr/bin/env python3

import sqlite3
from flask import render_template

# import global config
from ..config import conf

# set blueprint object
from flask import Blueprint
blueprint = Blueprint('run', __name__)


@blueprint.route("/run/<int:run_id>")
def page_run(run_id):

    # todo: implements

    # page title
    page_title = "Run"
    page_subtitle = (
        "under construction"
    )

    # render view
    return render_template(
        "run/main.html.j2",
        page_title=page_title,
        page_subtitle=page_subtitle
    )
