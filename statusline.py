#!/usr/bin/env python3
"""Claude Code statusline script - Windows native version"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import json
import math
import time
import subprocess
import os

def parse_input():
    import threading
    result = [{}]
    def _read():
        try:
            data = sys.stdin.buffer.read()
            if data and data.strip():
                result[0] = json.loads(data.decode('utf-8', errors='replace'))
        except Exception:
            pass
    t = threading.Thread(target=_read, daemon=True)
    t.start()
    t.join(timeout=1.0)
    return result[0]

data = parse_input()

# ── Parse fields ──────────────────────────────────────────────
MODEL       = data.get('model', {}).get('display_name', 'Claude')
DIR         = data.get('workspace', {}).get('current_dir', '')
COST        = float(data.get('cost', {}).get('total_cost_usd', 0) or 0)
PCT         = int(float(data.get('context_window', {}).get('used_percentage', 0) or 0))
CTX_SIZE    = data.get('context_window', {}).get('context_window_size')
DURATION_MS = int(data.get('cost', {}).get('total_duration_ms', 0) or 0)
LINES_ADD   = data.get('cost', {}).get('total_lines_added')
LINES_DEL   = data.get('cost', {}).get('total_lines_removed')
VIM_MODE    = data.get('vim', {}).get('mode', '')
AGENT       = data.get('agent', {}).get('name', '')
VERSION     = data.get('version', '')

RATE_5H     = data.get('rate_limits', {}).get('five_hour', {}).get('used_percentage')
RATE_7D     = data.get('rate_limits', {}).get('seven_day', {}).get('used_percentage')
RESET_5H    = data.get('rate_limits', {}).get('five_hour', {}).get('resets_at')
RESET_7D    = data.get('rate_limits', {}).get('seven_day', {}).get('resets_at')

ctx = data.get('context_window', {})
TOTAL_IN    = ctx.get('total_input_tokens')
TOTAL_OUT   = ctx.get('total_output_tokens')
API_MS      = int(data.get('cost', {}).get('total_api_duration_ms', 0) or 0)

cur = ctx.get('current_usage', {})
CACHE_READ   = cur.get('cache_read_input_tokens')
CACHE_CREATE = cur.get('cache_creation_input_tokens')
CUR_INPUT    = cur.get('input_tokens')

# ── ANSI Colors ───────────────────────────────────────────────
RESET   = '\033[0m'
BOLD    = '\033[1m'
DIM     = '\033[2m'
CYAN    = '\033[36m'
GREEN   = '\033[32m'
YELLOW  = '\033[33m'
RED     = '\033[31m'
MAGENTA = '\033[35m'
BLUE    = '\033[34m'
WHITE   = '\033[37m'
SEP     = f'{DIM} | {RESET}'

def color_pct(val):
    if val >= 80: return RED
    if val >= 50: return YELLOW
    return GREEN

def fmt_dur(ms):
    total = ms // 1000
    h, rem = divmod(total, 3600)
    m, s   = divmod(rem, 60)
    if h > 0:   return f'{h}h {m:02d}m'
    if m > 0:   return f'{m}m {s:02d}s'
    return f'{s}s'

def fmt_countdown(reset_at):
    if not reset_at or reset_at == 'null':
        return ''
    diff = int(reset_at) - int(time.time())
    if diff <= 0: return 'now'
    h, rem = divmod(diff, 3600)
    m = rem // 60
    return f'{h}h {m}m'

def fmt_tokens(t):
    if t is None or t == 'null': return '0'
    t = int(t)
    if t >= 1_000_000: return f'{t/1_000_000:.1f}M'
    if t >= 1_000:     return f'{t/1_000:.1f}K'
    return str(t)

# ── Git info ──────────────────────────────────────────────────
BRANCH = ''
REPO_LINK = os.path.basename(DIR) if DIR else ''
try:
    r = subprocess.run(
        ['git', '-C', DIR, 'branch', '--show-current'],
        capture_output=True, text=True, timeout=3
    )
    if r.returncode == 0:
        BRANCH = r.stdout.strip()

    remote = subprocess.run(
        ['git', '-C', DIR, 'remote', 'get-url', 'origin'],
        capture_output=True, text=True, timeout=3
    )
    if remote.returncode == 0:
        url = remote.stdout.strip()
        url = url.replace('git@github.com:', 'https://github.com/')
        if url.endswith('.git'):
            url = url[:-4]
        repo_name = url.split('/')[-1]
        REPO_LINK = f'\033]8;;{url}\a{repo_name}\033]8;;\a'
except Exception:
    pass

# ── Git file stats ─────────────────────────────────────────────
GIT_STATS = ''
try:
    m_r = subprocess.run(['git', '-C', DIR, 'diff', '--name-only'], capture_output=True, text=True, timeout=3)
    a_r = subprocess.run(['git', '-C', DIR, 'ls-files', '--others', '--exclude-standard'], capture_output=True, text=True, timeout=3)
    d_r = subprocess.run(['git', '-C', DIR, 'diff', '--diff-filter=D', '--name-only'], capture_output=True, text=True, timeout=3)
    gm = len([x for x in m_r.stdout.splitlines() if x])
    ga = len([x for x in a_r.stdout.splitlines() if x])
    gd = len([x for x in d_r.stdout.splitlines() if x])
    parts = []
    if gm: parts.append(f'{YELLOW}{gm}M{RESET}')
    if ga: parts.append(f'{GREEN}{ga}A{RESET}')
    if gd: parts.append(f'{RED}{gd}D{RESET}')
    GIT_STATS = ' '.join(parts)
except Exception:
    pass

# ── Context bar ───────────────────────────────────────────────
BAR_W  = 15
filled = PCT * BAR_W // 100
empty  = BAR_W - filled
bar_c  = color_pct(PCT)
BAR = bar_c + '●' * filled + RESET + DIM + '○' * empty + RESET

# ── Context size label ────────────────────────────────────────
CTX_LABEL = ''
if CTX_SIZE:
    CTX_LABEL = f'{DIM}1M{RESET}' if int(CTX_SIZE) >= 1_000_000 else f'{DIM}200K{RESET}'

# ── Cache hit rate ─────────────────────────────────────────────
CACHE_HIT = ''
if CACHE_READ is not None and CUR_INPUT is not None and int(CUR_INPUT or 0) != 0:
    total = int(CACHE_READ or 0) + int(CUR_INPUT or 0) + int(CACHE_CREATE or 0)
    if total > 0:
        pct = int(CACHE_READ) * 100 // total
        cc  = color_pct(100 - pct)
        CACHE_HIT = f'{DIM}cache{RESET} {cc}{pct}%{RESET}'

# ══════════════════════════════════════════════════════════════
# LINE 1
# ══════════════════════════════════════════════════════════════
L1 = f'{CYAN}{BOLD}{MODEL}{RESET}'
if CTX_LABEL:  L1 += f' {CTX_LABEL}'
if VERSION:    L1 += f' {DIM}v{VERSION}{RESET}'
L1 += f'{SEP}{WHITE}{REPO_LINK}{RESET}'
if BRANCH:     L1 += f' {DIM}({BRANCH}){RESET}'

lines_part = ''
if LINES_ADD and str(LINES_ADD) != '0':
    lines_part = f'{GREEN}+{LINES_ADD}{RESET}'
if LINES_DEL and str(LINES_DEL) != '0':
    sep_str = ' ' if lines_part else ''
    lines_part += f'{sep_str}{RED}-{LINES_DEL}{RESET}'
if lines_part:
    L1 += f'{SEP}{lines_part} {DIM}lines{RESET}'

if GIT_STATS:  L1 += f'{SEP}{GIT_STATS}'
if AGENT:      L1 += f'{SEP}{MAGENTA}{AGENT}{RESET}'
if VIM_MODE:
    if VIM_MODE == 'NORMAL':
        L1 += f'{SEP}{BLUE}{BOLD}NOR{RESET}'
    elif VIM_MODE == 'INSERT':
        L1 += f'{SEP}{GREEN}{BOLD}INS{RESET}'
    elif VIM_MODE == 'VISUAL':
        L1 += f'{SEP}{MAGENTA}{BOLD}VIS{RESET}'
    elif VIM_MODE == 'VISUAL LINE':
        L1 += f'{SEP}{MAGENTA}{BOLD}V-L{RESET}'
    else:
        L1 += f'{SEP}{DIM}{VIM_MODE}{RESET}'

# ══════════════════════════════════════════════════════════════
# LINE 2
# ══════════════════════════════════════════════════════════════
DUR = fmt_dur(DURATION_MS)
L2 = f'{BAR} {DIM}{PCT}%{RESET}{SEP}{YELLOW}${COST:.2f}{RESET}{SEP}{DIM}{DUR}{RESET}'

if RATE_5H is not None:
    r5 = int(round(float(RATE_5H)))
    r5c = color_pct(r5)
    L2 += f'{SEP}{DIM}5h{RESET} {r5c}{r5}%{RESET}'
    if RESET_5H and RESET_5H != 'null':
        cd = fmt_countdown(RESET_5H)
        if cd: L2 += f' {DIM}({cd}){RESET}'

if RATE_7D is not None:
    r7 = int(round(float(RATE_7D)))
    r7c = color_pct(r7)
    L2 += f'{SEP}{DIM}7d{RESET} {r7c}{r7}%{RESET}'
    if RESET_7D and RESET_7D != 'null':
        cd = fmt_countdown(RESET_7D)
        if cd: L2 += f' {DIM}({cd}){RESET}'

# ══════════════════════════════════════════════════════════════
# LINE 3
# ══════════════════════════════════════════════════════════════
L3 = CACHE_HIT or ''

IN_FMT   = fmt_tokens(TOTAL_IN)
OUT_FMT  = fmt_tokens(TOTAL_OUT)
tok_part = f'{DIM}in:{RESET} {CYAN}{IN_FMT}{RESET} {DIM}out:{RESET} {MAGENTA}{OUT_FMT}{RESET}'
L3 = (L3 + SEP + tok_part) if L3 else tok_part

API_DUR = fmt_dur(API_MS)
if DURATION_MS > 0 and API_MS > 0:
    api_pct = API_MS * 100 // DURATION_MS
    L3 += f'{SEP}{DIM}api wait{RESET} {CYAN}{API_DUR}{RESET} {DIM}({api_pct}%){RESET}'
else:
    L3 += f'{SEP}{DIM}api wait{RESET} {CYAN}{API_DUR}{RESET}'

cur_fmt    = fmt_tokens(CUR_INPUT)
cache_r    = fmt_tokens(CACHE_READ)
cache_c    = fmt_tokens(CACHE_CREATE)
L3 += f'{SEP}{DIM}cur{RESET} {cur_fmt} {DIM}in{RESET} {cache_r} {DIM}read{RESET} {cache_c} {DIM}write{RESET}'

# ── Output ────────────────────────────────────────────────────
print(L1)
print(L2)
print(L3)
