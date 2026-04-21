#!/usr/bin/env python3
import os
from colorama import Fore, Style, init

init(autoreset=True)

P = Fore.MAGENTA
C = Fore.CYAN
G = Fore.GREEN
Y = Fore.YELLOW
R = Fore.RED
W = Fore.WHITE
DIM = Style.DIM
B = Style.BRIGHT
RST = Style.RESET_ALL

def cp(color, text):
    return f"{color}{B}{text}{RST}"

def dim(text):
    return f"{DIM}{text}{RST}"

def clr():
    os.system("clear")

BANNER = f"""{P}{B}
 ██████╗ ██████╗  ██████╗ ██╗  ██╗██╗   ██╗
 ██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝╚██╗ ██╔╝
 ██████╔╝██████╔╝██║   ██║ ╚███╔╝  ╚████╔╝
 ██╔═══╝ ██╔══██╗██║   ██║ ██╔██╗   ╚██╔╝
 ██║     ██║  ██║╚██████╔╝██╔╝ ██╗   ██║
 ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝{RST}{C}{B}
 ██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗
 ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗
 ███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝
 ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗
 ██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║
 ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝{RST}
 {DIM}Scrape · Filter · Validate · Profile · Score{RST}
"""

def progress_bar(filled, total, width=40, color=P):
    pct = filled / total if total > 0 else 0
    n = int(pct * width)
    return f"{color}{'█' * n}{DIM}{'░' * (width - n)}{RST}"

def type_badge(t):
    cols = {"residential": G, "mobile": C, "datacenter": R, "unknown": DIM}
    return f"{cols.get(t, DIM)}{B}[{t[:4].upper()}]{RST}"

def stars(score):
    n = 5 if score >= 80 else 4 if score >= 60 else 3 if score >= 45 else 2 if score >= 30 else 1
    col = G if score >= 60 else Y if score >= 35 else R
    return f"{col}{B}{'★' * n}{'☆' * (5 - n)}{RST}"

def lat_col(l):
    return G if l < 2 else Y if l < 4 else R
