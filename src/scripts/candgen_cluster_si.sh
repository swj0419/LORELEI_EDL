lang=si
year=20190701
pool=20
ilcode="10"
kbdir=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/outdir
golddir=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/gold/wikiname/${lang}_edl_wiki.tab
overwrite=1
google=1
google_top=5
google_map=1
g_trans=0
tsl=0
spell=0

inlink=0
mtype=0
classifier=0
bert=0
wiki_contain=0

# -------------------------------------------------------------------------------------------------------- #
NER_INDIR=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/input/${lang}

ROOTDIR=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/our_output/${lang}
TADIR=google${google}_top${google_top}_map${google_map}_gtrans${g_trans}_tsl${tsl}_spell${spell}_inlink${inlink}_mtype${mtype}_clas${classifier}_bert${bert}_wc${wiki_contain}

OUTDIR=${ROOTDIR}/${TADIR}

CANDGEN_OUTDIR=${OUTDIR}/candgen

echo "RUNNING CANDGEN"
echo ${NER_INDIR}
python link_entity.py --kbdir ${kbdir} --lang ${lang} --indir ${NER_INDIR} --outdir ${CANDGEN_OUTDIR} --pool ${pool} --year ${year} --overwrite ${overwrite} --google ${google} --google_top ${google_top} --google_map ${google_map} --g_trans ${g_trans} --tsl ${tsl} --spell ${spell} --inlink ${inlink} --mtype ${mtype} --classifier ${classifier} --bert ${bert} --wiki_contain ${wiki_contain} --ilcode ${ilcode}
cp link_entity.py ${OUTDIR}/link_entity.py

#echo "generating some stats ..."
#python compute_cand_stats.py --indir ${CANDGEN_OUTDIR}

echo "CREATING TAB FILE under ${OUTDIR}"
python utils/json2tab.py --indir ${OUTDIR}

echo "evaluate"
python utils/evaluate_candgen.py -i ${CANDGEN_OUTDIR}.tab -g ${golddir}

# chmod -R 777 ${OUTDIR}