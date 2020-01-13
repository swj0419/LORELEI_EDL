from ccg_nlpy.core.text_annotation import TextAnnotation
from tqdm import tqdm
import os
import argparse
import logging
from collections import defaultdict


def compute_cand_stats(tafiles, args):
    mention2cand = dict()
    for i, tafile in tqdm(enumerate(tafiles)):
        docta = TextAnnotation(json_str=open(os.path.join(args.indir,tafile)).read())
        docid = tafile.split("/")[-1]
        tokens2offset = defaultdict(list)
        # tokens2offset
        for token, offset in zip(docta.get_tokens, docta.char_offsets):
            tokens2offset[token].append(offset)
        candgen_view = docta.get_view("CANDGEN")
        for cons in candgen_view.cons_list:
            offset = tokens2offset[cons["tokens"]].pop(0)
            mention_name = f"{docid[:-5]}:{offset[0]}-{offset[1]}"
            if mention_name in mention2cand:
                logging.info("found duplicate mentions")
            if 'labelScoreMap' in cons:
                labelScoreMap = cons['labelScoreMap']
                mention2cand[mention_name] = labelScoreMap
            else:
                mention2cand[mention_name] = ["NIL"]
    return mention2cand

def compute_precision(golden_mention2id, golden_mention2attr, golden_mention2text, mention2cand, mention2l2smap, not1_outfile, uncovered_outfile):
    unc_outf = open(uncovered_outfile, 'w')
    unc_outf.write(f'hard/easy\tmention\tspan\tlabel\tcandidates\n')
    not1_outf = open(not1_outfile, 'w')
    not1_outf.write(f'hard/easy\tmention\tspan\tlabel\tcandidates\n')
    # hit@1
    total_notnil, total_nil = 0, 0
    easy_total_notnil, easy_total_nil = 0, 0
    hard_total_notnil, hard_total_nil = 0, 0
    hit1, hit3, hit5, hitn = 0, 0, 0, 0
    easy_hit1, easy_hit3, easy_hit5, easy_hitn = 0, 0, 0, 0
    hard_hit1, hard_hit3, hard_hit5, hard_hitn = 0, 0, 0, 0
    nil_hit = 0
    missed = 0

    for mention, labels in golden_mention2id.items():
        if mention not in mention2cand:
            missed += 1
            continue
        cand = mention2cand[mention]
        # not nil
        if "nil" not in labels[:3]:
            total_notnil += 1
            if golden_mention2attr[mention] == 1:
                hard_total_notnil += 1
            elif golden_mention2attr[mention] == 0:
                easy_total_notnil += 1
            labels = set(labels.split("|"))
            if labels.intersection(set(cand[:1])):
                hit1 += 1
                if golden_mention2attr[mention]==1:
                    hard_hit1 += 1
                elif golden_mention2attr[mention] == 0:
                    easy_hit1 += 1
            elif labels.intersection(set(cand)):
                not1_outf.write(f'{golden_mention2attr[mention]}\t{golden_mention2text[mention]}\t{mention}\t{labels}\t{mention2l2smap[mention]}\n')
            if labels.intersection(set(cand[:3])):
                hit3 += 1
                if golden_mention2attr[mention]==1:
                    hard_hit3 += 1
                elif golden_mention2attr[mention] == 0:
                    easy_hit3 += 1
            if labels.intersection(set(cand[:5])):
                hit5 += 1
                if golden_mention2attr[mention]==1:
                    hard_hit5 += 1
                elif golden_mention2attr[mention] == 0:
                    easy_hit5 += 1
            if labels.intersection(set(cand)):
                hitn += 1
                if golden_mention2attr[mention]==1:
                    hard_hitn += 1
                elif golden_mention2attr[mention] == 0:
                    easy_hitn += 1
            else:
                unc_outf.write(f'{golden_mention2attr[mention]}\t{golden_mention2text[mention]}\t{mention}\t{labels}\t{cand}\n')
        else:
            total_nil += 1
            if cand == [""]:
                nil_hit += 1
    unc_outf.close()
    not1_outf.close()
    if easy_total_notnil > 0:
        print(f"not nil: {easy_total_notnil} easy mentions; hit, @1: {round(easy_hit1/easy_total_notnil, 3)}, "
          f"@3: {round(easy_hit3/easy_total_notnil, 3)}, @5: {round(easy_hit5/easy_total_notnil, 3)}, "
              f"@n: {round(easy_hitn / easy_total_notnil, 3)}")
    if hard_total_notnil > 0:
        print(f"not nil: {hard_total_notnil} hard mentions; hit, @1: {round(hard_hit1 / hard_total_notnil, 3)}, "
          f"@3: {round(hard_hit3 / hard_total_notnil, 3)}, @5: {round(hard_hit5 / hard_total_notnil, 3)}, "
              f"@n: {round(hard_hitn / hard_total_notnil, 3)}")

    print(f"not nil: hit@1: {round(hit1 / total_notnil, 3)}, hit@3: {round(hit3 / total_notnil, 3)}, "
          f"hit@5: {round(hit5 / total_notnil, 3)}, hit@n: {hitn}/{total_notnil} = {round(hitn / total_notnil, 3)}")
    if total_nil > 0:
        print(f"nil: precision: {round(nil_hit/total_nil, 3)}")
    print(f'Missed linking mention {missed} / {total_notnil}')

def read_edl_tab(file):
    mention2id = {}
    mention2attr = {}
    mention2text = {}
    hard_or_not = False
    for line in open(file):
        line = line.strip().split('\t')
        if line[1] == "mention_id":
            if line[0] == 'HARD_OR_NOT':
                hard_or_not = True
            continue
        mention2id[line[3]] = line[4].lower()
        # For wiki data
        text = line[2]
        # # For lorelei data
        # text = line[2].split('|')[1] if '|' in line[2] else line[2]
        mention2text[line[3]] = text
        if hard_or_not:
            mention2attr[line[3]] = int(line[0])
        else:
            mention2attr[line[3]] = 1
    return mention2id, mention2attr, mention2text

def read_cand_tab(file):
    mention2cand = {}
    mention2l2smap = {}
    for line in open(file):
        line = line.strip("\n").split('\t')
        if line[0] == "token_span":
            continue
        mention2cand[line[0]] = line[4].lower().split(", ")
        if len(line) < 6:
            mention2l2smap[line[0]] = line[4]
        else:
            mention2l2smap[line[0]] = line[5]
    return mention2cand, mention2l2smap


if __name__ == '__main__':
    server = "/pool0/webserver/incoming"
    # server = "/mnt/macniece"
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--infile', type=str, default = f'{server}/experiment_tmp/EDL2019/data/our_output/om/google1_top1_map1_gtrans0_tsl0_spell0_inlink0_mtype0_clas0_bert0_wc0/candgen.tab')
    parser.add_argument('-g', '--edl_golden_file', type=str, default=f'{server}/experiment_tmp/EDL2019/data/gold/wikiname/om_edl_wiki.tab')
    args = parser.parse_args()
    args.uncovered_outfile = args.infile + '.uncovered'
    args.not1_outfile = args.infile + '.nothit1'
    print(args)

    golden_mention2id, golden_mention2attr, golden_mention2text = read_edl_tab(args.edl_golden_file)
    mention2cand, mention2l2smap = read_cand_tab(args.infile)
    print(f'Computing precision and outputting analyzed result to {args.uncovered_outfile} and {args.not1_outfile}...')
    compute_precision(golden_mention2id, golden_mention2attr, golden_mention2text, mention2cand, mention2l2smap, args.not1_outfile, args.uncovered_outfile)



