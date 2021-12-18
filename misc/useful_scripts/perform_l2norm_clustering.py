import sqlite3
import pandas as pd
import numpy as np
from os import path
from sys import argv
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import normalize
from sklearn.cluster import Birch


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


def fetch_bgc_features(result_folder):
    print("loading bgc features...")
    with sqlite3.connect(path.join(result_folder, "result/data.db")) as con:
        cur = con.cursor()
        bgc_ids = [row[0] for row in cur.execute("select id from bgc order by id asc").fetchall()]
        hmm_ids = [row[0] for row in cur.execute("select id, name from hmm where db_id=1 order by id asc").fetchall()]
        bgc_features = pd.DataFrame(
            np.zeros((len(bgc_ids), len(hmm_ids)), dtype=np.uint8),
            index=bgc_ids,
            columns=hmm_ids
        )
        for bgc_id, hmm_id, value in cur.execute((
            "select bgc_id, hmm_id, value"
            " from bgc_features,bgc,hmm"
            " where bgc_features.bgc_id=bgc.id"
            " and hmm.id=bgc_features.hmm_id"
            " and hmm.db_id=1"
        )).fetchall():
            bgc_features.at[bgc_id, hmm_id] = value
    return bgc_features


def get_hmm_names(result_folder):
    with sqlite3.connect(path.join(result_folder, "result/data.db")) as con:
        cur = con.cursor()
        ids, names = list(zip(*cur.execute("select id, name from hmm where db_id=1 order by id asc").fetchall()))
        hmm_names = pd.Series(names, index=ids)
        return hmm_names


def fetch_gcf_models(features, threshold):
    birch = Birch(
        n_clusters=None,  # no global clustering
        compute_labels=False,  # only calc centroids
        copy=False,  # data already copied
        threshold=threshold,
        branching_factor=features.shape[0]
    )

    # call birch
    birch.fit(
        features
    )

    # save centroids
    return birch.subcluster_centers_


def fetch_gcf_membership(features, gcf_models):
    nn = NearestNeighbors()
    nn.fit(gcf_models)

    result = nn.kneighbors(
        normalize(features.values, norm="l2"),
        n_neighbors=1
    )
    
    return pd.DataFrame(
        {
            "gcf": gcf_models.index[result[1][:, 0]],
            "dist": result[0][:, 0]
        }, index = features.index
    )

   
def main():
    try:
        bigslice_result_folder = argv[1]
        threshold = float(argv[2])
        output_gcf_features_tsv_path = argv[3]
        output_bgc_membership_path = argv[4]
    except:
        print("usage: python perform_l2norm_clustering.py <bigslice_result_folder> <threshold_0.0-1.4> <output_gcf_features_tsv_path> <output_bgc_membership_path>")
        return 1

    print("extracting bgc features...")
    bgc_features = fetch_bgc_features(bigslice_result_folder)
    bgc_features.columns = get_hmm_names(bigslice_result_folder)

    print("extracting bgc metadata...")
    bgc_metadata = fetch_bgc_metadata(bigslice_result_folder).loc[bgc_features.index]

    print("calculating GCF features...")
    gcf_models = fetch_gcf_models(
    	normalize(bgc_features[bgc_metadata["contig_edge"] == 0], norm="l2")[
    		np.argsort(bgc_features[bgc_metadata["contig_edge"] == 0].sum(axis=1))
    	], threshold
    )
    gcf_models = pd.DataFrame(gcf_models, columns=bgc_features.columns)

    print ("saving to file...")
    gcf_models.to_csv(output_gcf_features_tsv_path, sep="\t")

    print("assigning BGC memberships...")
    bgc_memberships = fetch_gcf_membership(bgc_features, gcf_models)

    print ("saving to file...")
    bgc_memberships.to_csv(output_bgc_membership_path, sep="\t")

    return 0

if __name__ == "__main__":
    main()