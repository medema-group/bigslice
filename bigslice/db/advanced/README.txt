HOW TO GENERATE BIG-SLICE MODELS:

# biosynthetic pfams
1. Make a directory called "biosynthetic_pfams" in this directory:
	- mkdir ./biosynthetic_pfams
2. Copy the file "./templates/biopfam.tsv" to folder created in #1:
	- cp ./templates/biopfam.tsv ./biosynthetic_pfams/
3. Edit the content of "biopfam.tsv":
	- set fourth column's values to "included" for pHMM models you want to include

# sub pfams
4. Make a directory called "sub_pfams" in this directory:
	- mkdir ./sub_pfams
5. Copy the file "./templates/corepfam.tsv" to folder created in #4:
	- cp ./templates/corepfam.tsv ./sub_pfams/
6. Edit the content of "corepfam.tsv":
	- copy the lines from #3, discarding their fourth columns to mark them as "core-pfams", thus having sub_pfams generated for

7. (optional) Adjust configuration in "./config.py"
8. Run "generate_databases.py"
	- python3 ./generate_databases.py
9. Copy model folders to the db parent folder:
	- mkdir ../models
	- cp -r ./biosynthetic_pfams ../models/
	- cp -r ./sub_pfams ../models/