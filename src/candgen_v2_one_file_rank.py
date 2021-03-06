import argparse, copy, json, os, sys, re
from ccg_nlpy.core.text_annotation import TextAnnotation
from ccg_nlpy.core.view import View
from collections import Counter, defaultdict
# from spellchecker import SpellChecker
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from pytorch_pretrained_bert import BertTokenizer, BertModel
import logging
logging.basicConfig(level=logging.INFO)
import operator
from multiprocessing import Pool
from nltk.tokenize import MWETokenizer, sent_tokenize
import torch
import pickle
import wikipedia
from bs4 import BeautifulSoup
import requests
import pymongo
from tqdm import tqdm
import sys

from utils.google_search import query2enwiki, query2gmap_api, or2hindi
from utils.cheap_dicts import dictionary
from utils.language_utils import correct_surface, remove_suffix
from utils.inlinks_v2 import Inlinks
from utils.translit_gen_util import init_model, phrase_translit
from utils.mongo_backed_dict import MongoBackedDict
from wiki_kb.candidate_gen_v2 import CandidateGenerator
from wiki_kb.title_normalizer_v2 import TitleNormalizer
import utils.constants as K




feature_map = ["P","A"]
# logging.basicConfig(format=':%(levelname)s: %(message)s', level=logging.INFO)
logging.basicConfig(format=':%(levelname)s: %(message)s', level=logging.DEBUG)


def softmax(x):
    """Compute softmax values for each sets of scores in x."""
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)  # only difference


def mask_sents(surface, text):
    sents = sent_tokenize(text)
    masked_sents = []
    for sent in sents:
        pre_pos = 0
        while surface in sent[pre_pos:]:
           low = pre_pos + sent[pre_pos:].index(surface)
           high = low + len(surface)
           masked_sents.append('[CLS] ' + sent[:low] + ' [MASK] ' + sent[high:] + ' [SEP]')
           pre_pos = high + 1
    return masked_sents


def s2maskedvec(masked_sents):
    vecs = []
    for sent in masked_sents:
        tokenized_text = tokenizer.tokenize(sent)
        pos = tokenized_text.index('[MASK]')
        indexed_tokens = tokenizer.convert_tokens_to_ids(tokenized_text)
        # Convert token to vocabulary indices
        indexed_tokens = tokenizer.convert_tokens_to_ids(tokenized_text)

        # Convert inputs to PyTorch tensors
        tokens_tensor = torch.tensor([indexed_tokens])

        # Predict hidden states features for each layer
        with torch.no_grad():
            encoded_layers, _ = model(tokens_tensor)
            vecs.append(encoded_layers[11][0].numpy()[pos])
    m_vec = np.mean(vecs, axis=0)
    return m_vec


def clean_query(query_str):
    if query_str[-1] == ",":
        query_str = query_str[:-1]
    f = re.compile('(#|\(|\)|@)')
    query_str = f.sub(' ', query_str)
    query_str = re.sub('\s+', ' ', query_str).strip()
    return query_str.lower()


def get_wiki_summary(url):
    try:
        res = requests.get(url, verify=True)
        soup = BeautifulSoup(res.text, 'html.parser')
        paragraphs = soup.select("p")
        smr = '\n'.join([para.text for para in paragraphs[0:5]])
        try:
            entity_wiki = str(paragraphs[0]).split("</b>")[0].split("<b>")[1]
        except:
            entity_wiki = str(paragraphs[1]).split("</b>")[0].split("<b>")[1]
    except Exception as e:
        smr = ''
        entity_wiki = " "
    return smr, entity_wiki


def load_tsl_concept(concept_file, translit_data):
    concept_pair = open(concept_file, 'r', encoding='utf8')
    raw_concepts = [line.strip().split('\t') for line in concept_pair]
    raw_concepts = sorted(raw_concepts, reverse=True, key=lambda x: len(x[0]))
    concept_pair.close()
    translition = {}
    translit_data = open(translit_data, 'r', encoding='utf8')
    for line in translit_data:
        try:
            tmp = line.strip().split('\t')
            translition[tmp[0]] = tmp[1]
        except:
            pass
    return raw_concepts, translition


class CandGen:
    def __init__(self, lang=None, year=None,
                 inlinks=None,
                 tsl=None,
                 wiki_cg=None,
                 tsl_concept_pair=None,
                 tsl_translit_dict=None,
                 spellchecker=None):
        self.init_counters()
        self.lang = lang
        self.year = year
        self.inlinks = inlinks
        self.spellchecker = spellchecker
        self.cheap_dict = dictionary[lang] if lang in dictionary else {}
        self.translit_model = tsl
        self.concept_pair, self.translit_dict = tsl_concept_pair, tsl_translit_dict
        self.wiki_cg = wiki_cg
        self.en_normalizer = TitleNormalizer(lang="en")


    def load_or_checker(self):
        or_spell = None
        # or_spell = SpellChecker(language=None, distance=2)
        or_spell.word_frequency.load_dictionary('spellchecker/or_entity_dictionary.gz')
        return or_spell

    def load_kb(self, kbdir):
        self.m = MongoBackedDict(dbname='data/enwiki/idmap/enwiki-20190701.id2t.t2id')
        self.en_t2id = MongoBackedDict(dbname=f"data/enwiki/idmap/enwiki-20190701.id2t.t2id")
        self.en_id2t = MongoBackedDict(dbname=f"data/enwiki/idmap/enwiki-20190701.id2t.id2t")
        en_id2t_filepath = os.path.join(kbdir, 'enwiki', 'idmap', f'enwiki-{self.year}.id2t')
        self.fr2entitles = MongoBackedDict(dbname=f"{self.lang}2entitles")
        fr2entitles_filepath = os.path.join(kbdir, f'{self.lang}wiki', 'idmap', f'fr2entitles')
        self.t2id = MongoBackedDict(dbname=f"{self.lang}_t2id")

        if self.en_t2id.size() == 0 or self.en_id2t.size() == 0:
            logging.info(f'Loading en t2id and id2t...')
            en_id2t = []
            ent2id = defaultdict(list)
            for line in tqdm(open(en_id2t_filepath)):
                parts = line.strip().split("\t")
                if len(parts) != 3:
                    logging.info("bad line %s", line)
                    continue
                page_id, page_title, is_redirect = parts
                key = page_title.replace('_', ' ').lower()
                ent2id[key].append(page_id)
                en_id2t.append({'key': page_id, 'value':
                    {'page_id': page_id, 'name':page_title, 'searchname': key}, 'redirect':is_redirect})
            ent2id_list = []
            for k, v in ent2id.items():
                ent2id_list.append({'key': k, 'value': v})
            logging.info("inserting %d entries into english t2id", len(ent2id_list))
            self.en_t2id.cll.insert_many(ent2id_list)
            self.en_t2id.cll.create_index([("key", pymongo.HASHED)])

            logging.info("inserting %d entries into english id2t", len(en_id2t))
            self.en_id2t.cll.insert_many(en_id2t)
            self.en_id2t.cll.create_index([("key", pymongo.HASHED)])

        if self.fr2entitles.size() == 0:
            logging.info(f'Loading fr2entitles and {self.lang} t2id...')
            fr2en = []
            t2id = []
            f = open(fr2entitles_filepath)
            for idx, l in enumerate(f):
                parts = l.strip().split("\t")
                if len(parts) != 2:
                    logging.info("error on line %d %s", idx, parts)
                    continue
                frtitle, entitle = parts
                key = frtitle.replace('_', ' ').lower()
                enkey = entitle.replace('_', ' ').lower()
                fr2en.append({"key": key, "value": {'frtitle': frtitle, 'entitle': entitle, 'enkey':enkey}})
                t2id.append({"key": key, "value": self.en_t2id[enkey]})
            logging.info(f"inserting %d entries into {self.lang}2entitles", len(fr2en))
            self.fr2entitles.cll.insert_many(fr2en)
            self.fr2entitles.cll.create_index([("key", pymongo.HASHED)])
            logging.info(f"inserting %d entries into {self.lang} t2id", len(t2id))
            self.t2id.cll.insert_many(t2id)
            self.t2id.cll.create_index([("key", pymongo.HASHED)])

    def extract_cands(self, cands):
        wiki_titles, wids, wid_cprobs = [], [], []
        for cand in cands:
            wikititle, p_t_given_s, p_s_given_t = cand.en_title, cand.p_t_given_s, cand.p_s_given_t
            nrm_title = self.en_normalizer.normalize(wikititle)
            if nrm_title == K.NULL_TITLE:  # REMOVED or nrm_title not in en_normalizer.title2id
                logging.info("bad cand %s nrm=%s", wikititle, nrm_title)
                continue
            wiki_id = self.en_normalizer.title2id[nrm_title]
            # if wiki_id is none
            if wiki_id is None:
                wiki_id = self.en_normalizer.title2id[wikititle]
                if wiki_id is None:
                    continue
                wiki_titles.append(wikititle)
                wids.append(wiki_id)
                wid_cprobs.append(p_t_given_s)
                continue
            wiki_titles.append(nrm_title)
            wids.append(wiki_id)
            wid_cprobs.append(p_t_given_s)
        return wiki_titles, wids, wid_cprobs

    def init_counters(self):
        self.eng_words = 0
        self.nils = 0
        self.no_wikis = 0
        self.trans_hits = 0
        self.total, self.total_hits, self.prior_correct, self.nil_correct = 0, 0, 0, 0


    def init_l2s_map(self, eids, args = None):
        l2s_map = {}
        for eid in eids:
            title = self.en_id2t[eid]
            # print(eid, title)
            # if eid is None:
            #     print("eid none", eid)
            # if title is None:
            #     print("title none", title)
            try:
                key = "|".join([eid, title])
            except:
                print("eid", eid, title)
                print("end")
                continue
            if not key in l2s_map:
            # if title not in self.inlinks:
            #     logging.info("not in inlinks %s, keeping []", title)
            #     inlinks = []
            # else:
            #     inlinks = self.inlinks[title]
                l2s_map[key] = 100
        # for k in l2s_map:
        #     if args.inlink:
        #         l2s_map[k] /= Z
        #     else:
        #         l2s_map[k] = 1
        return l2s_map

    def cross_check_score(self, l2s_map, eids):
        freq = dict(Counter(eids))
        for cand, v in l2s_map.items():
            cand_eid = cand.split("|")[0]
            l2s_map[cand] = l2s_map[cand] * (3 ** freq[cand_eid]) if cand_eid in eids else l2s_map[cand] * 0.1
        return l2s_map

    def wiki_contain_score(self, l2s_map, query_str, args):
        for cand in l2s_map.keys():
            cand_name = cand.split("|")[1]
            score = 1
            if cand_name in args.eid2wikisummary:
                summary = args.eid2wikisummary[cand_name]
            else:
                try:
                    summary = wikipedia.summary(cand_name)
                    args.eid2wikisummary.cll.insert_one({"key": cand_name, "value": summary})
                except:
                    args.eid2wikisummary.cll.insert_one({"key": cand_name, "value": ""})
                    summary = ""
            # check summary contains the query
            score = score * 2 if query_str + "," in summary else score * 1
            l2s_map[cand] *= score
        return l2s_map

    def bert_score(self, l2smap, query_emb, l2s_map, args):
        cand2sim = {}
        max_cand = None
        max_sim = -1000
        for cand in l2smap:
            cand_eid = cand.split("|")[0]
            cand_name = cand.split('|')[1]
            # request summary
            if cand_eid in args.eid2wikisummary:
                summary = args.eid2wikisummary[cand_eid]
                entity_wiki = args.eid2wikisummary_entity[cand_eid]
            else:
                summary, entity_wiki = get_wiki_summary(f"https://en.wikipedia.org/?curid={cand_eid}")
                args.eid2wikisummary.cll.insert_one({"key": cand_eid, "value": summary})
                args.eid2wikisummary_entity.cll.insert_one({"key": cand_eid, "value": entity_wiki})
            summary = summary.lower()
            # bert
            try:
                cand_name = entity_wiki
            except:
                print("error")
            if cand_name in summary:
                cand_emb = s2maskedvec(mask_sents(cand_name, summary))
                sim = cosine_similarity([cand_emb], [query_emb])[0][0]
                cand2sim[cand] = sim
                if sim > max_sim:
                    max_sim = sim
                    max_cand = cand
            elif cand_name.lower() in summary:
                cand_emb = s2maskedvec(mask_sents(cand_name.lower(), summary))
                sim = cosine_similarity([cand_emb], [query_emb])[0][0]
                cand2sim[cand] = sim
                if sim > max_sim:
                    max_sim = sim
                    max_cand = cand
            else:
                logging.info("not in summary", cand_name)
                continue

        if len(cand2sim) > 1:
            l2s_map[max_cand] *= 1.5
        # logging.info("cand2sim", cand2sim)
        return l2s_map

    def get_context(self, query_str, text, k = 10):
        if query_str in text:
            tokenizer = MWETokenizer()
            query_str_tokens = tuple(query_str.split())
            query_str_dashed = "_".join(query_str_tokens)
            tokenizer.add_mwe(query_str_tokens)
            text_token = tokenizer.tokenize(text.split())
            try:
                t_start = text_token.index(query_str_dashed)
            except:
                return None, None, None
            t_end = t_start + 1
            start_index = max(t_start - k, 0)
            end_index = min(t_end + k, len(text_token))
            text_token_query = text_token[start_index:t_start] + text_token[t_end + 1:end_index]
            context = " ".join(text_token_query)
            context_mention = text_token[start_index:t_start] + [query_str] + text_token[t_end + 1:end_index]
            context_mention = " ".join(context_mention)
            return context, text_token_query, context_mention
        else:
            return None, None, None

    def get_l2s_map(self, eids_google, eids_google_maps, eids_wikicg, eids_total, ner_type, query_str, text, args):
        l2s_map = self.init_l2s_map(eids_total, args=args)
        # check if generated cadidates
        if len(l2s_map) == 0 or len(l2s_map) == 1:
            return l2s_map

        l2s_map = self.cross_check_score(l2s_map, eids_google + eids_google_maps + eids_wikicg)


        #update score
        for cand in l2s_map.copy().keys():
            cand_eid = cand.split("|")[0]
            score = 1
            l2s_map[cand] *= score

        logging.info("Processed looping candidates")

        # get context:
        if args.bert:
            context, context_tokens, context_mention = self.get_context(query_str, text, k=10)

        # check context bert
        if args.bert and context is not None:
            query_emb = s2maskedvec(mask_sents(query_str, context_mention))
            l2s_map = self.bert_score(l2s_map, query_emb, l2s_map, args)
            logging.info("Processed candidates bert")

        # Normalize
        sum_s = sum(list(l2s_map.values()))
        for can, s in l2s_map.items():
            l2s_map[can] = s/sum_s
        return l2s_map

    def correct_surf(self,token):
        region_list = ["district of", "district", "city of", "state of", "province of", "division", "city", "valley","province"]
        token = token.lower()
        for i in region_list:
            token = token.replace(i, "").strip()
        return token

    def default_type(self, l2s_map, max_cand):
        l2s_map = dict(sorted(l2s_map.items(), key=operator.itemgetter(1), reverse=True))
        # del l2s_map[max_cand]
        max_cand_name, max_cand_eid = max_cand.split("|")[1], max_cand.split("|")[0]
        max_cand_name = self.correct_surf(max_cand_name)
        if "feature_class" in self.en_id2t[max_cand_eid]:
            eid_type = self.en_id2t[max_cand_eid]["feature_class"]
        else:
            return max_cand
        capital_features = ["PPLA", "PPLA2", "PPLC"]
        district_set = pickle.load(open(
            f"/shared/experiments/xyu71/lorelei2017/src/lorelei_kb/IL11-12-District/dis_il{self.lang}.pickle",
            "rb"))
        if "feature_code" in self.en_id2t[max_cand_eid]:
            eid_fcode = self.en_id2t[max_cand_eid]["feature_code"][2:]
        else:
            eid_fcode = ""

        if self.lang == "ilo":
            if eid_fcode not in capital_features:
                if max_cand_name in district_set and eid_type == "P":
                    for k, v in l2s_map.items():
                        k_name, k_id = self.correct_surf(k.split("|")[1]), k.split("|")[0]
                        if "feature_class" in self.en_id2t[k_id]:
                            if k_name == max_cand_name and self.en_id2t[k_id]["feature_class"] == "A":
                                return k
        elif self.lang == "or":
            if eid_type == "P":
                for k, v in l2s_map.items():
                    k_name, k_id = self.correct_surf(k.split("|")[1]), k.split("|")[0]
                    if "feature_class" in self.en_id2t[k_id]:
                        if k_name == max_cand_name and self.en_id2t[k_id]["feature_class"] == "A":
                            return k
        return max_cand

    def get_maxes_l2s_map(self, l2s_map):
        # pick max
        if len(l2s_map) == 0:
            max_cand, max_score = "NIL", 1.0
        else:
            maxes_l2s_map = {cand: score for cand, score in l2s_map.items() if score == max(l2s_map.values())}
            max_cand = list(maxes_l2s_map.keys())[0]
            max_score = l2s_map[max_cand]
        return max_cand, max_score

    def compute_hits_for_ta(self, docta, outfile, only_nils=False, args=None):
        if not args.overwrite:
            if os.path.exists(outfile):
                logging.error("file %s exists ... skipping", outfile)
                return
        try:
            ner_view = docta.get_view("NER_CONLL")
        except:
            return
        candgen_view_json = copy.deepcopy(ner_view.as_json)
        text = docta.text
        predict_mode = True

        if "constituents" not in candgen_view_json["viewData"][0]:
            return
        for idx, cons in enumerate(candgen_view_json["viewData"][0]["constituents"]):
            self.total += 1
            query_str = cons["tokens"]
            # query_str = clean_query(query_str)
            ner_type = cons["label"]

            eids_google, eids_wikicg, eids_google_maps = [], [], []

            # swj query
            #
            eids_google, eids_wikicg, eids_google_maps = self.get_lorelei_candidates(query_str, ner_type=ner_type, args=args)
            eids_total =  eids_google + eids_google_maps + eids_wikicg

            # for eid in eids_wikicg:
            #     if eid is None:
            #         print("error: ", eid, query_str)
            #         1/0

            logging.info("got %d candidates for query:%s", len(set(eids_total)), query_str)


            l2s_map = self.get_l2s_map(eids_google, eids_google_maps, eids_wikicg, eids_total, ner_type=ner_type, query_str=query_str, text=text, args=args)

            logging.info(f"got {len(l2s_map)} candidates after ranking for {query_str}: {l2s_map}")
            max_cand, max_score = self.get_maxes_l2s_map(l2s_map)

            if len(l2s_map) > 0 and args.lang in ["ilo", "or"]:
                max_cand_default = self.default_type(l2s_map, max_cand)
                if max_cand_default != max_cand:
                    max_score = 1.0
                    max_cand = max_cand_default
                logging.info(f"got candidate after default")

            if len(l2s_map) > 0:
                cons["labelScoreMap"] = l2s_map
            cons["label"] = max_cand
            cons["score"] = max_score

        candgen_view_json["viewName"] = "CANDGEN"
        candgen_view = View(candgen_view_json, docta.get_tokens)
        docta.view_dictionary["CANDGEN"] = candgen_view
        docta_json = docta.as_json
        with open(outfile, 'w', encoding='utf-8') as f:
            json.dump(docta_json, f, ensure_ascii=False, indent=True)
        # json.dump(docta_json, open(outfile, "w"), indent=True)
        self.report(predict_mode=predict_mode)

    def get_lorelei_candidates(self, query_str, romanized_query_str=None, ner_type=None, args=None):
        # SKB+SG
        desuf_query_str = remove_suffix(query_str, self.lang)
        dot_query_str_list = correct_surface(query_str, self.lang)
        desuf_dot_query_str_list = correct_surface(desuf_query_str, self.lang)

        if args.wikicg:
            wiki_titles, wids, wid_cprobs = self.extract_cands(self.wiki_cg.get_candidates(surface=query_str))
            eids_wikicg = wids
        else:
            eids_wikicg = []

        # SG suffix dot suffix+dot
        if args.google == 1:
            eids_google, g_wikititles = self._get_candidates_google(query_str, top_num=args.google_top)
            # if not eids_google:
            for i in [desuf_query_str] + dot_query_str_list + desuf_dot_query_str_list:
                e, t = self._get_candidates_google(i, top_num=args.google_top)
                eids_google += e
                g_wikititles += t
            eids_google = list(set(eids_google))
        else:
            eids_google = []

        # logging.info("got %d candidates for query:%s from google", len(eids_google), query_str)

        eids_google_maps = []
        if ner_type in ['GPE', 'LOC'] and args.google_map:
            google_map_name = query2gmap_api(query_str, self.lang)
            eids_google_maps += self._exact_match_kb(google_map_name, args)
            eids_google_maps += self._get_candidates_google(google_map_name, lang='en', top_num=args.google_top)[0]
            # if not eids_google_maps:
            google_map_name_suf = query2gmap_api(desuf_query_str, self.lang)
            google_map_name_dot = [query2gmap_api(k, self.lang) for k in dot_query_str_list]
            google_map_name_suf_dot = [query2gmap_api(k, self.lang) for k in desuf_dot_query_str_list]
            eids_google_maps += self._exact_match_kb(google_map_name_suf, args)
            eids_google_maps += self._get_candidates_google(google_map_name_suf, lang='en', top_num=args.google_top)[0]

            eids_google_maps += [h for k in google_map_name_dot for h in self._exact_match_kb(k, args)]
            eids_google_maps += [h for k in google_map_name_dot for h in self._get_candidates_google(k, lang='en', top_num=args.google_top)[0]]

            eids_google_maps += [h for k in google_map_name_suf_dot for h in self._exact_match_kb(k, args)]
            eids_google_maps += [h for k in google_map_name_suf_dot for h in self._get_candidates_google(k, lang='en', top_num=args.google_top)[0]]
        eids_google_maps = list(set(eids_google_maps))
        # logging.info("got %d candidates for query:%s from google map", len(set(eids_google_maps)), query_str)

        return eids_google, eids_wikicg, eids_google_maps

    def _get_candidates_google(self, surface, top_num=1, lang=None):
        eids = []
        wikititles = []
        if surface is None or len(surface) < 2:
            return eids, wikititles
        if surface in self.cheap_dict:
            surface = self.cheap_dict[surface]
        if lang is None:
            lang = self.lang
        en_surfaces = query2enwiki(surface, lang)[:top_num]
        wikititles = []
        for ent in en_surfaces:
            ent_normalize = ent.replace(" ", "_")
            wikititles.append(ent_normalize)
            if ent_normalize not in self.en_t2id:
                print("bad title")
                continue
            else:
                eids.append(self.en_t2id[ent_normalize])
        return eids, wikititles

    def _exact_match_kb(self, surface, args):
        eids = []
        if surface is None:
            return eids
        # surface = surface.lower()
        # logging.info("===> query string:%s len:%d", surface, len(surface))
        if len(surface) < 2:
            # logging.info("too short a query string")
            return []
        # Exact Match
        eids += self.get_phrase_cands(surface)
        return eids

    def get_phrase_cands(self, surf):
        surf = surf.lower()
        ans = []
        if surf in self.t2id:
            cands = self.t2id[surf]
            # logging.info("#phrase cands geoname %d for %s", len(cands), surf)
            ans += cands
        if surf in self.en_t2id:
            cands = self.en_t2id[surf]
            ans += cands
        return ans

    def report(self, predict_mode):
        if not predict_mode:
            logging.info("total_hits %d/%d=%.3f", self.total_hits, self.total, self.total_hits / self.total)
            logging.info("prior correct %d/%d=%.3f", self.prior_correct, self.total, self.prior_correct / self.total)
            logging.info("nil correct %d/%d=%.3f", self.nil_correct, self.total, self.nil_correct / self.total)
        else:
            logging.info("saw total %d", self.total)

    def get_romanized(self, cons, rom_view):
        overlap_cons = rom_view.get_overlapping_constituents(cons['start'], cons['end'])
        romanized = " ".join([c["label"] for c in overlap_cons[1:-1]])
        logging.info("str:%s romanized:%s", cons["tokens"], romanized)
        return romanized


if __name__ == '__main__':
    PARSER = argparse.ArgumentParser(description='Short sample app')
    PARSER.add_argument('--kbdir', default="/shared/EDL19/wiki_outdir", type=str)
    PARSER.add_argument('--goldfile', default="", type=str)
    PARSER.add_argument('--nolog', action="store_true")
    PARSER.add_argument('--lang', default='ta', type=str)
    PARSER.add_argument('--year', default="20190701")
    PARSER.add_argument('--pool', default=1, type=int)
    PARSER.add_argument('--indir', default='/pool0/webserver/incoming/experiment_tmp/EDL2019/data/input/ta')
    PARSER.add_argument('--outdir', default='/pool0/webserver/incoming/experiment_tmp/EDL2019/data/ptm/try')
    PARSER.add_argument('--overwrite', default=1, type=int)

    # For Cand gen
    PARSER.add_argument('--google', default=0, type=int)
    PARSER.add_argument('--google_top', default=3, type=int)
    PARSER.add_argument('--google_map', default=0, type=int)
    PARSER.add_argument('--g_trans', default=0, type=int)
    PARSER.add_argument('--tsl', default=0, type=int)
    PARSER.add_argument('--or2hin', default=0, type=int)
    PARSER.add_argument('--spell', default=0, type=int)
    PARSER.add_argument('--wikicg', default=1, type=int) # use P(t|m)
    # For Ranking
    PARSER.add_argument('--inlink', default=0, type=int)
    PARSER.add_argument('--mtype', default=0, type=int)
    PARSER.add_argument('--bert', default=0, type=int)
    PARSER.add_argument('--wiki_contain', default=0, type=int)

    args = PARSER.parse_args()

    logging.info(args)

    if args.indir is None or args.outdir is None:
        logging.info("require --indir and --outdir")
        sys.exit(0)
    else:
        logging.info(f'Generating candidates using {args.indir} and {args.outdir}')

    if args.lang not in ['si', 'or']:
        args.tsl = 0
    if args.lang not in ['or']:
        args.g_trans = 0
        args.or2hin = 0
        args.spell = 0

    if args.nolog:
        logging.disable(logging.INFO)

    if not args.lang:
        sys.exit('No language specified.')

    if args.inlink:
        inlinks = Inlinks()
        logging.info("inlinks loaded %d", inlinks.inlinks.size())
        inlinks = inlinks.inlinks
    else:
        inlinks = None

    if args.tsl:
        tsl = init_model('./hma_translit/model/or/or_data.vocab',
                   './hma_translit/model/or/or.model')
        tsl_concept_pair, tsl_translit_dict = load_tsl_concept('./hma_translit/model/or/concept_pairs.txt',
                          './hma_translit/model/or/translit_data.txt')
    else:
        tsl = None

    wiki_cg = CandidateGenerator(K=5,
                                 kbfile=None,
                                 lang=args.lang,
                                 use_eng=False,
                                 fallback=True)
    wiki_cg.load_probs("data/{}wiki/probmap/{}wiki-{}".format(args.lang, args.lang, args.year))

    # load bert
    if args.bert:
        if args.lang == 'ilo':
            tokenizer = BertTokenizer.from_pretraiBertModel.from_pretrainedned('/shared/experiments/xyu71/lorelei2017/src/bert/il11_370kSteps')
            model = BertModel.from_pretrained('/shared/experiments/xyu71/lorelei2017/src/bert/il11_370kSteps', from_tf=False)
        elif args.lang == 'or':
            tokenizer = BertTokenizer.from_pretrained('/shared/experiments/xyu71/lorelei2017/src/bert/il12_370kSteps')
            model = BertModel.from_pretrained('/shared/experiments/xyu71/lorelei2017/src/bert/il12_370kSteps', from_tf=False)
        else:
            tokenizer = BertTokenizer.from_pretrained('bert-base-multilingual-cased')
            model = BertModel.from_pretrained('/pool0/webserver/incoming/experiment_tmp/EDL2019/src/bert/multilingual_bert')


    lang = args.lang

    # Wiki load in ============================Important===========================
    cg = CandGen(lang=args.lang, year=args.year, inlinks=inlinks, tsl=tsl, wiki_cg = wiki_cg)
    cg.load_kb(args.kbdir)

    # Mongodb
    args.eid2wikisummary = MongoBackedDict(dbname="eid2wikisummary")
    args.eid2wikisummary_entity = MongoBackedDict(dbname="eid2wikisummary_entity")

    # args.mention2url_entity = MongoBackedDict(dbname=f"mention2url_entity_{args.lang}")
    # args.mention2gmap_entity = MongoBackedDict(dbname=f"mention2gmap_entity_{args.lang}")

    file_names = os.listdir(args.indir)
    infile_outfile_list = [(os.path.join(args.indir, n), os.path.join(args.outdir, n + '.json')) for n in file_names]

    def process_file(file):
        infile = os.path.join(args.indir, file)
        outfile = os.path.join(args.outdir, file + '.json')
        logging.info(f'Processing {infile} and output to {outfile}')
        try:
            docta = TextAnnotation(json_str=open(infile, encoding='utf8', errors='ignore').read())
        except:
            return
        docid = infile.split("/")[-1]
        logging.info("processing docid %s", docid)
        cg.compute_hits_for_ta(docta=docta, outfile=outfile, args=args)

    if args.pool > 1:
        p = Pool(args.pool)
        p.map(process_file, file_names)
        p.close()
    else:
        for file in file_names:
            process_file(file)
