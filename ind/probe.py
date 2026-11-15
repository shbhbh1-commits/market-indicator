import requests, json, time, os, re
H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36'}
out = {}
def rec(k, f):
    t = time.time()
    try: out[k] = f()
    except Exception as e: out[k] = 'ERR ' + repr(e)[:250]
    out[k + '_s'] = round(time.time() - t, 1)
    json.dump(out, open('ind/probe_out.json', 'w'), ensure_ascii=False, indent=1)
def get(u, **kw):
    r = requests.get(u, headers=H, timeout=(10, 40), **kw); return {'st': r.status_code, 'ct': r.headers.get('content-type'), 'txt': r.text[:400]}
rec('kosis', lambda: get('https://kosis.kr/openapi/statisticsList.do?method=getList&apiKey=x&vwCd=MT_ZTITLE&parentListId=&format=json&jsonVD=Y'))
rec('datagokr', lambda: get('https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList?serviceKey=x&strtYymm=202601&endYymm=202601&cntyCd=US&hsSgn=8504'))
rec('jnto_page', lambda: (lambda r: {'st': r.status_code, 'xlsx': re.findall(r'href="([^"]+\.xlsx)"', r.text)[:8]})(requests.get('https://www.jnto.go.jp/statistics/data/visitors-statistics/', headers=H, timeout=(10, 40))))
rec('worldsteel', lambda: get('https://worldsteel.org/media/press-releases/'))
rec('reb', lambda: get('https://www.reb.or.kr/r-one/openapi/SttsApiTblData.do?KEY=x&STATBL_ID=A_2024_00045&DTACYCLE_CD=WK&Type=json'))
k = os.environ.get('FRED_API_KEY', '')
for s in ['POILDUBUSDM', 'PIORECRUSDM', 'PCOALAUUSDM', 'PNICKUSDM', 'PZINCUSDM', 'PALUMUSDM', 'PWHEAMTUSDM', 'PMAIZMTUSDM', 'PSOYBUSDM', 'PSUGAISAUSDM', 'PCU335311335311', 'WPU101']:
    rec('fred_' + s, lambda s=s: (lambda j: {'n': len(j.get('observations', [])), 'last': j.get('observations', [{}])[-1] if j.get('observations') else j})(requests.get(f'https://api.stlouisfed.org/fred/series/observations?series_id={s}&api_key={k}&file_type=json&observation_start=2025-01-01', timeout=(10, 40)).json()))
tick = ['091160.KS','000660.KS','005930.KS','267260.KS','010120.KS','298040.KS','009540.KS','010140.KS','011200.KS','091180.KS','005380.KS','305720.KS','117460.KS','096770.KS','011170.KS','117680.KS','005490.KS','010130.KS','117700.KS','000720.KS','300720.KS','102960.KS','042670.KS','241560.KS','139260.KS','023530.KS','004170.KS','228800.KS','008770.KS','090430.KS','7532.T','3099.T','8801.T','097950.KS','003230.KS','033780.KS','002310.KS','213500.KS','^SOX','HG=F','BZ=F','CL=F','NG=F','JPY=X','1343.T','8233.T']
def yq(t):
    j = requests.get(f'https://query1.finance.yahoo.com/v8/finance/chart/{t}?range=5d&interval=1d', headers=H, timeout=(10, 30)).json()
    m = j['chart']['result'][0]['meta']; return f"{m.get('longName') or m.get('shortName')} {m.get('regularMarketPrice')}"
for t in tick: rec('y_' + t, lambda t=t: yq(t))
