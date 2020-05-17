#!/usr/bin/env python3

import sqlite3
from flask import render_template, request
import math

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
    """ for overview summary """
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


@blueprint.route("/api/run/get_statistics_summary")
def get_statistics_summary():
    """ for statistic summary """
    run_id = request.args.get('run_id', type=int)
    result = {}
    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()

        # set clustering id, get threshold
        clustering_id, result["threshold"] = cur.execute(
            ("select id, threshold"
             " from clustering"
             " where run_id=?"),
            (run_id, )
        ).fetchall()[0]

        # fetch gcf total counts
        result["gcf_total_counts"] = cur.execute(
            ("select count(id)"
             " from gcf"
             " where clustering_id=?"),
            (clustering_id, )
        ).fetchall()[0][0]

        # fetch singleton gcfs
        result["gcf_singleton_counts"] = cur.execute(
            ("select count(gcf_id)"
             " from ("
             " select gcf.id as gcf_id, count(bgc.id) as bgc_counts"
             " from bgc, gcf, gcf_membership"
             " where gcf_membership.bgc_id=bgc.id"
             " and gcf_membership.gcf_id=gcf.id"
             " and gcf.clustering_id=?"
             " and gcf_membership.rank=0"
             " and gcf_membership.membership_value<700"
             " group by gcf.id"
             " )"
             " where bgc_counts == 1"),
            (clustering_id, )
        ).fetchall()[0][0]

        # fetch bgc assigned to gcf
        result["bgc_assigned_counts"], \
            result["gcf_assigned_counts"] = cur.execute(
            ("select count(distinct bgc.id), count(distinct gcf.id)"
             " from bgc, gcf, gcf_membership"
             " where gcf_membership.bgc_id=bgc.id"
             " and gcf_membership.gcf_id=gcf.id"
             " and gcf.clustering_id=?"
             " and gcf_membership.rank=0"
             " and gcf_membership.membership_value<=?"),
            (clustering_id, result["threshold"])
        ).fetchall()[0]

        # fetch bgc not assigned to gcf
        result["bgc_not_assigned_counts"] = cur.execute(
            ("select count(distinct bgc.id), count(distinct gcf.id)"
             " from bgc, gcf, gcf_membership"
             " where gcf_membership.bgc_id=bgc.id"
             " and gcf_membership.gcf_id=gcf.id"
             " and gcf.clustering_id=?"
             " and gcf_membership.rank=0"
             " and gcf_membership.membership_value>?"),
            (clustering_id, result["threshold"])
        ).fetchall()[0][0]

    return result


@blueprint.route("/api/run/get_statistics_dist")
def get_statistics_dist():
    """ for bgc counts barplot """
    run_id = request.args.get('run_id', type=int)
    result = {}
    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()

        # set clustering id and threshold
        clustering_id, result["threshold"] = cur.execute(
            ("select id, threshold"
             " from clustering"
             " where run_id=?"),
            (run_id, )
        ).fetchall()[0]

        # get list of ranks
        ranks = sorted([row[0] for row in cur.execute(
            ("select distinct rank"
                " from gcf, gcf_membership"
                " where gcf_membership.gcf_id=gcf.id"
                " and gcf.clustering_id=?"),
            (clustering_id, )
        ).fetchall()])

        # get labels and values
        result["labels"] = ["rank-{}".format(rank) for rank in ranks]
        selector = ("select avg(membership_value)"
                    " from bgc, gcf, gcf_membership"
                    " where gcf_membership.bgc_id=bgc.id"
                    " and gcf_membership.gcf_id=gcf.id"
                    " and gcf.clustering_id=?"
                    " and gcf_membership.rank=?")
        result["values_complete"] = [float("{:.2f}".format(cur.execute(
            ("{} and bgc.on_contig_edge is 0".format(selector)),
            (clustering_id, rank)
        ).fetchall()[0][0] or 0)) for rank in ranks]
        result["values_fragmented"] = [float("{:.2f}".format(cur.execute(
            ("{} and bgc.on_contig_edge is 1".format(selector)),
            (clustering_id, rank)
        ).fetchall()[0][0] or 0)) for rank in ranks]
        result["values_unknown"] = [float("{:.2f}".format(cur.execute(
            ("{} and bgc.on_contig_edge is null".format(selector)),
            (clustering_id, rank)
        ).fetchall()[0][0] or 0)) for rank in ranks]

    return result


@ blueprint.route("/api/run/get_statistics_bgc_counts")
def get_statistics_bgc_counts():
    """ for bgc counts barplot """
    run_id = request.args.get('run_id', type=int)
    result = {}
    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()

        # set clustering id, get threshold
        clustering_id, threshold = cur.execute(
            ("select id, threshold"
             " from clustering"
             " where run_id=?"),
            (run_id, )
        ).fetchall()[0]

        # general selector for bgc counts
        selector = (" select gcf.id as gcf_id, count(bgc.id) as bgc_counts"
                    " from bgc, gcf, gcf_membership"
                    " where gcf_membership.bgc_id=bgc.id"
                    " and gcf_membership.gcf_id=gcf.id"
                    " and gcf.clustering_id=?"
                    " and gcf_membership.rank=0"
                    " and gcf_membership.membership_value<=?"
                    " group by gcf.id")

        # get bins and labels
        bin_counts = request.args.get('bin_counts', default=10, type=int)
        bins = [(1, 1)]
        labels = ["singletons"]
        min_counts, avg_counts, max_counts = cur.execute(
            (
                "select min(bgc_counts), avg(bgc_counts), max(bgc_counts)"
                " from ({})".format(selector)
            ), (clustering_id, threshold)).fetchall()[0]
        bin_size = math.ceil(((avg_counts - min_counts) * 2) / bin_counts)
        min_bin = 2
        while min_bin < (avg_counts + bin_size):
            max_bin = min_bin + bin_size
            bins.append((min_bin, max_bin))
            labels.append("{}-{} BGCs".format(min_bin, max_bin))
            min_bin = max_bin
        bins.append((bins[-1][1] + 1, math.ceil(max_counts)))
        labels.append("> {} BGCs".format(bins[-1][0] - 1))
        result["min"] = min_counts
        result["avg"] = float("{:.2f}".format(avg_counts))
        result["max"] = max_counts
        result["bins"] = bins
        result["labels"] = labels

        # get values
        result["values"] = [cur.execute((
            "select count(bgc_counts)"
            " from ({})"
            " where bgc_counts >= ?"
            " and bgc_counts <= ?".format(selector)
        ), (clustering_id, threshold,
            min_c, max_c)).fetchall()[0][0]
            for min_c, max_c in bins]

    return result


@blueprint.route("/api/run/get_gcf_table")
def get_gcf_table():
    """ for gcf datatable """
    result = {}
    result["draw"] = request.args.get('draw', type=int)

    # translate request parameters
    run_id = request.args.get('run_id', default=0, type=int)
    result["run_id"] = run_id
    offset = request.args.get('start', type=int)
    limit = request.args.get('length', type=int)

    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()

        # set clustering id and threshold
        clustering_id, threshold = cur.execute(
            ("select id, threshold"
             " from clustering"
             " where run_id=?"),
            (run_id, )
        ).fetchall()[0]

        # fetch total records (all gcfs in the dataset)
        result["recordsTotal"] = cur.execute(
            ("select count(id)"
             " from gcf"
             " where clustering_id=?"),
            (clustering_id,)).fetchall()[0][0]

        # fetch total records (filtered)
        result["recordsFiltered"] = cur.execute(
            ("select count(id)"
             " from gcf"
             " where clustering_id=?"),
            (clustering_id,)).fetchall()[0][0]

        # get max gcf id

        # fetch data for table
        result["data"] = []
        for row in cur.execute(
            ("select id, id_in_run"
             " from gcf"
             " where clustering_id=?"
             " limit ? offset ?"),
                (clustering_id, limit, offset)).fetchall():
            gcf_id, gcf_accession = row

            # todo: fetch directly from gcf.name (need schema update)
            gcf_name = "GCF_{:0{width}d}".format(
                gcf_accession, width=math.ceil(
                    math.log10(result["recordsTotal"])))

            # fetch core members count
            core_members = cur.execute(
                (
                    "select count(bgc_id)"
                    " from gcf_membership"
                    " where gcf_id=?"
                    " and rank=0"
                    " and membership_value <= ?"
                ),
                (gcf_id, threshold)).fetchall()[0][0]

            # fetch putative members count
            putative_members = cur.execute(
                (
                    "select count(bgc_id)"
                    " from gcf_membership"
                    " where gcf_id=?"
                    " and rank=0"
                    " and membership_value > ?"
                ),
                (gcf_id, threshold)).fetchall()[0][0]

            # fetch classes counts
            class_counts = cur.execute(
                (
                    "select chem_class.name || ':' || chem_subclass.name"
                    " as chem_class,"
                    " count(gcf_membership.bgc_id) as bgc"
                    " from chem_class, chem_subclass,"
                    " bgc_class, gcf_membership"
                    " where gcf_membership.gcf_id=?"
                    " and gcf_membership.bgc_id=bgc_class.bgc_id"
                    " and bgc_class.chem_subclass_id=chem_subclass.id"
                    " and chem_subclass.class_id=chem_class.id"
                    " and rank=0"
                    " and membership_value <= ?"
                    " group by chem_class"
                    " order by bgc desc"
                ),
                (gcf_id, threshold)).fetchall()

            # fetch taxon counts
            taxon_counts = cur.execute(
                (
                    "select taxon.name as taxon,"
                    " count(gcf_membership.bgc_id) as bgc"
                    " from taxon, bgc_taxonomy, gcf_membership"
                    " where gcf_membership.gcf_id=?"
                    " and gcf_membership.bgc_id=bgc_taxonomy.bgc_id"
                    " and bgc_taxonomy.taxon_id=taxon.id"
                    " and taxon.level=5"  # genus
                    " and membership_value <= ?"
                    " group by taxon"
                    " order by bgc desc"
                ),
                (gcf_id, threshold)).fetchall()

            result["data"].append([
                gcf_name,  # gcf
                core_members,  # core members
                putative_members,  # putative members
                class_counts,  # representative class
                taxon_counts,  # representative taxon
                gcf_id  # gcf_id
            ])

    return result
