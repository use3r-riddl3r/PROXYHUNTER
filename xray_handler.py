#!/usr/bin/env python3
import base64
import re
import json
import time
import ipaddress
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from ui import progress_bar, cp, dim, P, C, G, R, Y, DIM
from constants import (XRAY_RE, SOURCES_XRAY_SUB, XRAY_TELEGRAM_CHANNELS, 
                       IP_API_FIELDS, IP_API_BATCH, DC_CIDRS_FALLBACK, CIDR_FETCH_URLS)
from scraper import make_session, extract_proxies
from validator import port_open
from profiler import classify_type, score_proxy

def _xray_uris(src):
    if src and isinstance(src[0], dict):
        return [p["uri"] for p in src]
    return src

def _decode_sub(text):
    text = text.strip()
    try:
        padded = text + "=" * (-len(text) % 4)
        decoded = base64.b64decode(padded).decode("utf-8", errors="ignore")
        lines = [l.strip() for l in decoded.splitlines() if l.strip()]
        if any(l.startswith(("vmess://", "vless://", "trojan://", "ss://", "hysteria")) for l in lines):
            return lines
    except Exception:
        pass
    return [l.strip() for l in text.splitlines() if l.strip()]

def _extract_xray_uris(text):
    found = set()
    for line in _decode_sub(text):
        if any(line.startswith(p) for p in ("vmess://", "vless://", "trojan://", "ss://", "hysteria2://", "hysteria://", "tuic://")):
            found.add(line)
    for m in XRAY_RE.finditer(text):
        found.add(m.group(0))
    return found

def run_xray_scrape(state):
    print(f"\n  {cp(C, '[1/2]')} Fetching {cp(C, str(len(SOURCES_XRAY_SUB)))} subscription sources ...\n")
    session = make_session()
    found = set()
    total = len(SOURCES_XRAY_SUB)

    for i, url in enumerate(SOURCES_XRAY_SUB):
        try:
            r = session.get(url, timeout=15)
            if r.status_code == 200:
                uris = _extract_xray_uris(r.text)
                found.update(uris)
        except Exception:
            pass
        pct = (i + 1) / total
        bar = progress_bar(pct * total, total, 40, P)
        print(f"  {bar}  {cp(G, str(len(found)))} nodes  {dim(f'{i+1}/{total}')}  ", end="\r")

    print(f"\n\n  {cp(G, '[+]')} Subscriptions: {cp(G, str(len(found)))} nodes\n")

    print(f"  {cp(C, '[2/2]')} Scraping {cp(C, str(len(XRAY_TELEGRAM_CHANNELS)))} Telegram channels ...\n")
    tg_session = make_session(ua="Mozilla/5.0 (compatible; TelegramBot/1.0)")
    before = len(found)

    for i, ch in enumerate(XRAY_TELEGRAM_CHANNELS):
        try:
            r = tg_session.get(f"https://t.me/s/{ch}", timeout=15)
            if r.status_code == 200:
                uris = _extract_xray_uris(r.text)
                found.update(uris)
                msg_ids = re.findall(r'data-post="[^/]+/(\d+)"', r.text)
                if msg_ids:
                    oldest = min(int(m) for m in msg_ids)
                    r2 = tg_session.get(f"https://t.me/s/{ch}?before={oldest}", timeout=15)
                    if r2.status_code == 200:
                        found.update(_extract_xray_uris(r2.text))
        except Exception:
            pass
        status = cp(G, f"+{len(found)-before}") if len(found) > before else dim("0")
        print(f"  {dim(f'[{i+1}/{len(XRAY_TELEGRAM_CHANNELS)}]')}  {cp(C, f't.me/{ch}'):<40}  {status}  ", end="\r")
        before = len(found)
        time.sleep(0.3)

    print()
    nodes = sorted(found)
    state.xray_nodes = nodes

    protos = {}
    for n in nodes:
        p = n.split("://")[0].lower()
        protos[p] = protos.get(p, 0) + 1

    print(f"\n{P}  ── XRAY SUMMARY ─────────────────────────{P}")
    for proto, cnt in sorted(protos.items(), key=lambda x: -x[1]):
        bar_n = min(30, int((cnt / max(protos.values())) * 30))
        bar = f"{P}{'█' * bar_n}{DIM}{'░' * (30 - bar_n)}"
        print(f"  {cp(C, proto.ljust(12))}  {bar}  {cp(G, str(cnt))}")
    print(f"\n  {cp(G, '[+]')} Total: {cp(G, str(len(nodes)))} unique Xray nodes\n")
    input(dim("  press enter to continue ..."))

def _parse_xray_host_port(uri):
    try:
        proto = uri.split("://")[0].lower()
        rest = uri.split("://", 1)[1]

        if proto == "vmess":
            padded = rest.split("#")[0] + "=" * (-len(rest.split("#")[0]) % 4)
            cfg = json.loads(base64.b64decode(padded).decode("utf-8", errors="ignore"))
            return str(cfg.get("add", "")), int(cfg.get("port", 0))

        elif proto in ("vless", "trojan"):
            hostpart = rest.split("?")[0].split("#")[0]
            if "@" in hostpart:
                hostpart = hostpart.split("@", 1)[1]
            host, port = hostpart.rsplit(":", 1)
            return host.strip("[]"), int(port)

        elif proto == "ss":
            rest = rest.split("#")[0]
            if "@" in rest:
                hostpart = rest.rsplit("@", 1)[1].split("?")[0]
                host, port = hostpart.rsplit(":", 1)
                return host.strip("[]"), int(port)
            else:
                decoded = base64.b64decode(rest + "=" * (-len(rest) % 4)).decode("utf-8", errors="ignore")
                hostpart = decoded.split("@", 1)[1] if "@" in decoded else ""
                host, port = hostpart.rsplit(":", 1)
                return host.strip("[]"), int(port)

        elif proto in ("hysteria", "hysteria2", "tuic"):
            hostpart = rest.split("?")[0].split("#")[0]
            if "@" in hostpart:
                hostpart = hostpart.split("@", 1)[1]
            host, port = hostpart.rsplit(":", 1)
            return host.strip("[]"), int(port)

    except Exception:
        pass
    return None, None

def run_xray_cidr_filter(state):
    if not state.xray_nodes:
        print(f"\n  {cp(R, '[!]')} No Xray nodes — scrape first.\n")
        input(dim("  press enter ...")); return

    if not state.dc_networks:
        print(f"\n  {cp(P, '[*]')} Fetching DC CIDR list ...", end="", flush=True)
        for url in CIDR_FETCH_URLS:
            try:
                r = requests.get(url, timeout=15)
                if r.status_code == 200:
                    nets = []
                    for line in r.text.splitlines():
                        line = line.strip()
                        if line and not line.startswith("#"):
                            try:
                                nets.append(ipaddress.ip_network(line, strict=False))
                            except ValueError:
                                pass
                    if nets:
                        print(f"  {cp(G, str(len(nets)))} ranges loaded")
                        state.dc_networks = nets
                        break
            except Exception:
                continue
        if not state.dc_networks:
            nets = []
            for line in DC_CIDRS_FALLBACK:
                try:
                    nets.append(ipaddress.ip_network(line, strict=False))
                except ValueError:
                    pass
            print(f"  {cp(Y, 'fallback')} ({len(nets)} ranges)")
            state.dc_networks = nets

    kept = []
    dropped = 0
    total = len(state.xray_nodes)

    print(f"\n  {cp(P, '[*]')} CIDR filtering {cp(C, str(total))} Xray nodes ...\n")

    for i, uri in enumerate(state.xray_nodes):
        host, port = _parse_xray_host_port(uri)
        if not host:
            dropped += 1
            continue
        try:
            ip_obj = ipaddress.ip_address(host)
            if any(ip_obj in net for net in state.dc_networks):
                dropped += 1
            else:
                kept.append(uri)
        except ValueError:
            kept.append(uri)

        if i % 100 == 0 or i == total - 1:
            pct = (i + 1) / total
            bar = progress_bar(pct * total, total, 40, P)
            print(f"  {bar}  {cp(G, str(len(kept)))} kept  {cp(R, str(dropped))} dropped  ", end="\r")

    print()
    state.xray_filtered = kept
    pct_d = round((dropped / total) * 100, 1) if total else 0
    print(f"\n  {cp(G, '[+]')} {cp(G, str(len(kept)))} kept  {cp(R, str(dropped))} DC/invalid dropped ({pct_d}%)\n")
    input(dim("  press enter to continue ..."))

def run_xray_port_check(state):
    src = state.xray_filtered or state.xray_nodes
    if not src:
        print(f"\n  {cp(R, '[!]')} No Xray nodes — scrape first.\n")
        input(dim("  press enter ...")); return

    total = len(src)
    threads = state.settings["port_threads"]
    timeout = state.settings["port_timeout"]
    alive = []
    done = [0]
    lock = threading.Lock()

    print(f"\n  {cp(P, '[*]')} Port checking {cp(C, str(total))} Xray nodes ({threads} threads, {timeout}s) ...\n")

    def worker(uri):
        host, port = _parse_xray_host_port(uri)
        result = None
        if host and port:
            t0 = time.time()
            ok = port_open(f"{host}:{port}", timeout)
            if ok:
                result = {
                    "uri": uri,
                    "proxy": f"{host}:{port}",
                    "proto": uri.split("://")[0].lower(),
                    "latency": round(time.time() - t0, 2),
                }
        with lock:
            done[0] += 1
            if result:
                alive.append(result)
            pct = done[0] / total
            bar = progress_bar(pct * total, total, 40, C)
            print(f"  {bar}  {cp(G, str(len(alive)))} alive  {dim(f'{done[0]}/{total}')}  ", end="\r")

    with ThreadPoolExecutor(max_workers=threads) as ex:
        list(as_completed({ex.submit(worker, uri): uri for uri in src}))

    print()
    state.xray_alive = alive
    state.xray_profiled = []
    dropped = total - len(alive)
    pct_d = round((dropped / total) * 100, 1) if total else 0
    print(f"\n  {cp(G, '[+]')} {cp(G, str(len(alive)))} alive  {cp(R, str(dropped))} dead ({pct_d}%)\n")
    input(dim("  press enter to continue ..."))

def run_xray_profile(state):
    if not state.xray_alive:
        print(f"\n  {cp(R, '[!]')} No alive Xray nodes — run port check first.\n")
        input(dim("  press enter ...")); return

    proxies = state.xray_alive
    total = len(proxies)
    chunks = [proxies[i:i + 100] for i in range(0, total, 100)]
    profiled = []

    print(f"\n{cp(P, '[*]')} Profiling {cp(C, str(total))} Xray nodes via ip-api.com ...\n")

    for idx, chunk in enumerate(chunks):
        print(f"  {dim(f'Batch {idx+1}/{len(chunks)} ...')}    ", end="\r")
        payload = [{"query": p["proxy"].split(":")[0], "fields": IP_API_FIELDS} for p in chunk]
        try:
            r = requests.post(IP_API_BATCH, json=payload, timeout=15)
            geo = r.json() if r.status_code == 200 else [{}] * len(chunk)
        except Exception:
            geo = [{}] * len(chunk)

        for pd, g in zip(chunk, geo):
            if not g or g.get("status") != "success":
                g = {}
            isp = g.get("isp", "Unknown")
            org = g.get("org", "")
            hosting = g.get("hosting", False)
            ptype = classify_type(isp, org, hosting)
            sc = score_proxy(pd["latency"], ptype, hosting)
            profiled.append({
                **pd,
                "isp": isp, "org": org,
                "country": g.get("country", "?"), "cc": g.get("countryCode", "?"),
                "city": g.get("city", "?"), "hosting": hosting,
                "type": ptype, "score": sc
            })

        if idx < len(chunks) - 1:
            time.sleep(1.4)

    state.xray_profiled = sorted(profiled, key=lambda x: x["score"], reverse=True)
    print(f"\n\n{cp(G, '[+]')} Profiling complete\n")
    input(dim("  press enter to continue ..."))
