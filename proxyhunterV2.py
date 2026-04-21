#!/usr/bin/env python3
import sys
import time
import json
import os

try:
    import requests
except ImportError:
    print("pip install requests colorama"); sys.exit(1)

try:
    from colorama import Fore
except ImportError:
    print("pip install colorama"); sys.exit(1)

from ui import cp, dim, clr, BANNER, P, C, G, R, Y, B, DIM, RST, type_badge, stars, lat_col
from state import State
from constants import SOURCES_GITHUB, SOURCES_API, TELEGRAM_CHANNELS, SOURCES_HTML
from scraper import scrape_github_api, scrape_telegram, scrape_gists, scrape_html, scrape_tor
from filters import run_cidr_filter
from validator import run_port_filter, run_validate
from profiler import run_profile
from xray_handler import run_xray_scrape, run_xray_cidr_filter, run_xray_port_check, run_xray_profile, _xray_uris
from format_converter import run_format_converter

state = State()

def apply_preset(mode):
    s = state.settings
    if mode == "quick":
        s["source_tier"] = 1
        s["src_github"] = True
        s["src_api"] = True
        s["src_telegram"] = False
        s["src_gists"] = False
        s["src_html"] = False
        s["src_tor"] = False
    elif mode == "standard":
        s["source_tier"] = 2
        s["src_github"] = True
        s["src_api"] = True
        s["src_telegram"] = True
        s["src_gists"] = False
        s["src_html"] = False
        s["src_tor"] = False
    elif mode == "full":
        s["source_tier"] = 3
        s["src_github"] = True
        s["src_api"] = True
        s["src_telegram"] = True
        s["src_gists"] = True
        s["src_html"] = True
        s["src_tor"] = True

def source_selection_menu():
    while True:
        clr(); print(BANNER)
        s = state.settings
        t = s["source_tier"]
        g1 = sum(1 for _, _, tier in SOURCES_GITHUB if tier == 1)
        g12 = sum(1 for _, _, tier in SOURCES_GITHUB if tier <= 2)
        g3 = len(SOURCES_GITHUB)
        g_n = g1 if t == 1 else g12 if t == 2 else g3
        tg_n = len(TELEGRAM_CHANNELS) + len(s["extra_telegram"])

        def tick(key):
            return cp(G, "✓") if s[key] else cp(R, "✗")

        print(f"{P}{B}  SOURCE SELECTION{RST}\n")
        print(f"  {dim('── PRESETS ──────────────────────────────────────')}")
        print(f"  {cp(C, '[Q]')} Quick     {dim('T1 GitHub + APIs only  (~fastest)')}")
        print(f"  {cp(C, '[S]')} Standard  {dim('T1+T2 GitHub + APIs + Telegram')}")
        print(f"  {cp(C, '[F]')} Full      {dim('Everything including Gists+HTML+Tor')}")
        print(f"\n  {dim('── CATEGORIES ───────────────────────────────')}")
        print(f"  {cp(Y, '[1]')} {tick('src_github')}  GitHub Lists   {dim(f'{g_n} sources at tier ≤{t}')}")
        print(f"  {cp(Y, '[2]')} {tick('src_api')}  API Endpoints  {dim(f'{len(SOURCES_API)} endpoints')}")
        print(f"  {cp(Y, '[3]')} {tick('src_telegram')}  Telegram       {dim(f'{tg_n} channels')}")
        print(f"  {cp(Y, '[4]')} {tick('src_gists')}  GitHub Gists   {dim('searches')}")
        print(f"  {cp(Y, '[5]')} {tick('src_html')}  HTML Scrapers  {dim(f'{len(SOURCES_HTML)} sites')}")
        tor_addr = s["tor_proxy"][:25]
        print(f"  {cp(Y, '[6]')} {tick('src_tor')}  Tor .onion     {dim(f'via {tor_addr}')}")
        print(f"\n  {dim('── OPTIONS ──────────────────────────────────────')}")
        print(f"  {cp(Y, '[T]')} GitHub Tier  : {cp(Y, str(t))}  {dim(f'(1={g1}  2={g12}  3={g3} sources)')}")
        print(f"  {cp(Y, '[A]')} Add Telegram channel")
        print(f"\n  {cp(G, '[G]')} {cp(G, 'Go — start scraping')}")
        print(f"  {dim('[0]')} Back\n")

        choice = input(f"  {P}{B}>{RST} ").strip().lower()

        if choice == "q":
            apply_preset("quick")
        elif choice == "s":
            apply_preset("standard")
        elif choice == "f":
            apply_preset("full")
        elif choice == "1":
            s["src_github"] = not s["src_github"]
        elif choice == "2":
            s["src_api"] = not s["src_api"]
        elif choice == "3":
            s["src_telegram"] = not s["src_telegram"]
        elif choice == "4":
            s["src_gists"] = not s["src_gists"]
        elif choice == "5":
            s["src_html"] = not s["src_html"]
        elif choice == "6":
            s["src_tor"] = not s["src_tor"]
        elif choice == "t":
            v = input("  Tier (1/2/3): ").strip()
            if v in ("1", "2", "3"):
                s["source_tier"] = int(v)
        elif choice == "a":
            ch = input("  Channel name (without t.me/): ").strip()
            if ch and ch not in s["extra_telegram"]:
                s["extra_telegram"].append(ch)
                print(f"  {cp(G, '[+]')} Added: {ch}")
                time.sleep(0.8)
        elif choice == "g":
            return True
        elif choice == "0":
            return False

def run_scrape(skip_menu=False):
    if not skip_menu:
        if not source_selection_menu():
            return

    s = state.settings
    results = {}
    totals = {}

    clr(); print(BANNER)
    print(f"{P}{B}  SCRAPING{RST}\n")

    if s["src_github"] or s["src_api"]:
        res, n = scrape_github_api(state)
        results.update(res)
        totals["github/api"] = n

    if s["src_telegram"]:
        before = len(results)
        res, n = scrape_telegram(state)
        results.update(res)
        totals["telegram"] = len(results) - before

    if s["src_gists"]:
        before = len(results)
        res, n = scrape_gists(state)
        results.update(res)
        totals["gists"] = len(results) - before

    if s["src_html"]:
        before = len(results)
        res, n = scrape_html(state)
        results.update(res)
        totals["html"] = len(results) - before

    if s["src_tor"]:
        before = len(results)
        res, n = scrape_tor(state)
        results.update(res)
        totals["tor"] = len(results) - before

    state.raw_proxies = results
    state.filtered = {}
    state.valid = []
    state.profiled = []
    state.last_sources = totals

    print(f"\n{P}{B}  ── SCRAPE SUMMARY ──────────────────────────{RST}")
    for cat, n in totals.items():
        bar_n = min(30, int((n / max(totals.values(), default=1)) * 30))
        bar = f"{P}{'█' * bar_n}{DIM}{'░' * (30 - bar_n)}{RST}"
        print(f"  {cp(C, cat.ljust(12))}  {bar}  {cp(G, str(n))}")
    print(f"\n  {cp(G, '[+]')} Total: {cp(G, str(len(results)))} unique proxies\n")
    input(dim("  press enter to continue ..."))

def run_full_pipeline():
    clr(); print(BANNER)
    if not source_selection_menu():
        return
    clr(); print(BANNER)
    print(f"{P}{B}  FULL PIPELINE{RST}  {dim('Scrape → CIDR Filter → Port Check → Validate → Profile')}\n")

    run_scrape(skip_menu=True)
    clr(); print(BANNER)
    run_cidr_filter(state)
    clr(); print(BANNER)
    run_port_filter(state)
    clr(); print(BANNER)
    run_validate(state)
    clr(); print(BANNER)
    run_profile(state)

def status_bar():
    r = len(state.raw_proxies)
    f = len(state.filtered)
    v = len(state.valid)
    p = len(state.profiled)
    a = f" {DIM}→{RST} "
    return (f"  {dim('raw:')} {cp(C, str(r))}{a}"
            f"{dim('filtered:')} {cp(Y, str(f))}{a}"
            f"{dim('live:')} {cp(G, str(v))}{a}"
            f"{dim('profiled:')} {cp(P, str(p))}")

def show_results():
    data = state.profiled or state.valid
    if not data:
        print(f"\n{cp(R, '[!]')} No results yet.\n")
        input(dim("  press enter ...")); return

    rows = state.settings["show_rows"]
    profiled = bool(state.profiled)
    clr(); print(BANNER)

    print(f"  {P}{B}{'─' * 108}{RST}")
    if profiled:
        print(f"  {'PROXY':<22} {'PROTO':<7} {'LAT':<7} {'TYPE':<13} {'SCORE':<6} {'STARS':<13} {'CC':<4} ISP")
    else:
        print(f"  {'PROXY':<22} {'PROTO':<7} {'LATENCY'}")
    print(f"  {P}{B}{'─' * 108}{RST}")

    for p in data[:rows]:
        lc = lat_col(p["latency"])
        if profiled:
            print(f"  {cp(C, p['proxy']):<22} {dim(p['proto']):<7} {lc}{B}{str(p['latency'])+'s':<7}{RST} "
                  f"{type_badge(p['type']):<13} {cp(Y, str(p['score'])):<7} {stars(p['score']):<13} "
                  f"{dim(p['cc']):<4} {dim(p['isp'][:45])}")
        else:
            print(f"  {cp(C, p['proxy']):<22} {dim(p['proto']):<7} {lc}{B}{p['latency']}s{RST}")

    print(f"  {P}{B}{'─' * 108}{RST}")
    print(f"\n  Showing {min(rows, len(data))} of {len(data)}\n")
    input(dim("  press enter to continue ..."))

def show_stats():
    data = state.profiled
    if not data:
        print(f"\n{cp(R, '[!]')} No profiled data.\n")
        input(dim("  press enter ...")); return

    total = len(data)
    by_type = {}
    for p in data:
        by_type.setdefault(p["type"], []).append(p)
    avg_sc = round(sum(p["score"] for p in data) / total, 1)
    avg_lat = round(sum(p["latency"] for p in data) / total, 2)
    top_cc = {}
    for p in data:
        top_cc[p["cc"]] = top_cc.get(p["cc"], 0) + 1
    top_cc = sorted(top_cc.items(), key=lambda x: -x[1])[:8]

    clr(); print(BANNER)
    print(f"\n{P}{B}  ╔{'═' * 62}╗")
    print(f"  ║{'  PROXY HUNTER — SESSION STATS':^62}║")
    print(f"  ╠{'═' * 62}╣{RST}")
    print(f"{P}{B}  ║{RST}  Raw scraped    : {cp(C, str(len(state.raw_proxies))):<42}{P}{B}║{RST}")
    if state.filtered:
        print(f"{P}{B}  ║{RST}  After filters  : {cp(Y, str(len(state.filtered))):<42}{P}{B}║{RST}")
    print(f"{P}{B}  ║{RST}  Live validated  : {cp(G, str(len(state.valid))):<42}{P}{B}║{RST}")
    print(f"{P}{B}  ║{RST}  Profiled        : {cp(G, str(total)):<42}{P}{B}║{RST}")
    print(f"{P}{B}  ║{RST}  Avg score       : {cp(Y, str(avg_sc)):<42}{P}{B}║{RST}")
    print(f"{P}{B}  ║{RST}  Avg latency     : {cp(C, str(avg_lat)+'s'):<42}{P}{B}║{RST}")

    if state.last_sources:
        print(f"{P}{B}  ╠{'═' * 62}╣{RST}")
        print(f"{P}{B}  ║{'  SOURCE BREAKDOWN':^62}║{RST}")
        print(f"{P}{B}  ╠{'═' * 62}╣{RST}")
        mx = max(state.last_sources.values(), default=1)
        for cat, n in state.last_sources.items():
            bar_n = int((n / mx) * 28)
            bar = f"{C}{'█' * bar_n}{DIM}{'░' * (28 - bar_n)}{RST}"
            print(f"{P}{B}  ║{RST}  {cp(C, cat.ljust(12))}  {cp(G, str(n).rjust(6))}  {bar}  {P}{B}║{RST}")

    print(f"{P}{B}  ╠{'═' * 62}╣{RST}")
    print(f"{P}{B}  ║{'  TYPE BREAKDOWN':^62}║{RST}")
    print(f"{P}{B}  ╠{'═' * 62}╣{RST}")
    for t in ["residential", "mobile", "unknown", "datacenter"]:
        if t not in by_type:
            continue
        items = by_type[t]
        avg = round(sum(p["score"] for p in items) / len(items), 1)
        col = {"residential": G, "mobile": C, "datacenter": R, "unknown": DIM}.get(t, DIM)
        label = f"{col}{B}{t.upper():<14}{RST}"
        bar_n = int((len(items) / total) * 28)
        bar = f"{col}{'█' * bar_n}{DIM}{'░' * (28 - bar_n)}{RST}"
        print(f"{P}{B}  ║{RST}  {label} {cp(C, str(len(items)).rjust(5))}  {bar}  avg {cp(Y, str(avg))} {P}{B}║{RST}")

    print(f"{P}{B}  ╠{'═' * 62}╣{RST}")
    print(f"{P}{B}  ║{'  TOP COUNTRIES':^62}║{RST}")
    print(f"{P}{B}  ╠{'═' * 62}╣{RST}")
    for cc, cnt in top_cc:
        bar_n = int((cnt / total) * 28)
        bar = f"{C}{'█' * bar_n}{DIM}{'░' * (28 - bar_n)}{RST}"
        print(f"{P}{B}  ║{RST}  {cp(C, cc.ljust(4))}  {cp(G, str(cnt).rjust(5))}  {bar}  {P}{B}║{RST}")
    print(f"{P}{B}  ╚{'═' * 62}╝{RST}\n")
    input(dim("  press enter to continue ..."))

def run_export():
    data = state.profiled or state.valid
    if not data:
        print(f"\n{cp(R, '[!]')} Nothing to export.\n")
        input(dim("  press enter ...")); return

    clr(); print(BANNER)
    print(f"{P}{B}  EXPORT{RST}\n")
    print(f"  {cp(C, '[1]')} All live")
    print(f"  {cp(G, '[2]')} Residential only")
    print(f"  {cp(C, '[3]')} Mobile only")
    print(f"  {cp(Y, '[4]')} Residential + Mobile  {dim('(best for automation)')}")
    print(f"  {cp(C, '[5]')} Custom  {dim('(min score + type)')}")
    print(f"  {cp(P, '[6]')} Full JSON profiles")
    print(f"\n  {dim('[0]')} Back\n")

    choice = input(f"  {P}{B}>{RST} ").strip()
    if choice == "0":
        return

    fname = input(f"\n  Filename {dim('[proxies.txt]')}: ").strip() or "proxies.txt"

    def write_list(items, path):
        with open(path, "w") as f:
            f.writelines(p["proxy"] + "\n" for p in items)
        print(f"\n  {cp(G, '[+]')} {len(items)} proxies → {cp(C, path)}")

    if choice == "1":
        write_list(data, fname)
    elif choice == "2":
        write_list([p for p in data if p.get("type") == "residential"], fname)
    elif choice == "3":
        write_list([p for p in data if p.get("type") == "mobile"], fname)
    elif choice == "4":
        write_list([p for p in data if p.get("type") in ("residential", "mobile")], fname)
    elif choice == "5":
        min_sc = int(input(f"  Min score {dim('[0]')}: ").strip() or "0")
        ft = input(f"  Type {dim('[all/residential/mobile/datacenter]')}: ").strip() or "all"
        write_list([p for p in data if p.get("score", 0) >= min_sc and (ft == "all" or p.get("type") == ft)], fname)
    elif choice == "6":
        fname = fname.replace(".txt", ".json")
        with open(fname, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\n  {cp(G, '[+]')} Full profiles → {cp(C, fname)}")

    input(f"\n  {dim('press enter to continue ...')}")

def run_load():
    clr(); print(BANNER)
    print(f"{P}{B}  LOAD FROM FILE{RST}\n")
    path = input("  File path: ").strip()
    if not path or not os.path.exists(path):
        print(f"\n  {cp(R, '[!]')} File not found.\n")
        input(dim("  press enter ...")); return

    raw = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            for proto in ("socks5", "socks4", "http", "https"):
                if line.startswith(proto + "://"):
                    raw[line.split("://")[1]] = proto
                    break
            else:
                raw[line] = "http"

    state.raw_proxies = raw
    state.filtered = {}
    state.valid = []
    state.profiled = []
    print(f"\n  {cp(G, '[+]')} Loaded {cp(G, str(len(raw)))} proxies\n")
    input(dim("  press enter to continue ..."))

def run_settings():
    while True:
        clr(); print(BANNER)
        s = state.settings
        print(f"{P}{B}  SETTINGS{RST}\n")
        print(f"  {cp(C, '[1]')} Protocols         : {cp(Y, ', '.join(s['protocols']))}")
        print(f"  {cp(C, '[2]')} Validate threads   : {cp(Y, str(s['threads']))}")
        print(f"  {cp(C, '[3]')} Port-check threads : {cp(Y, str(s['port_threads']))}")
        print(f"  {cp(C, '[4]')} Scrape threads     : {cp(Y, str(s['scrape_threads']))}")
        print(f"  {cp(C, '[5]')} Validate timeout   : {cp(Y, str(s['timeout'])+'s')}")
        print(f"  {cp(C, '[6]')} Port timeout       : {cp(Y, str(s['port_timeout'])+'s')}")
        print(f"  {cp(C, '[7]')} Table rows         : {cp(Y, str(s['show_rows']))}")
        print(f"  {cp(C, '[8]')} Tor proxy          : {cp(Y, s['tor_proxy'])}")
        print(f"\n  {dim('[0]')} Back\n")

        c = input(f"  {P}{B}>{RST} ").strip()
        if c == "0":
            break
        elif c == "1":
            v = input("  Protocols (e.g. http,socks5): ").strip()
            if v:
                s["protocols"] = [p.strip() for p in v.split(",")]
        elif c == "2":
            v = input("  Threads: ").strip()
            if v.isdigit():
                s["threads"] = int(v)
        elif c == "3":
            v = input("  Port threads: ").strip()
            if v.isdigit():
                s["port_threads"] = int(v)
        elif c == "4":
            v = input("  Scrape threads: ").strip()
            if v.isdigit():
                s["scrape_threads"] = int(v)
        elif c == "5":
            v = input("  Validate timeout: ").strip()
            if v.isdigit():
                s["timeout"] = int(v)
        elif c == "6":
            v = input("  Port timeout: ").strip()
            try:
                s["port_timeout"] = float(v)
            except ValueError:
                pass
        elif c == "7":
            v = input("  Rows: ").strip()
            if v.isdigit():
                s["show_rows"] = int(v)
        elif c == "8":
            v = input("  Tor proxy URL: ").strip()
            if v:
                s["tor_proxy"] = v

def xray_status_bar():
    r = len(state.xray_nodes)
    f = len(state.xray_filtered)
    a = len(state.xray_alive)
    p = len(state.xray_profiled)
    sep = f" {DIM}→{RST} "
    return (f"  {dim('xray raw:')} {cp(P, str(r))}{sep}"
            f"{dim('filtered:')} {cp(Y, str(f))}{sep}"
            f"{dim('alive:')} {cp(G, str(a))}{sep}"
            f"{dim('profiled:')} {cp(P, str(p))}")

def xray_show_stats():
    data = state.xray_profiled or state.xray_alive
    if not data:
        print(f"\n  {cp(R, '[!]')} No Xray data in session.\n")
        input(dim("  press enter ...")); return

    profiled = bool(state.xray_profiled)
    total = len(data)

    proto_counts = {}
    for p in data:
        proto_counts[p["proto"]] = proto_counts.get(p["proto"], 0) + 1

    clr(); print(BANNER)
    print(f"\n{P}{B}  ╔{'═' * 62}╗")
    print(f"  ║{'  PROXY HUNTER — XRAY STATS':^62}║")
    print(f"  ╠{'═' * 62}╣{RST}")
    print(f"{P}{B}  ║{RST}  Raw scraped    : {cp(C, str(len(state.xray_nodes))):<42}{P}{B}║{RST}")
    if state.xray_filtered:
        print(f"{P}{B}  ║{RST}  After CIDR     : {cp(Y, str(len(state.xray_filtered))):<42}{P}{B}║{RST}")
    print(f"{P}{B}  ║{RST}  Alive (port ✓) : {cp(G, str(len(state.xray_alive))):<42}{P}{B}║{RST}")
    if profiled:
        avg_sc = round(sum(p["score"] for p in data) / total, 1)
        avg_lat = round(sum(p["latency"] for p in data) / total, 2)
        print(f"{P}{B}  ║{RST}  Profiled       : {cp(G, str(total)):<42}{P}{B}║{RST}")
        print(f"{P}{B}  ║{RST}  Avg score      : {cp(Y, str(avg_sc)):<42}{P}{B}║{RST}")
        print(f"{P}{B}  ║{RST}  Avg latency    : {cp(C, str(avg_lat)+'s'):<42}{P}{B}║{RST}")

    print(f"{P}{B}  ╠{'═' * 62}╣{RST}")
    print(f"{P}{B}  ║{'  PROTOCOL BREAKDOWN':^62}║{RST}")
    print(f"{P}{B}  ╠{'═' * 62}╣{RST}")
    mx = max(proto_counts.values(), default=1)
    for proto, cnt in sorted(proto_counts.items(), key=lambda x: -x[1]):
        bar_n = int((cnt / mx) * 28)
        bar = f"{C}{'█' * bar_n}{DIM}{'░' * (28 - bar_n)}{RST}"
        print(f"{P}{B}  ║{RST}  {cp(C, proto.ljust(12))}  {cp(G, str(cnt).rjust(6))}  {bar}  {P}{B}║{RST}")

    print(f"{P}{B}  ╚{'═' * 62}╝{RST}\n")

    rows = state.settings["show_rows"]
    print(f"  {P}{B}{'─' * 108}{RST}")
    print(f"  {'NODE':<40} {'PROTO':<9} {'LAT':<7}")
    print(f"  {P}{B}{'─' * 108}{RST}")
    for p in data[:rows]:
        lc = lat_col(p["latency"])
        node = p.get("proxy", "?")
        print(f"  {cp(C, node):<40} {dim(p['proto']):<9} {lc}{B}{str(p['latency'])+'s':<7}{RST}")
    print(f"  {P}{B}{'─' * 108}{RST}")
    print(f"\n  Showing {min(rows, len(data))} of {total}\n")
    input(dim("  press enter to continue ..."))

def xray_export():
    import base64
    from xray_handler import _parse_xray_host_port

    raw = state.xray_profiled or state.xray_alive or state.xray_filtered or state.xray_nodes
    if not raw:
        print(f"\n  {cp(R, '[!]')} Nothing to export.\n")
        input(dim("  press enter ...")); return

    src = _xray_uris(raw)
    label = ("profiled" if state.xray_profiled else "alive" if state.xray_alive else "filtered" if state.xray_filtered else "raw")

    clr(); print(BANNER)
    print(f"{P}{B}  XRAY EXPORT{RST}  {dim(f'{len(src)} {label} nodes')}\n")
    print(f"  {cp(C, '[1]')} Raw URI list          {dim('one vmess/vless/trojan/ss per line')}")
    print(f"  {cp(C, '[2]')} Base64 subscription   {dim('paste into V2RayNG / Throne')}")
    print(f"  {cp(C, '[3]')} Clash YAML proxies    {dim('for Mihomo/Clash Meta configs')}")
    print(f"\n  {dim('[0]')} Back\n")

    choice = input(f"  {P}{B}>{RST} ").strip()
    if choice == "0":
        return

    fname = input(f"\n  Filename {dim('[xray_export.txt]')}: ").strip() or "xray_export.txt"

    if choice == "1":
        with open(fname, "w") as f:
            f.write("\n".join(src))
        print(f"\n  {cp(G, '[+]')} {len(src)} nodes → {cp(C, fname)}\n")

    elif choice == "2":
        blob = base64.b64encode("\n".join(src).encode()).decode()
        with open(fname, "w") as f:
            f.write(blob)
        print(f"\n  {cp(G, '[+]')} {len(src)} nodes → base64 sub → {cp(C, fname)}\n")

    elif choice == "3":
        out = fname.replace(".txt", ".yaml")
        with open(out, "w") as f:
            f.write("proxies:\n")
            for i, uri in enumerate(src):
                host, port = _parse_xray_host_port(uri)
                proto = uri.split("://")[0].lower()
                if host and port:
                    f.write(f"  - name: \"{proto}_{i+1}\"\n    type: {proto}\n    server: {host}\n    port: {port}\n")
        print(f"\n  {cp(G, '[+]')} Clash YAML → {cp(C, out)}\n")

    input(dim("  press enter ..."))

def xray_menu():
    while True:
        clr(); print(BANNER)
        print(xray_status_bar())
        print(f"\n  {P}{B}{'─' * 50}{RST}\n")
        print(f"  {cp(P, '[1]')} Full Pipeline    {dim('scrape → CIDR filter → port check → profile')}")
        print(f"  {P}{B}{'─' * 50}{RST}")
        print(f"  {cp(C, '[2]')} Scrape           {dim('GitHub subs + Telegram channels')}")
        print(f"  {cp(C, '[3]')} CIDR Filter      {dim('drop datacenter IPs')}")
        print(f"  {cp(C, '[4]')} Port Check       {dim('TCP connect to host:port')}")
        print(f"  {cp(C, '[5]')} Profile          {dim('ISP + type + score via ip-api')}")
        print(f"  {P}{B}{'─' * 50}{RST}")
        print(f"  {cp(C, '[6]')} Stats / View     {dim('protocol · type · country · score table')}")
        print(f"  {cp(G, '[7]')} Export / Convert {dim('URI · base64 · Clash YAML')}")
        print(f"\n  {dim('[0]')} Back  {dim('(nodes stay in session)')}\n")

        choice = input(f"  {P}{B}>{RST} ").strip()

        if choice == "0":
            return
        elif choice == "1":
            clr(); run_xray_scrape(state)
            clr(); print(BANNER); run_xray_cidr_filter(state)
            clr(); print(BANNER); run_xray_port_check(state)
            clr(); print(BANNER); run_xray_profile(state)
        elif choice == "2":
            clr(); run_xray_scrape(state)
        elif choice == "3":
            clr(); print(BANNER); run_xray_cidr_filter(state)
        elif choice == "4":
            clr(); print(BANNER); run_xray_port_check(state)
        elif choice == "5":
            clr(); print(BANNER); run_xray_profile(state)
        elif choice == "6":
            xray_show_stats()
        elif choice == "7":
            xray_export()

def vpn_check():
    try:
        ip = requests.get("https://api.ipify.org?format=json", timeout=6).json().get("ip", "?")
        geo = requests.get(f"http://ip-api.com/json/{ip}?fields=isp,country,hosting", timeout=6).json()
        isp = geo.get("isp", "?")
        country = geo.get("country", "?")
        hosting = geo.get("hosting", False)
        flag = f"{G}{B} ✔ VPN/DC exit{RST}" if hosting else f"{Y}{B} ⚠ check VPN{RST}"
        print(f"  {dim('Exit IP:')} {cp(C, ip)}  {dim(country)}  {dim('|')}  {dim(isp)}{flag}")
    except Exception:
        print(f"  {cp(R, '[!]')} Cannot verify exit IP")

def main_menu():
    clr(); print(BANNER)
    vpn_check()
    input(f"\n  {dim('press enter to continue ...')}")

    while True:
        clr(); print(BANNER)
        print(status_bar())
        print(f"\n  {P}{B}{'─' * 50}{RST}\n")
        print(f"  {cp(P, '[1]')} Full Pipeline    {dim('select sources → filter → validate → profile')}")
        print(f"  {P}{B}{'─' * 50}{RST}")
        print(f"  {cp(C, '[2]')} Scrape           {dim('choose sources interactively')}")
        print(f"  {cp(C, '[3]')} CIDR Filter      {dim('drop DC IPs  (local, instant)')}")
        print(f"  {cp(C, '[4]')} Port Check       {dim('drop dead ports  (TCP fast)')}")
        print(f"  {cp(C, '[5]')} Validate         {dim('confirm live proxies')}")
        print(f"  {cp(C, '[6]')} Profile          {dim('ISP + type + score')}")
        print(f"  {P}{B}{'─' * 50}{RST}")
        print(f"  {cp(C, '[7]')} View Results")
        print(f"  {cp(C, '[8]')} Stats")
        print(f"  {cp(G, '[9]')} Export")
        print(f"  {P}{B}{'─' * 50}{RST}")
        print(f"  {cp(P, '[X]')} Xray / V2Ray scraper  {dim('vmess · vless · trojan · ss')}")
        print(f"  {cp(Y, '[F]')} Format Converter       {dim('URI · Clash YAML · base64 sub · ip:port')}")
        print(f"  {cp(Y, '[L]')} Load from File")
        print(f"  {cp(Y, '[S]')} Settings")
        print(f"\n  {dim('[0]')} Exit\n")
        print(f"  {P}{B}{'─' * 50}{RST}\n")

        choice = input(f"  {P}{B}>{RST} ").strip().lower()

        if choice == "1":
            run_full_pipeline()
        elif choice == "2":
            run_scrape()
        elif choice == "3":
            clr(); print(BANNER); run_cidr_filter(state)
        elif choice == "4":
            clr(); print(BANNER); run_port_filter(state)
        elif choice == "5":
            clr(); print(BANNER); run_validate(state)
        elif choice == "6":
            clr(); print(BANNER); run_profile(state)
        elif choice == "7":
            show_results()
        elif choice == "8":
            show_stats()
        elif choice == "9":
            run_export()
        elif choice == "x":
            xray_menu()
        elif choice == "f":
            run_format_converter(state)
        elif choice == "l":
            run_load()
        elif choice == "s":
            run_settings()
        elif choice == "0":
            print(f"\n  {cp(P, 'bye')}\n"); sys.exit(0)

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n\n  {cp(Y, '[!]')} Interrupted\n")
        sys.exit(0)
