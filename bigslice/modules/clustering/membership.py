#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Copyright (C) 2020 Satria A. Kautsar
# Wageningen University & Research
# Bioinformatics Group
"""bigslice.modules.clustering.membership

Assign GCF memberships
"""

from os import path
from ..data.database import Database
from ..utils import store_pickle, load_pickle
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors


class Membership:
    """ defines membership values of GCF to BGC """

    def __init__(self, properties: dict):
        self.bgc_id = properties["bgc_id"]
        self.membership = properties["membership"]

    def save(self, database: Database):
        """save membership data"""
        for rank, pair in enumerate(self.membership):
            gcf_id, value = pair
            database.insert(
                "gcf_membership",
                {
                    "bgc_id": self.bgc_id,
                    "gcf_id": gcf_id,
                    "membership_value": value,
                    "rank": rank
                }
            )

    @staticmethod
    def assign(run_id: int,
               database: Database,
               top_hits: int = 3,
               threshold: int = None,
               bgc_database: Database = None,
               cache_folder: str = None
               ):
        """ assign membership """

        if not bgc_database:
            bgc_database = database

        # check if clustering data exists
        clustering_ids = database.select(
            "clustering",
            "WHERE clustering.run_id = " + str(run_id),
            props=["id"]
        )
        if len(clustering_ids) < 1:
            raise Exception("no clustering entry found for this run.")
        elif len(clustering_ids) > 1:
            raise Exception(
                "more than 1 clustering entry found," +
                " run is probably corrupted.")

        # prepare data frames
        # columns
        hmm_ids = [row[0] for row in database.select(
            "hmm,run",
            "WHERE hmm.db_id=run.hmm_db_id" +
            " AND run.id=?",
            parameters=(run_id, ),
            props=["hmm.id"],
            as_tuples=True
        )]

        # bgc_features
        if not bgc_database:  # normal run
            bgc_ids = [row[0] for row in database.select(
                "bgc,run_bgc_status",
                "WHERE run_bgc_status.run_id=?" +
                " AND run_bgc_status.bgc_id=bgc.id",
                parameters=(run_id, ),
                props=["bgc.id"],
                as_tuples=True
            )]
            bgc_features = pd.DataFrame(
                np.zeros((len(bgc_ids), len(hmm_ids)), dtype=np.uint8),
                index=bgc_ids, columns=hmm_ids)
            # fill bgc_features
            for bgc_id, hmm_id, value in database.select(
                "bgc_features,run_bgc_status",
                "WHERE run_bgc_status.run_id=?" +
                " AND run_bgc_status.bgc_id=bgc_features.bgc_id",
                parameters=(run_id, ),
                props=["bgc_features.bgc_id",
                       "bgc_features.hmm_id", "bgc_features.value"],
                as_tuples=True
            ):
                bgc_features.at[bgc_id, hmm_id] = value
        else:  # query run
            bgc_ids = [row[0] for row in bgc_database.select(
                "bgc",
                "WHERE 1",
                props=["bgc.id"],
                as_tuples=True
            )]
            bgc_features = pd.DataFrame(
                np.zeros((len(bgc_ids), len(hmm_ids)), dtype=np.uint8),
                index=bgc_ids, columns=hmm_ids)
            # fill bgc_features
            for bgc_id, hmm_id, value in bgc_database.select(
                "bgc_features",
                "WHERE 1",
                props=["bgc_features.bgc_id",
                       "bgc_features.hmm_id", "bgc_features.value"],
                as_tuples=True
            ):
                bgc_features.at[bgc_id, hmm_id] = value

        # gcf_features
        gcf_features = None
        clustering_id = database.select(
            "clustering",
            "WHERE run_id=?",
            parameters=(run_id, ),
            props=["id"],
            as_tuples=True
        )[0][0]
        if cache_folder:
            pickled_file_path = path.join(
                cache_folder, "clustering_{}.pkl".format(clustering_id))
            gcf_features = load_pickle(pickled_file_path)
        if gcf_features is not None:
            gcf_ids = gcf_features.index.astype(int)
        else:
            gcf_ids = [row[0] for row in database.select(
                "gcf,clustering",
                "WHERE clustering.run_id=?" +
                " AND gcf.clustering_id=clustering.id",
                parameters=(run_id, ),
                props=["gcf.id"],
                as_tuples=True
            )]
            gcf_features = pd.DataFrame(
                np.zeros((len(gcf_ids), len(hmm_ids)), dtype=np.uint8),
                index=gcf_ids, columns=hmm_ids)
            # fill gcf_features
            for gcf_id, hmm_id, value in database.select(
                "gcf_models,gcf,clustering",
                "WHERE clustering.run_id=?" +
                " AND gcf.clustering_id=clustering.id" +
                " AND gcf_models.gcf_id=gcf.id",
                parameters=(run_id, ),
                props=["gcf_models.gcf_id",
                       "gcf_models.hmm_id", "gcf_models.value"],
                as_tuples=True
            ):
                gcf_features.at[gcf_id, hmm_id] = value
            if cache_folder:
                # save pickled cache for quick membership assignment
                pickled_file_path = path.join(
                    cache_folder, "clustering_{}.pkl".format(clustering_id))
                store_pickle(gcf_features, pickled_file_path)

        # prepare nearest neighbor estimator
        nn = NearestNeighbors(
            metric='euclidean',
            algorithm='brute',
            n_jobs=1)
        nn.fit(gcf_features.values)

        # perform nearest neighbor search
        if top_hits is not None and threshold is None:
            if top_hits < 1:
                raise Exception(
                    "top_hits cannot be < 1")
            dists, centroids_idx = nn.kneighbors(X=bgc_features.values,
                                                 n_neighbors=top_hits,
                                                 return_distance=True)
        elif threshold is not None and top_hits is None:
            if threshold < 1:
                raise Exception(
                    "threshold cannot be < 0")
            dists, centroids_idx = nn.radius_neighbors(X=bgc_features.values,
                                                       radius=threshold,
                                                       return_distance=True,
                                                       sort_results=True)
        else:
            raise Exception(
                "only one of top_hits or threshold can be selected")

        # return membership objects
        return [
            Membership({
                "bgc_id": bgc_id,
                "membership": [
                    (int(gcf_ids[centroids_idx[i][n]]), int(dists[i][n]))
                    for n in range(centroids_idx[i].shape[0])
                ]})
            for i, bgc_id in enumerate(bgc_ids)]
