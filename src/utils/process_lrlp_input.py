import os, sys, shutil, json, re, requests
from zipfile import ZipFile
from tqdm import tqdm

from urllib.parse import quote


def build_input(langs, main_dir):
	for lang in langs:
		lang_dir = os.path.join(main_dir, lang)
		edl_gold = os.path.join(main_dir, lang, f'data/annotation/entity/{lang}_edl.tab')
		if not os.path.exists(edl_gold):
			continue
		data_tweets = os.path.join(main_dir, lang, f'data/monolingual_text/tweets')
		data_zipped = os.path.join(main_dir, lang, f'data/monolingual_text/zipped')
		output_ltf_all = os.path.join(main_dir, lang, f'data/monolingual_text/ltf_all')
		output_ltf = os.path.join(main_dir, lang, f'data/monolingual_text/ltf')
		output_input = f'/pool0/webserver/incoming/experiment_tmp/EDL2019/data/input/{langs[lang]}'
		if os.path.exists(output_ltf):
			os.system(f'rm -rf {output_ltf}')
		os.makedirs(output_ltf, exist_ok=True)
		if os.path.exists(output_ltf_all):
			os.system(f'rm -rf {output_ltf_all}')
		os.makedirs(output_ltf_all, exist_ok=True)
		if os.path.exists(output_input):
			os.system(f'rm -rf {output_input}')
		os.makedirs(output_input, exist_ok=True)
		files_needed = []
		for line in open(edl_gold).readlines()[1:]:
			files_needed.append(line.split('\t')[3].split(':')[0])
		files_needed = set(files_needed)
		print(len(files_needed))
		for file in os.listdir(data_tweets):
			if file[-8:] == '.ltf.xml' and file[:-8] in files_needed:
				shutil.copyfile(data_tweets + '/' + file, output_ltf + '/' + file)
				files_needed.remove(file[:-8])
		for file in os.listdir(data_zipped):
			if '.ltf.zip' in file:
				zipObj = ZipFile(os.path.join(data_zipped, file), 'r')
				for zipfile in zipObj.namelist():
					if zipfile[-8:] == '.ltf.xml' and zipfile[4:-8] in files_needed:
						zipObj.extract(zipfile, output_ltf_all)
						os.system(f'cp {output_ltf_all}/{zipfile} {output_ltf}/{zipfile[4:]}')
						os.system(f'rm -r {output_ltf_all}/ltf')
						files_needed.remove(zipfile[4:-8])
		if len(files_needed) != 0:
			print('error')
			print(len(files_needed), files_needed)
		os.chdir("/pool0/webserver/incoming/experiment_tmp/EDL2019/lorelei/lorelei2017")
		os.system(f'bash scripts/convert.sh ltf json {output_ltf} {output_input}')


def clean_input(need_lang=None):
	gold_dir = '/pool0/webserver/incoming/experiment_tmp/EDL2019/data/gold/wikiname_per'
	input_dir = '/pool0/webserver/incoming/experiment_tmp/EDL2019/data/input'
	for file in os.listdir(gold_dir):
		if need_lang is not None and need_lang not in file[:3]:
			continue
		gold_file = os.path.join(gold_dir, file)
		lang = file.split('_')[0]
		input_folder = os.path.join(input_dir, lang)
		files_needed = []
		for line in open(gold_file).readlines()[1:]:
			files_needed.append(line.split('\t')[3].split(':')[0])
		files_needed = set(files_needed)
		for input_file in os.listdir(input_folder):
			if input_file not in files_needed:
				print(input_file)
				os.system(f'rm {input_folder}/{input_file}')
		print(len(files_needed), len(os.listdir(input_folder)))


def add_view(need_lang=None):
	gold_dir = '/pool0/webserver/incoming/experiment_tmp/EDL2019/data/gold/wikiname_per'
	input_dir = '/pool0/webserver/incoming/experiment_tmp/EDL2019/data/input'
	for file in os.listdir(gold_dir):
		if need_lang is not None and need_lang not in file[:3]:
			continue
		gold_file = os.path.join(gold_dir, file)
		lang = file.split('_')[0]
		input_folder = os.path.join(input_dir, lang)
		extends = {}
		for line in open(gold_file).readlines()[1:]:
			extends[line.split('\t')[3]] = line.split('\t')[5]
			# filename, extend = line.split('\t')[3].split(':')
			# start, end = extend.split('-')
			# if filename not in extends:
			# 	extends[filename] = []
			# extends[filename].append((int(start), int(end)+1))


		for input_file in os.listdir(input_folder):
			missed = 0
			index_file = open(os.path.join(input_folder, input_file), 'r', encoding='utf8')
			ner_data = ''.join(index_file.readlines())
			ner_data = ner_data.replace("\n", "")
			ner_data = json.loads(ner_data)

			add_mentions = [k for k in extends if k.split(':')[0] == input_file]

			idx_list = ner_data["tokenOffsets"]
			idx_list2id = {(item["startCharOffset"], item["endCharOffset"]): i for i, item in enumerate(idx_list)}
			idx_list2ids = {item["startCharOffset"]: i for i, item in enumerate(idx_list)}
			idx_list2ide = {item["endCharOffset"]: i for i, item in enumerate(idx_list)}

			add_mentions = [(k, int(k.split(':')[1].split('-')[0]), int(k.split(':')[1].split('-')[1]) + 1) for k in add_mentions]
			add_mentions_changed = []
			for (k, start, end) in add_mentions:
				if start not in idx_list2ids or end not in idx_list2ide:
					print('token number not match', k)
					missed += 1
					continue
				add_mentions_changed.append((k, idx_list2ids[start], idx_list2ide[end] + 1))

			constituents = []
			if len(add_mentions_changed):
				constituents = [{"label": extends[item[0]], "score": 1.0, "start": item[1], "end": item[2]} for item in add_mentions_changed]

			ner_data["views"].append({'viewName': "NER_CONLL", 'viewData': [{
				"viewType": "edu.illinois.cs.cogcomp.core.datastructures.textannotation.View",
				"viewName": "NER_CONLL",
				"generator": "Ltf2TextAnnotation",
				"score": 1.0, "constituents": constituents}]})
			outstr = json.dumps(ner_data, ensure_ascii=False, indent=2)
			outfile = open(os.path.join(input_folder, input_file), 'w', encoding='utf8')
			outfile.write(outstr)
			outfile.close()
			if missed > 0:
				print(f'missed {missed}')


def clean_query(query_str):
	f = re.compile('(#|\(|\)|@|_|,|-)')
	query_str = f.sub(' ', query_str)
	query_str = re.sub('\s+', ' ', query_str).strip()
	return query_str.lower()


def filter_gold(input_dir, output_dir):
	for file in os.listdir(input_dir):
		easy_ones = []
		lang = file.split('_')[0]
		input_file = os.path.join(input_dir, file)
		output_file = os.path.join(output_dir, file)
		if os.path.exists(output_file):
			continue
		f = open(output_file, 'w')
		f.write(open(input_file).readlines()[0])
		for line in tqdm(open(input_file).readlines()[1:]):
			_, _, mention, _, entity, _, _, _, _ = line.split('\t')
			if mention in easy_ones:
				continue
			cleaned_mention = clean_query(mention)
			cleaned_entity = clean_query(entity)
			if cleaned_mention == cleaned_entity:
				easy_ones.append(mention)
			else:
				result = requests.get(f'https://{lang}.wikipedia.org/wiki/{quote(mention)}')
				if result.status_code == 200:  # the article exists
					easy_ones.append(mention)
				else:
					f.write(line)
		f.close()



if __name__ == '__main__':
	# langs = os.listdir(main_dir)
	langs = {'tam': 'ta',
	         'zul': 'zu',
	         'aka': 'ak',
	         'amh': 'am',
	         'hin': 'hi',
	         'ind': 'id',
	         'spa': 'es',
	         'ara': 'ar',
	         'rus': 'ru',
	         'swa': 'sw',
	         'wol': 'wo',
	         'vie': 'vi',
	         'fas': 'fa',
	         'tha': 'th',
	         'ben': 'bn',
	         'tgl': 'tl',
	         'hun': 'hu',
	         'cmn': 'zh'}
	         # 'uzb': 'uz',
	         # 'tur': 'tr',
	         # 'yor': 'yo',
	         # 'hau': 'ha'}
	# main_dir = '/shared/lorelei/lrlp'
	# build_input(langs, main_dir)
	# clean_input(need_lang='om')
	# add_view(need_lang='om')
	# filter_gold('/pool0/webserver/incoming/experiment_tmp/EDL2019/data/gold/wikiname_per',
	#             '/pool0/webserver/incoming/experiment_tmp/EDL2019/data/gold/wikiname_per_hard')


	# edl_gold = '/pool0/webserver/incoming/experiment_tmp/EDL2019/data/gold/il12_edl.tab'
	# ltf = '/shared/lorelei/evaluation-2019/il12/source/il12/setE/data/monolingual_text/il12/ltf'
	# output_ltf = '/shared/lorelei/evaluation-2019/il12/source/il12/setE/data/monolingual_text/il12/gold_ltf'
	# output_input = f'/pool0/webserver/incoming/experiment_tmp/EDL2019/data/input/or'

	# if os.path.exists(output_ltf):
	# 	os.system(f'rm -rf {output_ltf}')
	# os.makedirs(output_ltf, exist_ok=True)
	# if os.path.exists(output_input):
	# 	os.system(f'rm -rf {output_input}')
	# os.makedirs(output_input, exist_ok=True)
	# files_needed = []
	# for line in open(edl_gold).readlines()[1:]:
	# 	files_needed.append(line.split('\t')[3].split(':')[0])
	# files_needed = set(files_needed)
	# print(len(files_needed))
	#
	# for file in os.listdir(ltf):
	# 	if file[-8:] == '.ltf.xml' and file[:-8] in files_needed:
	# 		shutil.copyfile(ltf + '/' + file, output_ltf + '/' + file)
	# 		files_needed.remove(file[:-8])
	# if len(files_needed) != 0:
	# 	print('error')
	# 	print(len(files_needed), files_needed)
	# os.chdir("/pool0/webserver/incoming/experiment_tmp/EDL2019/lorelei/lorelei2017")
	# os.system(f'bash scripts/convert.sh ltf json {output_ltf} {output_input}')

	# clean_input(need_lang='om')
	# add_view(need_lang='or')