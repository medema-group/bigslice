![BiG-SLiCE](https://raw.githubusercontent.com/medema-group/bigslice/master/misc/github_images/bigslice_logo.png)
----------------------
***Bi**osynthetic **G**ene clusters - **S**uper **Li**near **C**lustering **E**ngine*

Quick start
---------------------
1. Make sure you have [HMMer](http://hmmer.org/) (version 3.2b1 or later) installed.
2. Install **BiG-SLiCE** using pip:
- from PyPI (not available yet, please use the 'from source' approach)
~~~console
user@local:~$ pip install bigslice
~~~
- from source (bleeding edge)
~~~console
user@local:~$ git clone git@github.com:medema-group/bigslice.git
user@local:~$ pip install ./bigslice/
~~~
3. Fetch the latest HMM models (± 470MB gzipped):
~~~console
user@local:~$ download_bigslice_hmmdb.py
~~~
4. Check your installation:
~~~console
user@local:~$ bigslice --version .
~~~
5. Run **BiG-SLiCE** clustering analysis: (see [wiki:Input folder](https://github.com/medema-group/bigslice/wiki/Input-folder) on how to prepare the input folder)
~~~console
user@local:~$ bigslice -i <input_folder> <output_folder>
~~~

Querying [antiSMASH](https://github.com/antismash/antismash) BGCs
---------------------
Using the `--query` mode, you can perform a blazing-fast query of a putative BGC against the pre-processed set of Gene Cluster Family (GCF) models that **BiG-SLiCE** outputs (for example, you can use our [pre-processed result on ~1.2M microbial BGCs from the NCBI database](.)). You will get a ranked list of GCFs and BGCs similar to the BGC in question, which will help in determining the function and/or novelty of said BGC. To perform a GCF query, simply use:
~~~console
user@local:~$ bigslice --query <antismash_output_folder> --n_ranks <int> <output_folder>
~~~
Which will perform a query analysis on the latest clustering result contained inside the output folder (see [wiki: Program parameters](https://github.com/medema-group/bigslice/wiki/Program-parameters) for more advanced options). Top-(n_ranks) matching GCFs will be returned along with their similarity measurements. You can then view the query results using the user interactive output (see below).

User Interactive output
---------------------
**BiG-SLiCE**'s output folder contains both the processed input data (in the form of an [SQLite3](https://www.sqlite.org/index.html) database file) and some scripts that power a mini web-app to visualize that data. To run this visualization engine, follow these steps:
1. Fulfill the web-app's package requirements:
~~~console
user@local:~$ pip install -r <output_folder>/requirements.txt
~~~
2. Run the [flask](https://flask.palletsprojects.com/en/1.1.x/) server:
~~~console
user@local:~$ bash <output_folder>/start_server.sh <port(optional)>
~~~
3. Open an internet browser, then go to the URL described by the previous step:
- e.g. `* Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)`
- then go to `http://0.0.0.0:5000` in your browser

What kind of software is this, anyway?
---------------------
![bgc_gcf_illustration](https://i.ibb.co/FmBfmHW/bgc-gcf-illustration.png)

Bacteria and Fungi produce a vast array of bioactive compounds in nature, which can be useful for us as antibiotics (see [this list](https://dx.doi.org/10.1016%2Fj.mib.2009.07.002)), antivirals (see [this list](https://doi.org/10.1038/ja.2017.115)) and anticancer agents (see [Salinisporamide](https://doi.org/10.1016/j.bmc.2008.10.075)). 

![figure_1](https://i.ibb.co/0twfQ81/figure-1.png)

This software was initially developed and is currently maintained by Satria Kautsar (twitter: [@satriaphd](https://twitter.com/satriaphd)). Contributions and feedbacks are very welcomed. Feel free to drop us an e-mail if you have any question regarding or related to **BiG-SLiCE**.

Find our software useful? Please cite!
---------------------
We are yet to publish our paper and pre-print. For now, feel free to refer to this poster doi on [figshare](https://figshare.com/):
> [https://doi.org/10.6084/m9.figshare.12206747.v1](https://doi.org/10.6084/m9.figshare.12206747.v1)
