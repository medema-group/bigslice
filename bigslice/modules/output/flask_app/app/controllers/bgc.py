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
blueprint = Blueprint('bgc', __name__)


@blueprint.route("/dataset/<int:dataset_id>/bgc/<int:bgc_id>")
def page_bgc_no_run(dataset_id, bgc_id):
    return redirect("/dataset/{}/bgc/{}/run/0".format(dataset_id, bgc_id))


@blueprint.route("/dataset/<int:dataset_id>/bgc/<int:bgc_id>/run/<int:run_id>")
def page_bgc(dataset_id, bgc_id, run_id):

    # page title
    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()

        # redirect if run_id/dataset_id == 0
        redir = False
        if dataset_id < 1:
            # fetch appropriate dataset_id
            dataset_id = cur.execute((
                "select dataset_id"
                " from bgc"
                " where id=?"
            ), (bgc_id, )).fetchall()[0][0]
            redir = True
        if run_id < 1:
            # fetch latest run
            run_id = cur.execute((
                "select id"
                " from run"
                " order by id desc"
                " limit 1"
            )).fetchall()[0][0]
            redir = True
        if redir:
            return redirect("/dataset/{}/bgc/{}/run/{}".format(
                dataset_id, bgc_id, run_id))

        # fetch bgc_name, dataset_name
        bgc_name, dataset_name = cur.execute((
            "select bgc.name, dataset.name"
            " from bgc, dataset"
            " where bgc.id=?"
            " and bgc.dataset_id=?"
            " and bgc.dataset_id=dataset.id"
        ), (bgc_id, dataset_id)).fetchall()[0]

        # fetch taxon for subtitle
        bgc_taxon_name = cur.execute((
            "select taxon.name"
            " from bgc_taxonomy, taxon, bgc"
            " where bgc.id=bgc_taxonomy.bgc_id"
            " and taxon.id=bgc_taxonomy.taxon_id"
            " and bgc.id=?"
            " order by taxon.level desc"
            " limit 1"
        ), (bgc_id, )).fetchall()[:1]

        # fetch clustering threshold
        threshold = cur.execute((
            "select threshold"
            " from clustering"
            " where clustering.run_id=?"
        ), (run_id, )).fetchall()[0][0]

        # set title and subtitle
        page_title = "BGC: {}".format(bgc_name)
        if len(bgc_taxon_name) <= 0:
            page_subtitle = ("From dataset: {}".format(dataset_name))
        else:
            page_subtitle = (
                "From <i>{}</i> (dataset: {})".format(
                    bgc_taxon_name[0][0], dataset_name))

        # status_id
        status_id, = cur.execute((
            "select status"
            " from run"
            " where id = ?"
        ), (run_id, )).fetchall()[0]

        # for run selector dropdown
        run_ids = [row[0] for row
                   in cur.execute((
                       "select id"
                       " from run"
                       " order by id asc"
                   )).fetchall()]

    # render view
    return render_template(
        "bgc/main.html.j2",
        bgc_id=bgc_id,
        dataset_id=dataset_id,
        run_id=run_id,
        run_ids=run_ids,
        threshold=threshold,
        status_id=status_id,
        page_title=page_title,
        page_subtitle=page_subtitle
    )

# APIs


@blueprint.route("/api/bgc/get_overview")
def get_overview():
    """ for bgc overview tables """
    result = {}
    bgc_id = request.args.get('bgc_id', type=int)

    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()

        # fetch direct properties
        (folder_path, file_path, on_contig_edge,
         result["length"], result["type"],
         result["type_desc"]) = cur.execute((
             "select orig_folder, orig_filename,"
             " on_contig_edge, length_nt, type,"
             " enum_bgc_type.description"
             " from bgc, enum_bgc_type"
             " where bgc.id=?"
             " and bgc.type=enum_bgc_type.code"
         ), (bgc_id, )).fetchall()[0]
        result["file_path"] = path.join("/", folder_path, file_path)
        result["fragmented"] = "yes" if on_contig_edge == 1 else (
            "no" if on_contig_edge == 0 else "n/a"
        )

        # fetch genes count
        result["genes_count"] = cur.execute((
            "select count(id)"
            " from cds"
            " where bgc_id=?"
        ), (bgc_id, )).fetchall()[0][0]

        # fetch taxonomy information
        result["taxon_desc"] = cur.execute((
            "select level, name"
            " from taxon_class"
            " order by level asc"
        )).fetchall()
        result["taxonomy"] = {
            row[0]: row[1] for row in cur.execute((
                "select level, taxon.name"
                " from taxon, bgc_taxonomy"
                " where taxon.id=bgc_taxonomy.taxon_id"
                " and bgc_taxonomy.bgc_id=?"
            ), (bgc_id, )).fetchall()
        }

        # fetch class information
        result["classes"] = cur.execute((
            "select chem_class.name, chem_subclass.name"
            " from bgc, bgc_class, chem_subclass, chem_class"
            " where bgc.id=bgc_class.bgc_id"
            " and bgc_class.chem_subclass_id=chem_subclass.id"
            " and chem_subclass.class_id=chem_class.id"
            " and bgc.id=?"
        ), (bgc_id, )).fetchall()

    return result


@blueprint.route("/api/bgc/get_arrower_objects")
def get_arrower_objects():
    """ for arrower js """
    result = {}
    bgc_ids = map(int, request.args.get('bgc_id', type=str).split(","))
    run_id = request.args.get('run_id', type=int)

    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()

        for bgc_id in bgc_ids:
            data = {}

            # get bgc name, length and description
            bgc_name, bgc_length, dataset_name = cur.execute((
                "select bgc.name, bgc.length_nt, dataset.name"
                " from bgc, dataset"
                " where bgc.id=?"
                " and bgc.dataset_id=dataset.id"
            ), (bgc_id, )).fetchall()[0]
            bgc_taxon_name = cur.execute((
                "select taxon.name"
                " from bgc_taxonomy, taxon, bgc"
                " where bgc.id=bgc_taxonomy.bgc_id"
                " and taxon.id=bgc_taxonomy.taxon_id"
                " and bgc.id=?"
                " order by taxon.level desc"
                " limit 1"
            ), (bgc_id, )).fetchall()[:1]

            data["id"] = "BGC: {}".format(bgc_name)
            data["start"] = 0
            data["end"] = bgc_length
            if len(bgc_taxon_name) <= 0:
                data["desc"] = ("From dataset: {}".format(dataset_name))
            else:
                data["desc"] = (
                    "From <i>{}</i> (dataset: {})".format(
                        bgc_taxon_name[0][0], dataset_name))

            # get cds
            data["orfs"] = []
            for cds_id, locus_tag, protein_id, \
                    cds_start, cds_end, cds_strand in cur.execute((
                        "select id, locus_tag, protein_id,"
                        " nt_start, nt_end, strand"
                        " from cds"
                        " where bgc_id=?"
                        " order by nt_start asc"
                    ), (bgc_id, )).fetchall():
                orf = {
                    "start": cds_start,
                    "end": cds_end,
                    "strand": cds_strand
                }

                orf_names = []
                if locus_tag:
                    orf_names.append(locus_tag)
                if protein_id:
                    orf_names.append(protein_id)
                if len(orf_names) < 1:
                    orf_names.append("n/a")
                orf["id"] = " / ".join(orf_names)

                orf["domains"] = []
                # get hsps
                for dom_id, dom_name, bitscore, dom_start, dom_end, \
                        sub_ids, sub_names, sub_scores in cur.execute((
                            "select hmm_id, hmm_name,"
                            " bitscore, cds_start, cds_end,"
                            " group_concat(sub_id),"
                            " group_concat(sub_name),"
                            " group_concat(sub_score)"
                            " from"
                            " (select hsp.id as hsp_id, hmm.id as hmm_id,"
                            " hmm.name as hmm_name, hsp.bitscore as bitscore,"
                            " hsp_alignment.cds_start as cds_start,"
                            " hsp_alignment.cds_end as cds_end,"
                            " hmmsub.id as sub_id,"
                            " substr(hmmsub.name,"
                            " instr(hmmsub.name, 'aligned_c')+8) as sub_name,"
                            " hspsub.bitscore as sub_score"
                            " from hmm, hsp, hsp_alignment, run"
                            " left join hsp_subpfam"
                            " on hsp_subpfam.hsp_parent_id=hsp.id"
                            " left join hsp as hspsub"
                            " on hspsub.id=hsp_subpfam.hsp_subpfam_id"
                            " left join hmm as hmmsub"
                            " on hmmsub.id=hspsub.hmm_id"
                            " where hsp.cds_id=?"
                            " and hsp_alignment.hsp_id=hsp.id"
                            " and hmm.id=hsp.hmm_id"
                            " and hmm.db_id=run.hmm_db_id"
                            " and run.id=?"
                            " order by cds_start, hspsub.bitscore asc"
                            ") group by hsp_id"
                        ), (cds_id, run_id)).fetchall():  # hsps:
                    dom_code = dom_name
                    if sub_ids:
                        dom_code += " [{}]".format(sub_names)
                    hsp = {
                        "code": dom_code,
                        "bitscore": bitscore,
                        "start": dom_start,
                        "end": dom_end
                    }

                    orf["domains"].append(hsp)
                data["orfs"].append(orf)

            # append
            result[bgc_id] = data

    return result


@blueprint.route("/api/bgc/get_word_cloud")
def get_word_cloud():
    """ for bgc features word cloud """
    result = {}
    bgc_id = request.args.get('bgc_id', type=int)
    limit = request.args.get('limit', default=20, type=int)

    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()

        result["words"] = []
        for name, weight in cur.execute((
            "select hmm.name,"
            " case"
            " when subpfam.parent_hmm_id > 0"
            " then sum(hsp.bitscore)"
            " else count(hsp.bitscore)*255"
            " end weight"
            " from hsp, cds, hmm"
            " left join subpfam on hmm.id=subpfam.hmm_id"
            " where hsp.cds_id=cds.id"
            " and cds.bgc_id=?"
            " and hsp.hmm_id=hmm.id"
            " group by hmm.name"
            " order by weight desc"
            " limit ?"
        ), (bgc_id, limit)).fetchall():
            result["words"].append({
                "text": name,
                "weight": weight
            })

    return result


@blueprint.route("/api/bgc/get_genes_table")
def get_genes_table():
    """ for genes datatable """
    result = {}
    result["draw"] = request.args.get('draw', type=int)

    # translate request parameters
    bgc_id = request.args.get('bgc_id', type=int)
    run_id = request.args.get('run_id', type=int)
    offset = request.args.get('start', type=int)
    limit = request.args.get('length', type=int)

    with sqlite3.connect(conf["db_path"]) as con:
        cur = con.cursor()

        # fetch total records (all bgcs in the dataset)
        result["recordsTotal"] = cur.execute((
            "select count(id)"
            " from cds"
            " where bgc_id=?"
        ), (bgc_id,)).fetchall()[0][0]

        # fetch total records (filtered)
        result["recordsFiltered"] = cur.execute((
            "select count(id)"
            " from cds"
            " where bgc_id=?"
        ), (bgc_id,)).fetchall()[0][0]

        # fetch data for table
        result["data"] = []
        for cds_id, start, end, strand, locus_tag, \
                protein_id, product, aa_seq in cur.execute((
                    "select id, nt_start, nt_end, strand,"
                    " locus_tag, protein_id, product, aa_seq"
                    " from cds"
                    " where bgc_id=?"
                    " order by nt_start asc"
                    " limit ? offset ?"
                ), (bgc_id, limit, offset)).fetchall():
            data = {}

            # gene name
            data["names"] = []
            if locus_tag:
                data["names"].append(locus_tag)
            if protein_id:
                data["names"].append(protein_id)
            if len(data["names"]) < 1:
                data["names"].append("n/a")

            # product
            data["product"] = product or "n/a"
            data["locus"] = (start, end, strand)
            data["aa_seq"] = aa_seq

            # domain information
            data["domains"] = []

            for dom_id, dom_name, bitscore, dom_start, dom_end, \
                    sub_ids, sub_names, sub_scores in cur.execute((
                        "select hmm_id, hmm_name,"
                        " bitscore, cds_start, cds_end,"
                        " group_concat(sub_id),"
                        " group_concat(sub_name),"
                        " group_concat(sub_score)"
                        " from"
                        " (select hsp.id as hsp_id, hmm.id as hmm_id,"
                        " hmm.name as hmm_name, hsp.bitscore as bitscore,"
                        " hsp_alignment.cds_start as cds_start,"
                        " hsp_alignment.cds_end as cds_end,"
                        " hmmsub.id as sub_id,"
                        " substr(hmmsub.name,"
                        " instr(hmmsub.name, 'aligned_c')+8) as sub_name,"
                        " hspsub.bitscore as sub_score"
                        " from hmm, hsp, hsp_alignment, run"
                        " left join hsp_subpfam"
                        " on hsp_subpfam.hsp_parent_id=hsp.id"
                        " left join hsp as hspsub"
                        " on hspsub.id=hsp_subpfam.hsp_subpfam_id"
                        " left join hmm as hmmsub"
                        " on hmmsub.id=hspsub.hmm_id"
                        " where hsp.cds_id=?"
                        " and hsp_alignment.hsp_id=hsp.id"
                        " and hmm.id=hsp.hmm_id"
                        " and hmm.db_id=run.hmm_db_id"
                        " and run.id=?"
                        " order by cds_start, hspsub.bitscore asc"
                        ") group by hsp_id"
                    ), (cds_id, run_id)).fetchall():
                dom_code = dom_name
                if sub_ids:
                    dom_code += " [{}]".format(sub_names)
                data["domains"].append([
                    dom_code,
                    bitscore,
                    dom_start,
                    dom_end
                ])

            result["data"].append([
                data["names"],
                data["product"],
                data["locus"],
                data["domains"],
                (cds_id, data["aa_seq"])
            ])

    return result


@blueprint.route("/api/bgc/get_gcf_hits_table")
def get_gcf_hits_table():
    """ for gcf hits datatable """
    result = {}
    result["draw"] = request.args.get('draw', type=int)

    # translate request parameters
    bgc_id = request.args.get('bgc_id', type=int)
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

        # fetch total records (all gcf in bgc)
        result["recordsTotal"] = cur.execute((
            "select count(gcf_id)"
            " from gcf, gcf_membership"
            " where bgc_id=?"
            " and gcf.id=gcf_membership.gcf_id"
            " and gcf.clustering_id=?"
        ), (bgc_id, clustering_id)).fetchall()[0][0]

        # fetch total records (filtered)
        result["recordsFiltered"] = cur.execute((
            "select count(gcf_id)"
            " from gcf, gcf_membership"
            " where bgc_id=?"
            " and gcf.id=gcf_membership.gcf_id"
            " and gcf.clustering_id=?"
        ), (bgc_id, clustering_id)).fetchall()[0][0]

        # fetch data for table
        result["data"] = []
        for gcf_id, gcf_accession, membership_value in cur.execute((
            "select gcf_id, id_in_run, membership_value"
            " from gcf, gcf_membership"
            " where bgc_id=?"
            " and gcf.id=gcf_membership.gcf_id"
            " and gcf.clustering_id=?"
            " order by rank asc"
            " limit ? offset ?"
        ), (bgc_id, clustering_id, limit, offset)).fetchall():

            # fetch gcf name
            gcf_name = "GCF_{:0{width}d}".format(
                gcf_accession, width=math.ceil(
                    math.log10(result["totalGCFrun"])))

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
                membership_value,
                (gcf_id, gcf_name),
                core_members,
                class_counts,
                taxon_counts
            ])
    return result


@blueprint.route("/api/bgc/get_homologous_bgcs")
def get_homologous_bgcs():
    """ for homologous bgcs for the datatable """
    result = {}
    result["draw"] = request.args.get('draw', type=int)

    # translate request parameters
    bgc_id = request.args.get('bgc_id', type=int)
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
        result["threshold"] = threshold

        # fetch total gcf count for this run
        result["totalGCFrun"] = cur.execute((
            "select count(id)"
            " from gcf"
            " where gcf.clustering_id=?"
        ), (clustering_id,)).fetchall()[0][0]

        # fetch total records (all bgcs sharing gcfs)
        result["recordsTotal"] = cur.execute((
            "select count(distinct bgc_features.bgc_id)"
            " from gcf_membership, bgc_features"
            " where gcf_id in"
            " ("
            "    select gcf_id"
            "    from gcf,gcf_membership"
            "    where bgc_id=?"
            "    and gcf_membership.gcf_id=gcf.id"
            "    and gcf.clustering_id=?"
            " )"
            " and gcf_membership.membership_value <= ?"
            " and gcf_membership.rank = 0"
            " and bgc_features.hmm_id"
            " in ("
            " select hmm_id"
            " from bgc_features, hmm, run"
            " where bgc_id=?"
            " and hmm_id=hmm.id"
            " and hmm.db_id=run.hmm_db_id"
            " and run.id=?"
            " )"
            " and bgc_features.bgc_id=gcf_membership.bgc_id"
            " and bgc_features.value >= 255"
            " and bgc_features.bgc_id!=?"
        ), (bgc_id, clustering_id,
            threshold, bgc_id, run_id, bgc_id)).fetchall()[0][0]

        # fetch total records (filtered)
        result["recordsFiltered"] = cur.execute((
            "select count(distinct bgc_features.bgc_id)"
            " from gcf_membership, bgc_features"
            " where gcf_id in"
            " ("
            "    select gcf_id"
            "    from gcf,gcf_membership"
            "    where bgc_id=?"
            "    and gcf_membership.gcf_id=gcf.id"
            "    and gcf.clustering_id=?"
            " )"
            " and gcf_membership.membership_value <= ?"
            " and gcf_membership.rank = 0"
            " and bgc_features.hmm_id"
            " in ("
            " select hmm_id"
            " from bgc_features, hmm, run"
            " where bgc_id=?"
            " and hmm_id=hmm.id"
            " and hmm.db_id=run.hmm_db_id"
            " and run.id=?"
            " )"
            " and bgc_features.bgc_id=gcf_membership.bgc_id"
            " and bgc_features.value >= 255"
            " and bgc_features.bgc_id!=?"
        ), (bgc_id, clustering_id,
            threshold, bgc_id, run_id, bgc_id)).fetchall()[0][0]

        # fetch bgc_name, dataset_name
        result["bgc_name"], result["dataset_name"] = cur.execute((
            "select bgc.name, dataset.name"
            " from bgc, dataset"
            " where bgc.id=?"
            " and bgc.dataset_id=dataset.id"
        ), (bgc_id, )).fetchall()[0]

        # fetch taxonomy descriptor
        result["taxon_desc"] = cur.execute((
            "select level, name"
            " from taxon_class"
            " order by level asc"
        )).fetchall()

        # fetch features count for query bgc
        result["total_features"] = cur.execute((
            "select count(distinct hmm.id)"
            " from bgc_features, hmm, run"
            " where bgc_features.bgc_id=?"
            " and bgc_features.hmm_id=hmm.id"
            " and hmm.db_id=run.hmm_db_id"
            " and run.id=?"
            " and bgc_features.value >= 255"
        ), (bgc_id, run_id, )).fetchall()[0][0]

        # fetch data for table
        result["data"] = []

        for target_bgc_id, gcf_id, gcf_accession, shared_count in cur.execute((
            "select bgc_features.bgc_id, gcf.id,"
            " gcf.id_in_run, count(distinct hmm_id) as counts"
            " from bgc_features,gcf_membership,gcf"
            " where gcf_membership.bgc_id=bgc_features.bgc_id"
            " and gcf.id=gcf_membership.gcf_id"
            " and gcf.clustering_id=?"
            " and gcf_membership.rank=0"
            " and gcf_membership.membership_value <= ?"
            " and bgc_features.bgc_id"
            " in ("
            " select distinct bgc_id"
            " from gcf_membership"
            " where gcf_id in"
            " ("
            "   select gcf_id"
            "   from gcf,gcf_membership"
            "   where bgc_id=?"
            "   and gcf_membership.gcf_id=gcf.id"
            "   and gcf.clustering_id=?"
            " )"
            " and gcf_membership.membership_value <= ?"
            " and gcf_membership.rank = 0"
            " )"
            " and bgc_features.hmm_id"
            " in ("
            " select hmm_id"
            " from bgc_features, hmm, run"
            " where bgc_id=?"
            " and hmm_id=hmm.id"
            " and hmm.db_id=run.hmm_db_id"
            " and run.id=?"
            " )"
            " and bgc_features.value >= 255"
            " and bgc_features.bgc_id!=?"
            " group by bgc_features.bgc_id"
            " order by counts desc"
            " limit ? offset ?"
        ),
            (clustering_id, threshold, bgc_id, clustering_id,
                threshold, bgc_id, run_id, bgc_id,
                limit, offset)).fetchall():

            # fetch basic information
            bgc_name, bgc_length, dataset_id, dataset_name = cur.execute((
                "select bgc.name, bgc.length_nt, dataset.id, dataset.name"
                " from bgc,dataset"
                " where bgc.dataset_id=dataset.id"
                " and bgc.id=?"
            ), (target_bgc_id, )).fetchall()[0]

            # fetch distance
            distance = int(math.sqrt(cur.execute((
                "select sum(sqsum)"
                " from"
                " ("
                " select case when count(value) > 1"
                " then"
                " (max(value)-min(value))*(max(value)-min(value))"
                " else"
                " max(value)*max(value)"
                " end as sqsum"
                " from bgc_features,hmm,run"
                " where bgc_id in (?, ?)"
                " and bgc_features.hmm_id=hmm.id"
                " and hmm.db_id=run.hmm_db_id"
                " and run.id=?"
                " and bgc_features.value > 0"
                " group by hmm_id"
                " )"
            ), (bgc_id, target_bgc_id, run_id)).fetchall()[0][0]))

            # fetch gcf name
            gcf_name = "GCF_{:0{width}d}".format(
                gcf_accession, width=math.ceil(
                    math.log10(result["totalGCFrun"])))

            # fetch taxonomy information
            taxonomy = {
                row[0]: row[1] for row in cur.execute((
                    "select taxon.level, taxon.name"
                    " from taxon, bgc_taxonomy"
                    " where taxon.id=bgc_taxonomy.taxon_id"
                    " and bgc_taxonomy.bgc_id=?"
                ), (target_bgc_id, )).fetchall()
            }

            # fetch class information
            classes = cur.execute((
                "select chem_class.name, chem_subclass.name"
                " from bgc, bgc_class, chem_subclass, chem_class"
                " where bgc.id=bgc_class.bgc_id"
                " and bgc_class.chem_subclass_id=chem_subclass.id"
                " and chem_subclass.class_id=chem_class.id"
                " and bgc.id=?"
            ), (target_bgc_id, )).fetchall()

            result["data"].append([
                (target_bgc_id, dataset_id, bgc_name),
                (gcf_id, gcf_name),
                shared_count,
                distance,
                "{:.02f}".format(bgc_length / 1000),
                taxonomy,
                classes,
                (dataset_id, dataset_name),
                (bgc_id, target_bgc_id)
            ])

    return result
