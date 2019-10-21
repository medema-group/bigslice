#!/usr/bin/env python3

"""
generate pHMM databases required by BIGSSCAPE to do its
feature extractions

"""

from os import path, makedirs, remove
import urllib.request
import gzip
import csv
import subprocess
from Bio import AlignIO


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
		
	else:
		print("Pfam-A.biosynthetic.hmm exists!")
	
	# build subpfams
	with open(path.join(dir_path, "sub_pfams", "corepfam.tsv"), "r") as corepfam:
		corepfam.readline()
		for line in corepfam:
			[pfam_accession, pfam_name, pfam_desc] = line.rstrip().split("\t")
			subpfam_hmm_path = path.join(dir_path, "sub_pfams", "{}.subpfam.hmm".format(pfam_accession))
			if not path.exists(subpfam_hmm_path):
				aligned_multifasta_path = fetch_alignment_file(pfam_accession, tmp_dir_path)
				tree_path = path.splitext(aligned_multifasta_path)[0] + ".newick"
				if path.exists(tree_path):
					remove(tree_path)
				if subprocess.call(["build_subpfam", "-o", tmp_dir_path, aligned_multifasta_path]) > 0:
					raise
			else:
				print("Found {}".format(subpfam_hmm_path))


def fetch_alignment_file(pfam_accession, folder_path):
	file_name = path.join(folder_path, "{}-alignment".format(pfam_accession.split(".")[0]))
	stockholm_path = "{}.stockholm".format(file_name)
	multifasta_path = "{}.fa".format(file_name)
	# get rp15 stockholm file
	if not path.exists(stockholm_path):
		url_download = "http://pfam.xfam.org/family/{}/alignment/rp15".format(pfam_accession.split(".")[0])
		print("Downloading from {}...".format(url_download))
		urllib.request.urlretrieve(url_download, stockholm_path)
	else:
		print("Found {}".format(stockholm_path))
	# convert to multifasta
	if not path.exists(multifasta_path):
		AlignIO.convert(stockholm_path, "stockholm", multifasta_path, "fasta")
	return multifasta_path


if __name__ == "__main__":
    main()