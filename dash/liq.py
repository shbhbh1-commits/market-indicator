# 유동성·신용·거시 모니터: FRED·일본 재무성·금융투자협회(KOFIA)·KRX에서 지표를 받아
# liq_series.json(시계열)·liq_summary.json(지표별 현재값·경보)·liq_keys.json(인증키 상태)·liq_log.json 생성
# GitHub Actions에서 매일 실행(FRED·재무성·KOFIA·KRX는 클라우드 샌드박스에서 막혀 있어 여기서 받음).
# 저장소 Secret: FRED_API_KEY(있으면 공식 API로 빠르고 안정적), KRX_API_KEY(VKOSPI) — 모두 무료 발급
import os, io, re, json, datetime as dt
import requests, pandas as pd, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TODAY = dt.date.today()
START_D = TODAY - dt.timedelta(days=430)          # 일별 지표
START_L = TODAY - dt.timedelta(days=365 * 6 + 60)  # 주·월·분기 지표(전년비 계산·3년 백분위용)
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'}
log = []
ERR = {}

def note(msg):
    print(msg, flush=True); log.append(msg)

def keyset(name):
    return bool(os.environ.get(name, '').strip())

# ---------------- 수집기 ----------------
_FRED, _FRED_FAIL = {}, {}
def fred(sid, start):
    if sid in _FRED: return _FRED[sid]
    if sid in _FRED_FAIL: raise RuntimeError(_FRED_FAIL[sid])
    key = os.environ.get('FRED_API_KEY', '').strip()
    if key:
        u = f'https://api.stlouisfed.org/fred/series/observations?series_id={sid}&api_key={key}&file_type=json&observation_start={start}'
        obs = requests.get(u, timeout=60).json()['observations']
        s = pd.Series([float(o['value']) if o['value'] not in ('.', '') else np.nan for o in obs], index=pd.to_datetime([o['date'] for o in obs])).dropna()
    else:
        last, r = None, None
        for h in (UA,):
            try:
                r = requests.get(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={start}', headers=h, timeout=(15, 90)); r.raise_for_status(); break
            except Exception as e:
                last, r = e, None
        if r is None:
            _FRED_FAIL[sid] = f'{str(last)[:120]} (FRED_API_KEY 등록 시 공식 API 사용)'
            raise RuntimeError(_FRED_FAIL[sid])
        df = pd.read_csv(io.StringIO(r.text)); df.columns = ['date', 'v']
        df['v'] = pd.to_numeric(df['v'], errors='coerce'); df = df.dropna()
        s = pd.Series(df['v'].values, index=pd.to_datetime(df['date']))
    note(f'FRED {sid}: {len(s)}개, 최근 {s.index[-1].date()} {s.iloc[-1]}')
    _FRED[sid] = s
    return s

FRED_IDS = {'BAMLH0A0HYM2': 'D', 'BAMLC0A0CM': 'D', 'WALCL': 'D', 'WTREGEN': 'D', 'RRPONTSYD': 'D', 'NFCI': 'L', 'DRTSCILM': 'L', 'T10Y2Y': 'D', 'T10Y3M': 'D',
            'DGS2': 'D', 'DFF': 'D', 'DFII10': 'D', 'T5YIFR': 'D', 'CPILFESL': 'L', 'PCEPILFE': 'L', 'PPIFIS': 'L', 'UNRATE': 'L', 'SAHMREALTIME': 'L', 'ICSA': 'L',
            'DTWEXBGS': 'D', 'M2SL': 'L'}
def prefetch_fred():
    """FRED를 병렬로 미리 받는다(키 없는 공개 경로는 한 건에 수십 초씩 걸려서). 실패한 것은 개별 지표에서 다시 오류로 잡힌다."""
    from concurrent.futures import ThreadPoolExecutor
    def one(sid):
        try: fred(sid, START_D if FRED_IDS[sid] == 'D' else START_L)
        except Exception as e: note(f'[FRED 실패] {sid}: {str(e)[:120]}')
    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(one, FRED_IDS))

_UST = {}
def ust(kind):
    """미 재무부 일별 금리 CSV(명목: daily_treasury_yield_curve, 실질: daily_treasury_real_yield_curve). FRED가 막힐 때 대체."""
    if kind in _UST: return _UST[kind]
    frames = []
    for y in range(START_D.year, TODAY.year + 1):
        u = (f'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{y}/all'
             f'?type={kind}&field_tdr_date_value={y}&page&_format=csv')
        r = requests.get(u, headers=UA, timeout=(15, 60)); r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text)); df['Date'] = pd.to_datetime(df['Date']); frames.append(df.set_index('Date'))
    df = pd.concat(frames).sort_index(); df.columns = [c.strip().upper() for c in df.columns]
    df = df[~df.index.duplicated(keep='last')]
    note(f'미 재무부 {kind}: {len(df)}일, 최근 {df.index[-1].date()}')
    _UST[kind] = df
    return df

def fred_or(sid, start, alt):
    try:
        return fred(sid, start)
    except Exception as e:
        s = alt()
        note(f'{sid}: FRED 실패 → 미 재무부 자료로 대체'); USED_ALT.add({'T10Y2Y': 'us_curve', 'T10Y3M': 'us_curve3m', 'DGS2': 'us_2y', 'DFII10': 'us_real10'}[sid])
        return s

def yoy(s, n=12):
    return (s / s.shift(n) - 1) * 100

_JGB = None
def jgb():
    """일본 재무성 국채 금리(일별, 만기별). 당월 파일 + 과거 전체 파일을 합친다."""
    global _JGB
    if _JGB is not None: return _JGB
    frames = []
    for u in ('https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/historical/jgbcme_all.csv',
              'https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv'):
        try:
            t = requests.get(u, headers=UA, timeout=60).content.decode('utf-8', 'replace').splitlines()
            hi = next(i for i, l in enumerate(t) if '10Y' in l and 'Date' in l)
            df = pd.read_csv(io.StringIO('\n'.join(t[hi:])))
            df = df.rename(columns={df.columns[0]: 'date'})
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date']).set_index('date')
            frames.append(df[['2Y', '10Y']].apply(pd.to_numeric, errors='coerce'))
        except Exception as e:
            note(f'[주의] 재무성 {u.split("/")[-1]}: {str(e)[:120]}')
    if not frames:
        raise RuntimeError('재무성 국채금리 파일을 받지 못함')
    df = pd.concat(frames).sort_index()
    df = df[~df.index.duplicated(keep='last')]
    df = df[df.index >= pd.Timestamp(START_D)]
    note(f'재무성 JGB: {len(df)}일, 최근 {df.index[-1].date()} 2Y {df["2Y"].iloc[-1]} 10Y {df["10Y"].iloc[-1]}')
    _JGB = df
    return df

_KOFIA = None
def kofia():
    """금융투자협회 FreeSIS 증시자금추이(일별): 투자자예탁금·신용융자잔고 등. 단위 백만원 → 조원."""
    global _KOFIA
    if _KOFIA is not None: return _KOFIA
    body = {'dmSearch': {'tmpV40': '1000000', 'tmpV41': '1', 'tmpV1': 'D', 'tmpV45': f'{START_D:%Y%m%d}', 'tmpV46': f'{TODAY:%Y%m%d}', 'OBJ_NM': 'STATSCU0100000060BO'}}
    r = requests.post('https://freesis.kofia.or.kr/meta/getMetaDataList.do', json=body, headers={**UA, 'Content-Type': 'application/json'}, timeout=60)
    j = r.json()
    rows = j.get('ds1') or next((v for v in j.values() if isinstance(v, list)), [])
    if not rows:
        raise RuntimeError(f'KOFIA 응답에 자료 없음: {r.text[:150]}')
    df = pd.DataFrame(rows)
    df.columns = [c.upper() for c in df.columns]
    df['date'] = pd.to_datetime(df['TMPV1'].astype(str).str.replace(r'\D', '', regex=True), format='%Y%m%d', errors='coerce')
    df = df.dropna(subset=['date']).set_index('date').sort_index()
    # 증시자금추이 열 순서: TMPV2 투자자예탁금, TMPV3 장내파생 예수금, TMPV4 RP 매도잔고, TMPV5 위탁매매 미수금, TMPV6 반대매매금액, TMPV7 미수금 대비 반대매매 비중
    # (열 정의는 liq_log의 샘플로 확인 — 아래 KOFIA_COLS 참고)
    _KOFIA = df.apply(lambda c: pd.to_numeric(c.astype(str).str.replace(',', ''), errors='coerce') if c.name.startswith('TMPV') and c.name != 'TMPV1' else c)
    note(f'KOFIA 증시자금: {len(df)}일, 최근 {df.index[-1].date()} 샘플 {json.dumps(rows[-1], ensure_ascii=False)[:300]}')
    return _KOFIA

_KOFIA_CR = None
def kofia_credit():
    """금융투자협회 FreeSIS 신용공여 잔고추이(일별): 신용거래융자 합계."""
    global _KOFIA_CR
    if _KOFIA_CR is not None: return _KOFIA_CR
    body = {'dmSearch': {'tmpV40': '1000000', 'tmpV41': '1', 'tmpV1': 'D', 'tmpV45': f'{START_D:%Y%m%d}', 'tmpV46': f'{TODAY:%Y%m%d}', 'OBJ_NM': 'STATSCU0100000070BO'}}
    r = requests.post('https://freesis.kofia.or.kr/meta/getMetaDataList.do', json=body, headers={**UA, 'Content-Type': 'application/json'}, timeout=60)
    j = r.json()
    rows = j.get('ds1') or next((v for v in j.values() if isinstance(v, list)), [])
    if not rows:
        raise RuntimeError(f'KOFIA 신용 응답에 자료 없음: {r.text[:150]}')
    df = pd.DataFrame(rows); df.columns = [c.upper() for c in df.columns]
    df['date'] = pd.to_datetime(df['TMPV1'].astype(str).str.replace(r'\D', '', regex=True), format='%Y%m%d', errors='coerce')
    df = df.dropna(subset=['date']).set_index('date').sort_index()
    _KOFIA_CR = df.apply(lambda c: pd.to_numeric(c.astype(str).str.replace(',', ''), errors='coerce') if c.name.startswith('TMPV') and c.name != 'TMPV1' else c)
    note(f'KOFIA 신용공여: {len(df)}일, 최근 {df.index[-1].date()} 샘플 {json.dumps(rows[-1], ensure_ascii=False)[:300]}')
    return _KOFIA_CR

KOFIA_COLS = {'deposit': 'TMPV2', 'credit': 'TMPV2'}   # 예탁금(증시자금추이 TMPV2), 신용융자 합계(신용공여 TMPV2) — 단위 백만원

def vkospi(have):
    """KRX OpenAPI(파생상품지수 일별시세, 무료 인증키 KRX_API_KEY). 이력에 없는 날만 받음(회당 최대 270일)."""
    key = os.environ.get('KRX_API_KEY', '').strip()
    if not key:
        raise RuntimeError('KRX_API_KEY 없음')
    days = [d for d in pd.bdate_range(START_D + dt.timedelta(days=60), TODAY) if d.strftime('%Y-%m-%d') not in have][-270:]
    out, err = {}, None
    for d in days:
        try:
            j = requests.get(f'https://data-dbg.krx.co.kr/svc/apis/idx/drvprod_dd_trd?basDd={d:%Y%m%d}', headers={'AUTH_KEY': key}, timeout=30).json()
            for x in j.get('OutBlock_1', []):
                if '변동성' in x.get('IDX_NM', '') and '200' in x.get('IDX_NM', '') and x.get('CLSPRC_IDX') not in (None, '', '-'):
                    out[d] = float(str(x['CLSPRC_IDX']).replace(',', '')); break
        except Exception as e:
            err = e
    if not out and not have:
        raise RuntimeError(f'KRX 응답에 VKOSPI 없음 {err or ""}')
    s = pd.Series(out, dtype=float).sort_index()
    note(f'KRX VKOSPI: 새로 {len(s)}일' + (f', 최근 {s.index[-1].date()} {s.iloc[-1]}' if len(s) else ''))
    return s

def netliq():
    w, t, r = fred('WALCL', START_D), fred('WTREGEN', START_D), fred('RRPONTSYD', START_D)
    idx = pd.date_range(min(w.index[0], t.index[0], r.index[0]), max(w.index[-1], t.index[-1], r.index[-1]), freq='B')
    df = pd.DataFrame({'w': w, 't': t, 'r': r}).reindex(idx.union(w.index).union(t.index).union(r.index)).sort_index().ffill()
    df = df[df.index.dayofweek < 5].dropna()
    return df.w / 1000 - df.t / 1000 - df.r

def kr_credit_ratio():
    d = kofia()[KOFIA_COLS['deposit']]; c = kofia_credit()[KOFIA_COLS['credit']]
    df = pd.DataFrame({'d': d, 'c': c}).dropna()
    return df.c / df.d * 100

# ---------------- 지표 정의 ----------------
# group, id, 제목, 부제, 단위, 위험방향(+1=오를수록 위험, -1=내릴수록 위험), 절대 경보선, 출처, 주기(D/W/M/Q), 수집 함수
L = lambda f: f
SERIES = [
    ('us_credit', 'us_hy', '미국 하이일드 스프레드', 'ICE BofA HY OAS', 'bp', 1, 500, 'FRED', 'D', lambda o: fred('BAMLH0A0HYM2', START_D) * 100),
    ('us_credit', 'us_ig', '미국 투자등급 스프레드', 'ICE BofA IG OAS', 'bp', 1, None, 'FRED', 'D', lambda o: fred('BAMLC0A0CM', START_D) * 100),
    ('us_credit', 'us_netliq', '미국 순유동성', '연준자산 − TGA − 역레포 ($B)', '$B', -1, None, 'FRED', 'D', lambda o: netliq()),
    ('us_credit', 'us_nfci', '시카고 연준 금융여건지수', 'NFCI · 0 초과 = 평균보다 긴축', '', 1, 0, 'FRED', 'W', lambda o: fred('NFCI', START_L)),
    ('us_credit', 'us_sloos', '은행 대출태도(기업대출 기준 강화 비율)', '시니어 론 오피서 서베이 · 순비율 %', '%', 1, 20, 'FRED', 'Q', lambda o: fred('DRTSCILM', START_L)),
    ('us_rates', 'us_curve', '미국 10년 − 2년', '장단기 금리차', 'bp', -1, 0, 'FRED', 'D', lambda o: fred_or('T10Y2Y', START_D, lambda: ust('daily_treasury_yield_curve')['10 YR'] - ust('daily_treasury_yield_curve')['2 YR']) * 100),
    ('us_rates', 'us_curve3m', '미국 10년 − 3개월', '뉴욕 연준 경기침체 확률 모델의 입력', 'bp', -1, 0, 'FRED', 'D', lambda o: fred_or('T10Y3M', START_D, lambda: ust('daily_treasury_yield_curve')['10 YR'] - ust('daily_treasury_yield_curve')['3 MO']) * 100),
    ('us_rates', 'us_2y', '미국 2년 국채금리', '향후 2년 연준 금리 경로 기대', '%', 1, None, 'FRED', 'D', lambda o: fred_or('DGS2', START_D, lambda: ust('daily_treasury_yield_curve')['2 YR'])),
    ('us_rates', 'us_ffr', '연방기금 실효금리', '현재 정책금리', '%', 1, None, 'FRED', 'D', lambda o: fred('DFF', START_D)),
    ('us_rates', 'us_real10', '미국 10년 실질금리', 'TIPS 10년 · 성장주 할인율', '%', 1, 2.0, 'FRED', 'D', lambda o: fred_or('DFII10', START_D, lambda: ust('daily_treasury_real_yield_curve')['10 YR'])),
    ('us_rates', 'us_be5y5', '5년 후 5년 기대인플레이션', '5y5y forward', '%', 1, 2.8, 'FRED', 'D', lambda o: fred('T5YIFR', START_D)),
    ('us_infl', 'us_ccpi', '근원 CPI (전년비)', '식품·에너지 제외 소비자물가', '%', 1, None, 'FRED', 'M', lambda o: yoy(fred('CPILFESL', START_L))),
    ('us_infl', 'us_cpce', '근원 PCE (전년비)', '연준 목표(2%) 기준 물가', '%', 1, None, 'FRED', 'M', lambda o: yoy(fred('PCEPILFE', START_L))),
    ('us_infl', 'us_ppi', 'PPI 최종수요 (전년비)', '생산자가 받는 판매가격', '%', 1, None, 'FRED', 'M', lambda o: yoy(fred('PPIFIS', START_L))),
    ('us_labor', 'us_unrate', '실업률', '미국 실업률', '%', 1, None, 'FRED', 'M', lambda o: fred('UNRATE', START_L)),
    ('us_labor', 'us_sahm', '삼 법칙 지표', '0.5%p 이상 = 침체 진입 신호', '%p', 1, 0.5, 'FRED', 'M', lambda o: fred('SAHMREALTIME', START_L)),
    ('us_labor', 'us_claims', '신규 실업수당 청구', '주간 · 천 건', 'K', 1, None, 'FRED', 'W', lambda o: fred('ICSA', START_L) / 1000),
    ('us_labor', 'us_dollar', '달러 가치(광의)', '무역가중 달러지수', '', 1, None, 'FRED', 'D', lambda o: fred('DTWEXBGS', START_D)),
    ('us_labor', 'us_m2', 'M2 통화량 (전년비)', '시중 유동성', '%', -1, None, 'FRED', 'M', lambda o: yoy(fred('M2SL', START_L))),
    ('jp', 'jp_2y', '일본 2년 국채금리', '일본은행 정책금리 기대', '%', 1, None, '일본 재무성', 'D', lambda o: jgb()['2Y']),
    ('jp', 'jp_10y', '일본 10년 국채금리', '엔 캐리·해외자금 환류 변수', '%', 1, None, '일본 재무성', 'D', lambda o: jgb()['10Y']),
    ('kr', 'kr_deposit', '투자자예탁금', '증시 대기자금 · 조원', '조원', -1, None, '금융투자협회', 'D', lambda o: kofia()[KOFIA_COLS['deposit']] / 1e6),
    ('kr', 'kr_credit', '신용거래융자 잔고', '빚투 규모 · 조원', '조원', 1, None, '금융투자협회', 'D', lambda o: kofia_credit()[KOFIA_COLS['credit']] / 1e6),
    ('kr', 'kr_margin', '미수금 반대매매 금액', '하루 강제청산 규모 · 억원', '억원', 1, None, '금융투자협회', 'D', lambda o: kofia()['TMPV6'] / 100),
    ('kr', 'kr_cratio', '신용잔고 ÷ 예탁금', '레버리지 과열도 · %', '%', 1, None, '금융투자협회', 'D', lambda o: kr_credit_ratio()),
    ('kr', 'vkospi', 'VKOSPI', '코스피200 30일 내재변동성', '', 1, 30, 'KRX', 'D', lambda o: vkospi(set(o.get('vkospi', {})))),
]
ACCUM = {'vkospi'}   # 매일 받은 값을 이력에 쌓는 지표(나머지는 매번 전체를 다시 받음)
# 주기별: (짧은 변화 일수, 라벨, 긴 변화 일수, 라벨, 백분위 기간(일), 보관 기간(일))
FREQ = {'D': (7, '1주', 30, '1개월', 365, 400), 'W': (7, '1주', 91, '3개월', 365 * 3, 365 * 5),
        'M': (35, '전월', 365, '1년', 365 * 3, 365 * 5), 'Q': (95, '전분기', 365, '1년', 365 * 5, 365 * 6)}

KEYS = [('FRED', 'FRED_API_KEY', '미국 신용·금리·물가·고용 전부', 'https://fredaccount.stlouisfed.org/apikeys'),
        ('KRX', 'KRX_API_KEY', 'VKOSPI', 'https://openapi.krx.co.kr → 인증키 신청 후 파생상품지수 API 이용신청')]
SRCKEY = {'FRED': 'FRED_API_KEY', 'KRX': 'KRX_API_KEY'}

USED_ALT = set()
def status_of(k, src):
    if k in USED_ALT: return 'FRED 막힘 · 미 재무부 자료로 대체 수집'
    key = SRCKEY.get(src)
    if k in ERR:
        if key and not keyset(key): return f'{key} 미등록 → 수집 안 됨'
        return '수집 실패: ' + ERR[k][:80]
    if key == 'FRED_API_KEY' and not keyset(key):
        return 'FRED 키 미등록 · 공개 CSV로 우회 수집 중'
    return '정상 수집'

def write_keys():
    rows = []
    for name, key, affect, how in KEYS:
        reg = keyset(key)
        bad = [x[1] for x in SERIES if x[7] == name and x[1] in ERR]
        if reg and not bad: st = '등록됨 · 정상 수집'
        elif reg: st = '등록됨 · 수집 오류: ' + ERR[bad[0]][:60]
        elif not bad: st = '미등록 · 공개 경로로 우회 수집 중(느림)'
        else: st = '미등록 · 수집 안 됨'
        rows.append({'source': name, 'key': key, 'registered': '등록' if reg else '미등록', 'state': st, 'affect': affect, 'issue_at': how, 'ok': bool(reg and not bad)})
    json.dump(rows, open(os.path.join(HERE, 'liq_keys.json'), 'w'), ensure_ascii=False, indent=1)

def main():
    old = {}
    p = os.path.join(HERE, 'liq_series.json')
    if os.path.exists(p):
        for r in json.load(open(p)):
            old.setdefault(r['id'], {})[r['date']] = r['value']
    prefetch_fred()
    rows, summ = [], []
    for order, (grp, k, title, sub, unit, sign, line, src, fq, fn) in enumerate(SERIES):
        try:
            s_new = fn(old).dropna()
        except Exception as e:
            note(f'[실패] {k}: {str(e)[:200]}'); ERR[k] = str(e)[:160]; s_new = pd.Series(dtype=float)
        a_days, a_lab, b_days, b_lab, pct_days, keep_days = FREQ[fq]
        cut = pd.Timestamp(TODAY - dt.timedelta(days=keep_days))
        d = dict(old.get(k, {})) if (k in ACCUM or k in ERR) else {}
        for i, v in s_new.items():
            d[pd.Timestamp(i).strftime('%Y-%m-%d')] = round(float(v), 4)
        d = {a: b for a, b in d.items() if a >= cut.strftime('%Y-%m-%d')}
        s = pd.Series(d, dtype=float).sort_index()
        s.index = pd.to_datetime(s.index)
        for i, v in s.items():
            rows.append({'id': k, 'date': i.strftime('%Y-%m-%d'), 'value': v})
        r = {'id': k, 'group': grp, 'order': order, 'title': title, 'subtitle': sub, 'unit': unit, 'risk_dir': sign, 'line': line, 'src': src, 'freq': fq,
             'lab_a': a_lab, 'lab_b': b_lab, 'pct_years': round(pct_days / 365), 'fresh': k not in ERR and len(s_new) > 0, 'value': None, 'asof': None,
             'chg_1w': None, 'chg_1m': None, 'pct_1y': None, 'median_1y': None, 'alert': False, 'why': '', 'status': status_of(k, src)}
        if len(s) >= 8:
            last, Lv = s.index[-1], s.iloc[-1]
            def ago(days):
                q = s[s.index <= last - pd.Timedelta(days=days)]
                return float(q.iloc[-1]) if len(q) else None
            win = s[s.index > last - pd.Timedelta(days=pct_days)]
            wa, wb = ago(a_days), ago(b_days)
            pct = float((win <= Lv).mean() * 100)
            step = max(1, int(round(len(win) / (pct_days / b_days))))  # 긴 변화 창에 해당하는 관측치 수
            chb = (win - win.shift(step)).dropna()
            sd = float(chb.std()) if len(chb) > 8 else None
            r.update(value=float(Lv), asof=last.strftime('%Y-%m-%d'), chg_1w=None if wa is None else float(Lv - wa), chg_1m=None if wb is None else float(Lv - wb),
                     pct_1y=round(pct), median_1y=float(win.median()))
            why = []
            riskpct = pct if sign > 0 else 100 - pct
            if riskpct >= 90: why.append(f'{r["pct_years"]}년 백분위 {round(pct)}%')
            if r['chg_1m'] is not None and sd and sign * r['chg_1m'] >= 2 * sd: why.append(f'{b_lab} 위험방향 급변')
            if line is not None and sign * (Lv - line) > 0: why.append(f'경보선 {line} {"초과" if sign > 0 else "하회"}')
            r['alert'] = bool(why); r['why'] = ' · '.join(why)
        summ.append(r)
    json.dump(rows, open(p, 'w'), ensure_ascii=False, separators=(',', ':'))
    json.dump(summ, open(os.path.join(HERE, 'liq_summary.json'), 'w'), ensure_ascii=False, indent=0)
    json.dump({'run': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'log': log}, open(os.path.join(HERE, 'liq_log.json'), 'w'), ensure_ascii=False, indent=1)
    write_keys()
    a = [x['title'] for x in summ if x['alert']]
    print(f'경보 {len(a)}개: {", ".join(a)}')

if __name__ == '__main__':
    main()
