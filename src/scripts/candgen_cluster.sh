#for lang in ta zu ak am hi id es ar ru sw wo vi fa th bn tl hu zh om ti rw si ilo or so
#for lang in ar fr he ta th tl tr ur zh #it de
#for lang in ru om ilo or #so
#for lang in ta zu ak am hi id es ar sw wo vi th bn tl hu zh fa ti si rw #so
#for lang in ta hi id es ar sw vi bn tl hu zh fa #so
for lang in $1
do
  for google_top in 1
    do
      for bert in 0
      do
      # parameter for
      year=20191020
      pool=1
      kbdir=/shared/EDL19/wiki_outdir
      overwrite=1
      google=1
    #  google_top=1
      google_map=1
      g_trans=0
      tsl=0
      spell=0

      wikidata=0
      wikicg=1
      pivoting=1

      inlink=0
      mtype=0
      classifier=0
      bert=0
      wiki_contain=0

      # -------------------------------------------------------------------------------------------------------- #
      if [ "$wikidata" -eq 0 ];then
        NER_INDIR=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/input/${lang}
        ROOTDIR=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/our_output/${lang}
        golddir=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/gold/wikiname_per/${lang}_wikiname.tab
      else
        NER_INDIR=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/input/${lang}_wiki
        ROOTDIR=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/our_output/${lang}_wiki
        golddir=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/gold/wikidata/${lang}_wikiname.tab
      fi

      TADIR=google${google}_top${google_top}_map${google_map}_gtrans${g_trans}_tsl${tsl}_spell${spell}_inlink${inlink}_mtype${mtype}_clas${classifier}_bert${bert}_wc${wiki_contain}_ptm${wikicg}_or2hin${pivoting}
      OUTDIR=${ROOTDIR}/${TADIR}

      CANDGEN_OUTDIR=${OUTDIR}/candgen

      echo "RUNNING CANDGEN"
      echo ${NER_INDIR}
      python link_entity_om.py --kbdir ${kbdir} --lang ${lang} --indir ${NER_INDIR} --outdir ${CANDGEN_OUTDIR} --pool ${pool} --year ${year} --overwrite ${overwrite} --google ${google} --google_top ${google_top} --google_map ${google_map} --g_trans ${g_trans} --tsl ${tsl} --spell ${spell} --inlink ${inlink} --mtype ${mtype} --classifier ${classifier} --bert ${bert} --wiki_contain ${wiki_contain} --wikicg ${wikicg} --pivoting ${pivoting} --wikidata ${wikidata}
      cp link_entity_om.py ${OUTDIR}/link_entity_om.py

      echo "CREATING TAB FILE under ${OUTDIR}"
      python utils/json2tab.py --indir ${OUTDIR}

      echo "evaluate"
#      golddir=/pool0/webserver/incoming/experiment_tmp/EDL2019/data/gold/wikiname/${lang}_edl_wiki.tab
      python utils/evaluate_candgen.py -i ${CANDGEN_OUTDIR}.tab -g ${golddir}

      chmod -R 777 ${OUTDIR}
   done
  done
done