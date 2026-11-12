# 유동성·신용 모니터: 12개 지표를 받아 liq_series.json(일별)·liq_summary.json(지표별 현재값·경보) 생성
# GitHub Actions에서 매일 실행(FRED·ECOS·KRX는 클라우드 샌드박스에서 막혀 있어 여기서 받음).
# 한국 금리는 ECOS_API_KEY(한국은행 ECOS 인증키, 저장소 Secret)가 있어야 받습니다.
import os, io, json, datetime as dt, traceback
import requests, pandas as pd, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = dt.date.today()
START = TODAY - dt.timedelta(days=430)
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'}
log = []

def note(msg):
    print(msg); log.append(msg)

def fred(sid):
    u = f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={START}'
    r = requests.get(u, headers=UA, timeout=60); r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df.columns = ['date', 'v']
    df['v'] = pd.to_numeric(df['v'], errors='coerce')
    s = df.dropna().set_index(pd.to_datetime(df.dropna()['date']))['v']
    note(f'FRED {sid}: {len(s)}개, 최근 {s.index[-1].date()} {s.iloc[-1]}')
    return s

def yahoo(sym):
    u = f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=2y&interval=1d'
    j = requests.get(u, headers=UA, timeout=60).json()['chart']['result'][0]
    s = pd.Series(j['indicators']['quote'][0]['close'], index=pd.to_datetime(j['timestamp'], unit='s').normalize()).dropna()
    s = s[s.index >= pd.Timestamp(START)]
    note(f'Yahoo {sym}: {len(s)}개, 최근 {s.index[-1].date()} {s.iloc[-1]:.2f}')
    return s

ECOS_ITEMS = {'ktb3': '010200000', 'ktb10': '010210000', 'aa3': '010300000', 'bbb3': '010320000', 'cd91': '010502000', 'cp91': '010503000'}
def ecos(code):
    key = os.environ.get('ECOS_API_KEY', '').strip()
    if not key:
        raise RuntimeError('ECOS_API_KEY 없음')
    u = f'https://ecos.bok.or.kr/api/StatisticSearch/{key}/json/kr/1/1000/817Y002/D/{START:%Y%m%d}/{TODAY:%Y%m%d}/{code}'
    j = requests.get(u, timeout=60).json()
    if 'StatisticSearch' not in j:
        raise RuntimeError(f'ECOS 응답 오류 {code}: {str(j)[:200]}')
    rows = j['StatisticSearch']['row']
    s = pd.Series([float(r['DATA_VALUE']) for r in rows], index=pd.to_datetime([r['TIME'] for r in rows], format='%Y%m%d'))
    note(f'ECOS {code} {rows[-1]["ITEM_NAME1"]}: {len(s)}개, 최근 {s.index[-1].date()} {s.iloc[-1]}')
    return s

def vkospi():
    errs = []
    # 1) KRX 정보데이터시스템 (파생상품지수 시세추이)
    try:
        h = dict(UA, Referer='https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201010106')
        form = {'bld': 'dbms/MDC/STAT/standard/MDCSTAT01201', 'locale': 'ko_KR', 'indIdx': '1', 'indIdx2': '300',
                'strtDd': f'{START:%Y%m%d}', 'endDd': f'{TODAY:%Y%m%d}', 'share': '2', 'money': '3', 'csvxls_isNo': 'false'}
        r = requests.post('https://data.krx.co.kr/comm/bldAttendant/getJsonData.cmd', data=form, headers=h, timeout=60)
        j = r.json(); rows = j.get('output') or []
        if rows:
            s = pd.Series([float(str(x['CLSPRC_IDX']).replace(',', '')) for x in rows], index=pd.to_datetime([x['TRD_DD'] for x in rows], format='%Y/%m/%d')).sort_index()
            if 10 < s.iloc[-1] < 150:
                note(f'KRX VKOSPI: {len(s)}개, 최근 {s.index[-1].date()} {s.iloc[-1]}')
                return s
        errs.append(f'KRX: {r.status_code} {str(j)[:150]}')
    except Exception as e:
        errs.append(f'KRX: {e}')
    raise RuntimeError(' / '.join(errs))

# id, 제목, 부제, 단위, 위험방향(+1=오를수록 위험, -1=내릴수록 위험), 절대 경보선, 출처
META = [
    ('kr_aa',   '회사채 AA- − 국고채 3년', '한국 우량 신용 스프레드', 'bp', 1, None, '한국은행 ECOS'),
    ('kr_bbb',  '회사채 BBB- − 국고채 3년', '한국 비우량 신용 스프레드', 'bp', 1, None, '한국은행 ECOS'),
    ('kr_cpcd', 'CP 91일 − CD 91일', '한국 단기자금 경색', 'bp', 1, None, '한국은행 ECOS'),
    ('kr_curve','국고채 10년 − 3년', '한국 장단기 금리차', 'bp', -1, None, '한국은행 ECOS'),
    ('us_hy',   '미국 하이일드 스프레드', 'ICE BofA HY OAS', 'bp', 1, None, 'FRED'),
    ('us_ig',   '미국 투자등급 스프레드', 'ICE BofA IG OAS', 'bp', 1, None, 'FRED'),
    ('us_netliq','미국 순유동성', '연준자산 − TGA − 역레포 ($B)', '$B', -1, None, 'FRED'),
    ('us_curve','미국 10년 − 2년', '미국 장단기 금리차', 'bp', -1, None, 'FRED'),
    ('vix',     'VIX', 'S&P500 30일 내재변동성', '', 1, 25, 'Yahoo(CBOE)'),
    ('vix_ratio','VIX ÷ VIX3M', '1 초과 = 단기 공포 > 장기(역전)', 'x', 1, 1.0, 'Yahoo(CBOE)'),
    ('move',    'MOVE', '미국 국채 내재변동성', '', 1, 130, 'Yahoo(ICE)'),
    ('vkospi',  'VKOSPI', '코스피200 30일 내재변동성', '', 1, 30, 'KRX'),
]

def build():
    S = {}
    def tryset(k, fn):
        try:
            S[k] = fn()
        except Exception as e:
            note(f'[실패] {k}: {e}')
    tryset('kr', lambda: {k: ecos(c) for k, c in ECOS_ITEMS.items()})
    if 'kr' in S:
        e = pd.DataFrame(S.pop('kr')).sort_index().ffill()
        S['kr_aa'] = (e.aa3 - e.ktb3) * 100
        S['kr_bbb'] = (e.bbb3 - e.ktb3) * 100
        S['kr_cpcd'] = (e.cp91 - e.cd91) * 100
        S['kr_curve'] = (e.ktb10 - e.ktb3) * 100
    tryset('us_hy', lambda: fred('BAMLH0A0HYM2') * 100)
    tryset('us_ig', lambda: fred('BAMLC0A0CM') * 100)
    def netliq():
        w, t, r = fred('WALCL'), fred('WTREGEN'), fred('RRPONTSYD')
        idx = pd.date_range(min(w.index[0], t.index[0], r.index[0]), max(w.index[-1], t.index[-1], r.index[-1]), freq='B')
        df = pd.DataFrame({'w': w, 't': t, 'r': r}).reindex(idx.union(w.index).union(t.index).union(r.index)).sort_index().ffill()
        df = df[df.index.dayofweek < 5].dropna()
        return df.w / 1000 - df.t / 1000 - df.r
    tryset('us_netliq', netliq)
    tryset('us_curve', lambda: fred('T10Y2Y') * 100)
    tryset('vix', lambda: yahoo('%5EVIX'))
    def ratio():
        v, v3 = yahoo('%5EVIX'), yahoo('%5EVIX3M')
        return (v / v3).dropna()
    tryset('vix_ratio', ratio)
    tryset('move', lambda: yahoo('%5EMOVE'))
    tryset('vkospi', vkospi)
    return S

def main():
    S = build()
    # 이전 파일과 합쳐 하루 실패해도 이력 유지
    old = {}
    p = os.path.join(HERE, 'liq_series.json')
    if os.path.exists(p):
        for r in json.load(open(p)):
            old.setdefault(r['id'], {})[r['date']] = r['value']
    rows, summ = [], []
    cut = pd.Timestamp(TODAY - dt.timedelta(days=400))
    for order, (k, title, sub, unit, sign, line, src) in enumerate(META):
        d = dict(old.get(k, {}))
        if k in S:
            s = S[k].dropna()
            s = s[s.index >= cut]
            for i, v in s.items():
                d[i.strftime('%Y-%m-%d')] = round(float(v), 4 if unit == 'x' else 2)
        d = {a: b for a, b in d.items() if a >= cut.strftime('%Y-%m-%d')}
        s = pd.Series(d, dtype=float).sort_index()
        s.index = pd.to_datetime(s.index)
        for i, v in s.items():
            rows.append({'id': k, 'date': i.strftime('%Y-%m-%d'), 'value': v})
        r = {'id': k, 'order': order, 'title': title, 'subtitle': sub, 'unit': unit, 'risk_dir': sign, 'line': line, 'src': src,
             'fresh': k in S, 'value': None, 'asof': None, 'chg_1w': None, 'chg_1m': None, 'pct_1y': None, 'median_1y': None, 'alert': False, 'why': ''}
        if len(s) > 30:
            last, L = s.index[-1], s.iloc[-1]
            def ago(days):
                q = s[s.index <= last - pd.Timedelta(days=days)]
                return float(q.iloc[-1]) if len(q) else None
            y1 = s[s.index > last - pd.Timedelta(days=365)]
            w, m = ago(7), ago(30)
            pct = float((y1 <= L).mean() * 100)
            ch21 = (y1 - y1.shift(21)).dropna()
            sd = float(ch21.std()) if len(ch21) > 20 else None
            r.update(value=float(L), asof=last.strftime('%Y-%m-%d'), chg_1w=None if w is None else float(L - w), chg_1m=None if m is None else float(L - m),
                     pct_1y=round(pct), median_1y=float(y1.median()))
            why = []
            riskpct = pct if sign > 0 else 100 - pct
            if riskpct >= 90: why.append(f'1년 백분위 {round(pct)}%')
            if r['chg_1m'] is not None and sd and sign * r['chg_1m'] >= 2 * sd: why.append('1개월 위험방향 급변')
            if line is not None and L > line: why.append(f'경보선 {line} 초과')
            r['alert'] = bool(why); r['why'] = ' · '.join(why)
        summ.append(r)
    json.dump(rows, open(p, 'w'), ensure_ascii=False, separators=(',', ':'))
    json.dump(summ, open(os.path.join(HERE, 'liq_summary.json'), 'w'), ensure_ascii=False, indent=0)
    json.dump({'run': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'log': log}, open(os.path.join(HERE, 'liq_log.json'), 'w'), ensure_ascii=False, indent=1)
    a = [x['title'] for x in summ if x['alert']]
    print(f'경보 {len(a)}개: {", ".join(a)}')

if __name__ == '__main__':
    main()
