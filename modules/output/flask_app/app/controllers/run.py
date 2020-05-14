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

    # page title
    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()
        status_id, = cur.execute((
            "select status"
            " from run"
            " where id = ?"
        ), (run_id, )).fetchall()[0]

        page_title = "Run-{:04d}".format(run_id)
        page_subtitle = ("Here you can find the complete summary "
                         "generated for this run. When a run "
                         "finishes, you can view the general "
                         "statistics of the run and browse through "
                         "all the GCFs and their BGC members assigned"
                         " by the algorithm. Click 'view' on the "
                         "data table to see the detailed summary page "
                         "of each GCF.")

    # render view
    return render_template(
        "run/main.html.j2",
        run_id=run_id,
        status_id=status_id,
        page_title=page_title,
        page_subtitle=page_subtitle
    )
