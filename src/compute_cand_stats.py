from __future__ import division
import argparse
import glob
from ccg_nlpy.core.text_annotation import TextAnnotation
import logging
import numpy as np
__author__ = 'Shyam'


class CandStats:
    def __init__(self):
        self.init_counters()

    def init_counters(self):
        self.nils = {}
        self.single_cands = {}
        # self.total_nils = 0
        # self.total_single_cands = 0
        self.gt1_cands = {}
        # self.total_gt1_cands = 0
        self.doc_num_mentions = {}
        self.uniq_mentions = {}

    def update_stats(self, docta, docid):
        candgen_view = docta.get_view("CANDGEN")
        nerview = docta.get_view("NER_CONLL")

        num_mentions = len(nerview.cons_list)
        uniq_mentions = set([con["tokens"] for con in nerview.cons_list])
        self.uniq_mentions[docid] = uniq_mentions
        self.doc_num_mentions[docid] = num_mentions

        self.nils[docid] = 0
        self.single_cands[docid] = 0
        self.gt1_cands[docid] = 0

        for cons in candgen_view.cons_list:
            if 'labelScoreMap' in cons:
                labelScoreMap = cons['labelScoreMap']
            else:
                labelScoreMap = {}

            if len(labelScoreMap) == 0:
                self.nils[docid] += 1
                # self.total_nils[] += 1
            elif len(labelScoreMap) == 1:
                self.single_cands[docid] += 1
                # self.total_single_cands += 1
            else:
                self.gt1_cands[docid] += 1
                # self.total_gt1_cands += 1

    def final_report(self):
        total_mentions = sum(self.doc_num_mentions.values())
        max_mentions = max(self.doc_num_mentions.values())
        mean_mentions = np.average(list(self.doc_num_mentions.values()))
        median_mentions = np.median(list(self.doc_num_mentions.values()))
        total_uniq_mentions = len(set.union(*[self.uniq_mentions[doc] for doc in self.uniq_mentions]))

        total_nils = sum(self.nils.values())
        total_single_cands = sum(self.single_cands.values())
        total_gt1_cands = sum(self.gt1_cands.values())
        max_cands = max(self.gt1_cands.values())
        mean_cands = np.mean(list(self.gt1_cands.values())) #sum(self.gt1_cands.values())/len(self.gt1_cands)
        median_cands = np.median(list(self.gt1_cands.values())) #sum(self.gt1_cands.values())/len(self.gt1_cands)
        logging.info("total #mentions %d", total_mentions)
        logging.info("total #uniq mentions %d", total_uniq_mentions)
        logging.info("max #mentions %d", max_mentions)
        logging.info("mean #mentions %.3f", mean_mentions)
        logging.info("median #mentions %d", median_mentions)
        logging.info("#no cands %d/%d=%.3f", total_nils, total_mentions, total_nils / total_mentions)
        logging.info("#single cands %d/%d=%.3f", total_single_cands, total_mentions,
                     total_single_cands / total_mentions)
        logging.info("#>1 cands %d/%d=%.3f", total_gt1_cands, total_mentions, total_gt1_cands / total_mentions)
        logging.info("#max cands %d", max_cands)
        logging.info("#mean cands when >1 %.3f", mean_cands)
        logging.info("#median cands when >1 %.3f", median_cands)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Short sample app')
    parser.add_argument('--indir', default=None, dest="indir")  # "../lorelei2017/tigrinya_jsons_gold_mentions"
    args = parser.parse_args()
    args = vars(args)
    json_dir = args["indir"]
    tafiles = glob.glob(json_dir + "/*")
    stats = CandStats()
    print("Total number of files: {}".format(len(tafiles)))
    for i, tafile in enumerate(tafiles):
        docta = TextAnnotation(json_str=open(tafile).read())
        docid = tafile.split("/")[-1]
        # logging.info("processing docid %s", docid)
        stats.update_stats(docta=docta, docid=docid)
        if i > 0 and i % 1000 == 0:
            print("Files done: {}".format(i))
    stats.final_report()
