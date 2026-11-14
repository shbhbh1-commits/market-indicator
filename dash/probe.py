import requests, json, time
out = {}
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36'}
def rec(k, f):
    t = time.time()
    try: out[k] = f()
    except Exception as e: out[k] = 'ERR ' + repr(e)[:300]
    out[k + '_sec'] = round(time.time() - t, 1)
for u in ['https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv',
          'https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/historical/jgbcme_all.csv']:
    def f(u=u):
        r = requests.get(u, headers=H, timeout=60); t = r.content.decode('utf-8', 'replace').splitlines()
        return {'status': r.status_code, 'n': len(t), 'head': t[:4], 'tail': t[-3:]}
    rec(u.split('/')[-1], f)
def kofia(obj, extra=None):
    body = {'dmSearch': {'tmpV40': '1000000', 'tmpV41': '1', 'tmpV1': 'D', 'tmpV45': '20261001', 'tmpV46': '20261113', 'OBJ_NM': obj}}
    if extra: body['dmSearch'].update(extra)
    r = requests.post('https://freesis.kofia.or.kr/meta/getMetaDataList.do', json=body, headers={**H, 'Content-Type': 'application/json'}, timeout=60)
    return {'status': r.status_code, 'text': r.text[:1500]}
for obj in ['STATSCU0100000060BO', 'STATSCU0100000070BO', 'STATSCU0100000020BO']:
    rec('kofia_' + obj, lambda obj=obj: kofia(obj))
def fred(sid):
    r = requests.get(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd=2026-01-01', headers=H, timeout=60)
    t = r.text.splitlines(); return {'status': r.status_code, 'n': len(t), 'tail': t[-2:]}
for s in ['T10Y3M', 'IRLTLT01JPM156N', 'NFCI', 'SAHMREALTIME', 'DFII10', 'T5YIFR', 'PPIFIS', 'CPILFESL', 'PCEPILFE', 'ICSA', 'DTWEXBGS', 'M2SL', 'DRTSCILM', 'UNRATE', 'DGS2', 'DFF', 'BAMLH0A0HYM2']:
    rec('fred_' + s, lambda s=s: fred(s))
json.dump(out, open('dash/probe_out.json', 'w'), ensure_ascii=False, indent=1)
