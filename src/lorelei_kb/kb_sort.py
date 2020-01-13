import argparse
import codecs
import time

import goslate
from googletrans import Translator

from lorelei_kb.load_geonames_kb_v2 import GeoNamesLoader

if __name__ == '__main__':
    # print(inpath+"\t"+outpath)
    parser = argparse.ArgumentParser(
        description='kb_pipline parser.\nThe output format might look like these:\nDefault: counts <tab> surface <tab> kbid\nTranslate Only: counts <tab> surface <tab> translation <tab> kbid\nGeoname Only: counts <tab> surface <tab> kbid <tab> kbname\nBoth Translate and Geoname: counts <tab> surface <tab> translation <tab> kbid <tab> kbname')
    parser.add_argument('inpath', action="store", help='Input file path')
    parser.add_argument('outpath', action="store", help='Output file path')
    parser.add_argument('trg', action="store", help='Target language')
    parser.add_argument('--ilcode', action="store", required=True, help='9 or 10')
    parser.add_argument('--src', action="store", required=False, help='Source language')
    parser.add_argument('--options', default="g", action="store", required=False,
                        help='Two options, t:translate using Google Translate; g:load geoname mapping.Default with option c')
    parser.add_argument('--format', default="raw", action="store", required=False,
                        help='Format of your file. Default raw tab file. Support raw:raw tab,th:three basic column, ts: translated file, geo:geonamed file')
    parser.add_argument('--thresh', default=0, action="store", required=False,
                        help='Threshold for translation. Only translate words whose frequency is greater than or equal to the threshold')
    parser.add_argument('--trans', default="google", action="store", required=False,
                        help='Translation method. Default using google. Support google and goslate')
    args = vars(parser.parse_args())

    inpath = args['inpath']
    outpath = args['outpath']
    inlang = args['src']
    outlang = args['trg']
    options = args['options']
    ilcode = args["ilcode"]
    format = args['format']
    threshold = int(args['thresh'])
    trans_method = args['trans']

    # print(outlang)
    # lines = []
    # with codecs.open(inpath,encoding = 'UTF-8') as f:
    #     lines = f.readlines()
    mydict = {}
    for line in codecs.open(inpath, encoding='UTF-8'):
        line = str(line)
        words = line.strip().split('\t')
        if 'raw' in format:
            surf = words[2]
            eid = words[4]
            if surf not in mydict:
                mydict[surf] = {"Count": 0, "ID": eid, "Translation": "NIL", "Mapping": "NIL","FClass":"NIL","FCode":"NIL"}
            count = mydict[surf]["Count"] + 1
            mydict[surf]["Count"] = count
        elif 'th' in format:
            count, surf, eid = words
            mydict[surf] = {"Count": count, "ID": eid, "Translation": "NIL", "Mapping": "NIL","FClass":"NIL","FCode":"NIL"}
        elif 'ts' in format:
            count, surf, trans, eid = words
            mydict[surf] = {"Count": count, "ID": eid, "Translation": trans, "Mapping": "NIL","FClass":"NIL","FCode":"NIL"}
        elif 'geo' in format:
            count, surf, trans, eid, mapping,fclass,fcode= words
            mydict[surf] = {"Count": count, "ID": eid, "Translation": trans, "Mapping": mapping,"FClass":fclass,"FCode":fcode}

    if 't' in options:
        if 'google' in trans_method:
            translator = Translator()
        else:
            translator = goslate.Goslate()

        for idx, entry in enumerate(mydict):
            row = mydict[entry]
            if row["Translation"] != "NIL" or int(row["Count"]) < threshold:
                continue
            try:
                if 'google' in trans_method:
                    translation = translator.translate(entry, dest=outlang).text
                else:
                    translation = translator.translate(entry, outlang)
                mydict[entry] = {"Count": row["Count"], "ID": row["ID"],
                                 "Translation": translation, "Mapping": row["Mapping"],"FClass":row["FClass"],"FCode":row["FCode"]}
                print("translating:" + str(idx))
                if idx > 0 and idx % 100 == 0:
                    print('wait')
                    time.sleep(10)
            except:
                print("NIL")
                # finally:
                #    print (str(dict[entry]["Count"])+"\t"+entry)

    if 'g' in options:
        geonames = GeoNamesLoader(ilcode=ilcode)
        for entry in mydict:
            eid = mydict[entry]["ID"]
            if eid in geonames:
                kbentry = geonames.get(eid=eid)
                name = kbentry['name']
                fclass = kbentry['feature_class'] if 'feature_class' in kbentry else "None"
                fcode = kbentry['feature_code'] if 'feature_code' in kbentry else "None"
                mydict[entry] = {"Count": mydict[entry]["Count"], "ID": mydict[entry]["ID"],
                                 "Translation": mydict[entry]["Translation"], "Mapping": name,"FClass":fclass,"FCode":fcode}
            else:
                mydict[entry] = {"Count": mydict[entry]["Count"], "ID": mydict[entry]["ID"],
                                 "Translation": mydict[entry]["Translation"], "Mapping": "NIL","FClass":"None","FCode":"None"}
        geonames.finish()
    mydict = sorted(mydict.items(), key=lambda d: int(d[1]["Count"]), reverse=True)
    with codecs.open(outpath, encoding='UTF-8', mode='w') as out:
        for outline in mydict:
            if 'g' in options:
                if 't' in options or 'ts' in format or 'geo' in format:
                    out.write(
                        str(outline[1]["Count"]) + "\t" + outline[0] + "\t"+outline[1]['Translation']+"\t"+outline[1]['ID']+"\t"+ outline[1]["Mapping"] + "\t" + str(
                            outline[1]["FClass"]) + "\t" + outline[1]['FCode'] + "\n")
                else:
                    out.write(
                        str(outline[1]["Count"]) + "\t" + outline[0] + "\t" + outline[0]+ "\t"+ outline[1]['ID']+"\t"+outline[1]['Mapping']+"\t"+ str(outline[1]["FClass"]) + "\t" + outline[1]['FCode'] + "\n")
            else:
                if 't' in options or 'ts' in format:
                    out.write(
                        str(outline[1]["Count"]) + "\t" + outline[0] + "\t" + outline[1]["Translation"] + "\t" + str(
                            outline[1]["ID"]) + "\n")
                else:
                    out.write(str(outline[1]["Count"]) + "\t" + outline[0] + "\t" +outline[0]+"\t"+ str(outline[1]["ID"]) + "\n")
