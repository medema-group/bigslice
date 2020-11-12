import urllib.request
import pickle
from sys import argv
from os import path, getpid, sched_getaffinity
from multiprocessing import Pool, Manager
import subprocess
import json
import argparse


def fetch_pool(num_threads: int):
    available_cpu_ids = list(sched_getaffinity(0))
    pool = Pool(processes=num_threads)
    try:
        # set cores for the multiprocessing pools
        all_cpu_ids = set()
        for i, p in enumerate(pool._pool):
            cpu_id = str(available_cpu_ids[len(available_cpu_ids) - (i % len(available_cpu_ids)) - 1])
            subprocess.run(["taskset",
                            "-p", "-c",
                            cpu_id,
                            str(p.pid)], check=True)
            all_cpu_ids.add(cpu_id)

        # set core for the main python script
        subprocess.run(["taskset",
                        "-p", "-c",
                        ",".join(all_cpu_ids),
                        str(getpid())], check=True)

    except FileNotFoundError:
        pass  # running in OSX?
    return pool

def fetch_taxonomy(results, ncbi_acc, gtdb_version):
    with urllib.request.urlopen(
        "https://gtdb.ecogenomic.org/api/v1/taxonomy/genome/" + ncbi_acc
    ) as response:
        try:
            resp = json.loads(response.read())
            if gtdb_version in resp["gtdb_taxonomy"]:
                results[ncbi_acc] = {
                    taxon: name[3:]
                    for taxon, name
                    in resp["gtdb_taxonomy"][gtdb_version].items()
                }
                print("Fetched: " + ncbi_acc)
            else:
                print("No entry: " + ncbi_acc)
        except Exception:
            print("Error: " + ncbi_acc)


def main():

    parser = argparse.ArgumentParser(
        description='Query taxonomy information from GTDB-API')
    parser.add_argument('ncbi_acc_list', metavar='ncbi_acc_path', type=str,
                        help=('text file with all NCBI GenBank/RefSeq'
                              ' accessions to query for'))
    parser.add_argument('output_file', metavar='output_file_path', type=str,
                        help=('output tsv file path'))
    parser.add_argument('-t', dest='threads', type=int, default=1,
                        help='number of threads to use (default: %(default)s)')
    parser.add_argument('--gtdb', dest='gtdb_version', type=str, default="R95",
                        help='number of threads to use (default: %(default)s)')
    args = parser.parse_args()

    ncbi_acc_path = path.abspath(args.ncbi_acc_list)
    output_file_path = path.abspath(args.output_file)
    threads = args.threads
    gtdb_version = args.gtdb_version

    # checks
    if path.exists(output_file_path):
        print("Output file path exists!")
        return

    # setup shared resources & pool
    manager = Manager()
    results = manager.dict()
    pool = fetch_pool(threads)

    with open(ncbi_acc_path, "r") as fp:
        for line in fp:
            if line.startswith("GCA_") or line.startswith("GCF_"):
                ncbi_acc = line.rstrip()
                results[ncbi_acc] = None

    print("Querying GTDB-API...")
    for ncbi_acc in results:
        pool.apply_async(
            fetch_taxonomy, args=(
                results,
                ncbi_acc,
                gtdb_version
            )
        )
    pool.close()
    pool.join()

    print("saving output...")
    with open(output_file_path, "w") as of:
        of.write(
            "\t".join([
                "#Genome folder",
                "Kingdom",
                "Phylum",
                "Class",
                "Order",
                "Family",
                "Genus",
                "Species",
                "Organism"
            ])
        )
        of.write("\n")
        for ncbi_acc, taxa in results.items():
            of.write("\t".join([
                ncbi_acc + "/",
                taxa["domain"],
                taxa["phylum"],
                taxa["class"],
                taxa["order"],
                taxa["family"],
                taxa["genus"],
                taxa["species"],
                ""
            ]))
            of.write("\n")


if __name__ == "__main__":
    main()
