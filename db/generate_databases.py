#!/usr/bin/env python3

"""
generate pHMM databases required by BIGSSCUIT to do its
feature extractions, and download MIBiG GBKs

"""

from os import path, makedirs, remove, rename, SEEK_END
from shutil import copy, rmtree, copyfileobj
from multiprocessing import cpu_count
from hashlib import md5
import urllib.request
import gzip
import csv
import glob
import subprocess
import tarfile
from Bio import AlignIO
from Bio.SearchIO import parse
from sys import exit


# default parameters
_PFAM_DATABASE_URL = "ftp://ftp.ebi.ac.uk/pub/" + \
    "databases/Pfam/releases/Pfam31.0/Pfam-A.hmm.gz"
_REFERENCE_PROTEINS_URL = "ftp://ftp.pir.georgetown.edu/databases/" + \
    "rps/rp-seqs-15.fasta.gz"
_MIBIG_GBKS_URL = "https://dl.secondarymetabolites.org/" + \
    "mibig/mibig_gbk_2.0.tar.gz"
_MIBIG_GBKS_COUNT = 1910


def main():
    dir_path = path.abspath(path.dirname(__file__))
    tmp_dir_path = path.join(dir_path, "tmp")

    # create temporary directory
    if not path.exists(tmp_dir_path):
        makedirs(tmp_dir_path)

    # download and unzip MIBiG dataset
    mibig_gbks_folder = path.join(dir_path, "mibig_gbks")
    if not path.exists(mibig_gbks_folder) or \
            len(glob.glob(
                path.join(mibig_gbks_folder, "BGC*.gbk"))
                ) != _MIBIG_GBKS_COUNT:
        if path.exists(mibig_gbks_folder):
            rmtree(mibig_gbks_folder)
        makedirs(mibig_gbks_folder)
        mibig_temp_file = path.join(
            tmp_dir_path, "mibig_gbk_2.0.tar.gz")
        if not path.exists(mibig_temp_file):
            print("Downloading mibig_gbk_2.0.tar.gz...")
            urllib.request.urlretrieve(
                _MIBIG_GBKS_URL, path.join(
                    tmp_dir_path, "mibig_gbk_2.0.tar.gz"))
        print("Extracting mibig_gbk_2.0.tar.gz...")
        with tarfile.open(mibig_temp_file, "r:gz") as mibig_zipped:
            mibig_zipped.extractall(path=tmp_dir_path)
            for mibig_file in glob.glob(path.join(tmp_dir_path, "*/BGC*.gbk")):
                copy(mibig_file, mibig_gbks_folder)
    else:
        print("MIBiG GBKs exist!")

    # prepare generate_hmm steps
    biosyn_pfam_tsv = path.join(dir_path, "biosynthetic_pfams", "biopfam.tsv")
    biosyn_pfam_hmm = path.join(
        dir_path, "biosynthetic_pfams", "Pfam-A.biosynthetic.hmm")
    biosyn_pfam_md5sum_path = path.splitext(biosyn_pfam_tsv)[0] + ".md5sum"
    biosyn_pfam_md5sum = md5sum(biosyn_pfam_tsv)
    sub_pfams_tsv = path.join(dir_path, "sub_pfams", "corepfam.tsv")
    sub_pfams_hmms = path.join(dir_path, "sub_pfams", "hmm")
    sub_pfams_md5sum = md5sum(sub_pfams_tsv)
    sub_pfams_md5sum_path = path.splitext(sub_pfams_tsv)[0] + ".md5sum"

    def get_pressed_hmm_filepaths(hmm_file_path):
        base_name = hmm_file_path
        return (
            base_name + ".h3i",
            base_name + ".h3f",
            base_name + ".h3m",
            base_name + ".h3p",
        )

    # create subpfam directory
    if not path.exists(sub_pfams_hmms):
        makedirs(sub_pfams_hmms)

    # check if Pfam-A.biosynthetic.hmm exists
    if not path.exists(biosyn_pfam_hmm):

        # (down)loads Pfam-A.hmm
        if not path.exists(path.join(tmp_dir_path, "Pfam-A.hmm.gz")):
            print("Downloading Pfam-A.hmm.gz...")
            urllib.request.urlretrieve(
                _PFAM_DATABASE_URL, path.join(
                    tmp_dir_path, "Pfam-A.hmm.gz"))

        # load biosynthetic pfams list
        biosynthetic_pfams = []
        with open(biosyn_pfam_tsv, "r") as biopfam_tsv:
            reader = csv.DictReader(biopfam_tsv, dialect="excel-tab")
            for row in reader:
                if row["Status"] == "included":
                    biosynthetic_pfams.append(row["Acc"])

        # apply biosynthetic pfams filtering
        with gzip.open(path.join(tmp_dir_path, "Pfam-A.hmm.gz"), "rt") as pfam:
            with open(biosyn_pfam_hmm, "w") as biopfam:
                print("Generating Pfam-A.biosynthetic.hmm...")
                temp_buffer = ""  # for saving a temporary hmm entry
                skipping = False
                for line in pfam:
                    if line.startswith("//") and len(temp_buffer) > 0:  # flush
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
                        except ValueError:
                            skipping = True

        assert len(biosynthetic_pfams) == 0

    else:
        # check md5sum
        if not path.exists(biosyn_pfam_md5sum_path):
            raise Exception(biosyn_pfam_hmm + " exists " +
                            "but no md5sum file found, " +
                            "please check or remove the old hmm file!")
        else:
            with open(biosyn_pfam_md5sum_path, "r") as f:
                old_md5sum = f.readline().rstrip()
                if old_md5sum != biosyn_pfam_md5sum:
                    raise Exception(biosyn_pfam_hmm + " exists " +
                                    "but the md5sum is not the same, " +
                                    "please check or remove the old hmm file!")
        print("Pfam-A.biosynthetic.hmm exists!")

        hmm_presses = get_pressed_hmm_filepaths(biosyn_pfam_hmm)
        hmm_pressed = True
        for hmm_press_file in hmm_presses:
            if not path.exists(hmm_press_file):
                hmm_pressed = False
                break
        if not hmm_pressed:
            print("Running hmmpress on Pfam-A.biosynthetic.hmm")
            for hmm_press_file in hmm_presses:
                if path.exists(hmm_press_file):
                    remove(hmm_press_file)
            if subprocess.call([
                "hmmpress",
                biosyn_pfam_hmm
            ]) > 0:
                raise

    # update md5sum
    with open(biosyn_pfam_md5sum_path, "w") as f:
        f.write(biosyn_pfam_md5sum)

    # ----------- sub_pfams ----------- #

    # fetch subpfams list
    sub_pfams = {}
    with open(sub_pfams_tsv, "r") as corepfam:
        corepfam.readline()  # skip header
        for line in corepfam:
            [pfam_accession, pfam_name, pfam_desc] = line.rstrip().split("\t")
            if pfam_accession in sub_pfams:
                raise Exception(
                    "Duplicated core pfam found in " + sub_pfams_tsv)
            else:
                sub_pfams[pfam_accession] = {
                    "name": pfam_name,
                    "desc": pfam_desc
                }

    # generate core pfams-only HMM
    core_hmms_path = path.join(tmp_dir_path, "core_pfams.hmm")
    with open(biosyn_pfam_hmm, "r") as full_hmm:
        with open(core_hmms_path, "w") as core_hmm:
            buf_text = ""
            cur_acc = ""
            cur_leng = 0
            have_ga = False
            for line in full_hmm:
                buf_text += line
                if line.startswith("ACC"):
                    cur_acc = line.rstrip().split(" ")[-1]
                elif line.startswith("GA"):
                    have_ga = True
                elif line.startswith("LENG"):
                    cur_leng = int(
                        line.rstrip().split(" ")[-1])
                elif line.startswith("//"):
                    if cur_acc in sub_pfams:
                        sub_pfams[cur_acc]["leng"] = cur_leng
                        if not have_ga:
                            before, after = buf_text.split("CKSUM")
                            buf_text = before + \
                                "GA    20.00 20.00;\n" + \
                                "CKSUM" + after
                        core_hmm.write(buf_text)
                    buf_text = ""
                    cur_acc = ""
                    have_ga = False
            if cur_acc in sub_pfams:
                if not have_ga:
                    before, after = buf_text.split("CKSUM")
                    buf_text = before + \
                        "GA    20.00 20.00;\n" + \
                        "CKSUM" + after
                core_hmm.write(buf_text)

    # download reference proteins dataset
    ref_prot_filename = path.basename(_REFERENCE_PROTEINS_URL)
    stored_ref_prot_filename = "subpfam_refprot.fa"
    if not path.exists(path.join(tmp_dir_path, stored_ref_prot_filename)):
        if not path.exists(path.join(tmp_dir_path, ref_prot_filename)):
            print("Downloading " + ref_prot_filename)
            urllib.request.urlretrieve(
                _REFERENCE_PROTEINS_URL, path.join(
                    tmp_dir_path, ref_prot_filename))
        file_ext = path.splitext(ref_prot_filename)[1]
        if file_ext in ["fasta", "fa"]:
            rename(
                path.join(tmp_dir_path, ref_prot_filename),
                path.join(tmp_dir_path, stored_ref_prot_filename)
            )
        elif file_ext == ".gz":
            with gzip.open(
                path.join(tmp_dir_path, ref_prot_filename), 'rb'
            ) as f_in:
                with open(
                    path.join(tmp_dir_path, stored_ref_prot_filename), 'wb'
                ) as f_out:
                    copyfileobj(f_in, f_out)
        else:
            raise Exception("Unrecognized file format! " + file_ext)

    print("Extracting subpfam reference proteins...")

    # run hmmscan to get aligned fasta files
    ref_prot_hmmtxt = path.join(
        tmp_dir_path, "subpfam_refprot_hits.txt")
    if not path.exists(ref_prot_hmmtxt):
        command = [
            "hmmsearch",
            "--acc",
            "--cut_ga",
            "--cpu", str(cpu_count()),
            "-o", ref_prot_hmmtxt,
            core_hmms_path,
            path.join(tmp_dir_path, stored_ref_prot_filename)
        ]
        ret = subprocess.run(command, check=True)
        if ret.returncode != 0:
            raise Exception("Error doing hmmsearch")
    else:
        with open(ref_prot_hmmtxt, "r") as fp:
            if next(reversed_fp_iter(fp)).rstrip() != "[ok]":
                # file is broken, remove
                raise Exception(
                    ref_prot_hmmtxt +
                    " is broken, please remove and rerun the script")

    # parse hmmtxt into alignment fastas
    for run_result in parse(ref_prot_hmmtxt, "hmmer3-text"):
        pfam_acc = run_result.accession
        model_len = sub_pfams[pfam_acc]["leng"]
        aligned_multifasta_path = path.join(
            tmp_dir_path,
            "ref-" + pfam_acc + ".aligned.fa"
        )

        with open(aligned_multifasta_path, "w") as fa:
            for hsp in run_result.hsps:
                # get hits aligned to model
                aligned_to_model = ""
                query_seq = str(hsp.query.seq)
                hit_seq = str(hsp.hit.seq)
                for i in range(hsp.query_start):
                    aligned_to_model += "-"
                for i in range(len(query_seq)):
                    if query_seq[i] != ".":
                        aligned_to_model += hit_seq[i]
                for i in range(model_len - len(aligned_to_model)):
                    aligned_to_model += "-"

                # write to fasta
                fa_acc = hsp.hit.id + "|" + \
                    str(hsp.hit_start) + "-" + str(hsp.hit_end)
                fa.write(">{}\n{}\n".format(fa_acc, aligned_to_model))

    # build subpfams
    for pfam_accession, pfam_properties in sub_pfams.items():
        subpfam_hmm_path = path.join(
            sub_pfams_hmms, "{}.subpfams.hmm".format(pfam_accession))
        if not path.exists(subpfam_hmm_path):
            print("Building {}...".format(subpfam_hmm_path))
            aligned_multifasta_path = path.join(
                tmp_dir_path,
                "ref-" + pfam_acc + ".aligned.fa"
            )
            temp_hmm_path = path.splitext(aligned_multifasta_path)[
                0] + ".subpfams.hmm"
            if not path.exists(temp_hmm_path):
                tree_path = path.splitext(aligned_multifasta_path)[
                    0] + ".newick"
                if path.exists(tree_path):
                    remove(tree_path)
                if subprocess.call([
                        "build_subpfam", "-o",
                        tmp_dir_path,
                        aligned_multifasta_path
                ]) > 0:
                    raise
            copy(temp_hmm_path, subpfam_hmm_path)
        else:
            # check hmmpress
            hmm_presses = get_pressed_hmm_filepaths(subpfam_hmm_path)
            hmm_pressed = True
            for hmm_press_file in hmm_presses:
                if not path.exists(hmm_press_file):
                    hmm_pressed = False
                    break
            if not hmm_pressed:
                print("Running hmmpress on {}".format(subpfam_hmm_path))
                for hmm_press_file in hmm_presses:
                    if path.exists(hmm_press_file):
                        remove(hmm_press_file)
                if subprocess.call([
                    "hmmpress",
                    subpfam_hmm_path
                ]) > 0:
                    raise

    # update md5sum
    print("Writing md5sums...")
    with open(sub_pfams_md5sum_path, "w") as f:
        f.write(sub_pfams_md5sum)

    # remove temp directory
    print("Removing temp directory...")
    rmtree(tmp_dir_path)

    print("done.")
    exit(0)


def fetch_alignment_file(pfam_accession, folder_path):
    file_name = path.join(
        folder_path, "{}-alignment".format(pfam_accession.split(".")[0]))
    stockholm_path = "{}.stockholm".format(file_name)
    multifasta_path = "{}.fa".format(file_name)
    # get rp15 stockholm file
    if not path.exists(stockholm_path):
        url_download = "http://pfam.xfam.org/family/{}/alignment/rp15".format(
            pfam_accession.split(".")[0])
        print("Downloading from {}...".format(url_download))
        urllib.request.urlretrieve(url_download, stockholm_path)
    else:
        # print("Found {}".format(stockholm_path))
        pass
        # print("Found {}".format(subpfam_hmm_path))
    # convert to multifasta
    if not path.exists(multifasta_path):
        AlignIO.convert(stockholm_path, "stockholm", multifasta_path, "fasta")
    return multifasta_path


def md5sum(filename):
    hash = md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(128 * hash.block_size), b""):
            hash.update(chunk)
    return hash.hexdigest()


def reversed_fp_iter(fp, buf_size=8192):
    """a generator that returns the lines of a file in reverse order
    ref: https://stackoverflow.com/a/23646049/8776239
    """
    segment = None
    offset = 0
    fp.seek(0, SEEK_END)
    file_size = remaining_size = fp.tell()
    while remaining_size > 0:
        offset = min(file_size, offset + buf_size)
        fp.seek(file_size - offset)
        buffer = fp.read(min(remaining_size, buf_size))
        remaining_size -= buf_size
        lines = buffer.splitlines(True)
        # the first line of the buffer is probably not a complete line so
        # we'll save it and append it to the last line of the next buffer
        # we read
        if segment is not None:
            # if the previous chunk starts right from the beginning of line
            # do not concat the segment to the last line of new chunk
            # instead, yield the segment first
            if buffer[-1] == '\n':
                # print 'buffer ends with newline'
                yield segment
            else:
                lines[-1] += segment
        segment = lines[0]
        for index in range(len(lines) - 1, 0, -1):
            if len(lines[index]):
                yield lines[index]
    # Don't yield None if the file was empty
    if segment is not None:
        yield segment


if __name__ == "__main__":
    main()
