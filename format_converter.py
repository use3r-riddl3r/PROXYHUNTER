#!/usr/bin/env python3
import base64
import os
from ui import cp, dim, P, C, G, R
from xray_handler import _decode_sub, _parse_xray_host_port

def _xray_uris(src):
    if src and isinstance(src[0], dict):
        return [p["uri"] for p in src]
    return src

def run_format_converter(state):
    while True:
        print()
        from ui import clr, BANNER
        clr()
        print(BANNER)
        print(f"{P}  FORMAT CONVERTER{P}\n")
        print(f"  {dim('Works with session data or a file — no paths needed for session')}\n")
        print(f"  {cp(C, '[1]')} ip:port  →  URI scheme    {dim('protocol://ip:port  (Throne, V2RayNG)')}")
        print(f"  {cp(C, '[2]')} ip:port  →  Clash YAML    {dim('proxies: block for Mihomo/Clash Meta')}")
        print(f"  {cp(C, '[3]')} URI list →  Base64 sub    {dim('encode as subscription blob')}")
        print(f"  {cp(C, '[4]')} Base64   →  raw URI list  {dim('decode subscription → one URI per line')}")
        print(f"  {cp(C, '[5]')} URI list →  ip:port only  {dim('strip protocol, extract host:port')}")
        print(f"\n  {dim('[0]')} Back\n")

        choice = input(f"  {P}>{P} ").strip()
        if choice == "0":
            return
        if choice not in ("1", "2", "3", "4", "5"):
            continue

        lines = _fc_get_lines(state)
        if not lines:
            input(dim("  press enter ..."))
            continue

        out = input(f"\n  Output file {dim('[output.txt]')}: ").strip() or "output.txt"

        if choice == "1":
            proto = input(f"  Protocol {dim('[http/socks4/socks5]')}: ").strip() or "http"
            with open(out, "w") as f:
                for l in lines:
                    host = l.split("://")[-1] if "://" in l else l
                    f.write(f"{proto}://{host}\n")
            print(f"\n  {cp(G, '[+]')} {len(lines)} → URI  →  {cp(C, out)}\n")

        elif choice == "2":
            proto = input(f"  Protocol {dim('[http/socks5]')}: ").strip() or "http"
            ptype = "http" if proto in ("http", "https") else "socks5"
            with open(out, "w") as f:
                f.write("proxies:\n")
                for i, l in enumerate(lines):
                    host = l.split("://")[-1] if "://" in l else l
                    try:
                        ip, port = host.rsplit(":", 1)
                        f.write(f"  - name: proxy_{i+1}\n    type: {ptype}\n    server: {ip}\n    port: {port}\n")
                    except ValueError:
                        pass
            print(f"\n  {cp(G, '[+]')} {len(lines)} → Clash YAML  →  {cp(C, out)}\n")

        elif choice == "3":
            blob = base64.b64encode("\n".join(lines).encode()).decode()
            with open(out, "w") as f:
                f.write(blob)
            print(f"\n  {cp(G, '[+]')} {len(lines)} URIs → base64 sub  →  {cp(C, out)}\n")

        elif choice == "4":
            decoded = _decode_sub("\n".join(lines))
            with open(out, "w") as f:
                f.write("\n".join(decoded))
            print(f"\n  {cp(G, '[+]')} Decoded {len(decoded)} lines  →  {cp(C, out)}\n")

        elif choice == "5":
            extracted = []
            for l in lines:
                if "://" in l:
                    host = l.split("://")[1].split("?")[0].split("#")[0].split("@")[-1]
                    extracted.append(host)
                else:
                    extracted.append(l)
            with open(out, "w") as f:
                f.write("\n".join(extracted))
            print(f"\n  {cp(G, '[+]')} {len(extracted)} host:port  →  {cp(C, out)}\n")

        input(dim("  press enter ..."))

def _fc_get_lines(state):
    print(f"\n  {cp(C, '[S]')} Use session data")
    print(f"  {cp(C, '[F]')} Load from file\n")
    src = input(f"  {P}>{P} ").strip().lower()

    if src == "s":
        xray = _xray_uris(state.xray_profiled or state.xray_alive or state.xray_filtered or state.xray_nodes)
        http = [p["proxy"] for p in (state.profiled or state.valid)]
        if xray and http:
            print(f"\n  {cp(C, '[1]')} HTTP/SOCKS session  {dim(f'({len(http)} proxies)')}")
            print(f"  {cp(C, '[2]')} Xray session        {dim(f'({len(xray)} nodes)')}\n")
            pick = input(f"  {P}>{P} ").strip()
            return xray if pick == "2" else http
        elif xray:
            return xray
        elif http:
            return http
        else:
            print(f"\n  {cp(R, '[!]')} No session data.\n")
            return []
    else:
        path = input(f"  File path: ").strip()
        if not path or not os.path.exists(path):
            print(f"\n  {cp(R, '[!]')} File not found.\n")
            return []
        with open(path) as f:
            return [l.strip() for l in f if l.strip()]
