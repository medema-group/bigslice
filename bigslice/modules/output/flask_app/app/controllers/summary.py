#!/usr/bin/env python3

from flask import render_template
import sqlite3

# import global config
from ..config import conf

# set blueprint object
from flask import Blueprint
blueprint = Blueprint('summary', __name__)


@blueprint.route("/summary")
def page_summary():

    # fetch data
    datasets = fetch_datasets_summary(conf["db_path"])
    runs = fetch_runs_summary(conf["db_path"])

    # page title
    page_title = "Summary"
    page_subtitle = (
        "Here you will find the summary of all datasets and runs included "
        "in this output package. Click 'view' to see "
        "the detailed information of each run/dataset."
    )

    # render view
    return render_template(
        "summary/main.html.j2",
        page_title=page_title,
        page_subtitle=page_subtitle,
        datasets=datasets,
        runs=runs
    )


def fetch_datasets_summary(db_path):
    """ fetch datasets summary """
    with sqlite3.connect(db_path) as con:
        datasets = []
        cur = con.cursor()
        for ds_id, ds_name, ds_desc in cur.execute(
                ("select id,name,description"
                    " from dataset"
                    " order by name asc")
        ).fetchall():
            # fetch genome counts
            genomes_count = cur.execute(
                ("select count(distinct orig_folder)"
                    " from bgc"
                    " where dataset_id=?"
                    " and orig_folder <> ''"),
                (ds_id, )
            ).fetchall()[0][0]
            # fetch bgc counts
            bgc_count = cur.execute(
                ("select count(id)"
                    " from bgc"
                    " where dataset_id=?"),
                (ds_id, )
            ).fetchall()[0][0]
            # fetch bgc with taxonomy counts
            bgc_count_taxonomy = cur.execute(
                ("select count(distinct bgc_id)"
                    " from bgc,bgc_taxonomy"
                    " where bgc.id=bgc_taxonomy.bgc_id"
                    " and bgc.dataset_id=?"),
                (ds_id, )
            ).fetchall()[0][0]
            datasets.append({
                "id": ds_id,
                "count_genomes": genomes_count,
                "count_bgcs": bgc_count,
                "count_bgcs_with_taxonomy": bgc_count_taxonomy,
                "name": ds_name,
                "desc": ds_desc
            })
        return datasets


def fetch_runs_summary(db_path):
    """ fetch runs summary """
    with sqlite3.connect(db_path) as con:
        runs = []
        cur = con.cursor()
        run_status_enum = {
            row[0]: row[1] for row in cur.execute(
                ("select id, name"
                    " from enum_run_status"
                    " order by id asc")
            )
        }
        for run_id, run_status in cur.execute(
                ("select run.id,run.status"
                    " from run"
                    " order by id asc")
        ).fetchall():
            # fetch bgc counts
            bgc_count = cur.execute(
                ("select count(bgc_id)"
                    " from run_bgc_status"
                    " where run_id=?"),
                (run_id, )
            ).fetchall()[0][0]
            # fetch gcf counts
            if run_status >= 5:  # CLUSTERING_FINISHED
                gcf_count = cur.execute(
                    ("select count(gcf.id)"
                        " from gcf,clustering"
                        " where gcf.clustering_id=clustering.id"
                        " and clustering.run_id=?"),
                    (run_id, )
                ).fetchall()[0][0]
                # fetch threshold
                threshold = cur.execute((
                    "select threshold"
                    " from clustering"
                    " where run_id=?"
                ), (run_id, )).fetchall()[0][0]
            else:
                gcf_count = "n/a"
                threshold = -1
            # fetch start time
            try:
                run_start = cur.execute(
                    ("select strftime('%Y-%m-%d %H:%M:%S', time_stamp)"
                        " from run_log"
                        " where run_id=? and message like 'run created %'"),
                    (run_id, )
                ).fetchall()[0][0]
            except IndexError:
                run_start = "n/a"
            # fetch end time
            try:
                run_finished = cur.execute(
                    ("select strftime('%Y-%m-%d %H:%M:%S', time_stamp)"
                        " from run_log"
                        " where run_id=? and message like 'run finished'"),
                    (run_id, )
                ).fetchall()[0][0]
            except IndexError:
                run_finished = "n/a"
            # fetch resumes
            run_resumes = [row[0] for row in cur.execute(
                ("select strftime('%Y-%m-%d %H:%M:%S', time_stamp)"
                    " from run_log"
                    " where run_id=? and message like 'run resumed %'"),
                (run_id, )
            ).fetchall()]
            # add to result
            run_name = "run-{:04d}".format(run_id)
            runs.append({
                "id": run_id,
                "name": run_name,
                "start": run_start,
                "finished": run_finished,
                "resumes": run_resumes,
                "status": run_status_enum[run_status],
                "count_bgcs": bgc_count,
                "count_gcfs": gcf_count,
                "threshold": float("{:.2f}".format(threshold))
            })
        return runs
