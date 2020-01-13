#!/usr/bin/env bash
ME=`basename $0` # for usage message

if [[ "$#" -ne 5 ]]; then 	# number of args
    echo "USAGE: ${ME} <vocabfile> <aligned_file> <fdev> <seed> <model_path>"
    exit
fi
vocabfile=$1
aligned_file=$2
fdev=$3
seed=$4
model=$5

time python -m seq2seq.main \
     --vocabfile ${vocabfile} \
     --aligned_file ${aligned_file} \
     --ftest ${fdev} \
     --mono \
     --beam_width 1 \
     --save ${model} \
     --seed ${seed}





if [[ $? == 0 ]]        # success
then
    :                   # do nothing
else                    # something went wrong
    echo "SOME PROBLEM OCCURED";            # echo file with problems
fi
