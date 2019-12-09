#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Copyright (C) 2019 Satria A. Kautsar
# Wageningen University & Research
# Bioinformatics Group
"""bigsscuit.modules.data.features

Handle manipulation and storage of features
for now, also do feature extraction

todo: separate features extraction method
todo: use parallel processing
todo: use Dask
"""

from os import path
from .database import Database
from ..utils import get_chunk
from datetime import datetime
from multiprocessing import Pool
import numpy as np
import pandas as pd


class Features:
    """Represents a features entry in the database"""

    def __init__(self, properties: dict, database: Database):
        self.id = properties.get("id", -1)
        self.database = database
        self.run_id = properties["run_id"]
        self.extraction_method = properties["method"]
        self.extraction_start = properties["start"]
        self.extraction_end = properties["end"]
        self.data = properties["data"]

    def save(self, output_folder: str, database: Database):
        """commits features data"""
        existing = database.select(
            "features",
            "WHERE run_id=? AND extraction_method=?",
            parameters=(self.run_id, self.extraction_method),
            props=["id"]
        )
        if existing:
            # for now, this should not get called
            raise Exception("not_implemented")
        else:
            # save to database
            self.id = database.insert(
                "features",
                {
                    "run_id": self.run_id,
                    "extraction_method": self.extraction_method,
                    "extraction_start": self.extraction_start,
                    "extraction_end": self.extraction_end
                }
            )
            # immediately commits, don't want to have double pickled file
            database.commit_inserts()

            # pickle data
            pickle_path = path.join(output_folder, "{}.pkl".format(self.id))
            self.data.to_pickle(pickle_path,
                                compression=None,
                                protocol=4
                                )

    @staticmethod
    def extract(run_id: int, method: str, database: Database, pool: Pool):

        start_time = datetime.now()

        # fetch bgc ids
        bgc_ids, bgc_status = map(tuple, list(zip(*database.select(
            "run_bgc_status",
            "WHERE run_id=?",
            parameters=(run_id, ),
            props=["bgc_id", "status"],
            as_tuples=True
        ))))

        bgc_status_all = set(bgc_status)
        for status in bgc_status_all:
            if status < 3:
                raise Exception("error: not all BGCs are subpfam_scanned")

        # prepare features extraction
        hmm_ids, parent_hmm_ids, hmm_names = map(
            tuple, list(zip(*database.select(
                "hmm,run LEFT JOIN subpfam ON hmm.id=subpfam.hmm_id",
                "WHERE hmm.db_id=run.hmm_db_id" +
                " AND run.id=?",
                parameters=(run_id, ),
                props=["hmm.id", "subpfam.parent_hmm_id", "hmm.name"],
                as_tuples=True
            ))))
        bgc_features = np.zeros(
            (len(bgc_ids), len(hmm_ids)), dtype=np.uint8)

        # for referencing the rows
        bgc_idx = {value: idx for idx, value in enumerate(bgc_ids)}
        hmm_idx = {value: idx for idx, value in enumerate(hmm_ids)}
        subpfam_ids = {}
        for i, hmm_id in enumerate(hmm_ids):
            parent_hmm_id = parent_hmm_ids[i]
            if parent_hmm_id:
                if parent_hmm_id not in subpfam_ids:
                    subpfam_ids[parent_hmm_id] = []
                subpfam_ids[parent_hmm_id].append(hmm_id)

        # fetch features in chunks
        for chunk, _ in get_chunk(bgc_ids, 100):
            hsps = {bgc_id: {} for bgc_id in chunk}
            for bgc_id, cds_id, hmm_id, bitscore in database.select(
                "hsp,cds",
                "WHERE hsp.cds_id = cds.id" +
                " AND cds.bgc_id in (" + ",".join(map(str, chunk)) + ")" +
                " AND hsp.hmm_id in (" + ",".join(map(str, hmm_ids)) + ")",
                props=["cds.bgc_id", "cds.id", "hsp.hmm_id",
                       "CAST(bitscore as INTEGER)"],
                as_tuples=True
            ):
                if cds_id not in hsps[bgc_id]:
                    hsps[bgc_id][cds_id] = {}
                if hmm_id not in hsps[bgc_id][cds_id]:
                    hsps[bgc_id][cds_id][hmm_id] = []
                hsps[bgc_id][cds_id][hmm_id].append(bitscore)

            for bgc_id in hsps:
                biosyn_present = set()  # per-bgc
                subpfam_bitscores = {}  # per-hmm
                for cds_id in hsps[bgc_id]:
                    for hmm_id in hsps[bgc_id][cds_id]:
                        bitscore = max(hsps[bgc_id][cds_id][hmm_id])
                        parent_hmm_id = parent_hmm_ids[hmm_idx[hmm_id]]
                        if not parent_hmm_id:  # biosyn
                            biosyn_present.add(hmm_id)
                        else:  # subpfam
                            if parent_hmm_id not in subpfam_bitscores:
                                subpfam_bitscores[parent_hmm_id] = {}
                            subpfam_bitscores[parent_hmm_id][
                                hmm_id] = max(
                                bitscore,
                                subpfam_bitscores[parent_hmm_id].get(hmm_id, 0)
                            )
                for hmm_id in biosyn_present:
                    bgc_features[bgc_idx[bgc_id], hmm_idx[hmm_id]] = 255
                for parent_hmm_id in subpfam_bitscores:
                    max_bitscore = max(
                        subpfam_bitscores[parent_hmm_id].values())
                    if max_bitscore > 0:
                        for hmm_id, bitscore in subpfam_bitscores[parent_hmm_id
                                                                  ].items():
                            bgc_features[bgc_idx[bgc_id], hmm_idx[hmm_id]
                                         ] = np.uint8(
                                (bitscore / max_bitscore) * 255)

        # create object
        end_time = datetime.now()
        properties = {
            "run_id": run_id,
            "start": start_time,
            "end": end_time,
            "method": method,
            "data": pd.DataFrame(
                data=bgc_features,
                index=bgc_ids,
                columns=hmm_names
            )
        }
        return Features(properties, database)
