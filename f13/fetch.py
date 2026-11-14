# 대가 13F 포트폴리오 추적: SEC EDGAR에서 최근 12개 분기 13F를 받아 분기별 보유·변화를 계산한다.
# 사용: python3 f13/fetch.py            → f13/raw/<id>.json(분기별 보유) + dash/f13_*.json 생성
# 출력이 바뀐 매니저(새 분기 공시)는 f13/new_filings.json 에 기록 → 일일 작업이 사유 조사를 붙인다.
import os, re, json, time, datetime as dt, urllib.parse
import xml.etree.ElementTree as ET
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
DASH = os.path.join(HERE, '..', 'dash')
RAW = os.path.join(HERE, 'raw'); os.makedirs(RAW, exist_ok=True)
H = {'User-Agent': os.environ.get('SEC_UA', 'market-indicator research bot')}
NQ = 12          # 최근 12개 분기(3년)
TOPN = 25        # 분기마다 상위 25개 종목은 시계열에 남김

def get(url, **kw):
    for i in range(4):
        try:
            r = requests.get(url, headers=H, timeout=40, **kw)
            if r.status_code == 200:
                time.sleep(0.12); return r
            if r.status_code in (429, 503): time.sleep(2 + i * 3); continue
            r.raise_for_status()
        except requests.RequestException:
            if i == 3: raise
            time.sleep(2)
    raise RuntimeError(url)

def filings(cik):
    d = get(f'https://data.sec.gov/submissions/CIK{cik:010d}.json').json()
    rows = []
    def add(r):
        for i, f in enumerate(r['form']):
            if f in ('13F-HR', '13F-HR/A'):
                rows.append({'form': f, 'filed': r['filingDate'][i], 'period': r['reportDate'][i], 'acc': r['accessionNumber'][i], 'cik': cik})
    add(d['filings']['recent'])
    for f in d['filings'].get('files', []):
        if f.get('filingTo', '9999') >= '2023-01-01':
            add(get('https://data.sec.gov/submissions/' + f['name']).json())
    return d['name'], rows

def strip(tag): return tag.split('}')[-1]

def parse_info(xml):
    root = ET.fromstring(xml)
    out = []
    for it in root.iter():
        if strip(it.tag) != 'infoTable': continue
        g = {strip(c.tag): c for c in it}
        sh = {strip(c.tag): (c.text or '').strip() for c in g.get('shrsOrPrnAmt', [])}
        out.append({'name': (g['nameOfIssuer'].text or '').strip(), 'cls': (g.get('titleOfClass').text or '').strip() if g.get('titleOfClass') is not None else '',
                    'cusip': (g['cusip'].text or '').strip().upper(), 'value': float(g['value'].text or 0),
                    'shares': float(sh.get('sshPrnamt') or 0), 'stype': sh.get('sshPrnamtType', 'SH'),
                    'pc': (g['putCall'].text or '').strip() if g.get('putCall') is not None else ''})
    return out

def load_filing(cik, acc):
    base = f'https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace("-", "")}/'
    idx = get(base + 'index.json').json()['directory']['item']
    xmls = [x['name'] for x in idx if x['name'].lower().endswith('.xml')]
    prim = [x for x in xmls if 'primary' in x.lower()]
    amend = ''
    if prim:
        t = get(base + prim[0]).text
        m = re.search(r'<(?:\w+:)?amendmentType>\s*([^<]+)<', t)
        amend = m.group(1).strip().upper() if m else ''
    rows = []
    for x in [x for x in xmls if x not in prim]:
        try:
            rows = parse_info(get(base + x).content)
            if rows: break
        except ET.ParseError:
            continue
    return rows, amend

def quarter_label(p):
    d = dt.date.fromisoformat(p); return f"{d.year}Q{(d.month - 1) // 3 + 1}"

def build_manager(m):
    ciks = m['cik'] if isinstance(m['cik'], list) else [m['cik']]
    cache_p = os.path.join(RAW, m['id'] + '.json')
    cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {'quarters': {}}
    fl, names = [], []
    for c in ciks:
        n, r = filings(c); names.append(n); fl += r
    ename = ' / '.join(names)
    periods = sorted({f['period'] for f in fl}, reverse=True)[:NQ]
    changed = []
    for p in periods:
        fs = [f for f in fl if f['period'] == p]
        fs = sorted(fs, key=lambda f: f['filed'])
        sig = '|'.join(f['acc'] for f in fs)
        if cache['quarters'].get(p, {}).get('sig') == sig:
            continue
        # CIK별로 보유를 만든 뒤 합친다(법인이 바뀐 퍼싱 스퀘어처럼 두 법인이 나눠 공시하는 경우). 같은 종목은 주식 수가 큰 쪽만 쓴다.
        per, filed = {}, fs[0]['filed']
        for f in fs:
            rows, amend = load_filing(f['cik'], f['acc'])
            h = per.get(f['cik'])
            if f['form'] == '13F-HR' or h is None or amend == 'RESTATEMENT':
                per[f['cik']] = rows; filed = max(filed, f['filed'])
            elif amend.startswith('NEW HOLDINGS'):
                per[f['cik']] = h + rows
        if len(per) == 1:
            hold = next(iter(per.values()))
        else:
            best = {}
            for c, rows in per.items():
                tot = {}
                for r in rows:
                    k = r['cusip'] + '|' + r['pc']; tot[k] = tot.get(k, 0) + r['shares']
                for k, v in tot.items():
                    if k not in best or v > best[k][1]: best[k] = (c, v)
            hold = [r for c, rows in per.items() for r in rows if best[r['cusip'] + '|' + r['pc']][0] == c]
        cache['quarters'][p] = {'sig': sig, 'filed': filed, 'rows': hold or []}
        changed.append(p)
    cache['quarters'] = {p: v for p, v in cache['quarters'].items() if p in periods}
    cache['entity'] = ename
    json.dump(cache, open(cache_p, 'w'), ensure_ascii=False, separators=(',', ':'))
    return cache, changed

def agg(rows):
    """CUSIP+옵션구분 단위로 합산. 옵션(Put/Call)은 별도 키. 금액을 천 달러 단위로 낸 공시는 달러로 환산."""
    px = sorted(r['value'] / r['shares'] for r in rows if r['stype'] == 'SH' and r['shares'] > 0 and not r['pc'])
    mult = 1000.0 if px and px[len(px) // 2] < 1.0 else 1.0
    a = {}
    for r in rows:
        k = r['cusip'] + ('|' + r['pc'].upper() if r['pc'] else '')
        x = a.setdefault(k, {'cusip': r['cusip'], 'name': r['name'], 'cls': r['cls'], 'pc': r['pc'].upper(), 'value': 0.0, 'shares': 0.0})
        x['value'] += r['value'] * mult; x['shares'] += r['shares']
    tot = sum(x['value'] for x in a.values() if not x['pc']) or 1.0
    for x in a.values(): x['weight'] = x['value'] / tot * 100
    return a, tot

# ---- CUSIP → 티커·섹터 (Yahoo 검색, 캐시) ----
MAP_P = os.path.join(HERE, 'cusip_map.json')
CMAP = json.load(open(MAP_P)) if os.path.exists(MAP_P) else {}
US_EX = {'NMS', 'NYQ', 'NGM', 'NCM', 'ASE', 'PCX', 'BTS', 'NAS', 'NYS', 'PNK', 'OQB', 'OQX', 'OEM'}
def clean(n):
    n = re.sub(r'[^A-Za-z0-9& ]', ' ', n.upper())
    drop = {'INC', 'CORP', 'CORPORATION', 'CO', 'LTD', 'PLC', 'NEW', 'DEL', 'COM', 'CL', 'A', 'B', 'SHS', 'HLDGS', 'HOLDINGS', 'GROUP', 'THE', 'SA', 'NV', 'AG', 'ADR', 'SPONSORED', 'SPON', 'LP', 'LLC'}
    return ' '.join(w for w in n.split() if w not in drop)[:40]
FIXED = {'02079K305': 'GOOGL', '02079K107': 'GOOG', '084670108': 'BRK-A', '084670702': 'BRK-B', '934423104': 'WBD', '881624209': 'TEVA'}
def ticker(cusip, name):
    if cusip in FIXED and CMAP.get(cusip, {}).get('t') != FIXED[cusip]:
        CMAP[cusip] = {'t': FIXED[cusip], 'sector': CMAP.get(cusip, {}).get('sector', ''), 'v': 2}
    if cusip in CMAP and CMAP[cusip].get('v') == 2: return CMAP[cusip]
    res, fb = {'t': '', 'sector': '', 'v': 2}, None
    for q in (cusip, clean(name)):
        if not q: continue
        try:
            j = requests.get('https://query1.finance.yahoo.com/v1/finance/search', params={'q': q, 'quotesCount': 6, 'newsCount': 0},
                             headers={'User-Agent': 'Mozilla/5.0'}, timeout=15).json()
            qs = [x for x in j.get('quotes', []) if x.get('quoteType') in ('EQUITY', 'ETF') and x.get('symbol')]
            us = [x for x in qs if x.get('exchange') in US_EX and '.' not in x['symbol']]
            pick = us[0] if us else None
            if not pick and qs and fb is None: fb = qs[0]
            if pick:
                res = {'t': pick['symbol'], 'sector': pick.get('sectorDisp') or pick.get('sector') or ('ETF' if pick['quoteType'] == 'ETF' else ''), 'v': 2}
                break
        except Exception:
            pass
        time.sleep(0.2)
    if not res['t'] and fb:
        res = {'t': fb['symbol'], 'sector': fb.get('sectorDisp') or fb.get('sector') or '', 'v': 2}
    CMAP[cusip] = res
    return res

def main():
    mgrs = json.load(open(os.path.join(HERE, 'managers.json')))
    summary, series, changes, newf = [], [], [], []
    for m in mgrs:
        try:
            cache, changed = build_manager(m)
        except Exception as e:
            print('[실패]', m['id'], e); summary.append({**{k: m[k] for k in ('id', 'name', 'firm', 'style')}, 'status': f'수집 실패: {str(e)[:80]}'}); continue
        qs = sorted(cache['quarters'])
        if not qs:
            summary.append({**{k: m[k] for k in ('id', 'name', 'firm', 'style')}, 'status': '13F 없음'}); continue
        A = {p: agg(cache['quarters'][p]['rows']) for p in qs}
        last, prev, first = qs[-1], (qs[-2] if len(qs) > 1 else None), qs[0]
        if changed and last in changed: newf.append({'id': m['id'], 'period': last, 'filed': cache['quarters'][last]['filed']})
        keep = set()
        for p in qs:
            top = sorted([k for k, x in A[p][0].items() if not x['pc']], key=lambda k: -A[p][0][k]['value'])[:TOPN]
            keep.update(top)
        cur, tot = A[last]
        pv = A[prev][0] if prev else {}
        fv = A[first][0]
        # 최근 분기 변화(옵션 제외)
        keys = set(k for k in cur if not cur[k]['pc']) | set(k for k in pv if not pv[k]['pc'])
        ch = []
        for k in keys:
            c, o = cur.get(k), pv.get(k)
            s1, s0 = (c or {}).get('shares', 0), (o or {}).get('shares', 0)
            split = 1
            if s0 > 0 and s1 > 0 and c['value'] > 0 and o['value'] > 0:
                ratio = s1 / s0; pr = (c['value'] / s1) / (o['value'] / s0)
                kk = ratio if ratio >= 1 else 1 / ratio
                kr = round(kk)
                # 주식 수가 정수배로 바뀌고 주당 가격이 그 역수로 바뀌었으면 분할·병합으로 보고 보정
                if ratio >= 1 and kr >= 2 and abs(kk - kr) < 0.45 and abs(pr * kr - 1) < 0.2:
                    split = kr if ratio >= 1 else 1 / kr
                    s0 = s0 * split
            if s0 == 0 and s1 > 0: act, pct = '신규', None
            elif s1 == 0 and s0 > 0: act, pct = '전량 매도', -100.0
            elif s0 > 0 and abs(s1 / s0 - 1) >= 0.02: act, pct = ('증가' if s1 > s0 else '감소'), (s1 / s0 - 1) * 100
            else: continue
            x = c or o
            f0 = fv.get(k, {}).get('shares', 0)
            ch.append({'mid': m['id'], 'key': m['id'] + ':' + k, 'cusip': x['cusip'], 'name': x['name'], 'action': act, 'shares_chg_pct': None if pct is None else round(pct, 1),
                       'shares_now': s1, 'shares_prev': s0, 'value_now': (c or {}).get('value', 0), 'weight_now': round((c or {}).get('weight', 0), 2),
                       'weight_prev': round((o or {}).get('weight', 0), 2), 'weight_chg': round((c or {}).get('weight', 0) - (o or {}).get('weight', 0), 2),
                       'shares_3y_pct': None if not f0 else round((s1 / f0 - 1) * 100, 1), 'weight_first': round(fv.get(k, {}).get('weight', 0), 2),
                       'split_adj': split if split != 1 else None, 'period': last, 'prev_period': prev})
        ch.sort(key=lambda r: -abs(r['weight_chg']))
        for r in ch[:30]:
            t = ticker(r['cusip'], r['name']); r['ticker'] = t['t']; r['sector'] = t['sector']
        changes += ch[:30]
        # 시계열(상위 종목)
        for k in keep:
            nm = next(A[p][0][k]['name'] for p in reversed(qs) if k in A[p][0])
            t = ticker(k, nm)
            for p in qs:
                x = A[p][0].get(k)
                series.append({'mid': m['id'], 'q': quarter_label(p), 'cusip': k, 'ticker': t['t'], 'name': nm,
                               'weight': round(x['weight'], 2) if x else 0, 'value': x['value'] if x else 0, 'shares': x['shares'] if x else 0})
        top10 = sorted([x for x in cur.values() if not x['pc']], key=lambda x: -x['value'])[:10]
        n_new = sum(1 for r in ch if r['action'] == '신규'); n_out = sum(1 for r in ch if r['action'] == '전량 매도')
        # 회전율(근사): 분기 비중 변화 절대값 합 / 2
        turn = sum(abs(r['weight_chg']) for r in ch) / 2
        sect = {}
        for x in cur.values():
            if x['pc']: continue
            s = CMAP.get(x['cusip'], {}).get('sector') or '기타·미분류'
            sect[s] = sect.get(s, 0) + x['weight']
        summary.append({'id': m['id'], 'name': m['name'], 'firm': m['firm'], 'style': m['style'], 'focus': m['focus'], 'note': m.get('note', ''),
                        'entity': cache['entity'], 'cik': m['cik'] if isinstance(m['cik'], int) else m['cik'][-1], 'period': quarter_label(last), 'period_end': last, 'filed': cache['quarters'][last]['filed'],
                        'prev_period': quarter_label(prev) if prev else '', 'first_period': quarter_label(first), 'n_quarters': len(qs),
                        'value_13f': tot, 'value_13f_prev': A[prev][1] if prev else None, 'value_13f_first': A[first][1],
                        'n_pos': sum(1 for x in cur.values() if not x['pc']), 'n_pos_prev': sum(1 for x in pv.values() if not x['pc']),
                        'top10_share': round(sum(x['weight'] for x in top10), 1), 'n_new': n_new, 'n_out': n_out, 'turnover': round(turn, 1),
                        'top_sector': max(sect, key=sect.get) if sect else '', 'top_sector_w': round(max(sect.values()), 1) if sect else None,
                        'top5': ', '.join((CMAP.get(x['cusip'], {}).get('t') or x['name']) for x in top10[:5]),
                        'edgar': f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={m["cik"] if isinstance(m["cik"], int) else m["cik"][-1]}&type=13F-HR', 'status': '정상'})
        print(m['id'], quarter_label(last), len(qs), '분기', '변화', len(ch), '신규분기' if m['id'] in [x['id'] for x in newf] else '')
        json.dump(CMAP, open(MAP_P, 'w'), ensure_ascii=False)
    json.dump(summary, open(os.path.join(DASH, 'f13_managers.json'), 'w'), ensure_ascii=False, indent=0)
    json.dump(changes, open(os.path.join(DASH, 'f13_changes.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    json.dump(series, open(os.path.join(DASH, 'f13_series.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    json.dump({'run': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'new': newf}, open(os.path.join(HERE, 'new_filings.json'), 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
