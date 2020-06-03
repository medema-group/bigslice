#!/usr/bin/env python3

import sqlite3
from flask import render_template, request, redirect
from flask import abort
import json
import math
from os import path
from typing import List

# import global config
from ..config import conf

# set blueprint object
from flask import Blueprint
blueprint = Blueprint('gcf', __name__)


@blueprint.route("/run/<int:run_id>/gcf/<int:gcf_id>")
def page_gcf(gcf_id, run_id):
    # page title
    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()

        # fetch total GCF in the run (for zero-indexing)
        total_gcf = cur.execute((
            "select count(gcf.id)"
            " from gcf, clustering"
            " where gcf.clustering_id=clustering.id"
            " and clustering.run_id=?"
        ), (run_id, )).fetchall()[0][0]

        # fetch gcf accession & clustering threshold
        gcf_accession, threshold = cur.execute((
            "select id_in_run, threshold"
            " from gcf, clustering"
            " where gcf.clustering_id=clustering.id"
            " and gcf.id=?"
            " and clustering.run_id=?"
        ), (gcf_id, run_id)).fetchall()[0]

        # set title and subtitle
        page_title = "GCF_{:0{width}d}".format(
            gcf_accession, width=math.ceil(
                math.log10(total_gcf)))
        page_subtitle = (
            "From Run-{:04d} (threshold: {:.2f}). At the bottom"
            " you can see the list of both 'core' members (BGCs having a"
            " distance of < T) and the 'putative' ones (BGCs having a distance"
            " > T, but have a best-match for this GCF model). Taxonomy"
            " statistics are only available for BGCs having their taxonomy"
            " assigned in the original input data."
        ).format(run_id, threshold)

    # render view
    return render_template(
        "gcf/main.html.j2",
        gcf_id=gcf_id,
        run_id=run_id,
        threshold=float("{:.2f}".format(threshold)),
        page_title=page_title,
        page_subtitle=page_subtitle
    )


@blueprint.route("/api/gcf/get_word_cloud")
def get_word_cloud():
    """ for gcf features word cloud """
    result = {}
    gcf_id = request.args.get('gcf_id', type=int)
    limit = request.args.get('limit', default=20, type=int)

    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()

        result["words"] = []
        for name, weight in cur.execute((
            "select hmm.name,"
            " gcf_models.value"
            " from gcf_models, hmm"
            " where hmm.id=gcf_models.hmm_id"
            " and gcf_models.gcf_id=?"
            " order by gcf_models.value desc"
            " limit ?"
        ), (gcf_id, limit)).fetchall():
            result["words"].append({
                "text": name,
                "weight": weight
            })

    return result


@blueprint.route("/api/gcf/get_dist_stats")
def get_dist_stats():
    """ for gcf distance statistics """
    result = {}
    gcf_id = request.args.get('gcf_id', type=int)
    bin_size = request.args.get('bin_size', default=100, type=int)
    threshold = request.args.get('threshold', type=float)
    result = {
        "labels": [],
        "core": [],
        "putative": []
    }

    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()

        # get min and max length_nt to calculate step-ups
        min_dist, max_dist = cur.execute((
            "select min(membership_value), max(membership_value)"
            " from gcf_membership"
            " where gcf_id=?"
            " and rank=0"
        ), (gcf_id, )
        ).fetchall()[0]

        # fetch counts per bin
        cur_min = 1
        while cur_min < max_dist:
            cur_max = cur_min + bin_size - 1

            # fetch labels
            result["labels"].append((cur_min, cur_max))

            # fetch values
            result["core"].append(cur.execute((
                "select count(bgc_id)"
                " from gcf_membership"
                " where gcf_id=?"
                " and rank=0"
                " and membership_value >= ?"
                " and membership_value <= ?"
                " and membership_value <= ?"
            ), (gcf_id, cur_min, cur_max, threshold)
            ).fetchall()[0][0])
            result["putative"].append(cur.execute((
                "select count(bgc_id)"
                " from gcf_membership"
                " where gcf_id=?"
                " and rank=0"
                " and membership_value >= ?"
                " and membership_value <= ?"
                " and membership_value > ?"
            ), (gcf_id, cur_min, cur_max, threshold)
            ).fetchall()[0][0])

            cur_min = cur_max + 1

    return result


@blueprint.route("/api/gcf/get_members")
def get_members():
    """ get members for the datatable """
    result = {}
    result["draw"] = request.args.get('draw', type=int)

    # translate request parameters
    gcf_id = request.args.get('gcf_id', type=int)
    run_id = request.args.get('run_id', type=int)
    result["run_id"] = run_id
    members_type = request.args.get('type', type=str)
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
        result["threshold"] = threshold

        # fetch total gcf count for this run
        result["totalGCFrun"] = cur.execute((
            "select count(id)"
            " from gcf"
            " where gcf.clustering_id=?"
        ), (clustering_id,)).fetchall()[0][0]

        # parameters for filtering membership values
        if members_type == "putative":
            selector = (
                " and gcf_membership.membership_value > ?"
                " and gcf_membership.rank = 0"
            )
        else:
            selector = (
                " and gcf_membership.membership_value <= ?"
                " and gcf_membership.rank = 0"
            )

        # fetch total records (all bgcs sharing gcfs)
        result["recordsTotal"] = cur.execute((
            "select count(distinct bgc_id)"
            " from gcf_membership,gcf"
            " where gcf_membership.gcf_id=gcf.id"
            " and gcf.id=?"
            " and gcf.clustering_id=?"
            "{}"
        ).format(selector), (
            gcf_id, clustering_id, threshold)).fetchall()[0][0]

        # fetch total records (filtered)
        result["recordsFiltered"] = cur.execute((
            "select count(distinct bgc_id)"
            " from gcf_membership,gcf"
            " where gcf_membership.gcf_id=gcf.id"
            " and gcf.id=?"
            " and gcf.clustering_id=?"
            "{}"
        ).format(selector), (
            gcf_id, clustering_id, threshold)).fetchall()[0][0]

        # fetch taxonomy descriptor
        result["taxon_desc"] = cur.execute((
            "select level, name"
            " from taxon_class"
            " order by level asc"
        )).fetchall()

        # fetch data for table
        result["data"] = []

        for bgc_id, bgc_name, dataset_id, dataset_name, dist, \
                bgc_length, genome in cur.execute((
                    "select bgc.id, bgc.name,"
                    " dataset.id, dataset.name,"
                    " gcf_membership.membership_value,"
                    " bgc.length_nt, bgc.orig_folder"
                    " from bgc, gcf_membership, dataset"
                    " where gcf_membership.gcf_id=?"
                    "{}"
                    " and gcf_membership.bgc_id=bgc.id"
                    " and dataset.id=bgc.dataset_id"
                    " order by gcf_membership.membership_value asc"
                    " limit ? offset ?"
                ).format(selector), (
                gcf_id, threshold, limit, offset
                )).fetchall():

            # fetch taxonomy information
            taxonomy = {
                row[0]: row[1] for row in cur.execute((
                    "select taxon.level, taxon.name"
                    " from taxon, bgc_taxonomy"
                    " where taxon.id=bgc_taxonomy.taxon_id"
                    " and bgc_taxonomy.bgc_id=?"
                ), (bgc_id, )).fetchall()
            }

            # fetch class information
            classes = cur.execute((
                "select chem_class.name, chem_subclass.name"
                " from bgc, bgc_class, chem_subclass, chem_class"
                " where bgc.id=bgc_class.bgc_id"
                " and bgc_class.chem_subclass_id=chem_subclass.id"
                " and chem_subclass.class_id=chem_class.id"
                " and bgc.id=?"
            ), (bgc_id, )).fetchall()

            result["data"].append([
                (dataset_id, dataset_name),
                genome if genome else "n/a",
                (bgc_id, dataset_id, bgc_name),
                float("{:.2f}".format(dist)),
                "{:.02f}".format(bgc_length / 1000),
                taxonomy,
                classes
            ])

        return result


@blueprint.route("/api/gcf/get_member_list_arower")
def get_member_ids():
    """ get member ids for arrowers """
    result = {}
    result["draw"] = request.args.get('draw', type=int)

    # translate request parameters
    gcf_id = request.args.get('gcf_id', type=int)
    run_id = request.args.get('run_id', type=int)
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

        # fetch total gcf count for this run
        result["totalGCFrun"] = cur.execute((
            "select count(id)"
            " from gcf"
            " where gcf.clustering_id=?"
        ), (clustering_id,)).fetchall()[0][0]

        # fetch total records (all bgcs sharing gcfs)
        result["recordsTotal"] = cur.execute((
            "select count(distinct bgc_id)"
            " from gcf_membership,gcf"
            " where gcf_membership.gcf_id=gcf.id"
            " and gcf.id=?"
            " and gcf.clustering_id=?"
            " and gcf_membership.rank = 0"
        ), (
            gcf_id, clustering_id)).fetchall()[0][0]

        # fetch total records (filtered)
        result["recordsFiltered"] = cur.execute((
            "select count(distinct bgc_id)"
            " from gcf_membership,gcf"
            " where gcf_membership.gcf_id=gcf.id"
            " and gcf.id=?"
            " and gcf.clustering_id=?"
            " and gcf_membership.rank = 0"
        ), (
            gcf_id, clustering_id)).fetchall()[0][0]

        # fetch data for table
        result["data"] = []

        for bgc_id, bgc_name, dataset_id, dataset_name, dist in cur.execute((
            "select bgc.id, bgc.name, dataset.id, dataset.name,"
            " gcf_membership.membership_value"
            " from bgc, dataset, gcf_membership"
            " where gcf_membership.gcf_id=?"
            " and gcf_membership.rank = 0"
            " and gcf_membership.bgc_id=bgc.id"
            " and dataset.id=bgc.dataset_id"
            " order by gcf_membership.membership_value asc"
            " limit ? offset ?"
        ), (
            gcf_id, limit, offset
        )).fetchall():
            result["data"].append([
                (dataset_id, dataset_name),
                (bgc_id, bgc_name, dataset_id, dataset_name),
                float("{:.2f}".format(dist)),
                bgc_id
            ])

        return result
