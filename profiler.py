#!/usr/bin/env python3
import time
import requests
from ui import cp, dim, G, Y, C, R, P, B, RST
from constants import IP_API_FIELDS, IP_API_BATCH, RESIDENTIAL_KEYWORDS, MOBILE_KEYWORDS, DC_KEYWORDS

def classify_type(isp, org, hosting):
    txt = f"{isp} {org}".lower()
    if hosting:
        return "datacenter"
    if any(k in txt for k in MOBILE_KEYWORDS):
        return "mobile"
    if any(k in txt for k in RESIDENTIAL_KEYWORDS):
        return "residential"
    if any(k in txt for k in DC_KEYWORDS):
        return "datacenter"
    return "unknown"

def score_proxy(latency, ptype, hosting):
    if latency < 0.5:
        speed = 40
    elif latency < 1.0:
        speed = 35
    elif latency < 2.0:
        speed = 25
    elif latency < 3.0:
        speed = 15
    elif latency < 5.0:
        speed = 5
    else:
        speed = 0
    tscores = {"residential": 40, "mobile": 35, "unknown": 20, "datacenter": 5}
    return min(100, speed + tscores.get(ptype, 20) + (0 if hosting else 20))

def run_profile(state):
    if not state.valid:
        print(f"\n{cp(R, '[!]')} No validated proxies — validate first.\n")
        input(dim("  press enter ...")); return

    proxies = state.valid
    total = len(proxies)
    chunks = [proxies[i:i + 100] for i in range(0, total, 100)]
    profiled = []

    print(f"\n{cp(C, '[*]')} Profiling {cp(C, str(total))} proxies via ip-api.com ...\n")

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

    state.profiled = sorted(profiled, key=lambda x: x["score"], reverse=True)
    print(f"\n\n{cp(G, '[+]')} Profiling complete\n")
    input(dim("  press enter to continue ..."))
