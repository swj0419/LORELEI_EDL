import os, sys, csv, json, re, csv, pickle, itertools, datetime, operator, random, time, argparse
from collections import defaultdict, Counter
from multiprocessing import Pool

from tqdm import tqdm
# import matplotlib.pyplot as plt
# import numpy as np
# import nltk
# from nltk import tokenize
# from sklearn.feature_extraction.text import TfidfVectorizer
from flashtext import KeywordProcessor

# import math
# import pandas as pd
# from statsmodels.formula.api import ols
# import statsmodels.api as sm
# from sklearn.datasets import make_blobs, load_iris
# from sklearn.feature_selection import SelectKBest, SelectPercentile, GenericUnivariateSelect, chi2, mutual_info_classif, f_classif, f_regression
# from sklearn.model_selection import train_test_split
# import seaborn as sns
# import glob, logging
# from ccg_nlpy.core.text_annotation import TextAnnotation


from googlesearch import search
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
# import wikipedia
# import xml.etree.ElementTree as ET

# Filter: Geo, level, context...

# from googleapiclient.discovery import build

google_api_key = 'AIzaSyDzwz905JyFQmmpVlF6JkujslnjrId0J1M'
swj_key = 'AIzaSyCCGOwk_0HBW5uL91yno5jF-jODjcCB3Jg'
my_cse_id = "008517825388850444903:eyrvyy-n0i4"

# URL = "https://www.googleapis.com/customsearch/v1"
URL = 'https://www.googleapis.com/customsearch/v1/siterestrict?'
map_URL = f'https://www.googleapis.com/geolocation/v1/geolocate?key={google_api_key}'

import googlemaps
gmaps = googlemaps.Client(key=google_api_key)

ENTITY_KEYWORD_IN_SUMMARY = ['district', 'District', 'province', 'Province', 'City',
                             'city', 'village', 'Village', 'Country', 'country']
keyword_processor_summary = KeywordProcessor()
keyword_processor_summary.add_keywords_from_list(ENTITY_KEYWORD_IN_SUMMARY)

# ENTITY_KEYWORD_IN_FREEBASE = ['location.', 'person.', 'organization.', ',government.']#, 'people', 'asteroid'

ENTITY_KEYWORD_IN_FREEBASE = ['location.location', 'people.person', 'organization.organization', 'business.business_operation',
                              'business.consumer_company', 'location.citytown']#, 'people', 'asteroid'

# keyword_processor_freebase = KeywordProcessor(
# keyword_processor_freebase.add_keywords_from_list(ENTITY_KEYWORD_IN_FREEBASE)
# langs=['en', 'ilo']
langs = ['or']


def wiki_url2entity(url, filter='CWBD'):
    en_entity = None
    il_entity = None
    en_soup = None
    is_entity = ''
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.split('.wikipedia')[0] in langs:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        il_entity = soup.title.string[:-12]
        if domain.split('.wikipedia')[0] == 'en':
            en_res = requests.get(url, verify=True)
            en_soup = BeautifulSoup(en_res.text, 'html.parser')
            en_entity = en_soup.title.string[:-12]
        else:
            enwiki_url = None
            for li in soup.find_all('li', {'class': 'interlanguage-link interwiki-en'}):
                enwiki_url = li.find("a")['href']
                en_entity = urlparse(enwiki_url).path[6:]
                en_res = requests.get(enwiki_url, verify=True)
                en_soup = BeautifulSoup(en_res.text, 'html.parser')

            if enwiki_url is None:
                for li in soup.select('li.interlanguage-link > a'):
                    link = li.get('href')
                    if 'en.wikipedia.org' in link:
                        enwiki_url = link
                        en_entity = urlparse(enwiki_url).path[6:]
                        en_res = requests.get(enwiki_url, verify=True)
                        en_soup = BeautifulSoup(en_res.text, 'html.parser')
                        break
    elif domain == "en" + '.wikipedia.org':
        en_res = requests.get(url, verify=True)
        en_soup = BeautifulSoup(en_res.text, 'html.parser')
        en_entity = en_soup.title.string[:-12]
    if en_soup:
        if 'C' in filter:
            if 'Coordinates' in en_soup.text:
                is_entity = 'C'
        if 'W' in filter:
            if not is_entity:
                if 'Website' in en_soup.text:
                    is_entity = 'W'
        if 'BD' in filter:
            if not is_entity:
                if 'Born' in en_soup.text:
                    if 'Alma mater' in en_soup.text:
                        is_entity = 'BD'
                    else:
                        is_entity = 'B'
        if not is_entity:
            paragraphs = en_soup.select("p")
            smr = '\n'.join([para.text for para in paragraphs[0:4]])
            if len(keyword_processor_summary.extract_keywords(smr[:100])) > 0:
                is_entity = 'S'
    return (url, en_entity, il_entity, is_entity)


def query2gmap_api(text):
    geocode_result = gmaps.geocode(text)
    place_name = gmaps.places(text)['results'][0]['name']
    return place_name


def query2urls_g_api(text, num=5):
    urls = []
    if 'https:' in text or isfloat(text) or text in ['.', '(', ')', ':', '', ','] or '@' in text or '#' in text:
        return urls

    query_input = text
    PARAMS = {'key': google_api_key, 'q': query_input, 'cx': '008517825388850444903:eyrvyy-n0i4', 'num': num}
    requests.adapters.DEFAULT_RETRIES = 5
    s = requests.session()
    s.keep_alive = False
    r = requests.get(url=URL, params=PARAMS)
    return_data = r.json()

    if 'items' in return_data:
        for url in return_data['items']:
            url = url['link']
            urls.append(url)
    else:
        print(query_input, return_data)
    return tuple(urls)


def read_edl_tab(file, range=None):
    mention2id = {}
    mention2text = {}
    if file[-7:] == 'edl.tab':
        lines = open(file).readlines()[1:]
    else:
        lines = open(file)
    for line in lines:
        line = line.strip().split('\t')
        if range is None or line[3].split(':')[0] in range:
            mention2id[line[3]] = line[4]
            text = line[2].split('|')[1] if '|' in line[2] else line[2]
            mention2text[line[3]] = text
    return mention2id, mention2text


def complete_edl_gold(mention2text_gf, edl_golden_file, edl_golden_file_completed):
    f = open(edl_golden_file_completed, 'w')
    for i, line in enumerate(open(edl_golden_file)):
        if i == 0:
            f.write(line)
            continue
        line = line.strip().split('\t')
        if '_' in line[2]:
            if line[3] in mention2text_gf:
                text = mention2text_gf[line[3]]
            else: # Not single token
                text = ''
                flag1, flag2 = False, False
                start, end = line[3].split(':')[1].split('-')[0], line[3].split('-')[-1]
                start, end = int(start), int(end)
                for mention in [k for k in mention2text_gf if k.split(':')[0] == line[3].split(':')[0]]:
                    t = mention2text_gf[mention]
                    if int(mention.split(':')[1].split('-')[0]) == start:
                        text += t
                        flag1 = True
                    elif int(mention.split(':')[1].split('-')[0]) > start:
                        if int(mention.split('-')[-1]) < end:
                            text += ' ' + t
                        elif int(mention.split('-')[-1]) == end:
                            text += ' ' + t
                            flag2 = True
                            break
                if not flag1 and flag2:
                    text = line[2]
            line[2] = text
        f.write('\t'.join(line) + '\n')
    f.close()


def get_mention2text_from_cand_jsons(folder, range=None, roman=0):
    mention2text = {}
    for file_path in tqdm(os.listdir(folder)):
        file_name = os.path.splitext(file_path)[0]
        if range is None or file_name in range:
            file_path = os.path.join(folder, file_path)
            data = ''.join(open(file_path).readlines())
            data = json.loads(data)
            for tokenOffset in data["tokenOffsets"]:
                mentionid = f"{file_name}:{tokenOffset['startCharOffset']}-{tokenOffset['endCharOffset']-1}"
                mention2text[mentionid] = tokenOffset['form'].replace("\u200d", "")
            if roman:
                for view in data['views']:
                    if view['viewName'] == 'ROMANIZATION':
                        for i, cons in enumerate(view['viewData'][0]['constituents']):
                            assert cons['start'] == i
                            mention2text[list(mention2text.keys())[i] + 'r'] = cons['label']
    return mention2text


def get_mention2text_from_ltf(folder, ngram=1, range=None):
    mention2text = {}
    for file_path in tqdm(os.listdir(folder)):
        file_name = file_path.split('.')[0]
        if range is None or file_name in range:
            file_path = os.path.join(folder, file_path)
            for line in open(file_path):
                if 'TOKEN id' in line:
                    root = ET.fromstring(line)
                    start = root.get('start_char')
                    end = root.get('end_char')
                    if int(start) >= int(end):
                        continue
                    # try:
                    text = line.split('</TOKEN>')[0].split('>')[-1]
                    # except Exception as e:
                    #     print(e)
                    mentionid = f"{file_name}:{start}-{end}"
                    mention2text[mentionid] = text.replace("\u200d", "")
    return mention2text


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def check_freebase(entity, freebase):
    flag = False
    if entity in freebase:
        types = freebase[entity].split(',')
        for item in ENTITY_KEYWORD_IN_FREEBASE:
            if item in types:
                flag = True
            else:
                if item+'.' in freebase[entity]:
                    flag = True

        if 'disease' in freebase[entity]:
            flag = False
    else:
        flag = False
    return flag


if __name__ == '__main__':
    print('Start to running main...')
    parser = argparse.ArgumentParser()
    parser.add_argument('--il', type=int, default=11)
    parser.add_argument('--annotate', type=int, default=0)
    parser.add_argument('--add_to_g_search', type=int, default=1)
    parser.add_argument('--add_to_url2entity', type=int, default=1)
    parser.add_argument('--home_dir', type=str, default=f'/shared/corpora/corporaWeb/lorelei/evaluation-2019/')
    parser.add_argument('--json_input', type=str, default=f'ner/train1')

    parser.add_argument('--mention2text_gf_path', type=str, default='mention2text_train1.pkl')
    parser.add_argument('--text2url_api_path', type=str, default='text2url_g_api.pkl')
    parser.add_argument('--url2entity_path', type=str, default='url2entity_WCBDS.pkl')

    parser.add_argument('--write_cand', type=int, default=1)
    parser.add_argument('--use_freebase', type=int, default=1)
    parser.add_argument('--freebase_path', type=str, default='/shared/experiments/xyu71/lorelei2017/src/google_search/data/title2freebase.pkl')
    parser.add_argument('--add_at', type=int, default=0)
    parser.add_argument('--constrain_len', type=int, default=0)
    parser.add_argument('--print_ana', type=int, default=0)
    parser.add_argument('--add_to_ner', type=int, default=0)
    parser.add_argument('--google_output_dir', type=str, default='google_fxy/data')
    parser.add_argument('--json_output', type=str, default='ner/train1_google_high_precision_freebase')
    args = parser.parse_args()

    args.json_input = os.path.join(args.home_dir, f'il{args.il}', f'{args.json_input}')
    print(f'input folder is {args.json_input}')
    args.google_output_dir = os.path.join(args.home_dir, f'il{args.il}', args.google_output_dir)
    if not os.path.exists(args.google_output_dir):
        os.makedirs(args.google_output_dir)
    args.json_output = os.path.join(args.home_dir, f'il{args.il}', args.json_output)
    if not os.path.exists(args.json_output):
        os.makedirs(args.json_output)

    args.ltf_folder = f'{args.home_dir}/il{args.il}/source/il{args.il}/setE/data/monolingual_text/il{args.il}/ltf'
    args.mention2text_gf_path = os.path.join(args.google_output_dir, args.mention2text_gf_path)
    args.text2url_api_path = os.path.join(args.google_output_dir, args.text2url_api_path)
    args.url2entity_path = os.path.join(args.google_output_dir, args.url2entity_path)
    print(args)

    print(f'Loading {args.mention2text_gf_path}')
    if not os.path.exists(args.mention2text_gf_path):
        mention2text_gf = get_mention2text_from_cand_jsons(args.json_input, roman=0)
        # mention2text_gf = get_mention2text_from_ltf(args.ltf_folder, range=golden_files)
        pickle.dump(mention2text_gf, open(args.mention2text_gf_path, 'wb'), protocol=pickle.HIGHEST_PROTOCOL)
    else:
        mention2text_gf = pickle.load(open(args.mention2text_gf_path, 'rb'))
    print(f'Found {len(mention2text_gf)} mentions in golden files, need to search for {len(set(mention2text_gf.values()))} words.')

    print(f'Loading {args.text2url_api_path}')
    if not os.path.exists(args.text2url_api_path):
        # unique_text = set([text.replace('\u200d', '') for text in mention2text_gf.values()])
        # queries = list(unique_text.union(set([text + ' wiki' for text in unique_text])))
        # p = Pool(5)
        # queries_urls = p.map(query2urls_g_api, queries)
        # p.close()
        # text2urls_api = {}
        # for i, urls in enumerate(queries_urls):
        #     text2urls_api[queries[i]] = list(urls)

        text2urls_api = {}
        for k, text in tqdm(mention2text_gf.items()):
            if '\u200d' in text:
                print('error', k, text)
                text = text.replace('\u200d', '')
            for query in [text]:
                if not query in text2urls_api:
                    urls = query2urls_g_api(query)
                    text2urls_api[query] = list(urls)
        pickle.dump(text2urls_api, open(args.text2url_api_path, 'wb'), protocol=pickle.HIGHEST_PROTOCOL)
    else:
        text2urls_api = pickle.load(open(args.text2url_api_path, 'rb'))
        if args.add_to_g_search:
            still_need = [k for k in mention2text_gf.values() if k.replace('\u200d', '') not in text2urls_api]
            if bool(len(still_need)):
                print(f'IMPORTANT!! Adding google search results for {len(set(still_need))} new tokens...')
                for k, text in tqdm(mention2text_gf.items()):
                    text = text.replace('\u200d', '')
                    for query in [text]:
                        if not query in text2urls_api:
                            urls = query2urls_g_api(query)
                            text2urls_api[query] = list(urls)
                pickle.dump(text2urls_api, open(args.text2url_api_path, 'wb'), protocol=pickle.HIGHEST_PROTOCOL)

    print(f'Loading text2wikiurl_api')
    text2wikiurls_api = {}
    for text, urls in text2urls_api.items():
        v = []
        for url in urls:
            if 'wikipedia.org' in url:
                v.append(url)
        text2wikiurls_api[text] = v


    print(f'{len([k for k in mention2text_gf.values() if text2wikiurls_api[k]])} direct mention texts and '
          # f'{len([k for k in mention2text_gf.values() if text2wikiurls_api[k+" wiki"]])} indirect mention texts'
          f'out of {len(mention2text_gf.values())} texts found wiki contents using google api')

    if not os.path.exists(args.url2entity_path):
        urls = set([url for urll in text2wikiurls_api.values() for url in urll])
        print(f'Starting to search entities for in total {len(urls)} urls and save to {args.url2entity_path}...')
        # url_entities = []
        # for url in tqdm(urls):
        #     url_entities.append(wiki_url2entity(url))
        p = Pool(30)
        url_entities = p.map(wiki_url2entity, urls)
        p.close()
        url2entity = {}
        for (url, en_entity, il_entity, is_entity) in url_entities:
            url2entity[url] = {'en_entity': en_entity, 'il_entity': il_entity, 'is_entity': is_entity}
        pickle.dump(url2entity, open(args.url2entity_path, 'wb'), protocol=pickle.HIGHEST_PROTOCOL)
    else:
        print(f'Using url2entity {args.url2entity_path}...')
        url2entity = pickle.load(open(args.url2entity_path, 'rb'))
        if args.add_to_url2entity:
            urls = set([url for urll in text2wikiurls_api.values() for url in urll])
            still_need = [url for url in urls if url not in url2entity]
            if bool(len(still_need)):
                print(f'IMPORTANT!! Adding url2entity results for {len(set(still_need))} new urls...')
                p = Pool(20)
                url_entities = p.map(wiki_url2entity, still_need)
                p.close()
                for (url, en_entity, il_entity, is_entity) in url_entities:
                    url2entity[url] = {'en_entity': en_entity, 'il_entity': il_entity, 'is_entity': is_entity}
                pickle.dump(url2entity, open(args.url2entity_path, 'wb'), protocol=pickle.HIGHEST_PROTOCOL)


    filter = ['C', 'S', 'BD']
    inform_list = ['location.']#, 'person.', 'organization.', ',government.']
    if args.use_freebase:
        freebase = pickle.load(open(args.freebase_path, 'rb'))

    # counter = Counter(mention2text_gf.values())
    g_found_mentions_entities_single = []
    for i, k in tqdm(enumerate(list(mention2text_gf.keys()))):
        text = mention2text_gf[k]
        # if text == 'mangngegmo':
        #     print('')
        assert '\u200d' not in text
        flag = False
        if len(text) <= 2:
            continue
        for url in text2urls_api[text][:1]:# + text2wikiurls_api[text+' wiki'][:2]:
            if url in url2entity:
                title = url2entity[url]['il_entity']
                if title:
                    if not (mention2text_gf[k] in title[:len(mention2text_gf[k])+1] or mention2text_gf[k] in title[-len(mention2text_gf[k]) - 1:]):
                        continue
                enen = url2entity[url]['en_entity']
                if args.use_freebase and enen in freebase:
                    flag = check_freebase(enen, freebase)

                if url2entity[url]['is_entity'] and url2entity[url]['is_entity'] in filter:
                    flag = True

        if args.add_at:
            if '#' in text:
                flag = True

        if flag:
                if k[-1] == 'r':
                    continue
                    # g_found_mentions_entities_single.append(k[:-1])
                else:
                    g_found_mentions_entities_single.append(k)
    g_found_mentions_entities = list(set(g_found_mentions_entities_single))

    print(f' g found mentions entities has {"?"} in golden, '
          f'with total {len(g_found_mentions_entities)}, unique text being {len(set([mention2text_gf[k] for k in g_found_mentions_entities]))}')

    if args.print_ana:
        # Print
        for k in g_found_mentions_entities:
            text = mention2text_gf[k]
            print(k, text)
            for url in text2urls_api[text]:
                print('\t', url)
            print('\n')

    if args.write_cand:
        label_dict = {'C': 'coordinate', 'C_wiki': 'coordinate with wiki', 'W': 'website',
                      'W_wiki': 'website with wiki', 'P': 'person by BD', 'P_wiki': 'person by BD with wiki',
                      'MNT': 'no wiki top1'}

        # add_cand
        print(f'Writing output to {args.json_output}')
        added = []
        for file_name in os.listdir(args.json_input):
            outfile = open(os.path.join(args.json_output, file_name), 'w', encoding='utf8')
            index_file = open(os.path.join(args.json_input, file_name), 'r', encoding='utf8')
            add_mentions = [k for k in g_found_mentions_entities if
                            k.split(':')[0] == file_name]  # and k not in ner_mention2id]
            if not os.path.exists(os.path.join(args.json_input, file_name)):
                print('no file', os.path.join(args.json_input, file_name))
                continue

            ner_data = ''.join(index_file.readlines())
            ner_data = ner_data.replace("\n", "")
            ner_data = json.loads(ner_data)
            idx_list = ner_data["tokenOffsets"]
            idx_list2id = {(item["startCharOffset"], item["endCharOffset"]): i for i, item in enumerate(idx_list)}

            add_mentions = [(k, int(k.split(':')[1].split('-')[0
                                    ]), int(k.split(':')[1].split('-')[1]) + 1) for k in add_mentions]
            add_mentions = [(k, idx_list2id[(start, end)], idx_list2id[(start, end)] + 1) for (k, start, end) in
                            add_mentions if (start, end) in idx_list2id]

            ner_mentions = []
            add_mentions_filtered = []
            for (i, al, ah) in add_mentions:
                add_mentions_filtered.append((i, al, ah))
            print(len(add_mentions), len(add_mentions_filtered))
            list_pos = 0
            constituents = []
            if len(add_mentions_filtered):
                added += add_mentions_filtered
                constituents = [{"label": "G", "score": 1.0,
                                 "start": item[1], "end": item[2]}
                                for item in add_mentions_filtered]

                ner_data["views"].append({'viewName': 'GOOGLE', 'viewData': [{
                    "viewType": "edu.illinois.cs.cogcomp.core.datastructures.textannotation.View",
                    "viewName": "GOOGLE",
                    "generator": "Ltf2TextAnnotation",
                    "score": 1.0, "constituents": constituents}]})
            outstr = json.dumps(ner_data, ensure_ascii=False, indent=2)
            outfile.write(outstr)
            outfile.close()

        if args.print_ana:
            print(added)
        print(len(added))

    # edl_golden_file = '/pool0/webserver/incoming/experiment_tmp/mayhew/lorelei/evaluation-2018/il10/source/il10_unseq/setE/data/annotation/il10/il10_edl.tab'
    # if os.path.exists(edl_golden_file):
    #
    #     golden_mention2id, golden_mention2text = read_edl_tab(edl_golden_file)
    #     g_found_golden_mentions_entities = [k for k in golden_mention2id if k in g_found_mentions_entities]
    #     g_found_not_golden_mentions_entities = [g for g in g_found_mentions_entities if g not in golden_mention2id]
    #
    #     print(f' g found mentions entities has {len(g_found_golden_mentions_entities)} in golden, '
    #           f'with total {len(g_found_mentions_entities)}')




    print("end")
