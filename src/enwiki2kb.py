from lorelei_kb.load_geonames_kb_v2 import GeoNamesLoader
from lorelei_kb.load_name_index_v2 import GeoNameIndex, AltNameIndex
# from candgen_v2_one_file_swj import CandGen
from utils.cheap_dicts import dictionary, mention2eid
from nilanalysis.utils import get_normalized_wikititle
from wiki_kb.title_normalizer_v2 import TitleNormalizer
from utils.inlinks_v2 import Inlinks
from utils.constants import NULL_TITLE


def get_word_cands(surf, geonames, altname_index, geoname_index):
    ans = []
    MAXCANDS = 500
    if surf in altname_index.word2ent:
        cands = altname_index.word2ent[surf]
        # logging.info("#cands altname %d for %s", len(cands), surf)
        if len(cands) < MAXCANDS:
            ans += cands
        # else:
            # logging.info("skipping cands for %s", surf)
    if surf in geoname_index.word2ent:
        cands = geoname_index.word2ent[surf]
        # logging.info("#cands geoname %d for %s", len(cands), surf)
        if len(cands) < MAXCANDS:
            ans += cands
        # else:
            # logging.info("skipping cands for %s", surf)
    ans = list(set(ans))
    # if len(ans) > 500:
        # logging.info("warning: surf %s has %d cands", surf, len(ans))
    return ans

def get_l2s_map(eids, geonames, normalizer, inlinks):
    Z = 1
    l2s_map = {}
    for eid in eids:

        try:
            title = get_normalized_wikititle(geonames, normalizer, eid)
        except Exception as e:
            print(e, eid)  # , args
            continue

        if title == NULL_TITLE:
            title = geonames[eid]["name"]
        key = "|".join([eid, title])
        # TODO add eids w/o wikititles

        if title not in inlinks:
            # logging.info("not in inlinks %s, keeping []", title)
            tmp_inlinks = []
        else:
            tmp_inlinks = inlinks[title]

        l2s_map[key] = len(tmp_inlinks) + 1
        Z += len(tmp_inlinks)
        # if Z == 0:
        #     Z = 1
    for k in l2s_map:
        l2s_map[k] /= Z

    return l2s_map


def find_max_kbid(cands, geonames, normalizer):
    l2s_map = get_l2s_map(cands, geonames, normalizer, inlinks)


    if len(l2s_map) == 0:
        prior_argmax = "NIL"
        prior_max = 1.0
    else:
        all_argmaxes = [cand for cand, score in l2s_map.items() if score == max(l2s_map.values())]
        prior_argmax = all_argmaxes[0]
        prior_max = l2s_map[all_argmaxes[0]]
    return prior_argmax, prior_max


def find_kbid(wiki_title, lang, geoname_index, altname_index, geonames, normalizer, cheap_dict, inlinks):
    if wiki_title in mention2eid[lang]:
        return mention2eid[lang][wiki_title]

    if len(wiki_title) < 2:
        # logging.info("too short a query string")
        return "NIL"
    if wiki_title in cheap_dict:
        # logging.info("found %s in dictionary!", wiki_title)
        wiki_title = cheap_dict[wiki_title]

    wiki_title = wiki_title.lower()

    cands = []
    if wiki_title in geoname_index.name2ent:
        cands += geoname_index.name2ent[wiki_title]
    if wiki_title in altname_index.name2ent:
        cands += altname_index.name2ent[wiki_title]

    if len(cands):
        kbid, prob = find_max_kbid(cands, geonames, normalizer)
        print(kbid)
        return kbid.split('|')[0]
    else:
        stop_words = ['district', 'city', 'province', 'of', 'state']
        for stop_word in stop_words:
            wiki_title = wiki_title.replace(stop_word, '')
        wiki_title = wiki_title.replace('  ', ' ')

        new_wiki = ""
        for token in wiki_title.split():
            if len(token):
                new_wiki += token

        if new_wiki in geoname_index.name2ent:
            cands += geoname_index.name2ent[new_wiki]
        if new_wiki in altname_index.name2ent:
            cands += altname_index.name2ent[new_wiki]

        if len(cands):
            kbid, prob = find_max_kbid(cands, geonames, normalizer)
            print(kbid)
            return kbid.split('|')[0]
        else:
            return 'NIL'


if __name__ == '__main__':
    ilcode = '11'
    ngramorders = "2,3,4,5"
    geoname_index = GeoNameIndex(ilcode=ilcode, ngramorders=ngramorders, overwrite=False)
    altname_index = AltNameIndex(ilcode=ilcode, ngramorders=ngramorders, overwrite=False)
    geonames = GeoNamesLoader(ilcode=ilcode)
    normalizer = TitleNormalizer()

    if ilcode == '11':
        lang = 'or'
    else:
        lang = 'ilo'
    cheap_dict = dictionary[lang]
    inlinks = Inlinks().inlinks

    infile_name = '/shared/experiments/xyu71/lorelei2017/illinois-cross-lingual-wikifier/output_fxy/il11.tab'
    outfile_name = '/shared/corpora/corporaWeb/lorelei/evaluation-2019/il11/edl_output/cp2/sub3/il11_en_rule.tab'
    # outfile_name = '/shared/experiments/xyu71/lorelei2017/illinois-cross-lingual-wikifier/output_fxy/try1_il11_3'

    infile = open(infile_name, 'r', encoding='utf8')
    max_nil = 0
    for line in infile:
        if line.strip().split()[-1][:3] == 'NIL':
            nil_num = int(line.strip().split()[-1][3:])
            if nil_num > max_nil:
                max_nil = nil_num
    infile.close()

    infile = open(infile_name, 'r', encoding='utf8')
    outfile = open(outfile_name, 'w', encoding='utf8')

    nil_dict = {}

    for line in infile:
        tmp_output = ['Penn']
        tmp_data = line.strip().split('\t')

        file_name = tmp_data[3].split(':')[0]

        tmp_output.append('%s-%s' % (file_name, tmp_data[1]))
        tmp_output += [tmp_data[2], tmp_data[3]]

        if tmp_data[-1][:3] == 'NIL':
            wiki_title = tmp_data[2]
        else:
            wiki_title = tmp_data[-1]

        kbid = find_kbid(wiki_title, lang, geoname_index, altname_index,
                         geonames, normalizer, cheap_dict, inlinks)

        if kbid == 'NIL':
            wiki_title = wiki_title.replace('_', ' ')
            kbid = find_kbid(wiki_title, lang, geoname_index, altname_index,
                             geonames, normalizer, cheap_dict, inlinks)

        if kbid == 'NIL':
            kbid = tmp_data[-1]

            if 'NIL' != tmp_data[-1][:3]:
                if tmp_data[-1] in nil_dict:
                    kbid = nil_dict[tmp_data[-1]]
                else:
                    kbid = 'NIL%05d' % (max_nil+1)
                    nil_dict[tmp_data[-1]] = kbid
                    max_nil += 1

        tmp_output.append(kbid)
        tmp_output += [tmp_data[5], 'NAM', '1.0']
        print(tmp_output)
        outfile.write('\t'.join(tmp_output) + '\n')

    infile.close()
    outfile.close()
