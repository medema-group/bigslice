import sqlite3
import pandas as pd
import numpy as np
from os import path, makedirs


def export_bgc_metadata(result_folder, csv_path, sep=","):
    with sqlite3.connect(path.join(result_folder, "result/data.db")) as con:
        cur = con.cursor()        
        bgc_ids = [row[0] for row in cur.execute("select id from bgc order by id asc").fetchall()]

        print("loading clustergbk metadata..")
        dataset_names, folder_paths, file_names, contig_edges, length_nts = list(zip(*cur.execute(
            "select dataset.name, bgc.orig_folder, bgc.orig_filename, bgc.on_contig_edge, bgc.length_nt"
            " from bgc,dataset"
            " where bgc.dataset_id=dataset.id"
            " order by bgc.id"
        ).fetchall()))

        print("loading taxonomy information..")
        taxonomy_info = []
        for taxon_title, taxon_level in cur.execute(
                "select name, level from taxon_class order by level asc"
            ).fetchall():
            taxa_names = pd.Series(
                np.full(len(bgc_ids), "n/a"),
                index=bgc_ids
            )

            try:
                taxa_bgc_ids, taxa_names = list(zip(*cur.execute((
                    "select bgc_taxonomy.bgc_id, taxon.name from bgc_taxonomy, taxon "
                    "where taxon.id=bgc_taxonomy.taxon_id and taxon.level=?"
                    ), (taxon_level,)).fetchall()))
                taxa_names[taxa_bgc_ids] = taxa_names
            except:
                pass
            taxonomy_info.append((taxon_title, taxa_names))

        print("loading class information..")
        class_titles = sorted(set([
            "{}:{}".format(class_name, subclass_name)\
            for class_name, subclass_name in cur.execute(
                "select chem_class.name, chem_subclass.name from chem_subclass, chem_class"
                " where chem_class.id=chem_subclass.class_id"
            ).fetchall()]))
        class_presences = {}
        for class_title in class_titles:
            class_name, subclass_name = class_title.split(":")
            subclass_presences = pd.Series(
                np.full(len(bgc_ids), False),
                index=bgc_ids
            )

            try:
                subclass_bgc_ids, = list(zip(*cur.execute((
                    "select distinct bgc_class.bgc_id from bgc_class, chem_subclass, chem_class "
                    "where chem_subclass.class_id=chem_class.id "
                    "and bgc_class.chem_subclass_id=chem_subclass.id "
                    "and chem_class.name like ? and chem_subclass.name like ?"
                    ), (class_name, subclass_name)).fetchall()))
                subclass_presences[subclass_bgc_ids] = True
            except:
                pass
            class_presences[class_title] = subclass_presences

        print("merging datasets...")
        bgc_metadata = {
            "dataset": dataset_names,
            "genome": folder_paths,
            "bgc": file_names,
            "contig_edge": contig_edges,
            "len_nt": length_nts
        }
        for taxon_title, taxa_names in taxonomy_info:
            bgc_metadata["taxon-" + taxon_title] = taxa_names.values
        for class_title in sorted(class_titles):
            bgc_metadata["class-" + class_title] = class_presences[class_title].values

        bgc_metadata = pd.DataFrame(bgc_metadata, index=bgc_ids)

        bgc_metadata.to_csv(csv_path, sep=sep)


def export_run_metadata(result_folder, csv_path, sep=","):
    with sqlite3.connect(path.join(result_folder, "result/data.db")) as con:
        cur = con.cursor()
        df = pd.read_sql((
            "select clustering.run_id, time_stamp, prog_params, status, threshold, num_centroids as num_gcfs"
            " from run join clustering on clustering.run_id=run.id"
            " join run_log on run_log.run_id=run.id"
            " where run_log.message like 'run created %'"
            " order by run.id"
        ), con, index_col="run_id")

        df.to_csv(csv_path, sep=sep)


def export_gcf_membership(result_folder, csv_path, sep=","):
    with sqlite3.connect(path.join(result_folder, "result/data.db")) as con:
        cur = con.cursor()        
        bgc_ids = [row[0] for row in cur.execute("select id from bgc order by id asc").fetchall()]

        df = pd.read_sql((
            "select bgc_id, gcf.id_in_run, run_id from gcf"
            " join gcf_membership on gcf.id=gcf_id join clustering on clustering.id=clustering_id where rank=0"
        ), con).pivot_table(
            values='id_in_run', index='bgc_id', columns='run_id', aggfunc='first'
        )
        df = df.reindex(sorted(df.columns), axis=1)
        df.columns = "run#" + df.columns.astype(str).values
        df = df.reindex(bgc_ids).fillna(-1).astype(int)

        df.to_csv(csv_path, sep=sep)


def export_tsv_to_folder(result_folder, output_folder):

    #first, check if folder exists
    if path.exists(output_folder):
        print((
            "Output folder exists! ({})".format(output_folder)
        ))
        return 1

    makedirs(output_folder)

    path_tsv = path.join(output_folder, "bgc_metadata.tsv")
    print("Exporting BGC metadata table... {}".format(path_tsv))
    export_bgc_metadata(result_folder, path_tsv, sep="\t")

    path_tsv = path.join(output_folder, "run_metadata.tsv")
    print("Exporting Run metadata table... {}".format(path_tsv))
    export_run_metadata(result_folder, path_tsv, sep="\t")

    path_tsv = path.join(output_folder, "gcf_membership.tsv")
    print("Exporting BGC-GCF membership table... {}".format(path_tsv))
    export_gcf_membership(result_folder, path_tsv, sep="\t")

    return 0