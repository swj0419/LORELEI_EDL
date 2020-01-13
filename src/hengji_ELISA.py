import argparse, copy, json, os, sys, re, requests, json
from ccg_nlpy.core.text_annotation import TextAnnotation
from ccg_nlpy.core.view import View
import logging
import operator
logging.basicConfig(level=logging.INFO)
from multiprocessing import Pool
from urllib.parse import quote

def link(query, lang):
	# query = 'Everest'
	# lang = 'vi'
	encoded = quote(query)
	# try:
	response = requests.get(f"http://blender09.cs.illinois.edu:3300/elisa_ie/entity_linking/{lang}?query={encoded}")
	if response.content == b'[]\n':
		results = []
	else:
		results = json.loads(response.content.decode('utf-8'))['results']
	# except Exception as e:
	# 	print(e)
	# 	print(query, encoded)
	return results


class CandGen:

	def __init__(self, lang=None):
		self.lang = lang

	def get_maxes_l2s_map(self, l2s_map):
		# pick max
		if len(l2s_map) == 0:
			max_cand, max_score = "NIL", 1.0
		else:
			maxes_l2s_map = {cand: score for cand, score in l2s_map.items() if score == max(l2s_map.values())}
			max_cand = list(maxes_l2s_map.keys())[0]
			max_score = l2s_map[max_cand]
		return max_cand, max_score

	def compute_hits_for_ta(self, docta, outfile, args=None):
		if not args.overwrite:
			if os.path.exists(outfile):
				logging.error("file %s exists ... skipping", outfile)
				return
		try:
			ner_view = docta.get_view("NER_CONLL")
			# rom_view = docta.get_view("ROMANIZATION")
		except:
			return
		candgen_view_json = copy.deepcopy(ner_view.as_json)
		text = docta.text
		predict_mode = True

		if "constituents" not in candgen_view_json["viewData"][0]:
			return
		for idx, cons in enumerate(candgen_view_json["viewData"][0]["constituents"]):
			query_str = cons["tokens"]
			results = link(query_str, self.lang)
			l2s_map = {}
			for item in results:
				score, wikititle = item['confidence'], item['kbid']
				l2s_map[f"{wikititle.replace('_', ' ')}|{wikititle.lower()}"] = score

			l2s_map = dict((x, y) for x, y in sorted(l2s_map.items(), key=operator.itemgetter(1), reverse=True))
			max_cand, max_score = self.get_maxes_l2s_map(l2s_map)

			if len(l2s_map) > 0:
				# do not send empty label2scoremaps!
				cons["labelScoreMap"] = l2s_map
			cons["label"] = max_cand
			cons["score"] = max_score

			logging.info(f"got {len(l2s_map)} candidates for {query_str}: {l2s_map}")

		candgen_view_json["viewName"] = "CANDGEN"
		candgen_view = View(candgen_view_json, docta.get_tokens)
		docta.view_dictionary["CANDGEN"] = candgen_view
		docta_json = docta.as_json
		with open(outfile, 'w', encoding='utf-8') as f:
			json.dump(docta_json, f, ensure_ascii=False, indent=True)

if __name__ == '__main__':
	PARSER = argparse.ArgumentParser(description='Short sample app')
	PARSER.add_argument('--nolog', action="store_true")
	PARSER.add_argument('--lang', default='ti', type=str)
	PARSER.add_argument('--pool', default=1, type=int)
	# PARSER.add_argument('--indir', default=)
	# PARSER.add_argument('--outdir', default='/pool0/webserver/incoming/experiment_tmp/EDL2019/data/hengji_output')
	PARSER.add_argument('--overwrite', default=1, type=int)

	args = PARSER.parse_args()
	# args.indir = f'/pool0/webserver/incoming/experiment_tmp/EDL2019/data/input/{args.lang}'
	# args.outdir = f'/pool0/webserver/incoming/experiment_tmp/EDL2019/data/hengji_output/{args.lang}/candgen'
	args.indir = f'/media/xingyu/DATA/Projects/EDL2019/data/input/{args.lang}_wiki'
	args.outdir = f'/media/xingyu/DATA/Projects/EDL2019/data/hengji_output/{args.lang}_wiki/candgen'
	os.makedirs(args.outdir, exist_ok=True)
	logging.info(args)

	lang = args.lang

	file_names = os.listdir(args.indir)
	cg = CandGen(lang=args.lang)


	def process_file(file):
		infile = os.path.join(args.indir, file)
		outfile = os.path.join(args.outdir, file + '.json')
		logging.info(f'Processing {infile} and output to {outfile}')
		try:
			docta = TextAnnotation(json_str=open(infile, encoding='utf8', errors='ignore').read())
		except:
			return
		docid = infile.split("/")[-1]
		logging.info("processing docid %s", docid)
		cg.compute_hits_for_ta(docta=docta, outfile=outfile, args=args)


	if args.pool > 1:
		p = Pool(args.pool)
		p.map(process_file, file_names)
		p.close()
	else:
		for file in file_names:
			process_file(file)

	# os.system(f'python /pool0/webserver/incoming/experiment_tmp/EDL2019/src/utils/json2tab.py --indir /pool0/webserver/incoming/experiment_tmp/EDL2019/data/hengji_output/{args.lang}')
	# os.system(f'python /pool0/webserver/incoming/experiment_tmp/EDL2019/src/utils/evaluate_candgen.py -i /pool0/webserver/incoming/experiment_tmp/EDL2019/data/hengji_output/{args.lang}/candgen.tab -g /pool0/webserver/incoming/experiment_tmp/EDL2019/data/gold/wikiname_per/${lang}_wikiname.tab')
	os.system(f'python /media/xingyu/DATA/Projects/EDL2019/src/utils/json2tab.py --indir /media/xingyu/DATA/Projects/EDL2019/data/hengji_output/{args.lang}_wiki')
	os.system(f'python /media/xingyu/DATA/Projects/EDL2019/src/utils/evaluate_candgen.py -i /media/xingyu/DATA/Projects/EDL2019/data/hengji_output/{args.lang}_wiki/candgen.tab -g /media/xingyu/DATA/Projects/EDL2019/data/gold/wikidata/{lang}_wikiname.tab')
