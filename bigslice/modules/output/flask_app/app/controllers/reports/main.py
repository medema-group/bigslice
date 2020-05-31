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


@blueprint.route("/api/reports/get_reports")
def get_reports():
    """ get report list for the datatable """
    result = {}
    result["draw"] = request.args.get('draw', type=int)

    # translate request parameters
    offset = request.args.get('start', type=int)
    limit = request.args.get('length', type=int)

    with sqlite3.connect(conf["reports_db_path"]) as con:
        cur = con.cursor()

        # fetch total records
        result["recordsTotal"] = cur.execute((
            "select count(id)"
            " from reports"
        ), ()).fetchall()[0][0]

        # fetch total records (filtered)
        result["recordsFiltered"] = cur.execute((
            "select count(id)"
            " from reports"
            " limit ? offset ?"
        ), (limit, offset)).fetchall()[0][0]

        # fetch data
        result["data"] = []
        for r_type, r_date, r_name, r_id in cur.execute((
            "select type, creation_date, name, id"
            " from reports"
            " order by creation_date desc"
        )).fetchall():
            result["data"].append([
                r_type,
                r_date,
                r_name,
                r_id
            ])

        return result
