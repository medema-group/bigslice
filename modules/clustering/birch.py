#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
# Copyright (C) 2020 Satria A. Kautsar
# Wageningen University & Research
# Bioinformatics Group
"""bigsscuit.modules.clustering.birch

Perform BIRCH clustering on features,
produce dataframe of centroids

todo: assign reference by datasets
"""

from os import path
from random import randint, seed
from datetime import datetime
import pickle
from ..data.database import Database
import numpy as np
import pandas as pd
from sklearn.cluster import Birch
from sklearn.metrics import pairwise_distances


class BirchClustering:
    """ handles clustering analysis of features in a run """

    def __init__(self, properties: dict, database: Database):
        self.database = database
        self.run_id = properties["run_id"]
        self.random_seed = properties["random_seed"]
        self.threshold = properties["threshold"]
        self.clustering_method = properties["method"]
        self.clustering_start = properties["start"]
        self.clustering_end = properties["end"]
        self.centroids = properties["centroids"]

    def save(self, output_folder: str):
        """commits features data"""
        existing = self.database.select(
            "clustering",
            "WHERE run_id=? AND clustering_method=?",
            parameters=(self.run_id, self.clustering_method),
            props=["id"]
        )
        if existing:
            # for now, this should not get called
            raise Exception("not_implemented")
        else:
            # save to database
            self.id = self.database.insert(
                "clustering",
                {
                    "run_id": self.run_id,
                    "clustering_method": self.clustering_method,
                    "clustering_start": self.clustering_start,
                    "clustering_end": self.clustering_end,
                    "num_centroids": self.centroids.shape[0],
                    "random_seed": self.random_seed,
                    "threshold": self.threshold
                }
            )
            # immediately commits, don't want to have double pickled file
            self.database.commit_inserts()

            # pickle data
            pickle_path = path.join(output_folder, "{}.pkl".format(self.id))
            with open(pickle_path, "wb") as pickle_file:
                pickle.dump(self.centroids, pickle_file, protocol=4)

    @staticmethod
    def run(run_id: int,
            features_folder: str,
            database: Database,
            threshold: np.float=-1,
            threshold_percentile: np.float=-1,
            random_seed: int=randint(1, 9999999)):
        """ run clustering and returns object """

        def preprocess(features: np.array):
            # todo: preprocess!
            preprocessed_features = features.astype(np.float)
            return preprocessed_features

        def fetch_threshold(df: pd.DataFrame,
                            percentile: np.float,
                            num_iter: int=100,
                            num_sample: int=1000
                            ):
            seed(random_seed)  # to make things reproducible
            if df.shape[0] < num_sample:
                num_sample = df.shape[0]
                num_iter = 1
            threshold = np.array([np.percentile(
                pairwise_distances(
                    df.sample(
                        num_sample,
                        random_state=randint(0, 999999)
                    ).values,
                    metric='euclidean',
                    n_jobs=-1
                ), percentile) for i in range(num_iter)]

            ).mean()
            return threshold

        # set properties
        properties = {
            "run_id": run_id,
            "random_seed": random_seed,
            "method": "birch"
        }

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

        # fetch pickled features
        feature_path = path.join(
            features_folder, "{}.pkl".format(feature_ids[0]["id"]))
        features_df = pd.read_pickle(feature_path)

        # initiate birch object
        birch = Birch(
            n_clusters=None,  # no global clustering
            compute_labels=False,  # only calc centroids
            copy=False  # data already copied
        )

        # start clustering
        properties["start"] = datetime.now()

        # set threshold
        if threshold >= 0:
            birch.threshold = threshold
        else:
            if threshold_percentile < 0:
                raise Exception("Threshold percentile can't be < 0.00")
            # set threshold based on sampling of features
            birch.threshold = fetch_threshold(
                features_df,
                threshold_percentile
            )
        properties["threshold"] = birch.threshold

        # set flat birch
        birch.branching_factor = features_df.shape[0]

        # call birch
        birch.fit(
            preprocess(
                features_df.values
            )
        )
        properties["end"] = datetime.now()

        # save centroids
        properties["centroids"] = np.uint8(birch.subcluster_centers_)

        return BirchClustering(properties, database)
