#!/usr/bin/env python3
import socket
import time
import threading
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from ui import progress_bar, cp, dim, C, G, R, DIM
from constants import TEST_URLS

def port_open(proxy_str, timeout=1.5):
    try:
        ip, port = proxy_str.rsplit(":", 1)
        sock = socket.create_connection((ip, int(port)), timeout=timeout)
        sock.close()
        return True
    except Exception:
        return False

def build_proxy_dict(proxy_str, proto):
    scheme = "http" if proto in ("http", "https") else proto
    return {"http": f"{scheme}://{proxy_str}", "https": f"{scheme}://{proxy_str}"}

def validate_one(proxy_str, proto, timeout):
    proxies = build_proxy_dict(proxy_str, proto)
    for url in TEST_URLS:
        try:
            t = time.time()
            r = requests.get(url, proxies=proxies, timeout=timeout, allow_redirects=True)
            if r.status_code == 200:
                return {"proxy": proxy_str, "proto": proto, "latency": round(time.time() - t, 2)}
        except Exception:
            continue
    return None

def run_port_filter(state):
    source = state.filtered or state.raw_proxies
    if not source:
        print(f"\n{cp(R, '[!]')} No proxies to port-check.\n")
        input(dim("  press enter ...")); return

    items = list(source.items())
    total = len(items)
    threads = state.settings["port_threads"]
    timeout = state.settings["port_timeout"]
    alive = {}
    done = [0]
    lock = threading.Lock()

    print(f"\n  {cp(C, '[*]')} Port check {cp(C, str(total))} proxies ({threads} threads, {timeout}s) ...\n")

    def worker(args):
        proxy, proto = args
        ok = port_open(proxy, timeout)
        with lock:
            done[0] += 1
            if ok:
                alive[proxy] = proto
            bar = progress_bar(done[0], total)
            print(f"  {bar}  {cp(G, str(len(alive)))} open  {dim(f'{done[0]}/{total}')}  ", end="\r")

    with ThreadPoolExecutor(max_workers=threads) as ex:
        list(as_completed({ex.submit(worker, i): i for i in items}))

    print()
    state.filtered = alive
    dropped = total - len(alive)
    pct_d = round((dropped / total) * 100, 1) if total else 0
    print(f"\n  {cp(G, '[+]')} {cp(G, str(len(alive)))} open  {cp(R, str(dropped))} closed ({pct_d}%)\n")
    input(dim("  press enter to continue ..."))

def run_validate(state):
    source = state.filtered or state.raw_proxies
    if not source:
        print(f"\n{cp(R, '[!]')} No proxies — scrape first.\n")
        input(dim("  press enter ...")); return

    items = list(source.items())
    total = len(items)
    threads = state.settings["threads"]
    timeout = state.settings["timeout"]
    valid = []
    done = [0]
    lock = threading.Lock()

    print(f"\n{cp(C, '[*]')} Validating {cp(C, str(total))} proxies ({threads} threads, {timeout}s) ...\n")

    def worker(args):
        result = validate_one(*args, timeout)
        with lock:
            done[0] += 1
            if result:
                valid.append(result)
            bar = progress_bar(done[0], total)
            print(f"  {bar}  {cp(G, str(len(valid)))} live  {dim(f'{done[0]}/{total}')}  ", end="\r")

    with ThreadPoolExecutor(max_workers=threads) as ex:
        list(as_completed({ex.submit(worker, i): i for i in items}))

    print()
    state.valid = valid
    print(f"\n{cp(G, '[+]')} {cp(G, str(len(valid)))} live proxies\n")
    input(dim("  press enter to continue ..."))
