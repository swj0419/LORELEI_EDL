import sys
sys.path.append("/pool0/webserver/incoming/experiment_tmp/EDL2019/src/utils/")
from  mongo_backed_dict import MongoBackedDict

# from utils.mongo_backed_dict import MongoBackedDict

import sys
sys.path.insert(0, "/home/luciahuo/lorelei2017/src/epitran/")

import logging
import epitran
import argparse

# from lorelei_kb.load_geonames_kb_v2 import GeoNamesLoader
logging.basicConfig(format='%(asctime)s: %(filename)s:%(lineno)d: %(message)s', level=logging.INFO)

# logging.basicConfig(format=':%(levelname)s: %(message)s', level=logging.INFO)
import time


def add_to_dict(names, eid, tmpdict):
    for name in names:
        if name not in tmpdict:
            tmpdict[name] = set([])
        tmpdict[name].add(eid)


def ngrams(s, n):
    ans = []
    for i in range(len(s) - n + 1):
        ans.append(s[i:i + n])
    return ans


def removeAll(string, inchars):
    for inch, in inchars:
        if inch in string:
            string = string.replace(inch, "")
    return string


def getngrams(s, ngram):
    ans = []
    if ngram == 0:
        ans.append(s)
    if ngram == 1:
        ans += s.split(" ")
    if ngram == 4:
        ans += ngrams(s, 4)
    if ngram == 3:
        ans += ngrams(s, 3)
    if ngram == 2:
        ans += ngrams(s, 2)
    if ngram == 5:
        # v = removeAll(s.lower(), "aeiou")
        # ans.append(v)
        ans += ngrams(s, 5)
    return ans


class AbstractIndex:
    def __init__(self, ilcode, overwrite=False, ngramorders=[]):
        # self.transliterator = epitran.Epitran("eng-Latn")
        self.index_name = self.get_index_name(ilcode)
        self.kbfile = self.get_kbfile(ilcode)
        self.name2ent = MongoBackedDict(dbname=self.index_name + ".phrase")
        self.word2ent = MongoBackedDict(dbname=self.index_name + ".word")
        # self.phon2ent = MongoBackedDict(dbname=self.index_name + ".phon")
        self.ngram2ent = {}
        self.ngramorders = ngramorders
        logging.info("Using ngram orders %s", ngramorders)
        # sys.exit(0)
        # for i in self.ngramorders:
        #     self.ngram2ent[i] = MongoBackedDict(dbname=self.index_name + ".ngram-{}".format(i))
        # index_type = "ngram2ent"  # temporary change to regenerate ngram 5
        indices = []
        all_empty = all([i.size() == 0 for i in indices])
        index_type = [] # list of indices to load
        if overwrite: # overwrite everything
            self.name2ent.drop_collection()
            self.word2ent.drop_collection()
            # self.phon2ent.drop_collection()
            # for i in self.ngramorders:
            #     self.ngram2ent[i].drop_collection()
            logging.info("overwriting for ilcode " + ilcode)
            index_type.append("all")
        else:
            if self.name2ent.size() == 0:
                self.name2ent.drop_collection()
                logging.info("reloading name2ent ...")
                index_type.append("name2ent")

            if self.word2ent.size() == 0:
                self.word2ent.drop_collection()
                logging.info("reloading word2ent ...")
                index_type.append("word2ent")

            # if self.phon2ent.size() == 0:
            #     self.phon2ent.drop_collection()
            #     logging.info("reloading phon2ent ...")
            #     index_type.append("phon2ent")

            # for i in self.ngramorders:
            #     if self.ngram2ent[i].size() == 0:
            #         logging.info("reloading ngram2ent of size " + i)
            #         self.ngram2ent[i].drop_collection()
            #         index_type.append(i + "gram2ent")

        if index_type:
            start = time.time()
            logging.info("loading from file %s", self.index_name)
            self.load_kb(index_type=index_type)
            logging.info("created in %d secs", time.time() - start)
        logging.info("%s loaded", self.index_name)

    def process_kb(self):
        raise NotImplementedError

    def get_index_name(self, ilcode):
        raise NotImplementedError

    def get_kbfile(self, ilcode):
        raise NotImplementedError

    def load_kb(self, index_type):
        name_map = {}
        word_map = {}
        phon_map = {}
        ngram_map = {}
        logging.info("index type:%s", index_type)
        # for i in self.ngramorders:
        #     if self.ngram2ent[i].size() == 0: # only generate entries for those grams that need to be loadeds
        #         ngram_map[i] = {}
        try:
            for names, eid in self.process_kb():
                names = set(names)
                is_all = len(index_type) == 1 and index_type[0] == "all"
                for t in index_type:
                    if is_all or t == "name2ent":
                        add_to_dict(names, eid, name_map)
                    if is_all or t == "word2ent":
                        toks = set([tok for n in names for tok in n.split(" ")])
                        add_to_dict(toks, eid, word_map)
                    # if is_all or t == "phon2ent":
                    #     phons = set([self.transliterator.transliterate(n) for n in names])
                    #     add_to_dict(phons, eid, phon_map)
                    # if is_all or t == "ngram2ent":
                    #     for i in ngram_map.keys():
                    #         ngramset = set([gram for n in names for gram in getngrams(n, ngram=i)])
                    #         add_to_dict(ngramset, eid, ngram_map[i])
            self.put_in_mongo(index_type, name_map, word_map, phon_map, ngram_map)
        except KeyboardInterrupt:
            logging.info("Ending prematurely. Inserting incomplete dictionaries into database.")
            self.put_in_mongo(index_type, name_map, word_map, phon_map, ngram_map)

    def put_in_mongo(self, index_type, name_map, word_map, phon_map, ngram_map):
        is_all = len(index_type) == 1 and index_type[0] == "all"
        for t in index_type:
            if is_all or t == "name2ent":
                self.name2ent.bulk_insert(name_map,
                                          insert_freq=len(name_map),
                                          value_func=lambda x: list(x))
            if is_all or t == "word2ent":
                self.word2ent.bulk_insert(word_map,
                                          insert_freq=len(word_map),
                                          value_func=lambda x: list(x))
            # if is_all or t == "phon2ent":
            #     phon_map = self.prune_map(phon_map)  # prune map
            #     self.phon2ent.bulk_insert(phon_map,
            #                               insert_freq=len(phon_map),
            #                               value_func=lambda x: list(x))
            # if is_all or t == "ngram2ent":
            #     for i in ngram_map.keys():
            #         ngram_map[i] = self.prune_map(ngram_map[i])
            #         self.ngram2ent[i].bulk_insert(ngram_map[i],
            #                                       insert_freq=len(ngram_map[i]),
            #                                       value_func=lambda x: list(x))

    def prune_map(self, nmap):
        # dict changes during iteration, so take care
        logging.info("map size before pruning %d", len(nmap))
        pruned = 0
        for k in list(nmap.keys()):
            if len(nmap[k]) > 5000:
                # logging.info("pruning entry for %s len=%d", k, len(nmap[k]))
                del nmap[k]
                pruned +=1
            # if pruned > 0 and pruned % 1000==0:
        logging.info("pruned %d entries", pruned)
        logging.info("map size after pruning %d", len(nmap))
        return nmap


class GeoNameIndex(AbstractIndex):
    def __init__(self, ilcode, overwrite, ngramorders):
        super().__init__(ilcode, overwrite, ngramorders)

    def get_index_name(self, ilcode):
        geoind = "geoname_il{}_index".format(ilcode)
        return geoind

    def get_kbfile(self, ilcode):
        if ilcode in ['9', '10']:
            basepath = "/shared/corpora/corporaWeb/lorelei/evaluation-2018/"
        elif ilcode in ['11', '12']:
            basepath = "/shared/corpora/corporaWeb/lorelei/evaluation-2019/"

        kbfile = basepath + "il{}/source/kb/IL{}_kb/data/entities.tab".format(ilcode, ilcode)
        return kbfile

    def process_kb(self):
        logging.info("processing geonames ...")
        for idx, line in enumerate(open(self.kbfile)):
            if idx > 0 and idx % 10000 == 0:
                logging.info("read %d lines", idx)
                # break
            parts = line.strip().split('\t')
            if len(parts) < 4:
                logging.info("bad line %s", line)
                logging.info(parts)
                continue
            eid, name = parts[2], parts[3]
            names = [name, name.lower(), name.strip()]
            if len(parts) > 4:
                asciiname = parts[4]

            else:
                # TODO make this ascii
                asciiname = name
            if len(asciiname.strip()) != 0:
                names.append(asciiname)
                names.append(asciiname.lower())
            yield names, eid


class AltNameIndex(AbstractIndex):
    def __init__(self, ilcode, overwrite, ngramorders):
        super().__init__(ilcode, overwrite, ngramorders)

    def get_index_name(self, ilcode):
        altind = "altname_il{}_index".format(ilcode)
        return altind

    def get_kbfile(self, ilcode):
        if ilcode in ['9', '10']:
            basepath = "/shared/corpora/corporaWeb/lorelei/evaluation-2018/"
        elif ilcode in ['11', '12']:
            basepath = "/shared/corpora/corporaWeb/lorelei/evaluation-2019/"
        kbfile = basepath + "il{}/source/kb/IL{}_kb/data/alternate_names.tab".format(ilcode, ilcode)
        return kbfile

    def process_kb(self):
        logging.info("processing alternate names ...")
        for idx, line in enumerate(open(self.kbfile)):
            if idx > 0 and idx % 1000000 == 0:
                logging.info("read %d lines", idx)
            parts = line.strip().split('\t')
            if len(parts) != 2:
                continue
            eid, name = parts
            names = [name, name.lower(), name.strip()]
            yield names, eid


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Short sample app')
    parser.add_argument('--orders', default="2,3,4,5", action="store")
    parser.add_argument('--ilcode', default="9", action="store")
    parser.add_argument('--write', action="store_true")
    args = parser.parse_args()
    args = vars(args)
    ilcode = args["ilcode"]
    args["orders"] = list(map(int, args["orders"].split(",")))
    geoname_index = GeoNameIndex(ilcode=ilcode,
                                 overwrite=args["write"],
                                 ngramorders=args["orders"])
    print(args["orders"])
    altname_index = AltNameIndex(ilcode=ilcode,
                                 overwrite=args["write"],
                                 ngramorders=args["orders"])
    # geonames = GeoNamesLoader(ilcode=ilcode)
    # try:
    #     while True:
    #         surface = input("enter surface:")
    #         if surface in geoname_index.name2ent:
    #             eids = geoname_index.name2ent[surface]
    #             print("geocands found:", len(eids))
    #             for idx, cand in enumerate(eids):
    #                 logging.info("eid %s %s", cand, geonames[cand]['name'])
    #         if surface in altname_index.name2ent:
    #             eids = altname_index.name2ent[surface]
    #             print("altcands found:", len(eids))
    #             for idx, cand in enumerate(eids):
    #                 logging.info("eid %s %s", cand, geonames[cand]['name'])

    # except KeyboardInterrupt:
    #     print('interrupted!')
