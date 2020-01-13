import os, sys, csv, json, re, csv, pickle, itertools, datetime, operator, random, time, argparse
from collections import defaultdict, Counter
from multiprocessing import Pool

from tqdm import tqdm
import matplotlib.pyplot as plt
import numpy as np
import nltk
from nltk import tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from flashtext import KeywordProcessor

import math
import pandas as pd
from statsmodels.formula.api import ols
import statsmodels.api as sm
from sklearn.datasets import make_blobs, load_iris
from sklearn.feature_selection import SelectKBest, SelectPercentile, GenericUnivariateSelect, chi2, mutual_info_classif, f_classif, f_regression
from sklearn.model_selection import train_test_split
import seaborn as sns
import glob, logging
from ccg_nlpy.core.text_annotation import TextAnnotation


from googlesearch import search
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
import wikipedia

from sklearn.feature_extraction.text import CountVectorizer

# input_vectorizer = CountVectorizer(input='content')
# input_vectorizer.fit(input_documents(['data/file1.txt', 'data/file2.txt']))


google_api_key = 'AIzaSyDzwz905JyFQmmpVlF6JkujslnjrId0J1M'
swj_key = 'AIzaSyCCGOwk_0HBW5uL91yno5jF-jODjcCB3Jg'
my_cse_id = "008517825388850444903:eyrvyy-n0i4"

# URL = "https://www.googleapis.com/customsearch/v1"
URL = 'https://www.googleapis.com/customsearch/v1/siterestrict?'

ENTITY_KEYWORD_IN_SUMMARY = ['district', 'District', 'province', 'Province', 'City',
                             'city', 'village', 'Village', 'Country', 'country']
keyword_processor_summary = KeywordProcessor()
keyword_processor_summary.add_keywords_from_list(ENTITY_KEYWORD_IN_SUMMARY)

ENTITY_KEYWORD_IN_FREEBASE = ['location.', 'person.', 'organization.', ',government.', 'people']#, 'people', 'asteroid'
keyword_processor_freebase = KeywordProcessor()
keyword_processor_freebase.add_keywords_from_list(ENTITY_KEYWORD_IN_FREEBASE)
langs=['en']


def url2text(url):
    en_entity = None
    en_soup = None
    text = None
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain == "en" + '.wikipedia.org':
        en_res = requests.get(url, verify=True)
        en_soup = BeautifulSoup(en_res.text, 'html.parser')
        en_entity = en_soup.title.string[:-12]
        text = en_soup.text
    return (en_entity, text)


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


def train():
    fit = glmnet(x=X_train.copy(), y=y_train.copy().astype(float), family='binomial', alpha=1, nlambda=1000)
    glmnetPrint(fit)
    glmnetPlot(fit, xvar='lambda', label=True)
    glmnetPlot(fit, xvar='dev', label=True)
    lamda = fit['lambdau'][-1]
    coef1 = glmnetCoef(fit, s=np.float64([lamda]), exact=False)
    choose_feature = np.arange(coef1.shape[0])[coef1.reshape((coef1.shape[0])) != 0]
    assert coef1.shape[0] == datas_all.shape[1] + 1
    for feature in choose_feature:
        if feature > 0:
            c = have_cycle(patterns[feature - 1].graph, patterns[feature - 1].central)
            if c > 0:
                print(f'feature {feature - 1} has cycle of size {c}, covering graphs {patterns[feature - 1].where}')

    pvalues = coef1
    pred_train = np.round(glmnetPredict(fit, X_train, ptype='class', s=np.float64([lamda])))
    accu_train = np.sum(pred_train.reshape(pred_train.shape[0]) == y_train) / pred_train.shape[0]
    pred_test = np.round(glmnetPredict(fit, X_test, ptype='class', s=np.float64([lamda])))
    accu_test = np.sum(pred_test.reshape(pred_test.shape[0]) == y_test) / pred_test.shape[0]
    if logger:
        logger.info(f'Model train accuracy is {round(accu_train, 3)}, test accuracy is {round(accu_test, 3)}')
        logger.info(f'Model predicted test data ids {test_ids} with labels {y_test} to be {pred_test}')
    else:
        print(f'Model train accuracy is {round(accu_train, 3)}, test accuracy is {round(accu_test, 3)}')
        print(f'Model predicted test labels {y_test} to be {pred_test}')


def add_bow(sentence, word2id):
    for text in sentence:
        if text not in word2id:
            word2id[text] = len(text)



def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


if __name__ == '__main__':

    # edl_golden_file_9 = '/shared/corpora/corporaWeb/lorelei/evaluation-2018/il9/il9_edl.tab'
    # kb_9 = '/shared/corpora/corporaWeb/lorelei/evaluation-2018/il9/source/kb/IL9_kb/data/il9_entities_new.tab'
    #
    # edl_golden_file_10 = '/shared/corpora/corporaWeb/lorelei/evaluation-2018/il10/il10_edl.tab'
    # kb_10 = '/shared/corpora/corporaWeb/lorelei/evaluation-2018/il10/source/kb/IL10_kb/data/il10_entities_extended.tab'
    #
    # golden_mention2id, golden_mention2text = read_edl_tab(edl_golden_file_10)
    # ids = set(list([k for kk in golden_mention2id.values() for k in kk.split('|') if k[:3] != 'NIL']))
    # id2kb = {}
    # for line in tqdm(open(kb_10)):
    #     line = line.split('\t')
    #     if line[2] in ids:
    #         id2kb[line[2]] = line
    #         if len(id2kb) >= len(ids):
    #             break
    # print(len(id2kb), len(ids))
    # freebase = pickle.load(open('/shared/experiments/xyu71/lorelei2017/src/google_search/data/title2freebase.pkl', 'rb'))
    # types = []
    # for id, kb in id2kb.items():
    #     if kb[3] in freebase:
    #         print(freebase[kb[3]])
    #         types.append(freebase[kb[3]])
    #
    # print(types)
    # s_types = [t for type in types for t in type.split(',')]
    # print(Counter(s_types).most_common())

    kb_path = '/shared/corpora/corporaWeb/lorelei/evaluation-2019/il11/source/kb/IL11_kb/data/entities_new.tab'
    kb_pkl_path = '/shared/corpora/corporaWeb/lorelei/evaluation-2019/il11/source/kb/IL11_kb/data/entities_new.pkl'
    # if not os.path.exists(kb_pkl_path):
    #     name2kb = {}
    #     for i, line in tqdm(enumerate(open(kb_path))):
    #         if i == 0:
    #             continue
    #         line = line.split('\t')
    #         name2kb[line[3]] = line
    #     pickle.dump(name2kb, open(kb_pkl_path, 'wb'), protocol=pickle.HIGHEST_PROTOCOL)
    # else:
    #     name2kb = pickle.load(open(kb_pkl_path, 'rb'))
    keyword_processor = KeywordProcessor()
    keyword_processor.add_keywords_from_list(['Rodrigo Duterte', 'Rodrigo', 'Duterte', 'https://en.wikipedia.org/wiki/Rodrigo_Duterte'])
    for i, line in tqdm(enumerate(open(kb_path))):
        result = keyword_processor.extract_keywords(line)
        if len(result) > 0:
            print(result)
            print(line.split('\t'))

    print("end")
