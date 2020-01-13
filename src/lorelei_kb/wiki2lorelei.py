import argparse
import logging
from lorelei_kb.load_geonames_kb_v2 import fields
from nilanalysis.utils import get_normalized_wikititle, get_normalized_wikititle_kbentry
from utils.constants import NULL_TITLE
from utils.mongo_backed_dict import MongoBackedDict
from wiki_kb.title_normalizer_v2 import TitleNormalizer
import sys
# sys.path.append("/shared/experiments/xyu71/lorelei2017/src/lorelei_kb")
# sys.path.append("/shared/experiments/xyu71/lorelei2017/src/nilanalysis")
# sys.path.append("/shared/experiments/xyu71/lorelei2017/src/wiki_kb")
#
# from load_geonames_kb_v2 import fields
# from utils import get_normalized_wikititle, get_normalized_wikititle_kbentry
# sys.path.append("/shared/experiments/xyu71/lorelei2017/src/utils")
# from constants import NULL_TITLE
# from mongo_backed_dict import MongoBackedDict
# from title_normalizer_v2 import TitleNormalizer


logging.basicConfig(format=':%(levelname)s: %(message)s', level=logging.INFO)
__author__ = 'Shyam'


class Wiki2Lorelei:
    def __init__(self, ilcode, overwrite=False):
        cll_name = "wiki2eid_il" + ilcode
        self.wiki2eids = MongoBackedDict(dbname=cll_name)
        self.normalizer = TitleNormalizer()
        if overwrite:
            self.wiki2eids.drop_collection()
            logging.info("computing wiki2eids map ...")
            self.compute_map(ilcode)
        logging.info("wiki2eids map loaded (size=%d)",self.wiki2eids.size())

    # @profile
    def compute_map(self, ilcode):
        basepath = "/shared/corpora/corporaWeb/lorelei/evaluation-2019/"
        kbfile = basepath + "il{}/source/kb/IL{}_kb/data/entities.tab".format(ilcode, ilcode, ilcode)
        tmp_map = {}
        for idx, line in enumerate(open(kbfile)):

            if idx > 0 and idx % 100000 == 0:
                logging.info("read %d lines", idx)

            parts = line.rstrip('\n').split('\t')
            if len(parts) < len(fields):
                logging.info("bad line %d nfields:%d expected:%d", idx, len(parts), len(fields))
                continue

            kbentry = {}
            for field, v in zip(fields, parts):
                if len(v) != 0:
                    kbentry[field] = v

            eid = kbentry["entityid"]
            title = get_normalized_wikititle_kbentry(title_normalizer=self.normalizer, kbentry=kbentry)

            if title == NULL_TITLE:
                continue

            if title not in tmp_map:
                tmp_map[title] = []
            tmp_map[title].append(eid)
        self.wiki2eids.bulk_insert(regular_map=tmp_map, insert_freq=len(tmp_map))


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description='Short sample app')
    PARSER.add_argument('--ilcode', required=True, dest="ilcode",
                        help="sometimes ilcode is different than lang e.g. tigrinya and amharic")
    PARSER.add_argument('--write', action="store_true", dest="write")
    args = PARSER.parse_args()
    args = vars(args)
    ilcode = args["ilcode"]
    write = args["write"]
    w2l = Wiki2Lorelei(ilcode=ilcode, overwrite=write)
    print("title:Kigali has eids:",w2l.wiki2eids["Kigali"])