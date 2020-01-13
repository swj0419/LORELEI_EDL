#for lang in zu ak am hi id es ar ru sw wo vi fa th bn tl hu zh ilo or so
for lang in ar fr he ta th tl tr ur zh #it de
do
   python hengji_ELISA.py --lang $lang
done

#for lang in ta zu ak am hi id es ar ru sw wo vi fa th bn tl hu zh om ti rw si ilo or so
for lang in ar fr he ta th tl tr ur zh #it de
do
  python /media/xingyu/DATA/Projects/EDL2019/src/utils/evaluate_candgen.py -i /media/xingyu/DATA/Projects/EDL2019/data/hengji_output/${lang}_wiki/candgen.tab -g /media/xingyu/DATA/Projects/EDL2019/data/gold/wikidata/${lang}_wikiname.tab

done