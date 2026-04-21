#!/usr/bin/env python3
import re

# ИСТОЧНИКИ GITHUB / API
SOURCES_GITHUB = [
    ("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",                           "http", 1),
    ("https://raw.githubusercontent.com/elliottophellia/yakumo/master/results/http/global/http_checked.txt", "http", 1),
    ("https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/http.txt",                        "http", 1),
    ("https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",         "http", 1),
    ("https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt",        "http", 1),
    ("https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt",                                  "http", 1),
    ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",                                "http", 2),
    ("https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",                                 "http", 2),
    ("https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt",                           "http", 2),
    ("https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",                        "http", 2),
    ("https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",                                   "http", 2),
    ("https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt",                                  "http", 2),
    ("https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",                       "http", 3),
    ("https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",                          "http", 3),
    ("https://raw.githubusercontent.com/almroot/proxylist/master/list.txt",                                   "http", 3),
    ("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",                        "socks4", 1),
    ("https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt",       "socks4", 1),
    ("https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks4.txt",                                "socks4", 1),
    ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",                              "socks4", 2),
    ("https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",                               "socks4", 2),
    ("https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks4.txt",                         "socks4", 2),
    ("https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",                                 "socks4", 2),
    ("https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt",                       "socks4", 3),
    ("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",                        "socks5", 1),
    ("https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt",       "socks5", 1),
    ("https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks5.txt",                                "socks5", 1),
    ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",                              "socks5", 2),
    ("https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",                               "socks5", 2),
    ("https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks5.txt",                         "socks5", 2),
    ("https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",                                 "socks5", 2),
    ("https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",                       "socks5", 3),
]

SOURCES_API = [
    ("https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&simplified=true",   "http",   1),
    ("https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks4&timeout=10000&country=all&simplified=true", "socks4", 1),
    ("https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all&simplified=true", "socks5", 1),
    ("https://www.proxy-list.download/api/v1/get?type=http",   "http",   1),
    ("https://www.proxy-list.download/api/v1/get?type=https",  "http",   1),
    ("https://www.proxy-list.download/api/v1/get?type=socks4", "socks4", 1),
    ("https://www.proxy-list.download/api/v1/get?type=socks5", "socks5", 1),
    ("https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc&protocols=http,https&speed=fast", "http", 1),
    ("https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc&protocols=socks4,socks5",         "socks4", 1),
    ("https://api.openproxy.space/lists/http",   "http",   2),
    ("https://api.openproxy.space/lists/socks5", "socks5", 2),
]

TELEGRAM_CHANNELS = [
    "proxiesfree", "proxylistfree", "socks5_proxy_list", "free_socks5_proxy", "http_proxy_fresh",
    "proxylistfresh", "free_proxy_list1", "proxy_lists", "fresh_proxy_list", "socks5proxyfree",
    "shadowsockskeys", "ProxyMega", "proxyland",
]

SOURCES_HTML = [
    "https://free-proxy-list.net/",
    "https://www.sslproxies.org/",
    "https://www.us-proxy.org/",
    "https://free-proxy-list.net/uk-proxy.html",
    "https://free-proxy-list.net/anonymous-proxy.html",
    "https://www.proxy-list.download/HTTPS",
    "https://www.proxy-list.download/HTTP",
]

SOURCES_TOR = [
    "http://pastebin3lrtfxnf.onion/archive",
    "http://strongbox7rqdc42p.onion/paste/",
    "http://zeronet6irsyypeq.onion/1GbG9jeHs3KMhj6FMkzUPJGBB7SnTVNRDP",
]

GIST_QUERIES = [
    "socks5 proxy list", "http proxy ip port", "proxy list socks4",
    "free proxy list ip:port", "working proxy list",
]

# КЛЮЧЕВЫЕ СЛОВА КЛАССИФИКАЦИИ
RESIDENTIAL_KEYWORDS = [
    "comcast","at&t","verizon","spectrum","cox","frontier","centurylink",
    "lumen","bt ","sky ","virgin","talk talk","vodafone","orange","sfr",
    "bouygues","deutsche telekom","telkom","optus","telstra","shaw",
    "bell canada","rogers","tele2","telenor","swisscom","a1 ","proximus",
    "kpn","t-home","chello","charter","cablevision","suddenlink","mediacom",
    "windstream","jio","airtel","bsnl","reliance","liberty","ziggo",
    "fastweb","infostrada","wind tre","tim brasil","oi internet",
]

MOBILE_KEYWORDS = [
    "t-mobile","tmobile","sprint","verizon wireless","at&t mobility",
    "boost mobile","cricket wireless","metro pcs","us cellular","three ",
    "o2 ","ee ","giffgaff","lebara","lyca","airtel mobile","jio mobile",
    "mobile","cellular","wireless","lte","4g","5g",
]

DC_KEYWORDS = [
    "amazon","aws","google","microsoft","azure","digitalocean","linode",
    "akamai","cloudflare","ovh","hetzner","leaseweb","rackspace","vultr",
    "contabo","scaleway","choopa","psychz","quadranet","sharktech",
    "hostwinds","server","hosting","datacenter","data center",
    "colocation","colo","vps","cloud","dedicated",
]

DC_CIDRS_FALLBACK = [
    "52.0.0.0/11","54.0.0.0/11","18.144.0.0/12","13.32.0.0/15",
    "13.35.0.0/16","3.80.0.0/12","3.96.0.0/13","15.152.0.0/13",
    "18.116.0.0/14","18.208.0.0/13","18.224.0.0/13","34.192.0.0/10",
    "34.0.0.0/9","35.184.0.0/13","35.192.0.0/11","35.224.0.0/12",
    "104.154.0.0/15","104.196.0.0/14","130.211.0.0/16",
    "13.64.0.0/11","13.104.0.0/14","23.96.0.0/13","40.64.0.0/10",
    "40.112.0.0/13","52.128.0.0/9","65.52.0.0/14","104.40.0.0/13",
    "104.131.0.0/16","104.236.0.0/16","107.170.0.0/16","138.197.0.0/16",
    "139.59.0.0/16","159.203.0.0/16","162.243.0.0/16","165.227.0.0/16",
    "167.99.0.0/16","188.166.0.0/16","198.199.0.0/16","45.55.0.0/16",
    "68.183.0.0/16","134.122.0.0/16","143.110.0.0/16","157.230.0.0/16",
    "95.216.0.0/16","116.203.0.0/16","136.243.0.0/16","138.201.0.0/16",
    "144.76.0.0/16","148.251.0.0/16","157.90.0.0/16","159.69.0.0/16",
    "167.235.0.0/16","168.119.0.0/16","176.9.0.0/16","188.40.0.0/16",
    "51.38.0.0/16","51.68.0.0/16","51.75.0.0/16","51.77.0.0/16",
    "51.89.0.0/16","51.91.0.0/16","51.195.0.0/16","51.210.0.0/16",
    "54.36.0.0/14","87.98.128.0/17","91.121.0.0/16","92.222.0.0/16",
    "45.32.0.0/20","45.63.0.0/18","45.76.0.0/15","64.237.32.0/19",
    "66.42.0.0/18","108.61.0.0/16","144.202.0.0/16","149.28.0.0/16",
    "45.33.0.0/17","45.56.0.0/21","45.79.0.0/16","50.116.0.0/20",
    "66.175.192.0/18","69.164.192.0/18","139.162.0.0/16","172.104.0.0/14",
    "51.15.0.0/16","163.172.0.0/16","104.16.0.0/12","104.24.0.0/14",
    "172.64.0.0/13","141.101.64.0/18","162.158.0.0/15","198.41.128.0/17",
    "135.181.0.0/16","142.132.0.0/14","195.201.0.0/16","192.81.128.0/17",
    "64.44.32.0/19","108.166.192.0/18","155.254.0.0/16",
    "85.17.0.0/16","37.58.0.0/16","95.211.0.0/16","192.99.0.0/16",
]

TEST_URLS = [
    "http://httpbin.org/ip",
    "http://api.ipify.org",
    "http://checkip.amazonaws.com",
]

XRAY_TELEGRAM_CHANNELS = [
    "NetAccount", "prrofile_orange", "VlessConfig", "TrojanV2ray",
]

SOURCES_XRAY_SUB = [
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge_base64.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub1.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub2.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub3.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Sub4.txt",
    "https://raw.githubusercontent.com/peasoft/NoMoreWalls/master/list.txt",
    "https://raw.githubusercontent.com/Leon406/SubCrawler/main/sub/share/all3",
    "https://raw.githubusercontent.com/mfuu/v2ray/master/v2ray",
    "https://raw.githubusercontent.com/freefq/free/master/v2",
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
    "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    "https://raw.githubusercontent.com/awesome-vpn/awesome-vpn/master/all",
    "https://raw.githubusercontent.com/tbbatbb/Proxy/master/dist/v2ray.config.txt",
    "https://raw.githubusercontent.com/w1770946466/Auto_proxy/main/Long_term_subscription_num",
    "https://raw.githubusercontent.com/Everyday-VPN/Everyday-VPN/main/subscription/main.txt",
    "https://raw.githubusercontent.com/vveg26/chromego_merge/main/sub/base64_merged_proxies.txt",
    "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_iran.txt",
    "https://raw.githubusercontent.com/soroushmirzaei/telegram-configs-collector/main/splitted/mixed",
    "https://raw.githubusercontent.com/Surfboardv2ray/TGParse/main/python/all",
    "https://raw.githubusercontent.com/MrMohebi/xray-proxy-grabber-telegram/master/collected-proxies/row-url/all.txt",
]

CIDR_FETCH_URLS = [
    "https://raw.githubusercontent.com/lord-alfred/ipranges/main/all.txt",
    "https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/firehol_level1.netset",
]

PROXY_RE = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3}):(\d{2,5})\b")
XRAY_RE = re.compile(r'(vmess|vless|trojan|ss|hysteria2?|tuic)://[A-Za-z0-9+/=@._:\-?&#%]+', re.IGNORECASE)

IP_API_FIELDS = "status,country,countryCode,city,isp,org,as,hosting,query"
IP_API_BATCH = "http://ip-api.com/batch"
