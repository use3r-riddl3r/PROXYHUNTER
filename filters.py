#!/usr/bin/env python3
import ipaddress
import requests
from ui import progress_bar, cp, dim, P, DIM, G, R, Y
from constants import DC_CIDRS_FALLBACK, CIDR_FETCH_URLS

def load_dc_networks(lines):
    nets = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            nets.append(ipaddress.ip_network(line, strict=False))
        except ValueError:
            pass
    return nets

def fetch_fresh_cidrs():
    print(f"\n  {cp(P, '[*]')} Fetching DC CIDR list ...", end="", flush=True)
    for url in CIDR_FETCH_URLS:
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 200:
                nets = load_dc_networks(r.text.splitlines())
                if nets:
                    print(f"  {cp(G, str(len(nets)))} ranges loaded")
                    return nets
        except Exception:
            continue
    nets = load_dc_networks(DC_CIDRS_FALLBACK)
    print(f"  {cp(Y, 'fallback')} ({len(nets)} ranges)")
    return nets

def run_cidr_filter(state):
    if not state.raw_proxies:
        print(f"\n{cp(R, '[!]')} No raw proxies — scrape first.\n")
        input(dim("  press enter ...")); return

    if not state.dc_networks:
        state.dc_networks = fetch_fresh_cidrs()

    items = list(state.raw_proxies.items())
    total = len(items)
    kept = {}
    dropped = 0

    print(f"\n  {cp(P, '[*]')} CIDR filtering {cp(P, str(total))} proxies ...\n")

    for i, (proxy, proto) in enumerate(items):
        ip = proxy.split(":")[0]
        try:
            ip_obj = ipaddress.ip_address(ip)
            if any(ip_obj in net for net in state.dc_networks):
                dropped += 1
            else:
                kept[proxy] = proto
        except ValueError:
            dropped += 1

        if i % 500 == 0 or i == total - 1:
            bar = progress_bar(len(kept), total, 40)
            print(f"  {bar}  {cp(G, str(len(kept)))} kept  {cp(R, str(dropped))} dropped  ", end="\r")

    print()
    state.filtered = kept
    pct_d = round((dropped / total) * 100, 1) if total else 0
    print(f"\n  {cp(G, '[+]')} {cp(G, str(len(kept)))} kept  {cp(R, str(dropped))} DC dropped ({pct_d}%)\n")
    input(dim("  press enter to continue ..."))
