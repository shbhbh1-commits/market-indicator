import requests, json, time, os
H = {'User-Agent': 'Mozilla/5.0'}
out = {}
K = os.environ.get('KOSIS_API_KEY', '').strip(); D = os.environ.get('DATA_GO_KR_KEY', '').strip(); F = os.environ.get('FRED_API_KEY', '').strip()
out['lens'] = {'kosis': len(K), 'datagokr': len(D), 'fred': len(F)}
def rec(k, f):
    try: out[k] = f()
    except Exception as e: out[k] = 'ERR ' + repr(e)[:250]
    json.dump(out, open('ind/probe_out.json', 'w'), ensure_ascii=False, indent=1)
rec('kosis_list', lambda: requests.get('https://kosis.kr/openapi/statisticsList.do', params={'method': 'getList', 'apiKey': K, 'vwCd': 'MT_ZTITLE', 'parentListId': '', 'format': 'json', 'jsonVD': 'Y'}, timeout=(10, 40)).text[:600])
rec('kosis_cpi', lambda: requests.get('https://kosis.kr/openapi/Param/statisticsParameterData.do', params={'method': 'getList', 'apiKey': K, 'itmId': 'ALL', 'objL1': '0', 'format': 'json', 'jsonVD': 'Y', 'prdSe': 'M', 'newEstPrdCnt': '2', 'orgId': '101', 'tblId': 'DT_1J22003'}, timeout=(10, 40)).text[:600])
for nm, u in [('dg_nitem', 'https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList'), ('dg_item', 'https://apis.data.go.kr/1220000/Itemtrade/getItemtradeList')]:
    rec(nm, lambda u=u: (lambda r: f'{r.status_code} {r.text[:900]}')(requests.get(u, params={'serviceKey': D, 'strtYymm': '202601', 'endYymm': '202609', 'cntyCd': 'US', 'hsSgn': '8504'}, timeout=(10, 40))))
rec('fred', lambda: requests.get(f'https://api.stlouisfed.org/fred/series/observations?series_id=PIORECRUSDM&api_key={F}&file_type=json&observation_start=2026-01-01', timeout=(10, 40)).text[:300])
