#!/usr/bin/env python3
# vim: set fileencoding=utf-8 :
#
# Copyright (C) 2019 Satria A. Kautsar
# Wageningen University & Research
# Bioinformatics Group
"""
Download models from BiG-SLiCE's central server
"""

# python imports
import urllib.request
import tarfile
from os import path
from hashlib import md5


# static variables
_SOURCE_PATH = "http://bioinformatics.nl/~kauts001/ltr/" + \
    "bigslice/bigslice-models.2020-04-27.tar.gz"
_MD5_CHECKSUM = "faa7af2ac42b8fd458245503e4fdd1e8"


def main():

    dir_path = path.abspath(path.dirname(__file__))
    models_folder = path.join(dir_path, "models")

    if not path.exists(models_folder):
        zipped_file = "bigslice_models.tar.gz"
        if not path.exists(zipped_file):
            print("Downloading bigslice_models.tar.gz...")
            urllib.request.urlretrieve(_SOURCE_PATH, zipped_file)

        print("Checking MD5 sums...")
        md5sum_downloaded = md5sum(zipped_file)
        if _MD5_CHECKSUM != md5sum_downloaded:
            print("'{}' vs '{}': doesn't match!".format(
                _MD5_CHECKSUM, md5sum_downloaded))
            return(1)

        print("Extracting bigslice_models.tar.gz...")
        with tarfile.open(zipped_file, "r:gz") as fp:
            fp.extractall(path=dir_path)

        print("done! (please remove the downloaded tar.gz file manually)")
        return(0)

    else:
        print("models folder exists!")
        return(1)


def md5sum(filename):
    hash = md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(128 * hash.block_size), b""):
            hash.update(chunk)
    return hash.hexdigest()


if __name__ == "__main__":
    main()
