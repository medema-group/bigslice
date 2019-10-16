#!/usr/bin/env python3

"""
generate pHMM databases required by BIGSSCAPE to do its
feature extractions

"""

from os import path, makedirs
import urllib.request
import gzip
import csv


# default parameters
_PFAM_DATABASE_URL = "ftp://ftp.ebi.ac.uk/pub/databases/Pfam/releases/Pfam31.0/Pfam-A.hmm.gz"


def main():
	dir_path = path.abspath(path.dirname(__file__))
	tmp_dir_path = path.join(dir_path, "tmp")

	# create temporary directory
	if not path.exists(tmp_dir_path):
	    makedirs(tmp_dir_path)

	# check if Pfam-A.biosynthetic.hmm exists
	if not path.exists(path.join(dir_path, "Pfam-A.biosynthetic.hmm")):

		# (down)loads Pfam-A.hmm
		if not path.exists(path.join(tmp_dir_path, "Pfam-A.hmm.gz")):
			print("Downloading Pfam-A.hmm.gz...")
			urllib.request.urlretrieve(_PFAM_DATABASE_URL, path.join(tmp_dir_path, "Pfam-A.hmm.gz"))

		# load biosynthetic pfams list
		biosynthetic_pfams = []
		with open(path.join(dir_path, "biosynthetic_pfams", "biopfam.tsv"), "r") as biopfam_tsv:
			reader = csv.DictReader(biopfam_tsv, dialect="excel-tab")
			for row in reader:
				if row["Status"] == "included":
					biosynthetic_pfams.append(row["Acc"])


		# apply biosynthetic pfams filtering
		with gzip.open(path.join(tmp_dir_path, "Pfam-A.hmm.gz"), "rt") as pfam:
			with open(path.join(dir_path, "Pfam-A.biosynthetic.hmm"), "w") as biopfam:
				print("Generating Pfam-A.biosynthetic.hmm...")
				temp_buffer = "" # for saving a temporary hmm entry
				skipping = False
				for line in pfam:
					if line.startswith("//") and len(temp_buffer) > 0: # flush
						if not skipping:
							biopfam.write(temp_buffer)
						temp_buffer = ""
						skipping = False
					if skipping:
						continue
					temp_buffer += line
					if line.startswith("ACC "):
						pfam_acc = line.split(" ")[-1].rstrip()
						try:
							biosynthetic_pfams.remove(pfam_acc)
						except:
							skipping = True

		assert len(biosynthetic_pfams) == 0
		

if __name__ == "__main__":
    main()