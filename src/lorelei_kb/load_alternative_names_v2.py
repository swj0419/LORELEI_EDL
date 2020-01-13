import sys

__author__ = 'Shyam'
import logging
import argparse
# sys.path.append("/shared/experiments/xyu71/lorelei2017/src/lorelei_kb")
# from load_geonames_kb_v2 import GeoNamesLoader

logging.basicConfig(format='%(asctime)s: %(filename)s:%(lineno)d: %(message)s', level=logging.INFO)
from lorelei_kb.load_geonames_kb_v2 import GeoNamesLoader
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
import pymongo


class AlternativeNamesLoader:
    def __init__(self, ilcode="9", hostname="localhost", port=27108, read_only=True, insert_freq=10000):
        self.client = MongoClient(hostname, port)
        self.ilcode = ilcode
        basepath = "/shared/corpora/corporaWeb/lorelei/evaluation-2019/"
        altfile = basepath + "il{}/source/kb/IL{}_kb/data/alternate_names.tab".format(ilcode, ilcode)

        self.db = self.client['mymongo']
        self.altnames_cll = self.db["altnames_il" + self.ilcode]
        self.read_only = read_only
        self.insert_freq = insert_freq
        if not self.read_only:
            if altfile is None:
                logging.info("please provide kbfile path")
                sys.exit(-1)
            logging.info("dropping old collection ...")
            self.altnames_cll.drop()
            self.load_kb(altfile)
            self.altnames_cll.create_index([("entityid", pymongo.HASHED)])
        logging.info("mongodb altnames_il%s ready! (size=%d)", self.ilcode, self.altnames_cll.count())

    def load_kb(self, altfile):
        logging.info("loading from %s", altfile)
        try:
            docbuffer = []
            for idx, line in enumerate(open(altfile)):
                if idx > 0 and idx % 1000000 == 0:
                    logging.info("read %d lines", idx)
                    # break
                parts = line.rstrip('\n').split('\t')
                if len(parts) != 2:
                    # print(parts, len(parts))
                    logging.info("bad line %d", idx)
                    continue
                eid, name = parts
                docbuffer.append({"entityid": eid, "alternatename": name})
                if idx > 0 and idx % self.insert_freq == 0:
                    try:
                        self.altnames_cll.insert_many(docbuffer)
                        logging.info("inserting %d lines", idx)
                        docbuffer = []
                    except BulkWriteError as bwe:
                        logging.info(bwe.details)
            # insert rest of buffer
            try:
                self.altnames_cll.insert_many(docbuffer)
            except BulkWriteError as bwe:

                logging.info(bwe.details)
        except KeyboardInterrupt:
            logging.info("ending prematurely.")

    def get(self, eid=None, name=None):
        if eid is not None:
            docs = self.altnames_cll.find_one({'entityid': eid})
            return docs
        elif name is not None:
            docs = self.altnames_cll.find({'alternatename': name})
            return docs

    def __getitem__(self, eid):
        doc = self.get(eid=eid)
        return doc

    def all_iterator(self):
        for post in self.altnames_cll.find():
            yield post

    def size(self):
        return self.altnames_cll.count()

    def finish(self):
        self.client.close()

    def __contains__(self, eid):
        doc = self.get(eid=eid)
        if doc is None:
            return False
        return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Short sample app')
    parser.add_argument('--ilcode', action="store", default="9", dest="ilcode")
    parser.add_argument('--write', action="store_true", dest="write")
    args = parser.parse_args()
    args = vars(args)
    ilcode = args["ilcode"]
    read_only = not args["write"]
    altnames = AlternativeNamesLoader(ilcode=ilcode, read_only=read_only)
    geonames = GeoNamesLoader(ilcode=ilcode)
    print(altnames.size())
    # tic = time.time()
    # toc = time.time()
    # logging.info("loaded lorelei_kb in %d sec", toc - tic)
    # from get_unicode_block import word_block

    # for kbentry in altnames.all_iterator():
    #     print(kbentry)
    #     eid = kbentry["entityid"]
    #     name = kbentry["alternatename"]
    #     print(kbentry, eid, name, geonames.get(eid=eid))
