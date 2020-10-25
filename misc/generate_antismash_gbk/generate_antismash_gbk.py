#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
#
# Copyright (C) 2020 Satria A. Kautsar
# Wageningen University & Research
# Bioinformatics Group
#
# require: biopython >= 1.69

"""generate custom antiSMASH regiongbks"""


from Bio import SeqIO
from Bio.SeqFeature import SeqFeature, FeatureLocation
import argparse
from os import path, listdir

def main():

    parser = argparse.ArgumentParser(
        description='Generate antiSMASH5-like regiongbks')
    parser.add_argument('source_gbk', metavar='source_gbk', type=str,
                        help='the source GenBank file')
    parser.add_argument('coordinates', metavar='coordinates', type=str,
                        help='CSV file describing all region coordinates')
    parser.add_argument('destination', metavar='destination', type=str,
                        help='destination folder for all regiongbks')

    args = parser.parse_args()
    source_gbk_path = path.abspath(args.source_gbk)
    source_gbk_name = path.splitext(path.basename(source_gbk_path))[0]
    coordinates_path = path.abspath(args.coordinates)
    dest_folder_path = path.abspath(args.destination)

    # check if destination folder exists
    if not path.exists(dest_folder_path):
        print("Destination folder doesn't exists!")
        return 1
    # check if destination folder is not empty
    elif len(listdir(dest_folder_path)) > 0:
        print("Destination folder is not empty!")
        return 1

    # parse regions metadata
    print("Parsing region coordinates...")
    bgc_coordinates = {}
    with open(coordinates_path, "r") as md:
        idx = 1
        for line in md:
            if not line.startswith("#"):
                record, start, end = line.rstrip("\n").split(",")
                start = int(start)
                end = int(end)
                if record not in bgc_coordinates:
                    bgc_coordinates[record] = []
                bgc_coordinates[record].append({
                    "start": start,
                    "end": end,
                    "num": idx
                })
                idx += 1

    for gbk in SeqIO.parse(source_gbk_path, "gb"):
        if gbk.id in bgc_coordinates:
            # generate regiongbks
            for region_meta in bgc_coordinates[gbk.id]:
                region_gbk = gbk[region_meta["start"]:region_meta["end"]]

                # make antiSMASH5-like structured comment
                region_gbk.annotations["structured_comment"] = {
                    "antiSMASH-Data": {
                        "Version": "5.X",
                        "Orig. start": region_meta["start"],
                        "Orig. end": region_meta["end"],
                        "Note": (
                            "This is not a true antiSMASH5 regiongbk!!"
                            " It is meant for use in BiG-SLiCE tool "
                            "(https://github.com/medema-group/bigslice)"
                        )
                    }
                }
                new_features = []

                # make protocluster feature (only for detecting type)
                proto_feature = SeqFeature(FeatureLocation(
                    0, len(region_gbk)), type="protocluster")
                new_features.append(proto_feature)

                # make region feature
                region_feature = SeqFeature(FeatureLocation(
                    0, len(region_gbk)), type="region")
                region_feature.qualifiers["contig_edge"] = ["False"]
                region_feature.qualifiers["product"] = ["unknown"]
                region_feature.qualifiers["region_number"] = [
                    region_meta["num"]
                ]
                region_feature.qualifiers["tool"] = ["antismash"]
                new_features.append(region_feature)

                # only keep CDS and genes, which is relevant for BiG-SLiCE
                for feature in region_gbk.features:
                    if feature.type in ["CDS", "gene"]:
                        if not feature.qualifiers.get("translation", None):
                            print((
                                "CDS {} is not translated "
                                "(don't have 'translation' qualifier)!"
                                " translating with BioPython "
                                "(default transl_table=11 if not filled).."
                            ).format(
                                feature.qualifiers.get("locus_tag", "n/a")
                            ))
                            feature.qualifiers["transl_table"] = [
                                feature.qualifiers.get("transl_table", 11)]
                            feature.qualifiers["translation"] = [
                                feature.translate(region_gbk).seq]
                        new_features.append(feature)

                region_gbk.features = new_features

                # write to file
                SeqIO.write(
                    region_gbk,
                    path.join(
                        dest_folder_path,
                        "{0}.region{1:03d}.gbk".format(
                            source_gbk_name,
                            region_meta["num"]
                        )
                    ),
                    "gb"
                )


if __name__ == "__main__":
    main()
