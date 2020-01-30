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
from typing import List
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
                    "random_seed": self.random_seed
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
            reference_bgc_ids: List[int]=[],
            random_seed: int=randint(1, 9999999)):
        """ run clustering and returns object """

        def preprocess(features: np.array):
            # todo: preprocess!
            preprocessed_features = features.astype(np.float)
            return preprocessed_features

        def fetch_threshold(df: pd.DataFrame,
                            percentile: int=1,
                            iter: int=100,
                            num_sample: int=1000
                            ):
            seed(random_seed)  # to make things reproducible
            threshold = np.array([np.percentile(
                pairwise_distances(
                    df.sample(
                        min(num_sample, int(0.1 * df.shape[0])),
                        random_state=randint(0, 999999)
                    ).values,
                    metric='euclidean',
                    n_jobs=-1
                ), percentile) for i in range(iter)]

            ).mean()
            return threshold

        # set properties
        properties = {
            "run_id": run_id,
            "random_seed": random_seed,
            "method": "birch"
        }

        # set if using reference/not
        reference_bgc_ids = np.array(reference_bgc_ids)
        use_reference = reference_bgc_ids.shape[0] > 0

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

        # run birch
        properties["start"] = datetime.now()
        if use_reference:
            # check if all reference features are in dataset
            ref_not_in_features = np.setdiff1d(
                reference_bgc_ids, features_df.index)
            if len(ref_not_in_features) > 0:
                raise Exception(
                    str(len(ref_not_in_features)) +
                    " out of " +
                    str(features_df.shape[0]) +
                    " reference BGCs are not in the features matrix"
                )
            # seed birch with reference features
            birch.threshold = 0
            birch.branching_factor = len(reference_bgc_ids)
            birch.fit(
                preprocess(
                    features_df.loc[reference_bgc_ids].values
                )
            )
            samples_df = features_df.loc[~features_df.index.isin(
                reference_bgc_ids)]
            if samples_df.shape[0] > 0:
                # set threshold based on references
                birch.threshold = fetch_threshold(
                    features_df.loc[reference_bgc_ids])
                # set flat birch
                birch.branching_factor = features_df.shape[0]
                # fitted features = non-reference features
                birch.partial_fit(
                    preprocess(
                        samples_df.values
                    )
                )
        else:
            # set threshold based on sampling of features
            birch.threshold = birch.threshold = fetch_threshold(
                features_df)
            # set flat birch
            birch.branching_factor = features_df.shape[0]
            # fitted features = all
            birch.fit(
                preprocess(
                    features_df.values
                )
            )
            pass
        properties["end"] = datetime.now()

        # save centroids
        properties["centroids"] = np.uint8(birch.subcluster_centers_)

        return BirchClustering(properties, database)
