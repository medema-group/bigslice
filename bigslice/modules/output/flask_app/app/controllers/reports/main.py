#!/usr/bin/env python3

import sqlite3
from flask import render_template, request

# import global config
from ...config import conf

# set blueprint object
from flask import Blueprint
blueprint = Blueprint('reports', __name__)


@blueprint.route("/reports/view")
def page_reports_list():

    # todo, filtering

    # page title
    page_title = "Reports"
    page_subtitle = ("Here you can find all generated"
                     " reports, including BGC query results"
                     " (via the <samp>--query</samp> mode in BiG-SLiCE's"
                     " main program).")

    # render view
    return render_template(
        "reports/main.html.j2",
        page_title=page_title,
        page_subtitle=page_subtitle
    )


@blueprint.route("/reports/new")
def page_reports_new():

    # todo, filtering

    # page title
    page_title = "Generate reports"
    page_subtitle = ("Feature is not yet available."
                     " We're working hard to extend the software's"
                     " functionalities to make it even more useful to you."
                     " Check out the <a href='/feedback'>'Feedback' page</a>"
                     " to see how you can contribute by submitting ideas,"
                     " bug reports, feature requests and actual codes to"
                     " improve BiG-SLiCE.")

    # render view
    return render_template(
        "reports/new.html.j2",
        page_title=page_title,
        page_subtitle=page_subtitle
    )
