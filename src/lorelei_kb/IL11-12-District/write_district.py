# coding: utf-8
import logging
import argparse
import sys

import pymongo
import pickle
import unicodedata

logging.basicConfig(format='%(asctime)s: %(filename)s:%(lineno)d: %(message)s', level=logging.INFO)
from pymongo import MongoClient


ilcode = "12"
il2dis = {"11":"IN","12":"PH"}
client = MongoClient("localhost", 27108)
db = client['mymongo']
district_cll = db[f"geonames_il{ilcode}"]
il_state = set([])
il_dis = set([])
#
region_list = ["district","division","city","valley","district of","city of"]
for i in district_cll.find({"country_code":il2dis[ilcode]}).distinct("admin1_code_name"):
    ascii_name = i.lower()
    ascii_name = unicodedata.normalize('NFD', ascii_name).encode('ascii', 'ignore').decode('UTF-8')
    ascii_name_token = ascii_name.split()
    if len(ascii_name_token)==2 and ascii_name_token[1] in region_list:
        ascii_name = " ".join(ascii_name_token[:-1])
    print(i)
    il_dis.add(ascii_name)

print("-----")
for i in district_cll.find({"country_code":il2dis[ilcode]}).distinct("admin2_code_name"):
    ascii_name = i.lower()
    ascii_name = unicodedata.normalize('NFD', ascii_name).encode('ascii', 'ignore').decode('UTF-8')
    ascii_name_token = ascii_name.split()
    if len(ascii_name_token)==2 and ascii_name_token[-1] in region_list:
        ascii_name = " ".join(ascii_name_token[:-1])
    print(i)
    il_dis.add(ascii_name)

il_total = il_dis| il_state
with open(f'dis_il{ilcode}.pickle', 'wb') as handle:
    pickle.dump(il_total, handle, protocol=pickle.HIGHEST_PROTOCOL)



