from tqdm import tqdm
import os
import argparse
import logging
from collections import defaultdict
import json


def candgen2tab(candgen_indir, candgen_outpath, **kwargs):
    g = open(candgen_outpath, 'w')
    g.write('token_span\tmention\tlink_id\tlink_title\tl2s\tl2s_map\n')
    for file_name in os.listdir(candgen_indir):
        file = file_name.split('.json')[0]
        index_file = open(os.path.join(candgen_indir, file_name), 'r', encoding='utf8')
        ner_data = ''.join(index_file.readlines())
        ner_data = ner_data.replace("\n", "")
        try:
            ner_data = json.loads(ner_data)
        except Exception as e:
            print(e, file_name)
        try:
            idx_list = ner_data["tokenOffsets"]
        except Exception as e:
            print(e)
        constituents = None
        for view in ner_data['views']:
            if view['viewName'] == 'CANDGEN':
                constituents = view['viewData'][0]['constituents']
                break
        if not constituents:
            continue
        for cons in constituents:
            label = cons['label']
            if label != 'NIL':
                # link_id, \
                link_title = label.split('|')[-1]
                link_id = label
            else:
                link_id, link_title = 'NIL', 'NIL'
            span_start, span_last = idx_list[cons['start']]['startCharOffset'], idx_list[cons['end']-1]['endCharOffset']

            span = f'{file}:{span_start}-{span_last-1}'
            token = cons['tokens']
            l2s_map = cons['labelScoreMap'] if 'labelScoreMap' in cons else {}
            l2s = []
            for l, s in l2s_map.items():
                l2s += [l.split('|')[1]]
                # l2s += [l.split('|')[0]]
                # l2s += [l + ': ' + str(round(s, 3))]
            l2s = ', '.join(l2s)
            g.write(f"{span}\t{token}\t{link_id}\t{link_title}\t{l2s}\t{l2s_map}\n")
    g.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--indir', type=str, default = "/pool0/webserver/incoming/experiment_tmp/EDL2019/data/chentse_output_ptm/tl_wiki")
    args = parser.parse_args()

    args.candgen_indir = os.path.join(args.indir, 'candgen')
    args.candgen_outpath = args.candgen_indir + '.tab'

    candgen2tab(**vars(args))
