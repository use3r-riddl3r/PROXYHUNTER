#!/usr/bin/env python3
import re
import time
import ipaddress
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from ui import progress_bar, cp, dim, P, C, G, R, Y, DIM
from constants import (SOURCES_GITHUB, SOURCES_API, TELEGRAM_CHANNELS, GIST_QUERIES,
                       SOURCES_HTML, SOURCES_TOR, PROXY_RE)

def make_session(proxies=None, ua=None):
    s = requests.Session()
    s.headers["User-Agent"] = ua or "Mozilla/5.0 (X11; Linux x86_64)"
    if proxies:
        s.proxies.update(proxies)
    return s

def extract_proxies(text, default_proto="http"):
    found = []
    for m in PROXY_RE.finditer(text):
        try:
            ipaddress.ip_address(m.group(1))
            if 1 <= int(m.group(2)) <= 65535:
                found.append((f"{m.group(1)}:{m.group(2)}", default_proto))
        except ValueError:
            pass
    return found

def scrape_one_url(url, proto, session):
    found = []
    try:
        r = session.get(url, timeout=12)
        if r.status_code != 200:
            return found
        if "geonode" in url:
            try:
                for e in r.json().get("data", []):
                    ip, port = e.get("ip", ""), e.get("port", "")
                    p = e.get("protocols", [proto])[0]
                    if ip and port:
                        found.append((f"{ip}:{port}", p))
                return found
            except Exception:
                pass
        if "openproxy" in url:
            try:
                data = r.json()
                if isinstance(data, list):
                    for item in data:
                        found += extract_proxies(str(item), proto)
                return found
            except Exception:
                pass
        found = extract_proxies(r.text, proto)
    except Exception:
        pass
    return found

def scrape_github_api(state):
    s = state.settings
    protocols = s["protocols"]
    max_tier = s["source_tier"]
    threads = s["scrape_threads"]
    session = make_session()
    results = {}

    tasks = []
    if s["src_github"]:
        tasks += [(u, p) for u, p, t in SOURCES_GITHUB if p in protocols and t <= max_tier]
    if s["src_api"]:
        tasks += [(u, p) for u, p, t in SOURCES_API if p in protocols]

    if not tasks:
        return results, 0

    done = [0]
    total = len(tasks)
    added = [0]

    def worker(args):
        url, proto = args
        entries = scrape_one_url(url, proto, session)
        with threading.Lock():
            done[0] += 1
            for proxy, pr in entries:
                if proxy not in results:
                    results[proxy] = pr
                    added[0] += 1
            pct = done[0] / total
            bar = progress_bar(pct * total, total, 30, P)
            print(f"  {bar} {dim(f'github/api {done[0]}/{total}')}  {cp(G, str(added[0]))} proxies  ", end="\r")

    with ThreadPoolExecutor(max_workers=threads) as ex:
        list(as_completed({ex.submit(worker, t): t for t in tasks}))

    print()
    return results, added[0]

def scrape_telegram_channel(channel, session, pages=3):
    found = []
    url = f"https://t.me/s/{channel}"
    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            return found
        found = extract_proxies(r.text)
        msg_ids = re.findall(r'data-post="[^/]+/(\d+)"', r.text)
        if msg_ids:
            oldest = min(int(m) for m in msg_ids)
            for _ in range(pages - 1):
                r2 = session.get(f"{url}?before={oldest}", timeout=15)
                if r2.status_code == 200:
                    found += extract_proxies(r2.text)
                    ids = re.findall(r'data-post="[^/]+/(\d+)"', r2.text)
                    if ids:
                        oldest = min(int(m) for m in ids)
                time.sleep(0.5)
    except Exception:
        pass
    return found

def scrape_telegram(state):
    s = state.settings
    channels = TELEGRAM_CHANNELS + s.get("extra_telegram", [])
    session = make_session(ua="Mozilla/5.0 (compatible; TelegramBot/1.0)")
    results = {}
    added = [0]

    print(f"\n  {cp(C, '[TG]')} Scraping {cp(C, str(len(channels)))} Telegram channels ...\n")

    for i, ch in enumerate(channels):
        entries = scrape_telegram_channel(ch, session)
        with threading.Lock():
            for proxy, proto in entries:
                if proxy not in results:
                    results[proxy] = proto
                    added[0] += 1
        status = cp(G, str(len(entries))) if entries else cp(R, "0")
        print(f"  {dim(f'[{i+1}/{len(channels)}]')}  {cp(C, f't.me/{ch}'):<45}  {status} proxies  ", end="\r")
        time.sleep(0.3)

    print()
    print(f"  {cp(G, '[+]')} Telegram: {cp(G, str(added[0]))} new proxies\n")
    return results, added[0]

def scrape_gists(state):
    session = make_session()
    results = {}
    added = [0]
    seen = set()

    print(f"\n  {cp(C, '[GH]')} Searching GitHub Gists ...\n")

    for query in GIST_QUERIES:
        try:
            r = session.get("https://gist.github.com/search", params={"q": query, "s": "updated"}, timeout=15)
            if r.status_code != 200:
                continue

            gist_ids = re.findall(r'href="/([a-zA-Z0-9][a-zA-Z0-9-]*/[a-f0-9]{20,})"', r.text)
            gist_ids = list(dict.fromkeys(gist_ids))[:8]

            for gid in gist_ids:
                if gid in seen:
                    continue
                seen.add(gid)
                try:
                    raw_url = f"https://gist.githubusercontent.com/{gid}/raw"
                    r2 = session.get(raw_url, timeout=10)
                    if r2.status_code == 200:
                        entries = extract_proxies(r2.text)
                        with threading.Lock():
                            for proxy, proto in entries:
                                if proxy not in results:
                                    results[proxy] = proto
                                    added[0] += 1
                    time.sleep(0.2)
                except Exception:
                    pass

            print(f"  {dim(f'query: {query[:40]}')}  {cp(G, str(added[0]))} found so far  ", end="\r")
            time.sleep(1)

        except Exception:
            continue

    print()
    print(f"  {cp(G, '[+]')} Gists: {cp(G, str(added[0]))} new proxies\n")
    return results, added[0]

def scrape_html_site(url, session):
    found = []
    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            return found
        pattern = re.compile(
            r'<td[^>]*>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>\s*<td[^>]*>(\d{2,5})</td>',
            re.IGNORECASE
        )
        for m in pattern.finditer(r.text):
            ip, port = m.group(1), m.group(2)
            try:
                ipaddress.ip_address(ip)
                if 1 <= int(port) <= 65535:
                    found.append((f"{ip}:{port}", "http"))
            except ValueError:
                pass
        if not found:
            found = extract_proxies(r.text)
    except Exception:
        pass
    return found

def scrape_html(state):
    session = make_session()
    results = {}
    added = [0]

    print(f"\n  {cp(C, '[HTML]')} Scraping {cp(C, str(len(SOURCES_HTML)))} HTML proxy sites ...\n")

    for i, url in enumerate(SOURCES_HTML):
        entries = scrape_html_site(url, session)
        n = 0
        for proxy, proto in entries:
            if proxy not in results:
                results[proxy] = proto
                n += 1
        added[0] += n
        status = cp(G, str(len(entries))) if entries else cp(R, "0")
        print(f"  {dim(f'[{i+1}/{len(SOURCES_HTML)}]')}  {dim(url[:55])}  {status} proxies  ", end="\r")
        time.sleep(0.5)

    print()
    print(f"  {cp(G, '[+]')} HTML: {cp(G, str(added[0]))} new proxies\n")
    return results, added[0]

def scrape_tor(state):
    try:
        import socks  # noqa
    except ImportError:
        print(f"\n  {cp(R, '[TOR]')} SOCKS support not installed.")
        print(f"  {dim('Run: pip install requests[socks] --break-system-packages')}\n")
        input(dim("  press enter ...")); return {}, 0

    tor_proxy = state.settings["tor_proxy"]
    proxies = {"http": tor_proxy, "https": tor_proxy}
    session = make_session(proxies=proxies)
    results = {}
    added = [0]

    print(f"\n  {cp(C, '[TOR]')} Scraping {cp(C, str(len(SOURCES_TOR)))} .onion sources via {dim(tor_proxy)} ...\n")
    print(f"  {dim('Note: .onion addresses may be stale — unreachable is expected')}\n")

    for i, url in enumerate(SOURCES_TOR):
        try:
            r = session.get(url, timeout=30)
            if r.status_code == 200:
                entries = extract_proxies(r.text)
                with threading.Lock():
                    for proxy, proto in entries:
                        if proxy not in results:
                            results[proxy] = proto
                            added[0] += 1
                status = cp(G, str(len(entries)))
            else:
                status = cp(R, str(r.status_code))
        except Exception:
            status = cp(R, "unreachable")

        print(f"  {dim(f'[{i+1}/{len(SOURCES_TOR)}]')}  {dim(url[:55])}  {status}  ", end="\r")

    print()
    print(f"  {cp(G, '[+]')} Tor: {cp(G, str(added[0]))} new proxies\n")
    return results, added[0]
