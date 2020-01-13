lang=tl
year=20190701
pool=15
kbdir=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/outdir

overwrite=1
google=1
google_top=1
google_map=1
g_trans=0
tsl=0
spell=0

inlink=0
mtype=0
classifier=0
bert=1
wiki_contain=0

# -------------------------------------------------------------------------------------------------------- #
NER_INDIR=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/input/${lang}

ROOTDIR=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/our_output/${lang}
TADIR=google${google}_top${google_top}_map${google_map}_gtrans${g_trans}_tsl${tsl}_spell${spell}_inlink${inlink}_mtype${mtype}_clas${classifier}_bert${bert}_wc${wiki_contain}

OUTDIR=${ROOTDIR}/${TADIR}
if [ -d ${OUTDIR} ]; then
    rm -rf ${OUTDIR}
fi
mkdir -p ${OUTDIR}

CANDGEN_OUTDIR=${OUTDIR}/candgen

echo "RUNNING CANDGEN"
echo ${NER_INDIR}
[ -d ${CANDGEN_OUTDIR} ] && echo "Directory ${CANDGEN_OUTDIR} exists." || mkdir -p ${CANDGEN_OUTDIR}
python candgen_v2_one_file.py --kbdir ${kbdir} --lang ${lang} --indir ${NER_INDIR} --outdir ${CANDGEN_OUTDIR}
--pool ${pool} --year ${year} --overwrite ${overwrite} --google ${google} --google_top ${google_top}
--google_map ${google_map} --g_trans ${g_trans} --tsl ${tsl} --spell ${spell} --inlink ${inlink} --mtype ${mtype}
--classifier ${classifier} --bert ${bert} --wiki_contain ${wiki_contain}
cp candgen_v2_one_file.py ${OUTDIR}/candgen_v2_one_file.py

echo "generating some stats ..."
python compute_cand_stats.py --indir ${CANDGEN_OUTDIR}

echo "CREATING TAB FILE under ${OUTDIR}"
python utils/json2tab.py --indir ${OUTDIR}

#echo "evaluate"
#python /shared/experiments/xyu71/lorelei2017/src/google_search/analyze/evaluate_2019.py --input_dir ${ROOTDIR} --edl_result ${TADIR} --il ${ILCODE}

