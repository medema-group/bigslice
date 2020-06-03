#!/usr/bin/env python3

from os import path
import math
import sqlite3
from flask import render_template, request

# import global config
from ...config import conf

def page_report_detail(report_id):

    # fetch query name and date
    with sqlite3.connect(conf["reports_db_path"]) as con:
        cur = con.cursor()
        with sqlite3.connect(conf["db_path"]) as con_source:
            cur_source = con_source.cursor()

            name, created = cur.execute((
                "select name, creation_date"
                " from reports"
                " where id=?"
                " and type=?"
            ), (report_id, "query")).fetchall()[0]

            # set run_id
            run_id = cur.execute((
                "select run_id"
                " from reports_run"
                " where report_id=?"
            ), (report_id, )).fetchall()[0][0]

            # set clustering id, get threshold
            clustering_id, threshold = cur_source.execute(
                ("select id, threshold"
                 " from clustering"
                 " where run_id=?"),
                (run_id, )
            ).fetchall()[0]

    # page title
    page_title = "Query result: {}".format(name)
    page_subtitle = "Overview of all BGC to GCF hits in this query."

    # render view
    return render_template(
        "reports/query/main.html.j2",
        page_title=page_title,
        page_subtitle=page_subtitle,
        report_id=report_id,
        run_id=run_id,
        clustering_id=clustering_id,
        threshold=threshold
    )


def page_query_detail(report_id, bgc_id):

    # fetch query name and date
    with sqlite3.connect(conf["reports_db_path"]) as con:
        cur = con.cursor()
        with sqlite3.connect(conf["db_path"]) as con_source:
            cur_source = con_source.cursor()

            name, created = cur.execute((
                "select name, strftime('%Y-%m-%d %H:%M:%S', creation_date)"
                " from reports"
                " where id=?"
                " and type=?"
            ), (report_id, "query")).fetchall()[0]

            # set run_id
            run_id = cur.execute((
                "select run_id"
                " from reports_run"
                " where report_id=?"
            ), (report_id, )).fetchall()[0][0]

            # set clustering id, get threshold
            clustering_id, threshold = cur_source.execute(
                ("select id, threshold"
                 " from clustering"
                 " where run_id=?"),
                (run_id, )
            ).fetchall()[0]

    # page title
    page_title = "Query result: {} (BGC: {})".format(name, bgc_id)
    page_subtitle = "(under construction)"

    # render view
    return render_template(
        "reports/query/detail/main.html.j2",
        page_title=page_title,
        page_subtitle=page_subtitle,
        bgc_id=bgc_id,
        run_id=run_id,
        clustering_id=clustering_id,
        threshold=threshold
    )


def get_overview():
    """ for overview summary """
    report_id = request.args.get('report_id', default=0, type=int)
    run_id = request.args.get('run_id', type=int)

    result = {}
    with sqlite3.connect(conf["reports_db_path"]) as con:
        cur = con.cursor()

        # validate report id & run id
        if len(cur.execute((
            "select id"
            " from reports"
            " where id=?"
            " and type=?"
        ), (report_id, "query")).fetchall()) < 1:
            return "500: data not available"

        if len(cur.execute((
            "select run_id"
            " from reports_run"
            " where report_id=?"
            " and run_id=?"
        ), (report_id, run_id)).fetchall()) < 1:
            return "500: data not available"

        result["created"] = cur.execute((
            "select strftime('%Y-%m-%d %H:%M:%S', creation_date)"
            " from reports"
            " where id=?"
        ), (report_id,)).fetchall()[0][0]

        # run name
        result["run_id"] = run_id
        result["run_name"] = "run-{:04d}".format(run_id)

        # bgc counts
        db_query_path = path.join(
            conf["reports_folder"], str(report_id), "data.db")
        with sqlite3.connect(db_query_path) as query_con:
            query_cur = query_con.cursor()
            result["bgc_counts"] = query_cur.execute((
                "select count(id)"
                " from bgc"
            )).fetchall()[0][0]

        return result


def get_bgc_table():
    """ for bgc datatable """
    result = {}
    result["draw"] = request.args.get('draw', type=int)

    # translate request parameters
    report_id = request.args.get('report_id', default=0, type=int)
    result["report_id"] = report_id
    run_id = request.args.get('run_id', default=0, type=int)
    result["run_id"] = run_id
    offset = request.args.get('start', type=int)
    limit = request.args.get('length', type=int)

    # validate report id & run id
    with sqlite3.connect(conf["reports_db_path"]) as con:

        cur = con.cursor()
        if len(cur.execute((
            "select id"
            " from reports"
            " where id=?"
            " and type=?"
        ), (report_id, "query")).fetchall()) < 1:
            return "500: data not available"

        if len(cur.execute((
            "select run_id"
            " from reports_run"
            " where report_id=?"
            " and run_id=?"
        ), (report_id, run_id)).fetchall()) < 1:
            return "500: data not available"

    db_query_path = path.join(
        conf["reports_folder"], str(report_id), "data.db")
    with sqlite3.connect(db_query_path) as con:
        cur = con.cursor()
        with sqlite3.connect(conf["db_path"]) as con_source:
            cur_source = con_source.cursor()

            # set clustering id, get threshold
            clustering_id, result["threshold"] = cur_source.execute(
                ("select id, threshold"
                 " from clustering"
                 " where run_id=?"),
                (run_id, )
            ).fetchall()[0]

            # fetch total gcf count for this run
            result["totalGCFrun"] = cur_source.execute((
                "select count(id)"
                " from gcf"
                " where gcf.clustering_id=?"
            ), (clustering_id,)).fetchall()[0][0]

            # fetch total records (all bgcs in the dataset)
            result["recordsTotal"] = cur.execute((
                "select count(id)"
                " from bgc"
                " order by id asc"
            )).fetchall()[0][0]

            # fetch total records (filtered)
            result["recordsFiltered"] = cur.execute((
                "select count(id)"
                " from bgc"
                " order by id asc"
            )).fetchall()[0][0]

            # fetch data for table
            result["data"] = []
            for bgc_id, bgc_name, bgc_length, on_contig_edge, gcf_id, \
                    membership_value in cur.execute((
                        "select bgc.id, bgc.orig_filename, bgc.length_nt,"
                        " bgc.on_contig_edge,"
                        " gcf_membership.gcf_id,"
                        " gcf_membership.membership_value"
                        " from bgc, gcf_membership"
                        " where gcf_membership.bgc_id=bgc.id"
                        " and gcf_membership.rank=0"
                        " order by bgc.orig_filename asc"
                        " limit ? offset ?"
                    ), (limit, offset)).fetchall():

                # fetch completeness
                if on_contig_edge == 1:
                    comp = "fragmented"
                elif on_contig_edge == 0:
                    comp = "complete"
                else:
                    comp = "n/a"

                # fetch class information
                subclass_ids = [str(row[0]) for row in cur.execute((
                    "select distinct chem_subclass_id"
                    " from bgc_class"
                    " where bgc_id=?"
                ), (bgc_id, )).fetchall()]
                class_names = cur_source.execute((
                    "select chem_class.name, chem_subclass.name"
                    " from chem_subclass, chem_class"
                    " where chem_subclass.class_id=chem_class.id"
                    " and chem_subclass.id in ({})".format(
                        ",".join(subclass_ids))
                )).fetchall()

                # fetch gcf information
                gcf_accession = cur_source.execute((
                    "select id_in_run"
                    " from gcf"
                    " where id=?"
                ), (gcf_id, )).fetchall()[0][0]
                gcf_name = "GCF_{:0{width}d}".format(
                    gcf_accession, width=math.ceil(
                        math.log10(result["totalGCFrun"])))

                result["data"].append([
                    bgc_name,
                    class_names,
                    "{:.02f}".format(bgc_length / 1000),
                    comp,
                    (gcf_id, gcf_name),
                    membership_value,
                    bgc_id
                ])

            return result


# register routes
routes = [
    ("bgc/<int:bgc_id>", page_query_detail)
]

# register api routes
routes_api = [
    ("bgc_list", get_bgc_table),
    ("overview", get_overview)
]
