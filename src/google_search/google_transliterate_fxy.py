import sys
sys.path.append("/shared/experiments/xyu71/lorelei2017/src")
# print(sys.path)
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
import pickle
import os
import pymongo
from pymongo import MongoClient
from utils.mongo_backed_dict import MongoBackedDict
import time
import googlemaps
from tqdm import tqdm
from multiprocessing import Pool

fxy_key = 'AIzaSyDzwz905JyFQmmpVlF6JkujslnjrId0J1M'
swj_key = 'AIzaSyCCGOwk_0HBW5uL91yno5jF-jODjcCB3Jg'
URL = "https://www.googleapis.com/customsearch/v1/siterestrict?"
map_URL = f'https://www.googleapis.com/geolocation/v1/geolocate?key={fxy_key}'
transliterate_URL = 'https://www.google.com/inputtools/request?'
replace = False



def query2trans_g_api(text, num=1):
    if '|' in text:
        text = text.replace('|', ' ')
    trans = None
    try:
        PARAMS = {'text': text, 'ime': "transliteration_en_or", 'num': num, 'cp': 0, 'cs': 1, 'ie': "utf-8",
              'oe': "utf-8", 'app': "lazeez-sms"}
        # requests.adapters.DEFAULT_RETRIES = 5
        # s = requests.session()
        # s.keep_alive = False
        r = requests.get(url=transliterate_URL, params=PARAMS)
        trans = r.json()[1][0][1][0]
    except Exception as e:
        print(text, e)
    return trans


if __name__ == '__main__':
    file = '/shared/experiments/xyu71/lorelei2017/src/google_search/data/il11_ORG'
    queries = list(set([line.strip() for line in open(file)]))
    # for query in queries:
    #     try:
    #         t = query2trans_g_api(query)
    #     except Exception as e:
    #         print(e, query)
    #         query = query.replace('|', ' ')
    #         t = query2trans_g_api(query)
    #     print(t)

    cll_name = 'ORG2il11'
    mention2il = MongoBackedDict(dbname=cll_name)
    mention2il.drop_collection()
    for query in queries:
        try:
            if '|' in query:
                query = query.replace('|', ' ')
            t = query2trans_g_api(query)
        except Exception as e:
            print(e, query)
            continue
        mention2il.cll.insert_one({"key": t, "value": query})

    # cll_name = 'gt2il11'
    # mention2il = MongoBackedDict(dbname=cll_name)
    # ilcode = '11'
    # cll_name = f"gt_il{ilcode}"
    # gt_il11 = MongoBackedDict(dbname=cll_name)
    #
    # cursor = gt_il11.cll.find(no_cursor_timeout=True)
    # queries = [c['asciiname'] for c in cursor[167000:]]
    # cursor.close()
    # p = Pool(30)
    # results = p.map(query2trans_g_api, queries)
    # p.close()
    #
    # for i, query in tqdm(enumerate(queries)):
    #     if results[i] is not None:
    #         mention2il.cll.insert_one({"key": results[i], "value": query})
    #
    # # # ascii_names = [c['asciiname'] for c in cursor[155005:]]
    # # for gt in tqdm():
    # #     query = gt['asciiname']
    # #     try:
    # #         if '|' in query:
    # #             query = query.replace('|', ' ')
    # #         t = query2trans_g_api(query)
    # #     except Exception as e:
    # #         print(e, query)
    # #         continue
    # #     mention2il.cll.insert_one({"key": t, "value": query})
    # # cursor.close()