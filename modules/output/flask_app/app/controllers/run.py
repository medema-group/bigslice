#!/usr/bin/env python3

import sqlite3
from flask import render_template, request

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


@blueprint.route("/api/run/get_overview")
def get_overview():
    """ for statistic summary """
    run_id = request.args.get('run_id', type=int)
    result = {}
    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()

        # get status, parameters, hmm_db_id
        result["status"], result["parameters"], hmm_db_id = cur.execute((
            "select enum_run_status.name, run.prog_params, run.hmm_db_id"
            " from run, enum_run_status"
            " where enum_run_status.id=run.status"
            " and run.id = ?"
        ), (run_id, )).fetchall()[0]

        # fetch start time
        try:
            result["started"] = cur.execute(
                ("select strftime('%Y-%m-%d %H:%M:%S', time_stamp)"
                    " from run_log"
                    " where run_id=? and message like 'run created %'"),
                (run_id, )
            ).fetchall()[0][0]
        except IndexError:
            result["start"] = "n/a"

        # fetch end time
        try:
            result["finished"] = cur.execute(
                ("select strftime('%Y-%m-%d %H:%M:%S', time_stamp)"
                    " from run_log"
                    " where run_id=? and message like 'run finished'"),
                (run_id, )
            ).fetchall()[0][0]
        except IndexError:
            result["finished"] = "n/a"

        # fetch resumes
        result["resumes"] = [row[0] for row in cur.execute(
            ("select strftime('%Y-%m-%d %H:%M:%S', time_stamp)"
                " from run_log"
                " where run_id=? and message like 'run resumed %'"),
            (run_id, )
        ).fetchall()]

        # get hmm counts
        result["hmm_counts"] = cur.execute(
            ("select count(id)"
             " from hmm"
             " where db_id=?"),
            (hmm_db_id, )
        ).fetchall()[0][0]
        result["hmm_subpfam_counts"] = cur.execute(
            ("select count(id)"
             " from hmm,subpfam"
             " where db_id=?"
             " and subpfam.hmm_id=hmm.id"),
            (hmm_db_id, )
        ).fetchall()[0][0]
        result["hmm_core_counts"] = cur.execute(
            ("select count(distinct id)"
             " from hmm,subpfam"
             " where db_id=?"
             " and subpfam.parent_hmm_id=hmm.id"),
            (hmm_db_id, )
        ).fetchall()[0][0]

        # get bgc/dataset counts
        result["bgc_counts_per_dataset"] = {
            row[0]: row[1] for row in cur.execute(
                ("select dataset.name, count(bgc.id)"
                 " from bgc, dataset, run_bgc_status"
                 " where bgc.id=run_bgc_status.bgc_id"
                 " and dataset.id=bgc.dataset_id"
                 " and run_bgc_status.run_id=?"
                 " group by dataset.name"),
                (run_id, )
            ).fetchall()
        }
        result["bgc_counts_total"] = sum(
            result["bgc_counts_per_dataset"].values())
        result["dataset_counts"] = len(result["bgc_counts_per_dataset"])

    return result
