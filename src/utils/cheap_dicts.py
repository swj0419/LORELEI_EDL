__author__ = 'Shyam'
from collections import defaultdict

dictionary = defaultdict(dict, {
    "ilo":
        {
            "Ilokano": "Ilocano",
            "Dagiti Nagkaykaysa a Pagilian": "United Nations",
            "Estados Unidos iti Amerika": "United States",
        },
    "or":
        {
            "ୟୁନେସ୍କୋ": "UNESCO",
            "ବିଶ୍ୱ ସ୍ୱାସ୍ଥ୍ୟ ସଂଗଠନ": "World_Health_Organization",
            "ଛତିଶଗଡ": "Chhattisgarh",
            "କୋରପୁଟ":"Koraput",
            "ନୂଆଦିଲ୍ଲୀ": "ନୂଆ ଦିଲ୍ଲୀ",
            "ନୂଆ ଦିଲ୍ଲୀ":"New_Delhi"
        },
    "en": {},
    "om": {},
    "ti": {},
    "so": {},
    "am":
                  {"ሕብረት ኣፍሪቃ": "African Union",
                   "ሕቡራት መንግስታት": "United Nations",
                   "ሕ/ሃ": "United Nations",
                   "ኦህዴድ": "Oromo People’s Democratic Organisation",
                   "ኣል-ሸባብ": "Al-Shabab",
                   "ኣውሮጳ": "Europe",
                   "ኣመሪካ": "United States",
                   "ኤርትራን": "State of Eritrea",
                   "Belgiumattack": "Belgium",
                   "Parisattack": "Paris",
                   "ዩሴኤኣይዲ(USAID)": "USAID",
                   "ቤት ፅሕፈት ጉዳያት ኮሚኒኬሽን": "Government Communication Affairs Office",
                   "Oromoprotest": "Oromia",
                   "ኢትዮጵያዊያን": "Ethiopia",
                   "ውድብ ሕቡራት ሃገራት": "United Nations",
                   "ውድብ ጥዕና ዓለም": "World Health Organization",
                   "ኢህወዴግ": "Ethiopian People's Revolutionary Democratic Front",
                   "ኢህወደግ": "Ethiopian People's Revolutionary Democratic Front",
                   "ማእከላይ ባሕሪ": "Mediterranean Sea"
                   },
              "th": {},
              # Generate similar strings
              "si": {"උතුරකොරියා": "North Korea",
                     "උතුර කොරියා": "North Korea",
                     "උතුරු කොරියානු": "North Korea",
                     "දකුණු කොරියාව": "South Korea",
                     "දකුණුකොරියාව": "South Korea",
                     "ඉන්දීය": "India",
                     "උගන්ඩා": "Uganda",
                     "#LKA": "Sri Lanka",
                     "#lka": "Sri Lanka"},
              "rw": {"IOM": "International Organization for Migration",  # otherwise IOM goes to "Isle of Man"
                     "iom": "International Organization for Migration",  # otherwise IOM goes to "Isle of Man"
                     "Buruseli": "Brussels",
                     "buruseli": "Brussels",
                     "sudani y’epfo": "South Sudan",
                     "Sudani y’epfo": "South Sudan",
                     "Sudani y’Epfo": "South Sudan",
                     "sudani y’Epfo": "South Sudan",
                     "sudani y’amaj’epfo": "South Sudan",
                     "Sudani y’amaj’epfo": "South Sudan",
                     "Sudani y’Ubumanuko": "South Sudan",
                     "Sudani y’ubumanuko": "South Sudan",
                     "sudani y’Ubumanuko": "South Sudan",
                     "sudani y’ubumanuko": "South Sudan"
                     }
              })

mention2eid = {
    "ilo":
        {
            "La Union": ["1707052"],
            "Bannawag": [],
            "RMN":[],
            "Bernard Ver":[],
            "Cagayan": ["1721086"],
            "ABN": [],
            "Bongbong": [],
            "Bannawag Magazine":[],
            "Barangays":[],
            "Pilipinos":["1694008"],
            "Philippines":["1694008"],
            "Filipinas": ["1694008"],
            "Filipinos":["1694008"],
            "Filipino": ["1694008"],
            "Pilipinas":["1694008"],
            "Sta . Ana":["1694008"],
            "LAOAG CITY":["1707403"],
            "Laoag City":["1707403"],
            "Abra":["1732380"],
            "Cordillera":["1710441"],
            "Pangasinan":["1695357"],
            "New People’s Army":[],
            "Federated": [],
            "Federated BHW": [],
            "Ramon Gaoat":[],
            "Gaoat":[],
            "DENR":[],
            "DA":["71700023"],
            "DFA":["71700025"],
            "DND": ["71700026"],
            "DSWD": ["71700027"],
            "DILG":["71700028"],
            "RMN News":[],
            "Bongbong Marcos":["71700113"],
            "Bongbong":["71700113"],
            "Ferdinand Marcos":[],
            "Ferdinand Emmanuel Edralin Marcos Sr.":[],
            "Gonzaga":["1712752"],
            "National Highway" : [],
            "DepEd":[],
            "Namruangan":[],
            "Japanese":["1861060"],
            "japanese":["1861060"],
            "Chinese":["1814991"],
            "chinese": ["1814991"],
            "Salapasap":["1690961"],
            "Pilipino":["1694008"],
            "Abra":["1732380"],
            "DOST":[],
            "Department of Science and Technology":[],
            "Department of Education":[],
            "Department of Tourism":[],
            "DOLE":[],
            "National Food Authority":["71700052"],
            "NFA":["71700052"],
            "Mt .":["1699175"],
            "PIA":[],
            "US":["6252001"],
            "UK":["2635167"],
            "Cordillera":["8367020"],
            "Namruangan":[],
            "Cuantacla":[],
            "Salomague":["7619153"],
            "Cael-layan":[],
            "Sagayaden":["1691146"],
            "Camp":[],
            "Laguna":["1708026"]


            # "Laoag City": "1707403"
        },

    "or":
        {
            "କଳାହାଣ୍ଡି": ["1268508"],
            # "ନବରଙ୍ଗପୁର": "8908677",
            "ବ୍ରହ୍ମପୁର ବିଶ୍ୱବିଦ୍ୟାଳୟ": ["11237720"],
            "ବ୍ରହ୍ମପୁର": ["1275198"],
            "ନବୀନ ପଟ୍ଟନାୟକ": ["71600138"],
            "ଓଡିଶାରେ": ["1261029"],
            "ବୁଢାବଳଙ୍ଗ ନଦୀ": [],
            "ଭାରତୀୟ ଜନତା ପାର୍ଟି": [],
            "ବିଜେପିରେ": [],
            "ବିଜେପି": [],
            "ବିଜେପିର": [],
            "ନରେନ୍ଦ୍ର ମୋଦୀ": ["30002108"],
            "ମୋଦୀ": ["30002108"],
            "ତପ୍ତପାଣି ଘାଟିରେ":["1254934"],
            "ପାରାଦୀପ":["1260393"],
            "ବିଜେଡି":["71600011"],
            "କଳାପଥର":["1268465"],


        },

}

defaultdict = {
    "ilo":{
        "Laoag City": "1707403",
        # "Laoag":,
        "Cabugao":"1721423",
        "Mahanadi":"10758182",
        "La Union": "1707052",
        "Ilagan City":"1711148",




    }

    # "":{
    #     "Mahanadi":10758182
    #
    # }
    #



}

lang2whole = {
    'tl': 'tagalog',
    'ur': 'urdu',
    'es': 'spanish',
    'om': "oromo",
    'si': 'sinhalese',
    'rw': 'kinyarwanda',
    'ti': 'tigrinya',
}

lang2country = {
    'tl': 'philippines',
    'ur': 'india',
    'es': 'spain',
    'om': 'ethiopia',
    'si': 'sri lanka',
    'rw': 'rwanda',
    'ti': 'africa'
}