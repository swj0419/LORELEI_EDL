import sys
sys.path.append("/pool0/webserver/incoming/experiment_tmp/EDL2019/src")
# print(sys.path)
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
import pickle
import os
from utils.mongo_backed_dict import MongoBackedDict
import time
import googlemaps


fxy_key = 'AIzaSyDzwz905JyFQmmpVlF6JkujslnjrId0J1M'
swj_key = 'AIzaSyCCGOwk_0HBW5uL91yno5jF-jODjcCB3Jg'
zza_key = 'AIzaSyDYCBPe-i5mQpxCpUzPWxKe1eDfcf-OfvE'
yxd_key = 'AIzaSyDsxlWUasFONP3XoplgT8_J25IP1cvwJ1M'
stephen_key = 'AIzaSyBOAvIEaI25ILPs0NvqjyARErxCq8gzqL0'
URL = "https://www.googleapis.com/customsearch/v1/siterestrict?"
zza_cx = '0000911301121285600808:ontqzvamvag'
fxy_cx = '008517825388850444903:eyrvyy-n0i4'
replace = False

def isEnglish(query):
    if ORIYA_BASE <= ord(query[int(len(query)/2)]) <= ORIYA_MAX:
        return False
    if ORIYA_BASE <= ord(query[int(len(query)/3)]) <= ORIYA_MAX:
        return False
    if ORIYA_BASE <= ord(query[int(len(query)/1.5)]) <= ORIYA_MAX:
        return False
    return True

def query2enwiki(query, lang):
    en_entities = []
    if lang == 'ilo':
        query += ' philippines'
    elif lang == 'or' and isEnglish(query):
        query += ' india'
    mention2gentities = MongoBackedDict(dbname=f"mention2gentities_{lang}")
    mention2gurls = MongoBackedDict(dbname=f"mention2gurls_{lang}")

    # if replace == True:
    #     mention2gentities.drop_collection()
    if query in mention2gentities:
        en_entities = mention2gentities[query]
    else:
        PARAMS = {'key': swj_key, 'q': query, 'cx': fxy_cx, 'num':5}
        requests.adapters.DEFAULT_RETRIES = 5
        s = requests.session()
        s.keep_alive = False
        r = requests.get(url=URL, params=PARAMS)
        return_data = r.json()
        if 'items' in return_data:
            urlss = return_data['items']
            urls = [u['link'] for u in urlss]
            mention2gurls.cll.insert_one({"key": query, "value": urls})
            for url in urls:
                enwiki_url = None
                parsed_url = urlparse(url)
                domain = parsed_url.netloc
                if domain == "en" + '.wikipedia.org':
                    enwiki_url = url
                elif domain == lang + '.wikipedia.org':
                    res = requests.get(url)
                    soup = BeautifulSoup(res.text, 'html.parser')
                    for li in soup.find_all('li', {'class': 'interlanguage-link interwiki-en'}):
                        enwiki_url = li.find("a")['href']
                    if enwiki_url is None:
                        for li in soup.select('li.interlanguage-link > a'):
                            link = li.get('href')
                            if 'en.wikipedia.org' in link:
                                enwiki_url = link
                                break
                if enwiki_url is not None:
                    en_res = requests.get(enwiki_url, verify=True)
                    en_soup = BeautifulSoup(en_res.text, 'html.parser')
                    entity = en_soup.title.string[:-12]
                    # entity = enwiki_url.split('/wiki/')[-1].replace('_', ' ')
                    if not entity in en_entities:
                        en_entities.append(entity)
            mention2gentities.cll.insert_one({"key": query, "value": en_entities})

    return en_entities


gmaps = googlemaps.Client(key=swj_key)


def query2gmap_api(text, lang, replace=False):
    if lang == 'or' and isEnglish(text):
        text += ' india'
    mention2gmap_entity = MongoBackedDict(dbname=f"mention2gmap_entity_{lang}")
    # if replace == True:
    #     mention2gmap_entity.drop_collection()
    if text in mention2gmap_entity:
        # en_entities = mention2gmap_entity[text]['name']
        # enwiki_urls = mention2url[query]
        en_entities = mention2gmap_entity[text]
        return en_entities

    place_name = None
    results = gmaps.places(text)
    if 'results' in results and results['results']:
        place_name = results['results'][0]['name']
        places = results['results']
    else:
        places = None
    if place_name is None:
        geocode_result = gmaps.geocode(text)
        # geo = geocode_result[0]['formatted_address']
        if geocode_result:
            if geocode_result[0]['address_components']:
                place_name = geocode_result[0]['address_components'][0]['long_name']
                geocodes = geocode_result
            else:
                geocodes = None
    # mention2gmap_entity.cll.insert_one({"key": text, "value": {'name': place_name, "places": places, "geocode": geocodes}})
    mention2gmap_entity.cll.insert_one({"key": text, "value": place_name})

    return place_name


def query2urls_g_api(text, num=5):
    urls = []
    if 'https:' in text or isfloat(text) or text in ['.', '(', ')', ':', '', ','] or '@' in text or '#' in text:
        return urls

    query_input = text
    PARAMS = {'key': swj_key, 'q': query_input, 'cx': '008517825388850444903:eyrvyy-n0i4', 'num': num}
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


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

ORIYA_BASE = int('0x0B00', base=16)
ORIYA_MAX = int('0x0B7F', base=16)
DEVANAGARI_BASE = int('0x0900', base=16)
DEVANAGARI_MAX = int('0x097F', base=16)


def or2hindi(surface):
    hindi_str = ""
    for char in surface:
        tmp = ord(char) - (ORIYA_BASE-DEVANAGARI_BASE)
        if DEVANAGARI_BASE <= tmp <= DEVANAGARI_MAX:
            hindi_str += chr(tmp)
        else:
            hindi_str += char
    return hindi_str


if __name__ == '__main__':
    # lang = "si"
    query = 'ගිංතොට'
    print(query2enwiki('wiki تحصیل شاہ پور', 'ur'))
    query2gmap_api(query)
    # r1 = 'https://www.google.com/inputtools/request?text=Vidyarthi&ime=transliteration_en_or&num=5&cp=0&cs=0&ie=utf-8&oe=utf-8&app=jsapi&uv=Bharatiya%3A%E0%AC%AD%E0%AC%BE%E0%AC%B0%E0%AC%A4%E0%AD%80%E0%AD%9F-0-1%3A%3B0%3B0&cb=_callbacks_._2jydeyg06'
    # r2 = 'http://www.google.com/inputtools/request?text=Morcha&ime=transliteration_en_or&num=5&cp=0&cs=0&ie=utf-8&oe=utf-8&app=jsapi&uv=Vidyarthi%3A%E0%AC%AC%E0%AC%BF%E0%AC%A6%E0%AD%8D%E0%AD%9F%E0%AC%BE%E0%AC%B0%E0%AD%8D%E0%AC%A5%E0%AD%80-0-1%3A%3B0%3B0&cb=_callbacks_._3jydf41zk'

    # en_entities = query2enwiki(query, lang)
    # print(enwiki_url)
    # print("end")

