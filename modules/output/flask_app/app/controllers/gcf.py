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

        # fetch bgc list (for demo only)
        core_bgcs = [{
            "id": row[0],
            "name": row[1],
            "dataset": row[2],
            "dist": row[3]
        } for row in cur.execute((
            "select bgc.id, bgc.name,"
            " dataset.name, gcf_membership.membership_value"
            " from bgc, gcf_membership, dataset"
            " where gcf_membership.gcf_id=?"
            " and gcf_membership.membership_value<=?"
            " and gcf_membership.rank=0"
            " and gcf_membership.bgc_id=bgc.id"
            " and dataset.id=bgc.dataset_id"
        ), (gcf_id, threshold)).fetchall()]
        putative_bgcs = [{
            "id": row[0],
            "name": row[1],
            "dataset": row[2],
            "dist": row[3]
        } for row in cur.execute((
            "select bgc.id, bgc.name,"
            " dataset.name, gcf_membership.membership_value"
            " from bgc, gcf_membership, dataset"
            " where gcf_membership.gcf_id=?"
            " and gcf_membership.membership_value>?"
            " and gcf_membership.rank=0"
            " and gcf_membership.bgc_id=bgc.id"
            " and dataset.id=bgc.dataset_id"
        ), (gcf_id, threshold)).fetchall()]

        # set title and subtitle
        page_title = "GCF_{:0{width}d}".format(
            gcf_accession, width=math.ceil(
                math.log10(total_gcf)))
        page_subtitle = "(a temporary visualization just for demo purpose)"

    # render view
    return render_template(
        "gcf/main.html.j2",
        gcf_id=gcf_id,
        run_id=run_id,
        core_bgcs=core_bgcs,
        putative_bgcs=putative_bgcs,
        page_title=page_title,
        page_subtitle=page_subtitle
    )
