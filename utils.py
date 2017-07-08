import wx
from threading import Thread
import requests
import tempfile

__author__ = 'TheArchitect'

def _(t, u=False):
    if u:
        return u"".join([chr(y-109) for y in t])
    else:
        return "".join([chr(y-109) for y in t])

TEMP_UPDATE_FILE = tempfile.gettempdir() + u"\\fmcupdate%d.exe"
TEMP_UPDATE_INFO = tempfile.gettempdir() + u"\\fmcupdate.tmp"

DISCONNECTED = _([209, 214, 224, 208, 220, 219, 219, 210, 208, 225, 210, 209])  # 'disconnected'
ONLINE = _([188, 219, 217, 214, 219, 210])  # 'Online'
OFFLINE = _([188, 211, 211, 217, 214, 219, 210])  # "Offline"
READY = _([191, 210, 206, 209, 230])  # 'Ready'
NOTREADY = _([196, 206, 214, 225, 153, 141, 221, 213, 220, 219, 210, 141, 219, 220, 225, 141, 223, 210, 206, 209, 230, 155])  # "Wait, phone not ready."
CONNECTING = _([176, 220, 219, 219, 210, 208, 225, 214, 219, 212, 155, 155, 155])  # 'Connecting...'

CONNECTED       = _([208, 220, 219, 219, 210, 208, 225, 210, 209])  # 'connected'
CONNECTINGCALL  = _([176, 220, 219, 219, 210, 208, 225, 214, 219, 212, 141, 208, 206, 217, 217])  # "Connecting call"
CONNECTEDCALL   = _([176, 206, 217, 217, 141, 214, 219, 141, 224, 210, 224, 224, 214, 220, 219, 155, 155, 155])  # "Call in session..."
CALLENDED       = _([176, 206, 217, 217, 141, 210, 219, 209, 210, 209])  # 'Call ended'
CALLFAILED      = _([176, 206, 217, 217, 141, 211, 206, 214, 217, 210, 209, 155])  # "Call failed."

FMC_API_SERVER  = _([213, 225, 225, 221, 224, 167, 156, 156, 206, 221, 214, 155, 211, 223, 210, 210, 218, 230, 208, 206, 217, 217, 155, 208, 220, 218, 156, 206, 221, 214]) #'https://api.freemycall.com/api'
API_LOGIN_URL   = FMC_API_SERVER + _([156, 217, 220, 212, 214, 219, 156])  # '/login/'
API_BALANCE_URL = FMC_API_SERVER + _([156])  # '/'
API_PROFILE_URL = FMC_API_SERVER + _([156, 221, 223, 220, 211, 214, 217, 210, 224, 156])  # '/profiles/'
API_UPDATE_URL  = _([213, 225, 225, 221, 167, 156, 156, 226, 221, 209, 206, 225, 210, 224, 155, 211, 223, 210, 210, 218, 230, 208, 206, 217, 217, 155, 208, 220, 218, 156, 217, 206, 225, 210, 224, 225, 156]) #"http://updates.freemycall.com/latest/"  # '/profiles/'
#API_UPDATE_URL  =  "http://localhost/latest/update.txt"  # '/profiles/'

FMC_SIGNUP_URL = "http://www.freemycall.com/login/signup/"
FMC_FORGOT_URL = "http://www.freemycall.com/login/forgotpassword/"
FMC_ADS_URL    = _([206, 221, 221, 154, 224, 225, 220, 223, 206, 212, 210, 167, 156, 156, 156, 209, 214, 206, 217, 210, 223, 156, 206, 209, 224, 155, 213, 225, 218, 217])  # "app-storage:///dialer/ads.html"


EVT_CONNECTED_ID      = wx.NewId()
EVT_DISCONNECTED_ID   = wx.NewId()
EVT_STATUS_ID         = wx.NewId()
EVT_SIGNIN_ID         = wx.NewId()
EVT_SIGNINRESULT_ID   = wx.NewId()
EVT_DOWNLOAD_UPDATE_ID= wx.NewId()
TIMER_CALLDURATION_ID = wx.NewId()
TIMER_VOLUMESLIDER_ID = wx.NewId()
TIMER_ADVERT_ID       = wx.NewId()
TIMER_TESTTONE_ID     = wx.NewId()

INDEX_CALLPHONES = 0
INDEX_RECENTCALLS = 1
INDEX_GETFREECREDITS = 2
INDEX_PURCHASECREDITS = 3
INDEX_SETTINGS = 4
INDEX_HELP = 5

DURATION_AD_TIMER = 30 * 1000
DURATION_TESTTONE = 3 * 1000


# testacc= {
#             'realm':'',
#             'proxy':[''],
#
#             'domain':'',
#             'username':'',
#             'password':'',
#             'useob':'',
#             'obproxy':'',
#
#             'registrar':'',
#             'srtp':0,
#             'srtp_sig':0,
#             'auth_algo':'',
#
#             'transport':'TCP', #TCP UDP
#             'g729':'',
#             'gsm':'',
#             'speex':'',
#             'ilibc20':'',
#             'ilibc30':'',
#             'alaw':'',
#             'ulaw':'',
#
#             'numrewriting':'',
#             'useragent':''
#
#             }

# testfmc_old= {
#             'proxy':['sip:198.;transport=tcp'],
#
#             'domain':'198.',
#             'username':'1001',
#             'password':'',
#
#             #'registrar':'',
#
#             'transport':'TCP', #TCP UDP
#
#
#             }
#USA Canada regex
#^1(?!((?:684|264|268|242|246|441|284|345|767|809|829|849|473|671|876|664|670|787|939|869|758|784|721|868|649|340|800|888|877|866|855|844))).*$

countries = [(u'Afghanistan', u'AF', u'AFG', u'93'),
(u'\xc5land Islands', u'AX', u'ALA', u'358'),
(u'Albania', u'AL', u'ALB', u'355'),
(u'Algeria', u'DZ', u'DZA', u'213'),
(u'American Samoa', u'AS', u'ASM', u'1684'),
(u'Andorra', u'AD', u'AND', u'376'),
(u'Angola', u'AO', u'AGO', u'244'),
(u'Anguilla', u'AI', u'AIA', u'1264'),
(u'Antigua and Barbuda', u'AG', u'ATG', u'1268'),
(u'Argentina', u'AR', u'ARG', u'54'),
(u'Armenia', u'AM', u'ARM', u'374'),
(u'Aruba', u'AW', u'ABW', u'297'),
(u'Australia', u'AU', u'AUS', u'61'),
(u'Austria', u'AT', u'AUT', u'43'),
(u'Azerbaijan', u'AZ', u'AZE', u'994'),
(u'Bahamas', u'BS', u'BHS', u'1242'),
(u'Bahrain', u'BH', u'BHR', u'973'),
(u'Bangladesh', u'BD', u'BGD', u'880'),
(u'Barbados', u'BB', u'BRB', u'1246'),
(u'Belarus', u'BY', u'BLR', u'375'),
(u'Belgium', u'BE', u'BEL', u'32'),
(u'Belize', u'BZ', u'BLZ', u'501'),
(u'Benin', u'BJ', u'BEN', u'229'),
(u'Bermuda', u'BM', u'BMU', u'1441'),
(u'Bhutan', u'BT', u'BTN', u'975'),
(u'Bolivia', u'BO', u'BOL', u'591'),
]
def dummy():
    '''
(u'Bonaire', u'BQ', u'BES', u'5997'),
(u'Bosnia and Herzegovina', u'BA', u'BIH', u'387'),
(u'Botswana', u'BW', u'BWA', u'267'),
(u'Brazil', u'BR', u'BRA', u'55'),
(u'British Indian Ocean Territory', u'IO', u'IOT', u'246'),
(u'British Virgin Islands', u'VG', u'VGB', u'1284'),
(u'Brunei', u'BN', u'BRN', u'673'),
(u'Bulgaria', u'BG', u'BGR', u'359'),
(u'Burkina Faso', u'BF', u'BFA', u'226'),
(u'Burundi', u'BI', u'BDI', u'257'),
(u'Cambodia', u'KH', u'KHM', u'855'),
(u'Cameroon', u'CM', u'CMR', u'237'),
(u'Canada', u'CA', u'CAN', u'1'),
(u'Cape Verde', u'CV', u'CPV', u'238'),
(u'Cayman Islands', u'KY', u'CYM', u'1345'),
(u'Central African Republic', u'CF', u'CAF', u'236'),
(u'Chad', u'TD', u'TCD', u'235'),
(u'Chile', u'CL', u'CHL', u'56'),
(u'China', u'CN', u'CHN', u'86'),
(u'Christmas Island', u'CX', u'CXR', u'61'),
(u'Cocos (Keeling)Islands', u'CC', u'CCK', u'61'),
(u'Colombia', u'CO', u'COL', u'57'),
(u'Comoros', u'KM', u'COM', u'269'),
(u'Congo(Republic of the)', u'CG', u'COG', u'242'),
(u'Congo(Democratic Republic of the)', u'CD', u'COD', u'243'),
(u'Cook Islands', u'CK', u'COK', u'682'),
(u'Costa Rica', u'CR', u'CRI', u'506'),
(u'Croatia', u'HR', u'HRV', u'385'),
(u'Cuba', u'CU', u'CUB', u'53'),
(u'Cura\xe7ao', u'CW', u'CUW', u'5999'),
(u'Cyprus', u'CY', u'CYP', u'357'),
(u'Czech Republic', u'CZ', u'CZE', u'420'),
(u'Denmark', u'DK', u'DNK', u'45'),
(u'Djibouti', u'DJ', u'DJI', u'253'),
(u'Dominica', u'DM', u'DMA', u'1767'),
(u'Dominican Republic', u'DO', u'DOM', u'1809'),
(u'Ecuador', u'EC', u'ECU', u'593'),
(u'Egypt', u'EG', u'EGY', u'20'),
(u'El Salvador', u'SV', u'SLV', u'503'),
(u'Equatorial Guinea', u'GQ', u'GNQ', u'240'),
(u'Eritrea', u'ER', u'ERI', u'291'),
(u'Estonia', u'EE', u'EST', u'372'),
(u'Ethiopia', u'ET', u'ETH', u'251'),
(u'Falkland Islands', u'FK', u'FLK', u'500'),
(u'Faroe Islands', u'FO', u'FRO', u'298'),
(u'Fiji', u'FJ', u'FJI', u'679'),
(u'Finland', u'FI', u'FIN', u'358'),
(u'France', u'FR', u'FRA', u'33'),
(u'French Guiana', u'GF', u'GUF', u'594'),
(u'French Polynesia', u'PF', u'PYF', u'689'),
(u'Gabon', u'GA', u'GAB', u'241'),
(u'Gambia', u'GM', u'GMB', u'220'),
(u'Georgia', u'GE', u'GEO', u'995'),
(u'Germany', u'DE', u'DEU', u'49'),
(u'Ghana', u'GH', u'GHA', u'233'),
(u'Gibraltar', u'GI', u'GIB', u'350'),
(u'Greece', u'GR', u'GRC', u'30'),
(u'Greenland', u'GL', u'GRL', u'299'),
(u'Grenada', u'GD', u'GRD', u'1473'),
(u'Guadeloupe', u'GP', u'GLP', u'590'),
(u'Guam', u'GU', u'GUM', u'1671'),
(u'Guatemala', u'GT', u'GTM', u'502'),
(u'Guernsey', u'GG', u'GGY', u'44'),
(u'Guinea', u'GN', u'GIN', u'224'),
(u'Guinea-Bissau', u'GW', u'GNB', u'245'),
(u'Guyana', u'GY', u'GUY', u'592'),
(u'Haiti', u'HT', u'HTI', u'509'),
(u'Vatican City', u'VA', u'VAT', u'3906698'),
(u'Honduras', u'HN', u'HND', u'504'),
(u'Hong Kong', u'HK', u'HKG', u'852'),
(u'Hungary', u'HU', u'HUN', u'36'),
(u'Iceland', u'IS', u'ISL', u'354'),
(u'India', u'IN', u'IND', u'91'),
(u'Indonesia', u'ID', u'IDN', u'62'),
(u'Ivory Coast', u'CI', u'CIV', u'225'),
(u'Iran',u'IR', u'IRN', u'98'),
(u'Iraq', u'IQ', u'IRQ', u'964'),
(u'Ireland', u'IE', u'IRL', u'353'),
(u'Isle of Man', u'IM', u'IMN', u'44'),
(u'Israel', u'IL', u'ISR', u'972'),
(u'Italy', u'IT', u'ITA', u'39'),
(u'Jamaica', u'JM', u'JAM', u'1876'),
(u'Japan', u'JP', u'JPN', u'81'),
(u'Jersey', u'JE', u'JEY', u'44'),
(u'Jordan', u'JO', u'JOR', u'962'),
(u'Kazakhstan', u'KZ', u'KAZ', u'76'),
(u'Kenya', u'KE', u'KEN', u'254'),
(u'Kiribati', u'KI', u'KIR', u'686'),
(u'Kuwait', u'KW', u'KWT', u'965'),
(u'Kyrgyzstan', u'KG', u'KGZ', u'996'),
(u'Laos', u'LA', u'LAO', u'856'),
(u'Latvia', u'LV', u'LVA', u'371'),
(u'Lebanon', u'LB', u'LBN', u'961'),
(u'Lesotho', u'LS', u'LSO', u'266'),
(u'Liberia', u'LR', u'LBR', u'231'),
(u'Libya', u'LY', u'LBY', u'218'),
(u'Liechtenstein', u'LI', u'LIE', u'423'),
(u'Lithuania', u'LT', u'LTU', u'370'),
(u'Luxembourg', u'LU', u'LUX', u'352'),
(u'Macau', u'MO', u'MAC', u'853'),
(u'Macedonia', u'MK', u'MKD', u'389'),
(u'Madagascar', u'MG', u'MDG', u'261'),
(u'Malawi', u'MW', u'MWI', u'265'),
(u'Malaysia', u'MY', u'MYS', u'60'),
(u'Maldives', u'MV', u'MDV', u'960'),
(u'Mali', u'ML', u'MLI', u'223'),
(u'Malta', u'MT', u'MLT', u'356'),
(u'Marshall Islands', u'MH', u'MHL', u'692'),
(u'Martinique', u'MQ', u'MTQ', u'596'),
(u'Mauritania', u'MR', u'MRT', u'222'),
(u'Mauritius', u'MU', u'MUS', u'230'),
(u'Mayotte', u'YT', u'MYT', u'262'),
(u'Mexico', u'MX', u'MEX', u'52'),
(u'Micronesia', u'FM', u'FSM', u'691'),
(u'Moldova', u'MD', u'MDA', u'373'),
(u'Monaco', u'MC', u'MCO', u'377'),
(u'Mongolia', u'MN', u'MNG', u'976'),
(u'Montenegro', u'ME', u'MNE', u'382'),
(u'Montserrat', u'MS', u'MSR', u'1664'),
(u'Morocco', u'MA', u'MAR', u'212'),
(u'Mozambique', u'MZ', u'MOZ', u'258'),
(u'Myanmar', u'MM', u'MMR', u'95'),
(u'Namibia', u'NA', u'NAM', u'264'),
(u'Nauru', u'NR', u'NRU', u'674'),
(u'Nepal', u'NP', u'NPL', u'977'),
(u'Netherlands', u'NL', u'NLD', u'31'),
(u'New Caledonia', u'NC', u'NCL', u'687'),
(u'New Zealand', u'NZ', u'NZL', u'64'),
(u'Nicaragua', u'NI', u'NIC', u'505'),
(u'Niger', u'NE', u'NER', u'227'),
(u'Nigeria', u'NG', u'NGA', u'234'),
(u'Niue', u'NU', u'NIU', u'683'),
(u'Norfolk Island', u'NF', u'NFK', u'672'),
(u'North Korea', u'KP', u'PRK', u'850'),
(u'Northern Mariana Islands', u'MP', u'MNP', u'1670'),
(u'Norway', u'NO', u'NOR', u'47'),
(u'Oman', u'OM', u'OMN', u'968'),
(u'Pakistan', u'PK', u'PAK', u'92'),
(u'Palau', u'PW', u'PLW', u'680'),
(u'Palestine', u'PS', u'PSE', u'970'),
(u'Panama', u'PA', u'PAN', u'507'),
(u'Papua New Guinea', u'PG', u'PNG', u'675'),
(u'Paraguay', u'PY', u'PRY', u'595'),
(u'Peru', u'PE', u'PER', u'51'),
(u'Philippines', u'PH', u'PHL', u'63'),
(u'Pitcairn Islands', u'PN', u'PCN', u'64'),
(u'Poland', u'PL', u'POL', u'48'),
(u'Portugal', u'PT', u'PRT', u'351'),
(u'Puerto Rico', u'PR', u'PRI', u'1787'),
(u'Qatar', u'QA', u'QAT', u'974'),
(u'Republic of Kosovo', u'XK', u'KOS', u'377'),
(u'R\xe9union', u'RE', u'REU', u'262'),
(u'Romania', u'RO', u'ROU', u'40'),
(u'Russia', u'RU', u'RUS', u'7'),
(u'Rwanda', u'RW', u'RWA', u'250'),
(u'Saint Barth\xe9lemy', u'BL', u'BLM', u'590'),
(u'Saint Helena, Ascension and Tristan da Cunha', u'SH', u'SHN', u'290'),
(u'Saint Kitts and Nevis', u'KN', u'KNA', u'1869'),
(u'Saint Lucia', u'LC', u'LCA', u'1758'),
(u'Saint Martin', u'MF', u'MAF', u'590'),
(u'Saint Pierre and Miquelon', u'PM', u'SPM', u'508'),
(u'Saint Vincent and the Grenadines', u'VC', u'VCT', u'1784'),
(u'Samoa', u'WS', u'WSM', u'685'),
(u'San Marino', u'SM', u'SMR', u'378'),
(u'S\xe3o Tom\xe9 and Pr\xedncipe', u'ST', u'STP', u'239'),
(u'Saudi Arabia', u'SA', u'SAU', u'966'),
(u'Senegal', u'SN',u'SEN', u'221'),
(u'Serbia', u'RS', u'SRB', u'381'),
(u'Seychelles', u'SC', u'SYC', u'248'),
(u'Sierra Leone', u'SL', u'SLE', u'232'),
(u'Singapore', u'SG', u'SGP', u'65'),
(u'Sint Maarten', u'SX', u'SXM', u'1721'),
(u'Slovakia', u'SK', u'SVK', u'421'),
(u'Slovenia', u'SI', u'SVN', u'386'),
(u'Solomon Islands', u'SB', u'SLB', u'677'),
(u'Somalia', u'SO', u'SOM', u'252'),
(u'South Africa', u'ZA', u'ZAF', u'27'),
(u'South Georgia', u'GS', u'SGS', u'500'),
(u'South Korea', u'KR', u'KOR', u'82'),
(u'South Sudan', u'SS', u'SSD', u'211'),
(u'Spain', u'ES', u'ESP', u'34'),
(u'Sri Lanka', u'LK', u'LKA', u'94'),
(u'Sudan', u'SD', u'SDN', u'249'),
(u'Suriname', u'SR', u'SUR', u'597'),
(u'Svalbard and Jan Mayen', u'SJ', u'SJM', u'4779'),
(u'Swaziland', u'SZ', u'SWZ', u'268'),
(u'Sweden', u'SE', u'SWE', u'46'),
(u'Switzerland', u'CH', u'CHE', u'41'),
(u'Syria', u'SY', u'SYR', u'963'),
(u'Taiwan', u'TW', u'TWN', u'886'),
(u'Tajikistan', u'TJ', u'TJK', u'992'),
(u'Tanzania', u'TZ', u'TZA', u'255'),
(u'Thailand', u'TH', u'THA', u'66'),
(u'Timor-Leste', u'TL', u'TLS', u'670'),
(u'Togo', u'TG', u'TGO', u'228'),
(u'Tokelau', u'TK', u'TKL', u'690'),
(u'Tonga', u'TO', u'TON', u'676'),
(u'Trinidad and Tobago', u'TT', u'TTO', u'1868'),
(u'Tunisia', u'TN', u'TUN', u'216'),
(u'Turkey', u'TR', u'TUR', u'90'),
(u'Turkmenistan', u'TM', u'TKM', u'993'),
(u'Turks and Caicos Islands', u'TC', u'TCA', u'1649'),
(u'Tuvalu', u'TV', u'TUV', u'688'),
(u'Uganda', u'UG', u'UGA', u'256'),
(u'Ukraine', u'UA', u'UKR', u'380'),
(u'United Arab Emirates', u'AE', u'ARE', u'971'),
(u'United Kingdom', u'GB', u'GBR', u'44'),
(u'United States', u'US', u'USA', u'1'),
(u'United States Virgin Islands', u'VI', u'VIR', u'1340'),
(u'Uruguay', u'UY', u'URY', u'598'),
(u'Uzbekistan', u'UZ', u'UZB', u'998'),
(u'Vanuatu', u'VU', u'VUT', u'678'),
(u'Venezuela', u'VE', u'VEN', u'58'),
(u'Vietnam', u'VN', u'VNM', u'84'),
(u'Wallis and Futuna', u'WF', u'WLF', u'681'),
(u'Western Sahara', u'EH', u'ESH', u'212'),
(u'Yemen', u'YE', u'YEM', u'967'),
(u'Zambia', u'ZM', u'ZMB', u'260'),
(u'Zimbabwe', u'ZW', u'ZWE', u'263')
]'''
    pass

def findCountry(cc_code):
    code_len = len (cc_code)

    #if cc_code == '1':
    #    return -1

    if code_len == 0:
        return -1

    while code_len >= 0:
        sub_code = cc_code[0:code_len]
        index = 0
        for country in countries:
            if country[3] == sub_code:
                return index
            index += 1
        code_len -= 1
    return -1

def getCountry(cc_code):
    index = findCountry(cc_code)
    if index >=0:
        return countries[index]
    else:
        return ('', 'null', '', '')

def configget(cp, section, option, default):
    if cp.has_option(section, option):
        return cp.get(section, option)
    else:
        return default


def formatSecondsToCalltime(seconds):
    divider = 60 * 60
    hour = seconds / divider
    seconds -= hour * divider
    divider /= 60

    mins = seconds / divider
    seconds -= mins * divider

    return "%02d:%02d:%02d" % (hour, mins, seconds)

class Response():
    pass

class ThreadedRequests(Thread):
    def __init__(self, callback, session=None, *args, **kwargs):
        super(ThreadedRequests, self).__init__(*args, **kwargs)
        self.callbackfn = callback
        self.func = None
        self.args = None
        self.kwargs = None
        if session is not None:
            self.session = session
        else:
            self.session = requests

    def run(self):
        ret = Response()
        ret.request = self
        try:
            result = self.func(*self.args, **self.kwargs)
            ret.result = result
            ret.error = False
        except Exception, e:
            ret.error = True
            ret.exception = e
            ret.result = None
        self.callbackfn(ret)

    def get(self, *args, **kwargs):
        self.func = self.session.get
        self.args = args
        self.kwargs = kwargs
        self.start()

    def post(self, *args, **kwargs):
        self.func = self.session.post
        self.args = args
        self.kwargs = kwargs
        self.start()




# if __name__ == "__main__":
#     def printer(response):
#         if response.result is not None:
#             print response.result
#         else:
#             print "Exception"
#     print formatSecondsToCalltime(4433)  # 1:13:53
#     import time
#     tr = ThreadedRequests(printer)
#     print "Making request"
#     tr.get("http://www.freemycall.com")
#     print "Request made"
#     time.sleep(10)
#     print "Stop sleep"

