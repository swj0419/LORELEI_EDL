import logging
import time
import sys
sys.path.append("/pool0/webserver/incoming/experiment_tmp/EDL2019/src/utils")
from mongo_backed_dict import MongoBackedDict
# from utils.mongo_backed_dict import MongoBackedDict

logging.basicConfig(format='%(asctime)s: %(filename)s:%(lineno)d: %(message)s', level=logging.INFO)

class Inlinks:
    """
    reads the outlinks file and computes the inlinks dictionary from it.
    saves it in a pickled dict for fast access.
    """

    def __init__(self, links_file, normalizer=None, overwrite=False):
        # normalizer = TitleNormalizer() if normalizer is None else normalizer
        if links_file is None:
            # links_file = "/shared/experiments/xyu71/lorelei2017/preprocess/outlinks.t2t"
            sys.exit('No inlink file given')
        self.normalizer = normalizer
        self.inlinks = MongoBackedDict(dbname="enwiki_inlinks")
        if self.inlinks.size() == 0 or overwrite:
            self.inlinks.drop_collection()
            start = time.time()
            logging.info("loading from file %s", links_file)
            self.load_link_info(links_file=links_file)
            logging.info("created in %d secs", time.time() - start)

    def load_link_info(self, links_file):
        logging.info("loading links %s ...", links_file)
        bad = 0
        mmap = {}
        for idx, line in enumerate(open(links_file)):
            if idx > 0 and idx % 1000000 == 0:
                logging.info("read %d", idx)
            line = line.strip().split('\t')
            if len(line) != 2:
                # logging.info("skipping bad line %s", line)
                bad += 1
                if bad % 10000 == 0:
                    logging.info("bad %d total %d", bad, idx)
                continue
            else:
                print(line)
            src = line[0]
            trgs = line[1].split(' ')
            for trg in trgs:
                if trg not in mmap:
                    mmap[trg] = []
                mmap[trg].append(src)
        logging.info("inserting regular map into mongo")
        self.inlinks.bulk_insert(regular_map=mmap,insert_freq=len(mmap))
        # DONT DO THIS! this inserts one by one, which is slow
        # for trg in mmap:
        #     self.inlinks[trg] = mmap[trg]
        logging.info("mongo map made")

if __name__ == "__main__":
    # s = Inlinks(overwrite=True)
    s = Inlinks()
    print(s.inlinks.size())
    for k in s.inlinks.all_iterator():
        print(k,len(s.inlinks[k]))
"/shared/experiments/xyu71/lorelei2017/preprocess/outlinks.t2t"