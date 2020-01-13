from mongo_backed_dict import MongoBackedDict
from ccg_nlpy.core.text_annotation import TextAnnotation
from tqdm import tqdm
import sys, os
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests

lang = 'si'
if len(sys.argv) > 1:
  lang = sys.argv[1]

input_dir = f'/pool0/webserver/incoming/experiment_tmp/EDL2019/data/input/{lang}'
# server = "/mnt/macniece"
server = "/pool0/webserver/incoming"
om_kb = f'/shared/lorelei/evaluation-20170804/LDC2017E19_LORELEI_EDL_Knowledge_Base_V1.0/kb/data/entities.tab'
om_gold = f'{server}/experiment_tmp/EDL2019/data/gold/il6_edl.tab'
om_out = f'{server}/experiment_tmp/EDL2019/data/gold/wikiname/om_edl_wiki.tab'

ti_kb = f'/shared/lorelei/evaluation-20170804/LDC2017E19_LORELEI_EDL_Knowledge_Base_V1.0/kb/data/entities.tab'
ti_gold = f'{server}/experiment_tmp/EDL2019/data/gold/il5_edl.tab'
ti_out = f'{server}/experiment_tmp/EDL2019/data/gold/wikiname/ti_edl_wiki.tab'

si_kb = f'/shared/lorelei/evaluation-2018/il10/source/kb/IL10_kb/data/entities.tab'
si_gold = f'{server}/experiment_tmp/EDL2019/data/gold/il10_edl.tab'
si_out = f'{server}/experiment_tmp/EDL2019/data/gold/wikiname/si_edl_wiki.tab'

rw_kb = f'/shared/lorelei/evaluation-2018/il9/source/kb/IL9_kb/data/entities.tab'
rw_gold = f'{server}/experiment_tmp/EDL2019/data/gold/il9_edl.tab'
rw_out = f'{server}/experiment_tmp/EDL2019/data/gold/wikiname/rw_edl_wiki.tab'

kb = {'si': si_kb, 'ti': ti_kb, 'om': om_kb, 'rw': rw_kb}
gold = {'si': si_gold, 'ti': ti_gold, 'om': om_gold, 'rw': rw_gold}
out = {'si': si_out, 'ti': ti_out, 'om': om_out, 'rw': rw_out}

kb_file = kb[lang]
gold_file = gold[lang]
out_file = out[lang]

print(f'Generating {out_file} from {kb_file} and {gold_file}')


m = MongoBackedDict(dbname='data/enwiki/idmap/enwiki-20190701.id2t.t2id')
db = open(kb_file, 'r', encoding='utf8')

gold_f = open(gold_file, 'r', encoding='utf8')
cols = gold_f.readline().strip().split('\t')
print(cols)
kb_pos = cols.index('kb_id')
mention_id_pos = cols.index('extents')
mention_text_pos = cols.index('mention_text')

columns = db.readline().strip().split('\t')
print(columns)
link_pos = columns.index('external_link')
id_pos = columns.index('entityid')
id2wiki = {}
for line in db:
  tmp = line[:-1].split('\t')
  id2wiki[tmp[id_pos]] = tmp[link_pos].split('|')

output_f = open(out_file, 'w', encoding='utf8')
output_f.write('\t'.join(cols + ['wiki_link\n']))

for line in tqdm(gold_f):
  tid = None
  wikiname = None
  entry = line[:-1].split('\t')
  mention_id = entry[mention_id_pos]
  filename,se =              mention_id.split(':')
  file = os.path.join(input_dir, filename)
  if not os.path.exists(file):
    print(file)
    continue
  docta = TextAnnotation(json_str=open(file, encoding='utf8', errors='ignore').read())
  mention_text = docta.text[int(se.split('-')[0]):int(se.split('-')[1])+1]
  # if not '_' in entry[mention_text_pos]:
  #   if not entry[mention_text_pos] == mention_text:
  #     print(entry[mention_text_pos], mention_text)
  entry[mention_text_pos] = mention_text
  assert entry[mention_text_pos] == mention_text

  if 'NIL' in entry[kb_pos]:
    wiki_link_final = "NAN"
    wikiname_pro = "NAN"
  else:
    wiki_links = set([item for kbid in entry[kb_pos].split('|') for item in id2wiki[kbid]])
    if wiki_links == {''}:
      continue
    for wiki_link in wiki_links:
      if "en.wikipedia" not in wiki_link:
        continue
      else:
        wiki_link_final = wiki_link

        en_res = requests.get(wiki_link, verify=True)
        en_soup = BeautifulSoup(en_res.text, 'html.parser')
        entity = en_soup.title.string[:-12]
        wikiname = entity.replace(' ', '_')

      # wikiname = wiki_link.split("/wiki/")[-1]
      # wikiname_pro = wikiname.replace("_", " ").lower()
  # print(wiki_link_final, wikiname_pro)
  if wikiname is not None and wikiname in m:
    # tid = [m[wikiname]]
    tid = [wikiname]

  if tid is None:
    entry[kb_pos] = "NIL"
  else:
    entry[kb_pos] = "|".join(tid)
  output_f.write('\t'.join(entry + [wiki_link_final]))
  output_f.write("\n")

output_f.close()

