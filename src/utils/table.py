import os
from mongo_backed_dict import MongoBackedDict

sorted_lang = 'ti\tom\tak\two\tzu\trw\tso\tam\tsi\tor\tilo\tbn\ttl\thi\tta\tth\tur\the\ttr\tid\thu\tvi\tzh\tfa\tsw\tar\tru\tes\tfr'.split('\t')
sorted_lang = ['ti', 'om', 'ak', 'wo', 'zu', 'rw', 'so', 'am', 'si', 'or', 'ilo', 'bn', 'tl', 'hi', 'ta', 'th', 'ur',
               'he', 'tr', 'id', 'hu', 'vi', 'zh', 'fa', 'sw', 'ar', 'ru', 'es', 'fr']
# sorted_lang = [	'ti', 'ak', 'om', 'zu', 'wo', 'rw', 'so', 'ilo', 'am', 'or', 'si', 'sw', 'tl', 'bn', 'ta', 'th', 'hi',
                   # 'ur', 'he', 'tr', 'hu', 'id', 'fa', 'ar', 'zh', 'vi', 'es', 'ru', 'fr']
lang_abv = {'ti': 'Tigrinya',
 'ak': 'Akan',
 'om': 'Oromo',
 'rw': 'Kinyarwanda',
 'zu': 'Zulu',
 'wo': 'Wolof',
 'so': 'Somali',
 'am': 'Amharic',
 'ilo': 'Ilocano',
 'or': 'Oria',
 'si': 'Sinahala',
 'tl': 'Tagalog',
 'hi': 'Hindi',
 'ta': 'Tamil',
 'bn': 'Bengali',
 'th': 'Thai',
 'id': 'Indonesian',
 'hu': 'Hungarian',
 'vi': 'Vietnamese',
 'sw': 'Swahili',
 'ar': 'Arabic',
 'fa': 'Persian',
 'ru': 'Russian',
 'es': 'Spanish',
 'zh': 'Chinese',
'fr': 'French', 'he': 'Hebrew','tr': 'Turkish', 'ur': 'Urdu'}
size_table='ti		0.0117	189	400\nak	Akan	0.2906724512	726	862\nom	Oromo	0.653203	621	1790\nrw	Kinyarwanda	0.6988	1670	1951\nzu		0.5023	1328	2116\nwo		0.6246	1231	2172\n' \
           'so		0.8707	4025	11672\nam		0.8394	8176	22790\nilo		0.871	12377	26922\nor		0.9201	12307	31846\nsi		0.9009	11314	35822\ntl	-tagalog	0.89165	64847	185680\nhi	-Hindi	0.833	74906	216363\nta		0.9103	76800	253834\nbn		0.6845	64183	299210\nth		0.9536	98088	326060\nid		0.8051	286723	828039\nhu		0.9156	331829	927299\nvi		0.9463	550111	1556601\nsw		0.9645	633168	2221193\nar		0.9512	633168	2221193\nfa		0.9534	603740	2443489\nru		0.9452	847036	3683863\nes		0.941	1005407	3705984\nzh		0.96173	602917	3822858'

hit1_ldc_table='ta	zu	ak	am	hi	id	es	ar	sw	wo	vi	th	bn	tl	hu	zh	fa	ru	om	ti	si	rw	ilo	or	so\n49.80%	19.60%	23.90%	23.30%	53.50%	59.20%	63.90%	73.30%	61.30%	16.60%	82.40%	40.00%	36.50%	61.40%	52.50%	61.40%	66.10%	53.90%	29.70%	0.00%	51.90%	35.10%	52.00%	42.60%	54.50%\n53.80%	19.80%	23.90%	24.60%	57.40%	62.20%	68.40%	75.10%	63.40%	16.60%	84.10%	48.30%	40.70%	63.20%	55.80%	66.40%	67.00%	54.10%	31.40%		52.90%	35.10%			\n19.60%	12.40%	38.00%	16.40%	40.30%	56.00%	57.80%	35.50%	62.00%	42.20%	72.10%	6.20%	7.30%	75.30%	26.30%	77.30%	46.10%	19.10%	25.60%	30.00%	72.00%	75.90%	74.20%	65.10%	45.00%\n58.20%	23.40%	54.00%	33.80%	62.90%	60.00%	56.60%	75.10%	65.40%	49.80%	81.40%	73.80%	46.90%	73.50%	48.00%	73.80%	75.30%	78.70%	43.90%	45.20%	62.70%	71.80%	74.90%	66.00%	71.80%\n' \
               '57.60%	23.80%	53.80%	30.70%	63.60%	59.10%	56.00%	75.60%	61.40%	51.80%	81.30%	73.50%	47.40%	74.10%	47.70%	73.80%	74.70%	78.60%	45.40%		64.10%		73.40%	66.70%	72.10%'
hitn_ldc_table='ta	zu	ak	am	hi	id	es	ar	sw	wo	vi	th	bn	tl	hu	zh	fa	ru	om	ti	si	rw	ilo	or	so	AVG\n57.40%	19.80%	23.90%	28.20%	63.90%	65.30%	78.10%	80.40%	69.60%	16.90%	86.90%	50.10%	46.40%	65.30%	66.40%	83.20%	76.10%	57.40%	33.20%	0.00%	54.10%	35.10%	53.20%	47.60%	55.10%	52.54%\n57.40%	19.80%	23.90%	28.20%	63.90%	65.30%	78.10%	80.40%	69.60%	16.90%	86.90%	50.10%	46.40%	65.30%	66.40%	83.20%	76.10%	57.40%	33.20%	0.00%	54.10%	35.10%	53.20%	47.60%	55.10%	52.54%\n24.40%	20.40%	60.70%	16.80%	45.80%	67.70%	69.80%	37.90%	72.20%	55.50%	76.90%	9.10%	9.90%	83.60%	32.20%	84.50%	53.40%	22.20%	26.20%	30.40%	78.20%	79.20%	79.50%	72.30%	54.30%	50.52%\n76.60%	41.10%	79.00%	38.20%	77.40%	74.60%	72.60%	87.50%	85.80%	63.50%	91.80%	79.50%	63.10%	88.30%	77.80%	88.00%	86.40%	90.40%	50.10%	46.40%	73.90%	82.60%	91.10%	78.60%	76.30%	74.42%\n77.80%	47.10%	79.00%	44.70%	79.00%	78.20%	87.90%	90.20%	90.00%	66.10%	95.00%	80.90%	65.00%	90.40%	87.20%	92.40%	89.50%	91.20%	57.20%	46.40%	76.80%	83.40%	91.70%	79.70%	77.40%	77.77%'

hit1_wiki_table='ar	fr	he	ta	th	tl	tr	ur	zh	AVG\n65.20%	62.70%	63.50%	71.50%	61.80%	68.00%	54.50%	59.50%	64.90%	63.51%\n69.20%	71.80%	68.40%	74.10%	74.20%	70.50%	56.80%	62.40%	71.20%	68.73%\n34.10%	50.30%	37.90%	16.90%	38.90%	50.50%	44.50%	43.60%	54.30%	41.22%\n66.10%	63.20%	64.60%	72.80%	68.10%	72.30%	57.10%	63.80%	67.40%	66.16%'

hitn_wiki_table='ar	fr	he	ta	th	tl	tr	ur	zh	AVG\n83.40%	81.90%	84.90%	85.80%	75.30%	80.40%	72.50%	73.50%	76.90%	79.40%\n83.40%	81.90%	84.90%	85.80%	75.30%	80.40%	72.50%	73.50%	76.90%	79.40%\n34.90%	61.20%	43.20%	20.50%	43.50%	58.80%	54.70%	51.00%	62.60%	47.82%\n85.50%	83.50%	86.80%	87.50%	82.40%	88.70%	76.50%	80.70%	80.30%	83.54%'


# table = hitn_wiki_table
#
# dict = {}
# langs = table.split('\n')[0].split('\t')
# for lang in langs:
# 	dict[lang] = []
# for line in table.split('\n')[1:]:
# 	for i, l in enumerate(line.split('\t')):
# 		dict[langs[i]].append(l)
#
# to_prt=[[], [], [], [], [], []]
# for lang in sorted_lang:
# 	if lang in langs:
# 		to_prt[0].append(lang_abv[lang])
# 		for i, p in enumerate(dict[lang]):
# 			to_prt[i+1].append(p)
# for line in to_prt:
# 	print('\t'.join(line))

ldc_dir='/pool0/webserver/incoming/experiment_tmp/EDL2019/data/gold/wikiname_per'
wiki_dir = '/pool0/webserver/incoming/experiment_tmp/EDL2019/data/gold/wikidata'
nums = 0
count = 0
dir = ldc_dir
golds = os.listdir(dir)
for lang in sorted_lang:
	for g in golds:
		if lang in g and 'train' not in g:
			count += 1
			t2id = MongoBackedDict(dbname=f"{lang}_t2id")
			# fr2entitles = MongoBackedDict(dbname=f"{lang}2entitles")
			# bilingual = 0
			# for t in t2id:
			# 	print(fr2entitles[t])
			# 	if fr2entitles[t]['entitle']!= '##name##':
			# 		bilingual += 1
			num = len([k for k in open(os.path.join(dir, g)).readlines() if k.split('\t')[4] != 'NIL'])
			nums += num
			print(f'{lang_abv[lang]}& {t2id.size()} & {num}  \ \ \midrule')
			break
print(nums / count)