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


def get_tokens(file):
    tokens = [line.strip('\n').split('\t')[1] for line in open(file)]
    return tokens


def add_view(json_input, json_output, additional_mentions, **kwargs):

    added = []
    for file_name in tqdm(os.listdir(json_input)):
        outfile = open(os.path.join(json_output, file_name), 'w', encoding='utf8')
        index_file = open(os.path.join(json_input, file_name), 'r', encoding='utf8')
        ner_data = ''.join(index_file.readlines())
        ner_data = ner_data.replace("\n", "")
        ner_data = json.loads(ner_data)

        for i, view in enumerate(ner_data['views']):
            if view['viewName'] == 'GOOGLE':
                del ner_data['views'][i]
                break

        idx_list = ner_data["tokenOffsets"]
        idx_list2id = {(item["startCharOffset"], item["endCharOffset"]): i for i, item in enumerate(idx_list)}
        s2id = {item["startCharOffset"]: i for i, item in enumerate(idx_list)}
        e2id = {item["endCharOffset"]: i for i, item in enumerate(idx_list)}

        add_mentions_span = [(k, int(k.split(':')[1].split('-')[0
                                ]), int(k.split(':')[1].split('-')[1])+1) for k in additional_mentions if k.split(':')[0] == file_name]
        add_mentions = []
        for (k, start, end) in add_mentions_span:
            start_id = s2id[start]
            end_id = e2id[end] + 1
            # if (start, end) in idx_list2id:
            #     add_mentions.append((k, idx_list2id[(start, end)], idx_list2id[(start, end)] + 1))
            # for (s, e), id in idx_list2id.items():
            #     if start == s:
            #         start_id = idx_list2id[(s, e)]
            #     if end == e:
            #         end_id = idx_list2id[(s, e)] + 1
            #         break
            add_mentions.append((k, start_id, end_id))

        add_mentions_filtered = add_mentions
        # print(len(add_mentions))

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


if __name__ == '__main__':
    print('Start to running main...')
    parser = argparse.ArgumentParser()
    parser.add_argument('--il', type=int, default=11)
    parser.add_argument('--home_dir', type=str, default=f'/shared/corpora/corporaWeb/lorelei/evaluation-2019/')
    parser.add_argument('--json_input', type=str, default=f'ner/all-ns-set1')
    parser.add_argument('--clm_result', type=str, default=f'/shared/corpora/corporaWeb/lorelei/evaluation-2019/il11/clm/all-ns-set1-clm.tab')
    parser.add_argument('--print_ana', type=int, default=0)
    parser.add_argument('--json_output', type=str, default='clm/clm_json/all-ns-set1-clm')
    args = parser.parse_args()

    args.json_input = os.path.join(args.home_dir, f'il{args.il}', f'{args.json_input}')
    print(f'input folder is {args.json_input}')
    args.json_output = os.path.join(args.home_dir, f'il{args.il}', args.json_output)
    if not os.path.exists(args.json_output):
        os.makedirs(args.json_output)

    clm_mentions = get_tokens(args.clm_result)
    add_view(additional_mentions=clm_mentions, **vars(args))
