# LORELEI_EDL 2019 
This repository includes the code of our LORELEI 2019 system, links to the data sets, and pretrained models.

## requirements
For faster processing we store the various maps (e.g. string to Wikipedia candidates, string to Lorelei KB candidates etc.) in a mongodb database collection. MongoDB stores various statistics (e.g. inlink counts for each Wikipedia page) and string-to-candidate indices that are used to compute candidates.

Make sure you preprocess Wikipedia dataset and load processed Wikipedia into Mongo.

For Cog-comp user,  To start up the Mongo DB daemon in macniece, run: 
```bash
mongod --dbpath /shared/bronte/upadhya3/tac2018/mongo_data
``` 

## Candidate Generator
The candidate generation script 
`src/link_entity.py ` takes a json serialized text annotation (containing the NER_CONLL view) and adds a CANDGEN view, which contains a dictionary from a candidate to its score.

To add candidates to a directory of JSON files containing the NER_CONLL view, run:
```
python thon_src/candgen_folder.sh <input directory> <output directory> <language code> <number of processes>
```

The various morphological forms are the following:  
1. De-suffixed form
1. De-prefixed form
3. Replaced character form

The algorithm returns `NIL` if no candidates are generated from the above processes. Returns the highest-probability candidate if there exists candidates from the above processes.


## Run the experiments all together
To run the experiments on LORELEI datasets of 22 languages, change directory to `LORELEI_EDL/src`, and use:

    langs="so es si" #so is abbreviation for Somali, es is for Spanish and si is for Sinhalese
    bash scripts/candgen_cluster.sh $langs 
    
In the script of candgen_cluster.sh: 
1. NER_INDIR refers to the folder containing NER_output JSON files
2. ROOTDIR refers to the EDL output folder
3. golddir refers to the folder containig gold EDL data
4. kbdir refers to the wikipedia data folder
5. google is switch for google query log
6. google_top refers to the number of top google results we take.
7. google_map is switch for google map
8. g_trans is switch for google transliteration
9. tsl is switch for trained transliteration model
10. wikicg is switch for ptm method
11. pivoting is switch for pivoting techniques
