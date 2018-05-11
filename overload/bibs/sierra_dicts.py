# -*- coding: utf-8 -*-
# defines control vocabulares used in Sierra records

# nypl acq types
NACQ_TYPE = {
    'p': 'purchase',
    'd': 'prepaid',
    'r': 'recharge',
    'e': 'exchange',
    'c': 'deposit',
    'm': 'undetermined',
    's': 'special',
    'g': 'gift',
    'l': 'lease'
}

# nypl claim codes
NCLAIM = {
    '-': '---',
    'n': 'no claims',
    'z': 'must claim',
    'r': 'rush dec md',
    'a': 'cl 1 dec md',
    'b': 'cl 2 dec md',
    'c': 'cl 3 dec md',
    'd': 'cl 4 dec md',
    'e': 'cl 5 dec md',
    'f': 'cl 6 dec md'
}

# nypl order code1 
NORDER_CODE1 = {
    'w': 'Wayne',
    'c': 'Celeste',
    '-': '---',
    'b': 'Kimberly',
    'f': 'CPRC',
    'n': 'Andrew',
    'l': 'Lequyen',
    'a': 'Marie-Agnes',
    'p': 'Pascale',
    'd': 'Douglas',
    'j': 'Jeaanette',
    'm': 'Marilin',
    's': 'serials project',
    'e': 'Eddie'
}

# nypl order code2
NORDER_CODE2 = {
    'r': 'research',
    'c': 'branch',
    '-': '-',
    'x': 'batch research',
    'y': 'batch branch',
    'e': 'doe educator'
}

# nypl order code 3
NORDER_CODE3 = {
    'd': 'domestic',
    'f': 'foreign',
    '-': 'no code'
}

# nypl order code 4
NORDER_CODE4 = {
    '-': '---',
    'n': 'suppress'
}

# nypl order item format
N_OFORM = {
    '-': 'undefined',
    'b': 'book',
    'p': 'periodical',
    's': 'serial',
    'm': 'microform',
    'c': 'score',
    'r': 'audio-other',
    'u': 'map',
    't': 'videocassette',
    'f': 'film',
    'd': 'cd-rom',
    'e': 'elec access',
    'k': 'kit-bk/audio',
    'v': 'dvd',
    'w': 'music cd',
    'i': 'audio book',
    'g': 'video game',
    'a': 'arch/manusc.',
    'h': 'print & photos',
    'l': 'large print',
    'j': 'realia',
    'q': 'ebook',
    'z': 'ejournal',
    'y': 'bluray',
    'o': 'print & electronic',
    'x': 'playway',
    '2': 'bookpack',
    '3': 'streaming media'
}

# nypl order type
NORDER_TYPE = {
    '-': 'undefined',
    'f': 'firm order',
    'o': 'stand order',
    'i': 'item s.o.',
    'a': 'approval plan',
    's': 'subscription',
    'l': 'lease',
    'g': 'gift'
}

# nypl order note
NORDER_NOTE = {
    '-': '---',
    '1': '1 month delay',
    '2': '2 month delay',
    '3': '3 month delay',
    '4': '6 month delay',
    '5': '9 month delay',
    '6': '1 year delay',
    '7': '1.5 year delay',
    '8': '2 year delay',
    '9': '3 year delay',
    'c': 'confirming',
    'f': 'rush+conf',
    'r': 'rush'
}

# nypl order status
N_OSTATUS = {
    'o': 'on order',
    'q': 'part paid',
    '1': 'on hold',
    'c': 'ser on order',
    'e': 'ser part paid',
    'g': 'serial liened',
    'a': 'fully paid',
    'z': 'cancelled',
    '2': 'approval rej',
    'd': 'serial paid',
    'f': 'serial no enc'
}

# languages
LANG = {
    'ara': 'Arabic',
    'ben': 'Bengali',
    'chi': 'Chinese',
    'eng': 'English',
    'fre': 'French',
    'ger': 'German',
    'heb': 'Hebrew',
    'hin': 'Hindi',
    'hun': 'Hungarian',
    'ita': 'Italian',
    'jpn': 'Japanese',
    'kor': 'Korean',
    'pan': 'Panjabi',
    'pol': 'Polish',
    'por': 'Portuguese',
    'rus': 'Russian',
    'san': 'Sanskrit',
    'spa': 'Spanish',
    'ukr': 'Ukrainian',
    'und': 'Undetermined',
    'urd': 'Urdu',
    'yid': 'Yiddish',
    'zxx': 'No linguistic content',
    'hat': 'Haitian French Creole',
    'alb': 'Albanian'
}


COUNTRIES = {
    "aa ": "Albania",

    "abc": "Alberta",

    "aca": "Australian Capital Territory",

    "ae ": "Algeria",

    "af ": "Afghanistan",

    "ag ": "Argentina",

    "ai ": "Armenia (Republic)",

    "aj ": "Azerbaijan",

    "aku": "Alaska",

    "alu": "Alabama",

    "am ": "Anguilla",

    "an ": "Andorra",

    "ao ": "Angola",

    "aq ": "Antigua and Barbuda",

    "aru": "Arkansas",

    "as ": "American Samoa",

    "at ": "Australia",

    "au ": "Austria",

    "aw ": "Aruba",

    "ay ": "Antarctica",

    "azu": "Arizona",

    "ba ": "Bahrain",

    "bb ": "Barbados",

    "bcc": "British Columbia",

    "bd ": "Burundi",

    "be ": "Belgium",

    "bf ": "Bahamas",

    "bg ": "Bangladesh",

    "bh ": "Belize",

    "bi ": "British Indian Ocean Territory",

    "bl ": "Brazil",

    "bm ": "Bermuda Islands",

    "bn ": "Bosnia and Herzegovina",

    "bo ": "Bolivia",

    "bp ": "Solomon Islands",

    "br ": "Burma",

    "bs ": "Botswana",

    "bt ": "Bhutan",

    "bu ": "Bulgaria",

    "bv ": "Bouvet Island",

    "bw ": "Belarus",

    "bx ": "Brunei",

    "ca ": "Caribbean Netherlands",

    "cau": "California",

    "cb ": "Cambodia",

    "cc ": "China",

    "cd ": "Chad",

    "ce ": "Sri Lanka",

    "cf ": "Congo (Brazzaville)",

    "cg ": "Congo (Democratic Republic)",

    "ch ": "China (Republic : 1949- )",

    "ci ": "Croatia",

    "cj ": "Cayman Islands",

    "ck ": "Colombia",

    "cl ": "Chile",

    "cm ": "Cameroon",

    "co ": "Curaçao",

    "cou": "Colorado",

    "cq ": "Comoros",

    "cr ": "Costa Rica",

    "ctu": "Connecticut",

    "cu ": "Cuba",

    "cv ": "Cabo Verde",

    "cw ": "Cook Islands",

    "cx ": "Central African Republic",

    "cy ": "Cyprus",

    "dcu": "District of Columbia",

    "deu": "Delaware",

    "dk ": "Denmark",

    "dm ": "Benin",

    "dq ": "Dominica",

    "dr ": "Dominican Republic",

    "ea ": "Eritrea",

    "ec ": "Ecuador",

    "eg ": "Equatorial Guinea",

    "em ": "Timor-Leste",

    "enk": "England",

    "er ": "Estonia",

    "es ": "El Salvador",

    "et ": "Ethiopia",

    "fa ": "Faroe Islands",

    "fg ": "French Guiana",

    "fi ": "Finland",

    "fj ": "Fiji",

    "fk ": "Falkland Islands",

    "flu": "Florida",

    "fm ": "Micronesia (Federated States)",

    "fp ": "French Polynesia",

    "fr ": "France",

    "fs ": "Terres australes et antarctiques françaises",

    "ft ": "Djibouti",

    "gau": "Georgia",

    "gb ": "Kiribati",

    "gd ": "Grenada",

    "gg ": "Guernsey",

    "gh ": "Ghana",

    "gi ": "Gibraltar",

    "gl ": "Greenland",

    "gm ": "Gambia",

    "go ": "Gabon",

    "gp ": "Guadeloupe",

    "gr ": "Greece",

    "gs ": "Georgia (Republic)",

    "gt ": "Guatemala",

    "gu ": "Guam",

    "gv ": "Guinea",

    "gw ": "Germany",

    "gy ": "Guyana",

    "gz ": "Gaza Strip",

    "hiu": "Hawaii",

    "hm ": "Heard and McDonald Islands",

    "ho ": "Honduras",

    "ht ": "Haiti",

    "hu ": "Hungary",

    "iau": "Iowa",

    "ic ": "Iceland",

    "idu": "Idaho",

    "ie ": "Ireland",

    "ii ": "India",

    "ilu": "Illinois",

    "im ": "Isle of Man",

    "inu": "Indiana",

    "io ": "Indonesia",

    "iq ": "Iraq",

    "ir ": "Iran",

    "is ": "Israel",

    "it ": "Italy",

    "iv ": "Côte d'Ivoire",

    "iy ": "Iraq-Saudi Arabia Neutral Zone",

    "ja ": "Japan",

    "je ": "Jersey",

    "ji ": "Johnston Atoll",

    "jm ": "Jamaica",

    "jo ": "Jordan",

    "ke ": "Kenya",

    "kg ": "Kyrgyzstan",

    "kn ": "Korea (North)",

    "ko ": "Korea (South)",

    "ksu": "Kansas",

    "ku ": "Kuwait",

    "kv ": "Kosovo",

    "kyu": "Kentucky",

    "kz ": "Kazakhstan",

    "lau": "Louisiana",

    "lb ": "Liberia",

    "le ": "Lebanon",

    "lh ": "Liechtenstein",

    "li ": "Lithuania",

    "lo ": "Lesotho",

    "ls ": "Laos",

    "lu ": "Luxembourg",

    "lv ": "Latvia",

    "ly ": "Libya",

    "mau": "Massachusetts",

    "mbc": "Manitoba",

    "mc ": "Monaco",

    "mdu": "Maryland",

    "meu": "Maine",

    "mf ": "Mauritius",

    "mg ": "Madagascar",

    "miu": "Michigan",

    "mj ": "Montserrat",

    "mk ": "Oman",

    "ml ": "Mali",

    "mm ": "Malta",

    "mnu": "Minnesota",

    "mo ": "Montenegro",

    "mou": "Missouri",

    "mp ": "Mongolia",

    "mq ": "Martinique",

    "mr ": "Morocco",

    "msu": "Mississippi",

    "mtu": "Montana",

    "mu ": "Mauritania",

    "mv ": "Moldova",

    "mw ": "Malawi",

    "mx ": "Mexico",

    "my ": "Malaysia",

    "mz ": "Mozambique",

    "nbu": "Nebraska",

    "ncu": "North Carolina",

    "ndu": "North Dakota",

    "ne ": "Netherlands",

    "nfc": "Newfoundland and Labrador",

    "ng ": "Niger",

    "nhu": "New Hampshire",

    "nik": "Northern Ireland",

    "nju": "New Jersey",

    "nkc": "New Brunswick",

    "nl ": "New Caledonia",

    "nmu": "New Mexico",

    "nn ": "Vanuatu",

    "no ": "Norway",

    "np ": "Nepal",

    "nq ": "Nicaragua",

    "nr ": "Nigeria",

    "nsc": "Nova Scotia",

    "ntc": "Northwest Territories",

    "nu ": "Nauru",

    "nuc": "Nunavut",

    "nvu": "Nevada",

    "nw ": "Northern Mariana Islands",

    "nx ": "Norfolk Island",

    "nyu": "New York (State)",

    "nz ": "New Zealand",

    "ohu": "Ohio",

    "oku": "Oklahoma",

    "onc": "Ontario",

    "oru": "Oregon",

    "ot ": "Mayotte",

    "pau": "Pennsylvania",

    "pc ": "Pitcairn Island",

    "pe ": "Peru",

    "pf ": "Paracel Islands",

    "pg ": "Guinea-Bissau",

    "ph ": "Philippines",

    "pic": "Prince Edward Island",

    "pk ": "Pakistan",

    "pl ": "Poland",

    "pn ": "Panama",

    "po ": "Portugal",

    "pp ": "Papua New Guinea",

    "pr ": "Puerto Rico",

    "pw ": "Palau",

    "py ": "Paraguay",

    "qa ": "Qatar",

    "qea": "Queensland",

    "quc": "Québec (Province)",

    "rb ": "Serbia",

    "re ": "Réunion",

    "rh ": "Zimbabwe",

    "riu": "Rhode Island",

    "rm ": "Romania",

    "ru ": "Russia (Federation)",

    "rw ": "Rwanda",

    "sa ": "South Africa",

    "sc ": "Saint-Barthélemy",

    "scu": "South Carolina",

    "sd ": "South Sudan",

    "sdu": "South Dakota",

    "se ": "Seychelles",

    "sf ": "Sao Tome and Principe",

    "sg ": "Senegal",

    "sh ": "Spanish North Africa",

    "si ": "Singapore",

    "sj ": "Sudan",

    "sl ": "Sierra Leone",

    "sm ": "San Marino",

    "sn ": "Sint Maarten",

    "snc": "Saskatchewan",

    "so ": "Somalia",

    "sp ": "Spain",

    "sq ": "Swaziland",

    "sr ": "Surinam",

    "ss ": "Western Sahara",

    "st ": "Saint-Martin",

    "stk": "Scotland",

    "su ": "Saudi Arabia",

    "sw ": "Sweden",

    "sx ": "Namibia",

    "sy ": "Syria",

    "sz ": "Switzerland",

    "ta ": "Tajikistan",

    "tc ": "Turks and Caicos Islands",

    "tg ": "Togo",

    "th ": "Thailand",

    "ti ": "Tunisia",

    "tk ": "Turkmenistan",

    "tl ": "Tokelau",

    "tma": "Tasmania",

    "tnu": "Tennessee",

    "to ": "Tonga",

    "tr ": "Trinidad and Tobago",

    "ts ": "United Arab Emirates",

    "tu ": "Turkey",

    "tv ": "Tuvalu",

    "txu": "Texas",

    "tz ": "Tanzania",

    "ua ": "Egypt",

    "uc ": "United States Misc. Caribbean Islands",

    "ug ": "Uganda",

    "un ": "Ukraine",

    "up ": "United States Misc. Pacific Islands",

    "utu": "Utah",

    "uv ": "Burkina Faso",

    "uy ": "Uruguay",

    "uz ": "Uzbekistan",

    "vau": "Virginia",

    "vb ": "British Virgin Islands",

    "vc ": "Vatican City",

    "ve ": "Venezuela",

    "vi ": "Virgin Islands of the United States",

    "vm ": "Vietnam",

    "vp ": "Various places",

    "vra": "Victoria",

    "vtu": "Vermont",

    "wau": "Washington (State)",

    "wea": "Western Australia",

    "wf ": "Wallis and Futuna",

    "wiu": "Wisconsin",

    "wj ": "West Bank of the Jordan River",

    "wk ": "Wake Island",

    "wlk": "Wales",

    "ws ": "Samoa",

    "wvu": "West Virginia",

    "wyu": "Wyoming",

    "xa ": "Christmas Island (Indian Ocean)",

    "xb ": "Cocos (Keeling) Islands",

    "xc ": "Maldives",

    "xd ": "Saint Kitts-Nevis",

    "xe ": "Marshall Islands",

    "xf ": "Midway Islands",

    "xga": "Coral Sea Islands Territory",

    "xh ": "Niue",

    "xj ": "Saint Helena",

    "xk ": "Saint Lucia",

    "xl ": "Saint Pierre and Miquelon",

    "xm ": "Saint Vincent and the Grenadines",

    "xn ": "Macedonia",

    "xna": "New South Wales",

    "xo ": "Slovakia",

    "xoa": "Northern Territory",

    "xp ": "Spratly Island",

    "xr ": "Czech Republic",

    "xra": "South Australia",

    "xs ": "South Georgia and the South Sandwich Islands",

    "xv ": "Slovenia",

    "xx ": "No place, unknown, or undetermined",

    "xxc": "Canada",

    "xxk": "United Kingdom",

    "xxu": "United States",

    "ye ": "Yemen",

    "ykc": "Yukon Territory",

    "za ": "Zambia",
}


N_MATFORM = {
    'p': 'archiwal mix',
    'm': 'computer file',
    'z': 'ebook',
    'x': 'game',
    't': 'manuscript',
    'h': 'microform',
    'j': 'music non-cd',
    'i': 'spoken word',
    'r': '3-d object',
    '7': 'teacher audio',
    'u': 'audiobook',
    'v': 'dvd',
    '3': 'e-video',
    'o': 'kit',
    'd': 'mauscript mus',
    '-': 'misc',
    'k': 'picture',
    's': 'vhs',
    '8': 'teacher set',
    '4': 'tablet',
    'a': 'book/text',
    'n': 'e-audiobook',
    'g': 'film,slicde,etc',
    'l': 'large print',
    'e': 'map',
    'y': 'music cd',
    'c': 'score',
    'w': 'web resource',
    'b': 'blu-ray'
}
