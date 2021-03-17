import sqlite3
import pandas as pd
import numpy as np
from os import path
from sys import argv

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
    
def main():
    try:
        bigslice_result_folder = argv[1]
        output_csv_path = argv[2]
    except:
        print("usage: python extract_features_matrix.py <bigslice_result_folder> <output_tsv_path>")
        return 1

    bigfam_features = fetch_bgc_features(bigslice_result_folder)
    bigfam_features.columns = get_hmm_names(bigslice_result_folder)

    print ("saving to file...")
    bigfam_features.to_csv(output_csv_path, sep="\t")
    return 0

if __name__ == "__main__":
    main()