# LORELEI_EDL 2019 
This repository includes the code of our LORELEI 2019 system, links to the data sets, and pretrained models.

## requirements
For faster processing we store the various maps (e.g. string to Wikipedia candidates, string to Lorelei KB candidates etc.) in a mongodb database collection. MongoDB stores various statistics (e.g. inlink counts for each Wikipedia page) and string-to-candidate indices that are used to compute candidates.

Make sure you preprocess Wikipedia dataset and load processed Wikipedia into Mongo.

For Cog-comp user,  To start up the Mongo DB daemon in macniece, run: 
```bash
mongod --dbpath /shared/bronte/upadhya3/tac2018/mongo_data
``` 

## Run the experiments
To run the experiments on LORELEI datasets of 22 languages, change directory to LORELEI_EDL/SRC, and use:

    langs="so es si" #so is abbreviation for Somali, es is for Spanish and si is for Sinhalese
    bash scripts/candgen_cluster.sh $langs 
    
In the script of candgen_cluster.sh: 
1. NER_INDIR refers to the folder containing NER_output JSON files
2. ROOTDIR refers to the EDL output folder
3. golddir refers to the folder containig gold EDL data