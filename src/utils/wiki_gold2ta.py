ENTITY_KEYWORD_IN_FREEBASE = ['location.location', 'people.person', 'organization.organization',
                              'business.business_operation',
                              'business.consumer_company', 'location.citytown']
GPE_ENTITY_KEYWORD_IN_FREEBASE = ['location.location', 'location.citytown']
PER_ENTITY_KEYWORD_IN_FREEBASE = ['people.person']
ORG_ENTITY_KEYWORD_IN_FREEBASE = ['organization.organization', 'business.business_operation',
                                  'business.consumer_company']
import json, os, sys
import pickle, re
from mongo_backed_dict import MongoBackedDict
from multiprocessing import Pool
import unicodedata


def strip_accents(text):
	ans = ''.join(c for c in unicodedata.normalize('NFKD', text) if unicodedata.category(c) != 'Mn')
	dict = {'Æ': 'AE', 'Ð': 'D', 'Ø': 'O', 'Þ': 'TH', 'ß': 'ss', 'æ': 'ae',
	        'ð': 'd', 'ø': 'o', 'þ': 'th', 'Œ': 'OE', 'œ': 'oe', 'ƒ': 'f', 'đ': 'd',
		    '–': '-', '‘': "'"}
	regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))
	ans = regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], ans)
	return ans


def check_freebase(entity, freebase):
	flag = False
	if entity in freebase:
		types = freebase[entity].split(',')
		for item in ENTITY_KEYWORD_IN_FREEBASE:
			if item in types:
				flag = item
			else:
				if item + '.' in freebase[entity]:
					flag = item
		if flag is not False:
			if flag in GPE_ENTITY_KEYWORD_IN_FREEBASE:
				flag = 'GPE'
			elif flag in PER_ENTITY_KEYWORD_IN_FREEBASE:
				flag = 'PER'
			elif flag in ORG_ENTITY_KEYWORD_IN_FREEBASE:
				flag = 'ORG'
			else:
				exit('Wrong freebase type')
	# if flag is False:
		# print("type_false")
	return flag


def find_longest_substring(string1, string2):
    answer = ""
    len1, len2 = len(string1), len(string2)
    for i in range(len1):
        match = ""
        for j in range(len2):
            if (i + j < len1 and string1[i + j] == string2[j]):
                match += string2[j]
            else:
                if (len(match) > len(answer)): answer = match
                match = ""
    return answer


def filter_string_intersection(str1, str2, threshold):
	if str1 == '' or str2 == '':
		return False
	inter = find_longest_substring(str1, str2)
	if len(inter)/len(str1) >= threshold and len(inter)/len(str2) >= threshold:
		return True
	else:
		return False


def wiki2ta(freebase, string_filter, m, filename, input_dir, output_dir, goldfile_g=None):
	gold = ''
	try:
		input_str_raw = ''.join(open(input_dir + '/' + filename + '.txt', 'r', encoding='utf8').readlines())
	except:
		print("cannot find file: ", filename)
		return
	out_filename = strip_accents(filename)

	input_str_raw = input_str_raw.replace('\n', ' ')
	input_str = re.sub(' +', ' ', input_str_raw).strip()

	tokens = []
	offsets = []
	ends = []
	prev_pos = 0

	for i, char in enumerate(input_str):
		if char == ' ':
			# if i > 0 and input_str[i-1] != ' ':
			tokens.append(input_str[prev_pos:i])
			offsets.append(prev_pos)
			ends.append(i)
			prev_pos = i+1

	if prev_pos < len(input_str):
		tokens.append(input_str[prev_pos:len(input_str)])
		offsets.append(prev_pos)
		ends.append(len(input_str))

	tokenOffsets = []
	for i in range(len(tokens)):
		tokenOffsets.append(
			{'form': tokens[i], 'startCharOffset': offsets[i], 'endCharOffset': offsets[i] + len(tokens[i])})

	token_constituents = [{"label": "", "score": 1.0, "start": i, "end": i + 1} for i in range(len(tokens))]
	token_view = {
		"viewName": "TOKENS",
		"viewData": [
			{
				"viewType": "edu.illinois.cs.cogcomp.core.datastructures.textannotation.TokenLabelView",
				"viewName": "TOKENS",
				"generator": "UserSpecified",
				"score": 1.0,
				"constituents": token_constituents
			}]
	}

	entity_dict = {}
	type_dict = {}

	wiki_constituents = []
	ner_constituents = []
	hard_attributes = []

	for line in open(input_dir + '/' + filename + '.mentions', 'r', encoding='utf8'):
		tmp = line.strip().split('\t')

		start_pos_raw = int(tmp[0])
		end_pos_raw = int(tmp[1])
		mention = input_str_raw[start_pos_raw:end_pos_raw]
		whilte_space_reduce_count1 = len(mention) - len(re.sub(' +', ' ', mention))
		mention = re.sub(' +', ' ', mention)
		# whilte_space_reduce_count1 = len(input_str_raw[:start_pos_raw-1]) - len(re.sub(' +', ' ', input_str_raw[:start_pos_raw-1]).strip())
		whilte_space_reduce_count2 = len(input_str_raw[:end_pos_raw]) - len(re.sub(' +', ' ', input_str_raw[:end_pos_raw]).strip())
		start_pos = start_pos_raw - whilte_space_reduce_count2 + whilte_space_reduce_count1
		end_pos = end_pos_raw - whilte_space_reduce_count2
		if not mention == input_str[start_pos:end_pos]:
			print('error')
			continue
		# assert mention == input_str[start_pos:end_pos]

		try:
			start_token = offsets.index(start_pos)
			end_token = ends.index(end_pos)+1
		except Exception as e:
			continue
			print(e)

		gold_entity = tmp[2]
		HARD_OR_NOT = tmp[4]
		hard_attributes.append(HARD_OR_NOT)
		# if gold_entity not in m:
		# 	print("not found: ", gold_entity)
		# 	continue
		entity_dict[gold_entity] = (tmp[0], tmp[1])
		type = check_freebase(gold_entity, freebase)
		type_dict[gold_entity] = type
		tmp_dict = {
			"label": gold_entity,
			"score": 1.0,
			"start": start_token,
			"end": end_token
		}

		ner_dict = {
			"label": type_dict[gold_entity],
			"score": 1.0,
			"start": start_token,
			"end": end_token
		}
		wiki_constituents.append(tmp_dict)
		ner_constituents.append(ner_dict)

		# to tab-
		flag = 1
		if type_filter:
			flag = flag & bool(type is not False)
		if string_filter:
			flag = flag & filter_string_intersection(gold_entity, mention, threshold=string_filter)
		if flag:
			# tid = [m[wikiname]]
			tid = gold_entity
			wikipage = 'http://en.wikipedia.org/wiki/' + gold_entity
			gold += f"{HARD_OR_NOT}\t{out_filename}\t{mention}\t{out_filename}:{start_pos}-{end_pos-1}\t{tid}\t{type_dict[gold_entity]}\tNAM\t1.0\t{wikipage}\n"
	wiki_view = {
		"viewName": "WIKIFIER",
		"viewData": [
			{
				"viewType": "edu.illinois.cs.cogcomp.core.datastructures.textannotation.View",
				"viewName": "WIKIFIER",
				"generator": "Ltf2TextAnnotation",
				"score": 1.0,
				"constituents": wiki_constituents
			}]
	}

	ner_view = {
		"viewName": "NER_CONLL",
		"viewData": [
			{
				"viewType": "edu.illinois.cs.cogcomp.core.datastructures.textannotation.View",
				"viewName": "NER_CONLL",
				"generator": "Ltf2TextAnnotation",
				"score": 1.0,
				"constituents": ner_constituents
			}]
	}

	sent_view = {
		"viewName": "SENTENCE",
		"viewData": [
			{
				"viewType": "edu.illinois.cs.cogcomp.core.datastructures.textannotation.SpanLabelView",
				"viewName": "SENTENCE",
				"generator": "UserSpecified",
				"score": 1.0,
				"constituents": [
					{
						"label": "SENTENCE",
						"score": 1.0,
						"start": 0,
						"end": 5
					}]
			}]
	}

	sentences = {
		"generator": "UserSpecified",
		"score": 1.0,
		"sentenceEndPositions": [len(tokens)]}

	# views = [ner_view, sent_view, token_view, wiki_view]
	views = [ner_view, token_view, wiki_view]

	document_json = {
		"corpusId": "",
		"id": out_filename,
		"text": input_str,
		"tokens": tokens,
		"tokenOffsets": tokenOffsets,
		"sentences": sentences,
		"views": views
	}

	try:
		with open(output_dir + '/' + out_filename, "w") as dump_f:
			json.dump(document_json, dump_f, ensure_ascii=False, indent=2)
	except Exception as e:
		print(e)
		return ''

	if not goldfile_g is None:
		goldfile_g.write(gold)
	return gold


if __name__ == '__main__':

	m = MongoBackedDict(dbname='data/enwiki/idmap/enwiki-20190701.id2t.t2id')
	freebase_path = '/pool0/webserver/incoming/experiment_tmp/EDL2019/data/title2freebase.pkl'
	freebase = pickle.load(open(freebase_path, 'rb'))
	root_dir = '/pool0/webserver/incoming/experiment_tmp/EDL2019/data/xlwikifier-wikidata/data'
	string_filter = 0
	type_filter = 0
	title = f'{f"str{string_filter}_" * bool(string_filter)}{"type_" * type_filter}{"filtered_" * bool(string_filter + type_filter)}'
	gold_dir = f'/pool0/webserver/incoming/experiment_tmp/EDL2019/data/gold/{title}wikidata/'
	error = 0
	pool = 10
	os.makedirs(gold_dir, exist_ok=True)

	# for lang in os.listdir(root_dir):
	# for lang in ['ar', 'de', 'fr', 'he', 'it', 'ta', 'th', 'tl', 'tr', 'ur', 'zh']:
	for lang in ['zh']:
		# lang = 'fr'
		ta_dir = os.path.join('/pool0/webserver/incoming/experiment_tmp/EDL2019/data/input', lang + '_wiki_train')

		input_dir = os.path.join(root_dir, lang, 'train')
		os.system(f'rm -r {ta_dir}')
		os.makedirs(ta_dir, exist_ok=True)
		gold_path = gold_dir + lang + '_wikiname_train.tab'
		print(f'Generating {gold_path} and {ta_dir} from {input_dir}')
		g = open(gold_path, 'w')
		g.write(
			'HARD_OR_NOT\tmention_id\tmention_text\textents\tkb_id\tentity_type\tmention_type\tconfidence\twiki_link\n')
		# filenames = set([f.split(".txt")[0] for f in os.listdir(input_dir)])
		filenames = []
		for f in os.listdir(input_dir):
			if f[-4:] == ".txt":
				filename = f.split(".txt")[0]
				if filename != '' and '/' not in filename:
					filenames.append(filename)
		assert len(set(filenames)) == len(filenames)
		if pool == 1:
			for filename in filenames:
				wiki2ta(freebase, string_filter, m, filename, input_dir, ta_dir, g)
			g.close()
		else:
			def process_file(file_name):
				return wiki2ta(freebase, string_filter, m, file_name, input_dir, ta_dir)
			p = Pool(pool)
			golds = p.map(process_file, filenames)
			p.close()
			g.write(''.join(golds))
			g.close()

		os.system(f'chmod -R 777 {ta_dir}')
		os.system(f'chmod 777 {gold_path}')
	# print("error files: ", error)