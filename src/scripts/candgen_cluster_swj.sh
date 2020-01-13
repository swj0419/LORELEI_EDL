#for lang in ta zu ak am hi id es ar ru sw wo vi fa th bn tl hu zh
for lang in ru
#for lang in ta ak am hi id es ar sw wo vi th bn tl hu zh,
do
  #lang=es
  year=20191020
  pool=20
  kbdir=/shared/EDL19/wiki_outdir
  #kbdir=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/outdir
  overwrite=1
  google=0
  google_top=0
  google_map=0
  g_trans=0
  tsl=0
  spell=0

  inlink=0
  mtype=0
  bert=0
  wiki_contain=0

  # -------------------------------------------------------------------------------------------------------- #
  NER_INDIR=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/input/${lang}

  ROOTDIR=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/ptm/${lang}
  echo "CREATE DIR"
  TADIR=google${google}_top${google_top}_map${google_map}_gtrans${g_trans}_tsl${tsl}_spell${spell}_inlink${inlink}_mtype${mtype}_bert${bert}_wc${wiki_contain}

  OUTDIR=${ROOTDIR}/${TADIR}

  CANDGEN_OUTDIR=${OUTDIR}/candgen

   mkdir -p $CANDGEN_OUTDIR

  echo "RUNNING CANDGEN"
  echo ${NER_INDIR}
  python candgen_v2_one_file_rank.py --kbdir ${kbdir} --lang ${lang} --indir ${NER_INDIR} --outdir ${CANDGEN_OUTDIR} --pool ${pool} --year ${year} --overwrite ${overwrite} --google ${google} --google_top ${google_top} --google_map ${google_map} --g_trans ${g_trans} --tsl ${tsl} --spell ${spell} --inlink ${inlink} --mtype ${mtype} --bert ${bert} --wiki_contain ${wiki_contain}
  cp candgen_v2_one_file_rank.py ${OUTDIR}/link_entity_om.py

  #echo "generating some stats ..."
  #python compute_cand_stats.py --indir ${CANDGEN_OUTDIR}

  echo "CREATING TAB FILE under ${OUTDIR}"
  python utils/json2tab.py --indir ${OUTDIR}

  echo "evaluate"
  #golddir=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/gold/wikiname/${lang}_edl_wiki.tab
  golddir=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/gold/wikiname_per/${lang}_wikiname.tab
  python utils/evaluate_candgen.py -i ${CANDGEN_OUTDIR}.tab -g ${golddir}

  chmod -R 777 ${OUTDIR}

done
