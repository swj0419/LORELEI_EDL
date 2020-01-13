# coding: utf-8
import logging
import argparse
import sys

import pymongo

logging.basicConfig(format='%(asctime)s: %(filename)s:%(lineno)d: %(message)s', level=logging.INFO)
from pymongo import MongoClient
from pymongo.errors import BulkWriteError

fields = ['origin', 'entity_type', 'entityid', 'name', 'asciiname', 'latitude', 'longitude', 'feature_class',
          'feature_class_name', 'feature_code', 'feature_code_name', 'feature_code_description', 'country_code',
          'country_code_name', 'cc2', 'admin1_code', 'admin1_code_name', 'admin2_code', 'admin2_code_name',
          'admin3_code', 'admin4_code', 'population', 'elevation', 'dem', 'timezone', 'modification_date',
          'per_gpe_loc_of_association', 'per_title_or_position', 'per_org_of_association', 'per_role_in_incident',
          'per_year_of_birth', 'per_year_of_death', 'per_gender', 'per_family_member', 'note', 'aim',
          'org_date_established', 'date_established_note', 'org_website', 'org_gpe_loc_of_association',
          'org_members_employees_per', 'org_parent_org', 'executive_board_members', 'jurisdiction',
          'trusteeship_council', 'national_societies', 'external_link']


class GeoNamesLoader:
    def __init__(self, ilcode="9", hostname="localhost", port=27108, read_only=True, insert_freq=10000):
        self.client = MongoClient(hostname, port)
        self.ilcode = ilcode
        basepath = "/shared/corpora/corporaWeb/lorelei/evaluation-2019/"
        kbfile = basepath + "il{}/source/kb/IL{}_kb/data/entities.tab".format(ilcode, ilcode)
        # kbfile = basepath + "il{}/source/kb/IL{}_kb/data/il{}_entities_new.tab".format(ilcode, ilcode, ilcode)
        # kbfile = basepath + "il{}/source/kb/IL{}_kb/data/il{}_entities.tab".format(ilcode, ilcode, ilcode)

        self.db = self.client['mymongo']
        # cll_name = "geonames_il"+self.ilcode
        cll_name = "geonames_il" + self.ilcode
        # cll_name = "geonames_il" + self.ilcode + "_new"
        self.geonames_cll = self.db[cll_name]
        self.read_only = read_only
        self.insert_freq = insert_freq
        if not self.read_only:
            if kbfile is None:
                logging.info("please provide kbfile path")
                sys.exit(-1)
            logging.info("dropping old collection ...")
            self.geonames_cll.drop()
            self.load_kb(kbfile)
            # unique=True cannot be supported right now
            self.geonames_cll.create_index([("entityid", pymongo.HASHED)])

        logging.info("mongodb %s ready! (size=%d)", cll_name, self.geonames_cll.count())

    def load_kb(self, kbfile):
        # took ~7 min for geonames (12M lines)
        try:
            docbuffer = []
            for idx, line in enumerate(open(kbfile)):
                if idx > 0 and idx % 1000000 == 0:
                    logging.info("read %d lines", idx)
                parts = line.rstrip('\n').split('\t')
                if len(parts) < len(fields):
                    logging.info("bad line %d nfields:%d expected:%d", idx, len(parts),len(fields))
                    # logging.info("%s",parts)
                    continue
                endict = {}
                for field, v in zip(fields, parts):
                    if len(v) != 0:
                        endict[field] = v
                docbuffer.append(endict)

                if idx > 0 and idx % self.insert_freq == 0:
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
    parser.add_argument('--ilcode', action="store", default="9", dest="ilcode")
    parser.add_argument('--write', action="store_true", dest="write")
    args = parser.parse_args()
    args = vars(args)
    ilcode = args["ilcode"]
    read_only = not args["write"]
    geonames = GeoNamesLoader(ilcode=ilcode, read_only=read_only)
    print("lorelei_kb size", geonames.size())
    doc = geonames.get(eid="281184")
    print(doc)
    doc = geonames.get(eid="71000119")
    print(doc)
    geonames.finish()
    # for doc in geonames.get(name="Roc Gros"):
    #     print(doc)
    # for idx, kbentry in enumerate(geonames.all_iterator()):
    #     if idx > 0 and idx % 1000000 == 0:
    #         logging.info("read %d", idx)
    # print(kbentry)
    # tic = time.time()
    # toc = time.time()
    # logging.info("loaded lorelei_kb in %d sec", toc - tic)
    # for k in geonames.keys():
    #     print(k, geonames[k])
