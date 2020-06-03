#!/usr/bin/env python3

import sqlite3
from flask import render_template, request
import json
from os import path

# import global config
from ..config import conf

# set blueprint object
from flask import Blueprint
blueprint = Blueprint('dataset', __name__)


@blueprint.route("/dataset/<int:dataset_id>")
def page_dataset(dataset_id):

    # page title
    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()
        if dataset_id > 0:
            page_title, page_subtitle = cur.execute((
                "select name, description"
                " from dataset"
                " where id = ?"
            ), (dataset_id, )).fetchall()[0]
            page_title = "Dataset: " + page_title
        else:
            page_title = "Dataset: &lt;all&gt;"
            page_subtitle = "Includes everything in the database: {}.".format(
                ", ".join([row[0] for row in cur.execute((
                    "select name"
                    " from dataset"
                )).fetchall()])
            )

    # render view
    return render_template(
        "dataset/main.html.j2",
        dataset_id=dataset_id,
        page_title=page_title,
        page_subtitle=page_subtitle
    )

# APIs


@blueprint.route("/api/dataset/get_bgc_table")
def get_bgc_table():
    """ for bgc datatable """
    result = {}
    result["draw"] = request.args.get('draw', type=int)

    # translate request parameters
    dataset_id = request.args.get('dataset_id', default=0, type=int)
    result["dataset_id"] = dataset_id
    offset = request.args.get('start', type=int)
    limit = request.args.get('length', type=int)

    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()

        # fetch total records (all bgcs in the dataset)
        result["recordsTotal"] = cur.execute((
            "select count(id)"
            " from bgc"
            " where dataset_id{}?"
        ).format("=" if dataset_id > 0 else "!="),
            (dataset_id,)).fetchall()[0][0]

        # fetch total records (filtered)
        result["recordsFiltered"] = cur.execute((
            "select count(id)"
            " from bgc"
            " where dataset_id{}?"
        ).format("=" if dataset_id > 0 else "!="),
            (dataset_id,)).fetchall()[0][0]

        # fetch taxonomy descriptor
        result["taxon_desc"] = cur.execute((
            "select level, name"
            " from taxon_class"
            " order by level asc"
        )).fetchall()

        # fetch data for table
        result["data"] = []
        for row in cur.execute((
            "select id as bgc_id"
            ",orig_folder as genome"
            ",orig_filename as bgc_name"
            ",length_nt,on_contig_edge"
            " from bgc"
            " where dataset_id{}?"
            " limit ? offset ?"
        ).format("=" if dataset_id > 0 else "!="),
                (dataset_id, limit, offset)).fetchall():
            bgc_id, genome, name, length, fragmented = row

            # fetch basic data
            data = {
                "bgc_id": bgc_id,
                "genome_name": genome if genome else "n/a",
                "bgc_name": name,
                "bgc_length": "{:.02f}".format(length / 1000)
            }
            if fragmented == 1:
                data["completeness"] = "fragmented"
            elif fragmented == 0:
                data["completeness"] = "complete"
            else:
                data["completeness"] = "n/a"

            # fetch genes count
            data["genes_count"] = cur.execute((
                "select count(id)"
                " from cds"
                " where bgc_id=?"
            ), (bgc_id, )).fetchall()[0][0]

            # fetch taxonomy information
            data["taxonomy"] = {
                row[0]: row[1] for row in cur.execute((
                    "select taxon.level, taxon.name"
                    " from taxon, bgc_taxonomy"
                    " where taxon.id=bgc_taxonomy.taxon_id"
                    " and bgc_taxonomy.bgc_id=?"
                ), (bgc_id, )).fetchall()
            }

            # fetch class information
            data["class_name"] = cur.execute((
                "select chem_class.name, chem_subclass.name"
                " from bgc, bgc_class, chem_subclass, chem_class"
                " where bgc.id=bgc_class.bgc_id"
                " and bgc_class.chem_subclass_id=chem_subclass.id"
                " and chem_subclass.class_id=chem_class.id"
                " and bgc.id=?"
            ), (bgc_id, )).fetchall()

            result["data"].append([
                data["genome_name"],
                data["bgc_name"],
                data["taxonomy"],
                data["class_name"],
                data["bgc_length"],
                data["genes_count"],
                data["completeness"],
                data["bgc_id"]
            ])

    return result


@blueprint.route("/api/dataset/get_stats")
def get_stats():
    """ for statistic summary """
    dataset_id = request.args.get('dataset_id', default=0, type=int)
    result = {}
    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()

        # get total bgc count
        result["total_bgcs"] = cur.execute((
            "select count(id)"
            " from bgc"
            " where dataset_id{}?"
        ).format("=" if dataset_id > 0 else "!="),
            (dataset_id,)).fetchall()[0][0]

        # get total genomes count
        result["total_genomes"] = cur.execute((
            "select count(distinct orig_folder)"
            " from bgc"
            " where dataset_id{}?"
            " and orig_folder not like ''"
        ).format("=" if dataset_id > 0 else "!="),
            (dataset_id,)).fetchall()[0][0]

        # get total bgc in genomes
        result["total_bgcs_in_genome"] = cur.execute((
            "select count(id)"
            " from bgc"
            " where dataset_id{}?"
            " and orig_folder not like ''"
        ).format("=" if dataset_id > 0 else "!="),
            (dataset_id,)).fetchall()[0][0]

        # get total bgc with taxonomy
        result["total_bgcs_with_taxonomy"] = cur.execute((
            "select count(distinct bgc_id)"
            " from bgc, bgc_taxonomy"
            " where bgc.dataset_id{}?"
            " and bgc.id=bgc_taxonomy.bgc_id"
        ).format("=" if dataset_id > 0 else "!="),
            (dataset_id,)).fetchall()[0][0]

    return result


@blueprint.route("/api/dataset/get_class_counts")
def get_class_counts():
    """ for dataset pie chart """
    dataset_id = request.args.get('dataset_id', default=0, type=int)
    result = {}
    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()

        # get distinct class counts
        for class_id, class_name in cur.execute((
            "select id, name"
            " from chem_class")
        ).fetchall():
            result[class_name] = cur.execute((
                "select count(distinct bgc_id) from ("
                "select bgc_id"
                " from bgc, bgc_class, chem_subclass"
                " where bgc.dataset_id{}?"
                " and bgc.id=bgc_class.bgc_id"
                " and chem_subclass.id=bgc_class.chem_subclass_id"
                " group by bgc_id"
                " having count(chem_subclass_id) == 1"
                " and chem_subclass.class_id=?"
                ")"
            ).format("=" if dataset_id > 0 else "!="),
                (dataset_id, class_id)).fetchall()[0][0]

        # get hybrid counts
        result["Hybrid"] = cur.execute((
            "select count(distinct bgc_id) from (select bgc_id"
            " from bgc, bgc_class"
            " where bgc.dataset_id{}?"
            " and bgc.id=bgc_class.bgc_id"
            " group by bgc_id"
            " having count(chem_subclass_id) > 1"
            ")"
        ).format("=" if dataset_id > 0 else "!="),
            (dataset_id, )).fetchall()[0][0]

        # get n/a counts
        bgc_count = cur.execute((
            "select count(distinct id)"
            " from bgc"
            " where dataset_id{}?"
        ).format("=" if dataset_id > 0 else "!="),
            (dataset_id, )).fetchall()[0][0]
        result["n/a"] = bgc_count - sum(result.values())

    for key in list(result.keys()):
        if result[key] < 1:
            del result[key]

    return result


@blueprint.route("/api/dataset/get_bgclength_hist")
def get_bgclength_hist():
    """ for dataset histogram of lengths """
    dataset_id = request.args.get('dataset_id', default=0, type=int)
    bin_size = request.args.get('bin_size', default=1000, type=int)
    result = {
        "labels": [],
        "complete": [],
        "fragmented": [],
        "n/a": []
    }
    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()

        # get min and max length_nt to calculate step-ups
        min_nt, max_nt = cur.execute((
            "select min(length_nt), max(length_nt)"
            " from bgc where dataset_id{}?"
        ).format("=" if dataset_id > 0 else "!="), (dataset_id, )
        ).fetchall()[0]

        # fetch counts per bin
        cur_min = 1
        while cur_min < max_nt:
            cur_max = cur_min + bin_size - 1

            # fetch labels
            result["labels"].append((cur_min, cur_max))

            # fetch complete bgcs count
            result["complete"].append(
                cur.execute((
                    "select count(id)"
                    " from bgc"
                    " where dataset_id{}?"
                    " and length_nt >= ?"
                    " and length_nt <= ?"
                    " and on_contig_edge == 0"
                ).format("=" if dataset_id > 0 else "!="),
                    (dataset_id, cur_min, cur_max)
                ).fetchall()[0][0]
            )

            # fetch fragmented bgcs count
            result["fragmented"].append(
                cur.execute((
                    "select count(id)"
                    " from bgc"
                    " where dataset_id{}?"
                    " and length_nt >= ?"
                    " and length_nt <= ?"
                    " and on_contig_edge == 1"
                ).format("=" if dataset_id > 0 else "!="),
                    (dataset_id, cur_min, cur_max)
                ).fetchall()[0][0]
            )

            # fetch n/a bgcs count (as4)
            result["n/a"].append(
                cur.execute((
                    "select count(id)"
                    " from bgc"
                    " where dataset_id{}?"
                    " and length_nt >= ?"
                    " and length_nt <= ?"
                    " and on_contig_edge is NULL"
                ).format("=" if dataset_id > 0 else "!="),
                    (dataset_id, cur_min, cur_max)
                ).fetchall()[0][0]
            )

            cur_min = cur_max + 1

    return json.dumps(result)
