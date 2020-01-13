# coding: utf-8
import logging
import argparse
import sys

import pymongo

logging.basicConfig(format='%(asctime)s: %(filename)s:%(lineno)d: %(message)s', level=logging.INFO)
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from load_geonames_kb_v2 import GeoNamesLoader

fields = ['entityid', 'name', 'asciiname', 'alternater_names']


class GZLoader:
    def __init__(self, ilcode="11", hostname="localhost", port=27108, read_only=True, insert_freq=10000, geonames=None):
        self.client = MongoClient(hostname, port)
        self.ilcode = ilcode
        kbfile = f"/shared/corpora/corporaWeb/lorelei/evaluation-2019/il{self.ilcode}/source/english_gazetteer.txt"

        self.db = self.client['mymongo']
        gazeteer_name = "gt_il" + self.ilcode
        self.geonames_cll = self.db[gazeteer_name]
        gazeteer_name = "gt_name2id_il" + self.ilcode
        self.gazeteer_name = self.db[gazeteer_name]
        self.ge = geonames

        self.read_only = read_only
        self.insert_freq = insert_freq
        if not self.read_only:
            if kbfile is None:
                logging.info("please provide kbfile path")
                sys.exit(-1)
            logging.info("dropping old collection ...")
            # self.geonames_cll.drop()
            self.load_kb(kbfile)
            # unique=True cannot be supported right now
            self.geonames_cll.create_index([("entityid", pymongo.HASHED)])
            # self.geonames_cll.create_index([("name", pymongo.HASHED)])

        # logging.info("mongodb %s ready! (size=%d)", cll_name, self.geonames_cll.count())


    def bulk_insert(self, gazeteer_name, regular_map, value_func=None, insert_freq=10000):
        """
        Writes a regular python dict (map) to mongo.
        Common idiom is bulk_insert(regular_map=mydict,insert_freq=len(mydict))
        :param regular_map:
        :param value_func:
        :param insert_freq:
        :return:
        """
        docs = []
        for idx, k in enumerate(regular_map):
            if value_func is None:
                val = regular_map[k]
            else:
                # print("applying valfunc")
                val = value_func(regular_map[k])
            # print(val)
            docs.append({"key": k, "value": val})
            if idx > 0 and idx % insert_freq == 0:
                logging.info("inserting %d", idx)
                gazeteer_name.insert_many(docs)
                logging.info("inserted %d", idx)
                docs = []
        # insert remaining ...
        if len(docs) > 0:
            gazeteer_name.insert_many(docs)
        logging.info("mongo map size %d", gazeteer_name.count())
        # logging.info("building hashed index on \"key\"")
        gazeteer_name.create_index([("key", pymongo.HASHED)])


    def load_kb(self, kbfile):
        # took ~7 min for geonames (12M lines)
        try:
            docbuffer = []
            namedict = {}
            for idx, line in enumerate(open(kbfile)):
                if idx > 0 and idx % 100000 == 0:
                    logging.info("read %d lines", idx)
                parts = line.rstrip('\n').split('\t')[:4]
                if len(parts) < len(fields):
                    logging.info("bad line %d nfields:%d expected:%d", idx, len(parts),len(fields))
                    # logging.info("%s",parts)
                    continue
                endict = {}
                names = []
                for field, v in zip(fields, parts):
                    if len(v) != 0:
                        endict[field] = v
                names += [parts[1], parts[2]]
                names += parts[3].split(",")
                eid = parts[0]
                if eid not in self.ge:
                    continue
                docbuffer.append(endict)


                print(f"finish:{idx}")
                namedict = {}
                for n in names:
                    namedict.setdefault(n, set([])).add(eid)
                self.bulk_insert(self.gazeteer_name, namedict, insert_freq=len(namedict), value_func=lambda x: list(x))


                if idx > 0 and idx % 10000 == 0:
                    print("insert")
                    try:
                        self.geonames_cll.insert_many(docbuffer)
                        logging.info("inserting %d lines", idx)
                        docbuffer = []

                    except BulkWriteError as bwe:
                        logging.info(bwe.details)
            # insert rest of buffer
            try:
                self.geonames_cll.insert_many(docbuffer)
            except BulkWriteError as bwe:
                logging.info(bwe.details)

        except KeyboardInterrupt:
            logging.info("ending prematurely.")

    def get(self, eid=None, name=None):
        if eid is not None:
            # extremely fast, returns on first hit
            doc = self.geonames_cll.find_one({'entityid': eid})
            return doc
        elif name is not None:
            # relatively slower than find_one
            docs = self.geonames_cll.find({'name': name})
            return docs

    def __contains__(self, eid):
        doc = self.get(eid=eid)
        if doc is None:
            return False
        return True

    def __getitem__(self, eid):
        doc = self.get(eid=eid)
        return doc

    def all_iterator(self):
        for post in self.geonames_cll.find():
            yield post

    def size(self):
        return self.geonames_cll.count()

    def finish(self):
        self.client.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Short sample app')
    # parser.add_argument('--kbfile', default=None, action="store", dest="kbfile")
    parser.add_argument('--ilcode', action="store", default="12", dest="ilcode")
    parser.add_argument('--write', action="store_true", dest="write")
    args = parser.parse_args()
    args = vars(args)
    ilcode = args["ilcode"]
    read_only = not args["write"]

    Org2eid = {}
    for line in open(f"/shared/experiments/xyu71/lorelei2017/python_src/lorelei_kb/il11-12-org-per/IL{ilcode}Org","r"):
        line =  line.strip().split("\t")
        eid, name = line[2], line[3]
        Org2eid[name] = eid

    Peo2eid = {}
    for line in open(f"/shared/experiments/xyu71/lorelei2017/python_src/lorelei_kb/il11-12-org-per/IL{ilcode}Per", "r"):
        line =  line.strip().split("\t")
        eid, name = line[2], line[3]
        Peo2eid[name] = eid

    client = MongoClient("localhost", 27108)
    db = client['mymongo']
    Peo2eid_cll = db[f"peo_name2id_il{ilcode}"]
    for k, v in Peo2eid.items():
        Peo2eid_cll.insert_one({"key": k, "value": v})

    Org2eid_cll = db[f"org_name2id_il{ilcode}"]
    Org2eid_cll.insert(Org2eid)
    for k, v in Org2eid.items():
        Org2eid_cll.insert_one({"key": k, "value": v})


    eid2peo = {v: k for k, v in Peo2eid.items()}
    eid2org = {v: k for k, v in Org2eid.items()}

    eid2peo_cll = db[f"name2id_peo_il{ilcode}"]
    for k, v in Peo2eid.items():
        eid2peo_cll.insert_one({"key": k, "value": v})

    eid2org_cll = db[f"name2id_org_il{ilcode}"]
    for k, v in Org2eid.items():
        eid2org_cll.insert_one({"key": k, "value": v})

    kbfile = f"/shared/corpora/corporaWeb/lorelei/evaluation-2019/il{ilcode}/source/english_gazetteer.txt"
    eid2gz = {}
    for line in open(kbfile,"r"):
        parts = line.rstrip('\n').split('\t')[:4]
        eid = parts[0]
        name = parts[1]
        eid2gz[eid] = name
    eid2gz_cll = db[f"eid2gz_il{ilcode}"]
    for k, v in eid2gz.items():
        eid2gz_cll.insert_one({"key": k, "value": v})
        logging.info("mongo map size %d", eid2gz_cll.count())











