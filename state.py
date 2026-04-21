#!/usr/bin/env python3

class State:
    def __init__(self):
        self.raw_proxies = {}
        self.filtered = {}
        self.valid = []
        self.profiled = []
        self.xray_nodes = []
        self.xray_filtered = []
        self.xray_alive = []
        self.xray_profiled = []
        self.dc_networks = []
        self.last_sources = {}
        self.settings = {
            "protocols": ["http", "socks4", "socks5"],
            "source_tier": 2,
            "threads": 50,
            "scrape_threads": 20,
            "port_threads": 200,
            "timeout": 8,
            "port_timeout": 1.5,
            "show_rows": 40,
            "tor_proxy": "socks5://127.0.0.1:9050",
            "src_github": True,
            "src_api": True,
            "src_telegram": False,
            "src_gists": False,
            "src_html": False,
            "src_tor": False,
            "extra_telegram": [],
        }
