import sqlite3
import pandas as pd
import numpy as np
from os import path
from sys import argv

def fetch_bgc_metadata(result_folder):
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
        bgc_metadata = pd.DataFrame({
            "dataset": dataset_names,
            "genome": folder_paths,
            "bgc": file_names,
            "contig_edge": contig_edges,
            "len_nt": length_nts
        }, index = bgc_ids)
        for taxon_title, taxa_names in taxonomy_info:
            bgc_metadata["taxon-" + taxon_title] = taxa_names.values
        for class_title in sorted(class_titles):
            bgc_metadata["class-" + class_title] = class_presences[class_title].values

        return bgc_metadata

    
def main():
    try:
        bigslice_result_folder = argv[1]
        output_csv_path = argv[2]
    except:
        print("usage: python extract_features_matrix.py <bigslice_result_folder> <output_tsv_path>")
        return 1

    bgc_metadata = fetch_bgc_metadata(bigslice_result_folder)

    print ("saving to file...")
    bgc_metadata.to_csv(output_csv_path, sep="\t")
    return 0

if __name__ == "__main__":
    main()