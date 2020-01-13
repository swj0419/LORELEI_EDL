lang=ur
year=20190701
pool=10
kbdir=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/outdir
golddir=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/gold/wikiname/${lang}_edl_wiki.tab


overwrite=1
google=0
google_top=1
google_map=0
g_trans=0
tsl=0
spell=0
wikicg=1

inlink=0
mtype=0
bert=0
wiki_contain=0

# -------------------------------------------------------------------------------------------------------- #
NER_INDIR=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/input/${lang}

ROOTDIR=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/candrank_output/${lang}
TADIR=google${google}_top${google_top}_map${google_map}_gtrans${g_trans}_tsl${tsl}_spell${spell}_inlink${inlink}_mtype${mtype}_bert${bert}_wc${wiki_contain}

OUTDIR=${ROOTDIR}/${TADIR}
if [ -d ${OUTDIR} ]; then
    rm -rf ${OUTDIR}
fi
mkdir -p ${OUTDIR}

CANDGEN_OUTDIR=${OUTDIR}/candgen

echo "RUNNING CANDGEN"
echo ${NER_INDIR}
[ -d ${CANDGEN_OUTDIR} ] && echo "Directory ${CANDGEN_OUTDIR} exists." || mkdir -p ${CANDGEN_OUTDIR}
python candgen_v2_one_file_rank.py --kbdir ${kbdir} --lang ${lang} --indir ${NER_INDIR} --outdir ${CANDGEN_OUTDIR} --pool ${pool} --year ${year} --overwrite ${overwrite} --google ${google} --google_top ${google_top} --google_map ${google_map} --g_trans ${g_trans} --tsl ${tsl} --spell ${spell} --inlink ${inlink} --mtype ${mtype} --bert ${bert} --wiki_contain ${wiki_contain} --wikicg ${wikicg}
cp candgen_v2_one_file_rank.py ${OUTDIR}/candgen_v2_one_file_rank.py

#echo "generating some stats ..."
#python compute_cand_stats.py --indir ${CANDGEN_OUTDIR}

echo "CREATING TAB FILE under ${OUTDIR}"
python utils/json2tab.py --indir ${OUTDIR}

echo "evaluate"
python utils/evaluate_candgen.py -i ${CANDGEN_OUTDIR}.tab -g ${golddir}
