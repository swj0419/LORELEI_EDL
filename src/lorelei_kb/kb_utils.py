def check_hit(eids, gold_eid):
    # TODO handle multiple gold_eids
    ans = any([eid == gold_eid for eid in eids])
    # if ans:
    #     logging.info("YAY!!")

    return ans


def get_wikititle(geonames, gold_eid):
    if "external_link" in geonames[gold_eid]:
        links = geonames[gold_eid]["external_link"].split("|")
        wiki_link = [link for link in links if "en.wikipedia" in link]
        if len(wiki_link) == 0:
            return None
        else:
            return wiki_link
    return None
