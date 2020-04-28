#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Copyright (C) 2020 Satria A. Kautsar
# Wageningen University & Research
# Bioinformatics Group
"""bigsscuit.modules.clustering.membership

Assign GCF memberships
"""

from os import path
from ..data.database import Database
import pandas as pd
from sklearn.neighbors import NearestNeighbors


class Membership:
    """ defines membership values of GCF to BGC """

    def __init__(self, properties: dict, database: Database):
        self.database = database
        self.bgc_id = properties["bgc_id"]
        self.membership = properties["membership"]

    def save(self):
        """save membership data"""
        for rank, pair in enumerate(self.membership):
            gcf_id, value = pair
            self.database.insert(
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
               features_folder: str,
               centroids_folder: str,
               database: Database,
               top_hits: int=3,
               threshold: int=None
               ):
        """ assign membership """

        # check if feature data exists
        feature_ids = database.select(
            "features",
            "WHERE features.run_id = " + str(run_id),
            props=["id"]
        )
        if len(feature_ids) < 1:
            raise Exception("no features entry found for this run.")
        elif len(feature_ids) > 1:
            raise Exception(
                "more than 1 features found, run is probably corrupted.")

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

        # fetch pickled features
        feature_path = path.join(
            features_folder, "{}.pkl".format(feature_ids[0]["id"]))
        features_df = pd.read_pickle(feature_path)
        bgc_ids = features_df.index

        # fetch pickled centroids
        centroid_path = path.join(
            centroids_folder, "{}.pkl".format(clustering_ids[0]["id"]))
        centroids_df = pd.read_pickle(centroid_path)
        gcf_ids = centroids_df.index

        # prepare nearest neighbor estimator
        nn = NearestNeighbors(
            metric='euclidean',
            algorithm='brute',
            n_jobs=1)
        nn.fit(centroids_df.values)

        # perform nearest neighbor search
        if top_hits is not None and threshold is None:
            if top_hits < 1:
                raise Exception(
                    "top_hits cannot be < 1")
            dists, centroids_idx = nn.kneighbors(X=features_df.values,
                                                 n_neighbors=top_hits,
                                                 return_distance=True)
        elif threshold is not None and top_hits is None:
            if threshold < 1:
                raise Exception(
                    "threshold cannot be < 0")
            dists, centroids_idx = nn.radius_neighbors(X=features_df.values,
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
                ]}, database)
            for i, bgc_id in enumerate(bgc_ids)]
