# 산업 지표 정원 수집기 — catalog.json의 API 지표(KOSIS·관세청·FRED·야후)를 받아 대시보드용 파일 2개를 만든다.
#   dash/ind_summary.json : 지표별 최신값·전년비·3개월 추세·신호 (뉴스 기반 지표는 '보도 기반' 행으로 포함)
#   dash/ind_series.json  : 지표별 시계열(최근 3년, 대표 시리즈 + 보조 시리즈)
#   ind/collect_log.json  : 지표별 수집 결과(성공/실패 사유). 인증키 내용은 절대 기록하지 않는다.
# GitHub Actions에서 매일 실행. Secret: KOSIS_API_KEY, DATA_GO_KR_KEY, FRED_API_KEY
import os, re, json, time, datetime as dt
from concurrent.futures import ThreadPoolExecutor
import requests, threading
DG_LOCK = threading.Lock(); HSLOG = {}   # data.go.kr는 동시 접속 시 연결을 끊는다 → 한 번에 하나씩

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
K_KOSIS = os.environ.get('KOSIS_API_KEY', '').strip(); K_DG = os.environ.get('DATA_GO_KR_KEY', '').strip(); K_FRED = os.environ.get('FRED_API_KEY', '').strip()
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'}
TODAY = dt.date.today()
MONTHS = 40
LOG = {}

def get(url, params=None, timeout=(15, 90), tries=3):
    last = None
    for a in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=timeout); r.raise_for_status(); return r
        except Exception as e:
            last = e; time.sleep(3 + 5 * a)
    raise RuntimeError(re.sub(r'(apiKey|serviceKey|api_key)=[^&\s]+', r'\1=***', str(last))[:200])

def ym(s):  # 'YYYYMM' / 'YYYY.MM' / 'YYYY-MM' -> 'YYYY-MM'
    s = re.sub(r'\D', '', str(s)); return f'{s[:4]}-{s[4:6]}'

# ---------------- KOSIS: 이름으로 코드를 찾아 조회 ----------------
_META = {}
def kmeta(org, tbl):
    k = (org, tbl)
    if k not in _META:
        j = get('https://kosis.kr/openapi/statisticsData.do', dict(method='getMeta', type='ITM', orgId=org, tblId=tbl, apiKey=K_KOSIS, format='json', jsonVD='Y')).json()
        if not isinstance(j, list): raise RuntimeError(f'메타 조회 실패: {j}')
        dims = {}
        for x in j: dims.setdefault(x['OBJ_ID'], []).append((x['ITM_ID'], (x.get('ITM_NM') or '').strip()))
        _META[k] = dims
    return _META[k]

def pick(lst, want):
    if want == 'ALL': return 'ALL'
    for c, n in lst:                     # 정확히 같은 이름 우선
        if n == want: return c
    for c, n in lst:
        if want in n: return c
    raise RuntimeError(f"'{want}' 항목을 찾지 못함 (후보 예: {', '.join(n for _, n in lst[:6])})")

def kosis(org, tbl, itm, dims, agg=None):
    """dims: 분류 순서대로 이름(또는 'ALL'). agg='sum'이면 ALL 분류를 합산, 'ytd'면 연누계를 월값으로."""
    meta = kmeta(org, tbl)
    objs = [o for o in meta if o != 'ITEM']
    p = dict(method='getList', orgId=org, tblId=tbl, itmId=pick(meta['ITEM'], itm), prdSe='M', newEstPrdCnt=str(MONTHS), apiKey=K_KOSIS, format='json', jsonVD='Y')
    for i, o in enumerate(objs):
        want = dims[i] if i < len(dims) else 'ALL'
        p[f'objL{i + 1}'] = pick(meta[o], want)
    j = get('https://kosis.kr/openapi/Param/statisticsParameterData.do', p).json()
    if not isinstance(j, list): raise RuntimeError(f"조회 실패: {j.get('errMsg', j) if isinstance(j, dict) else j}")
    s, unit = {}, ''
    for x in j:
        try: v = float(str(x['DT']).replace(',', ''))
        except Exception: continue
        d = ym(x['PRD_DE']); unit = x.get('UNIT_NM') or unit
        s[d] = s.get(d, 0) + v if agg == 'sum' else v if d not in s else s[d]
    if agg == 'ytd':
        out = {}
        for d in sorted(s):
            prev = f"{d[:4]}-{int(d[5:]) - 1:02d}"
            out[d] = s[d] - s[prev] if d[5:] != '01' and prev in s else (s[d] if d[5:] == '01' else None)
        s = {d: v for d, v in out.items() if v is not None}
    if not s: raise RuntimeError('자료 0건')
    return dict(sorted(s.items())), unit

# ---------------- 관세청 품목별·국가별 수출입(12개월 단위) ----------------
def customs(hs_list, cnty='', field='expDlr'):
    tot = {}
    end = TODAY.replace(day=1) - dt.timedelta(days=1)
    for back in range(3):
        e = dt.date(end.year - back, end.month, 1); s = dt.date(e.year - 1, e.month, 1) + dt.timedelta(days=32); s = s.replace(day=1)
        for hs in hs_list:
            with DG_LOCK:
                r = get('https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList', dict(serviceKey=K_DG, strtYymm=s.strftime('%Y%m'), endYymm=e.strftime('%Y%m'), cntyCd=cnty, hsSgn=hs), timeout=(20, 150), tries=5)
                time.sleep(0.5)
            code = re.search(r'<resultCode>(\d+)</resultCode>', r.text)
            if code and code.group(1) not in ('00', '0'):
                raise RuntimeError(re.search(r'<resultMsg>(.*?)</resultMsg>', r.text).group(1))
            items = [dict(re.findall(r'<(\w+)>([^<]*)</\1>', it)) for it in re.findall(r'<item>(.*?)</item>', r.text, re.S)]
            items = [f for f in items if f.get('year', '총계') != '총계' and f.get('hsCd', '-') != '-']
            codes = {f['hsCd'] for f in items}
            leaf = {c for c in codes if not any(o != c and o.startswith(c) for o in codes)}   # 상위 코드 소계와 하위 코드가 같이 오면 이중 합산 방지
            HSLOG.setdefault(hs, set()).update(leaf)
            for f in items:
                if f['hsCd'] not in leaf: continue
                d = ym(f['year'])
                if field == 'unit':
                    a = tot.setdefault(d, [0.0, 0.0]); a[0] += float(f.get('impDlr') or 0); a[1] += float(f.get('impWgt') or 0)
                else:
                    tot[d] = tot.get(d, 0) + float(f.get(field) or 0)
    if field == 'unit':
        tot = {d: (a / w * 1000 if w else None) for d, (a, w) in tot.items()}   # 달러/톤
        tot = {d: v for d, v in tot.items() if v}
        return dict(sorted(tot.items())), '달러/톤'
    if not tot: raise RuntimeError('자료 0건')
    return {d: v / 1e6 for d, v in sorted(tot.items())}, '백만달러'

# ---------------- FRED · 야후 ----------------
def fred(sid):
    start = (TODAY - dt.timedelta(days=31 * MONTHS)).isoformat()
    if K_FRED:
        obs = get('https://api.stlouisfed.org/fred/series/observations', dict(series_id=sid, api_key=K_FRED, file_type='json', observation_start=start)).json()['observations']
        s = {o['date'][:7]: float(o['value']) for o in obs if o['value'] not in ('.', '')}
    else:
        r = get(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}&cosd={start}')
        s = {}
        for line in r.text.splitlines()[1:]:
            d, v = line.split(',')[:2]
            if v not in ('.', ''): s[d[:7]] = float(v)
    if not s: raise RuntimeError('자료 0건')
    return s, ''

def yahoo(sym):
    j = get(f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}', dict(range='3y', interval='1wk')).json()['chart']['result'][0]
    ts, cl = j['timestamp'], j['indicators']['quote'][0]['close']
    s = {dt.datetime.utcfromtimestamp(t).strftime('%Y-%m-%d'): c for t, c in zip(ts, cl) if c is not None}
    if not s: raise RuntimeError('자료 0건')
    return s, j['meta'].get('currency', '')

# ---------------- 지표별 수집 정의(대표 시리즈가 첫 번째) ----------------
P = ['총지수']
SPEC = {
 'exp_volume': [('총지수', lambda: kosis('301', 'DT_403Y002', '수출물량지수', ['총지수'])), ('반도체', lambda: kosis('301', 'DT_403Y002', '수출물량지수', ['반도체'])),
                ('자동차및부품', lambda: kosis('301', 'DT_403Y002', '수출물량지수', ['자동차및부품'])), ('화학제품', lambda: kosis('301', 'DT_403Y002', '수출물량지수', ['화학제품']))],
 'cli': [('선행지수 순환변동치', lambda: kosis('101', 'DT_1C8015', '경기종합지수', ['선행지수 순환변동치'])), ('동행지수 순환변동치', lambda: kosis('101', 'DT_1C8015', '경기종합지수', ['동행지수 순환변동치']))],
 'cli_parts': [(n, (lambda n=n: kosis('101', 'DT_1C8015', '경기종합지수', [n]))) for n in ['재고순환지표(전월차)(%p)', '경제심리지수(전월차)(p)', '기계류내수출하지수(선박제외)(전월비)(%)', '건설수주액(전월비)(%)', '수출입물가비율(전월비)(%)', '코스피(전월비)(%)', '장단기금리차(전월차)(%p)']],
 'ipi_sector': [('제조업 출하', lambda: kosis('101', 'DT_1F02001', '생산자제품 출하지수(원지수)', ['전국', '제조업'])), ('제조업 재고', lambda: kosis('101', 'DT_1F02001', '생산자제품 재고지수(원지수)', ['전국', '제조업']))],
 'semi_cycle': [('반도체 출하', lambda: kosis('101', 'DT_1F02001', '생산자제품 출하지수(원지수)', ['전국', '반도체 제조업'])), ('반도체 재고', lambda: kosis('101', 'DT_1F02001', '생산자제품 재고지수(원지수)', ['전국', '반도체 제조업']))],
 'permit': [('전국', lambda: kosis('116', 'DT_MLTM_1948', '인허가실적', ['전국', '합계(가구수기준)'], 'ytd')), ('수도권', lambda: kosis('116', 'DT_MLTM_1948', '인허가실적', ['수도권', '합계(가구수기준)'], 'ytd'))],
 'start': [('전국', lambda: kosis('116', 'DT_MLTM_5386', '착공실적', ['총계', '총계', '전국']))],
 'unsold': [('미분양(전국)', lambda: kosis('101', 'DT_1YL202004E', '미분양현황', ['ALL', '계'], 'sum')), ('준공후 미분양', lambda: kosis('116', 'DT_MLTM_5328', '호', ['전국', '합계', '계', '계']))],
 'orders': [('수주총액', lambda: kosis('101', 'DT_1G1B002', '수주액', ['수주총액', '계'])), ('건축', lambda: kosis('101', 'DT_1G1B002', '수주액', ['수주총액', '건축'])), ('토목', lambda: kosis('101', 'DT_1G1B002', '수주액', ['수주총액', '토목']))],
 'cement_ppi': [('포틀랜드시멘트', lambda: kosis('301', 'DT_404Y016', '생산자물가지수(품목별)', ['포틀랜드시멘트'])), ('레미콘', lambda: kosis('301', 'DT_404Y016', '생산자물가지수(품목별)', ['레미콘']))],
 'csi': [('소비자심리지수', lambda: kosis('301', 'DT_511Y002', 'ALL', ['소비자심리지수', '전체']))],
 'retail_fmt': [(n, (lambda n=n: kosis('101', 'DT_1K41013', '불변지수', [n]))) for n in ['백화점', '대형마트', '면세점', '편의점', '인터넷 쇼핑']],
 'online': [('합계', lambda: kosis('101', 'DT_1KE10041', '거래액', ['합계', '계'])), ('음·식료품', lambda: kosis('101', 'DT_1KE10041', '거래액', ['음·식료품', '계'])), ('화장품', lambda: kosis('101', 'DT_1KE10041', '거래액', ['화장품', '계']))],
 'parcel': [('소화물 전문 운송업', lambda: kosis('101', 'DT_1KC2020', '불변지수', ['소화물 전문 운송업']))],
 'cpi': [('총지수', lambda: kosis('101', 'DT_1J22001', '소비자물가지수', ['전국', '0 총지수'])), ('근원(식료품·에너지 제외)', lambda: kosis('101', 'DT_1J22009', '소비자물가지수', ['식료품 및 에너지제외 지수'])),
         ('식료품', lambda: kosis('101', 'DT_1J22001', '소비자물가지수', ['전국', '01.1 식료품']))],
 'inbound': [(n, (lambda n=n: kosis('314', 'DT_TRD_SEX_ENT_AGG_MONTH', '계', [n]))) for n in ['총계', '중국', '일본', '미국', '대만']],
 'outbound': [('국민 해외출국', lambda: kosis('314', 'DT_SEX_DEP_AGG_MONTH', '내국인출국', ['계']))],
 # 관세청(수출 백만달러, 수입은 별도 표기)
 'semi_hs_mem': [('전체', lambda: customs(['854232'])), ('중국', lambda: customs(['854232'], 'CN')), ('대만', lambda: customs(['854232'], 'TW')), ('미국', lambda: customs(['854232'], 'US'))],
 'xfmr_exp': [('미국', lambda: customs(['8504'], 'US')), ('전체', lambda: customs(['8504']))],
 'cable_exp': [('전체', lambda: customs(['8544'])), ('미국', lambda: customs(['8544'], 'US'))],
 'ship_exp': [('전체', lambda: customs(['89']))],
 'car_exp': [('전체', lambda: customs(['8703'])), ('미국', lambda: customs(['8703'], 'US'))],
 'parts_exp': [('전체', lambda: customs(['8708'])), ('미국', lambda: customs(['8708'], 'US'))],
 'battery_exp': [('전체', lambda: customs(['850760'])), ('미국', lambda: customs(['850760'], 'US'))],
 'rebar_trade': [('수입', lambda: customs(['7214'], '', 'impDlr')), ('수출', lambda: customs(['7214']))],
 'pipe_us': [('미국', lambda: customs(['7305', '7306'], 'US'))],
 'needle_coke': [('수입', lambda: customs(['270820'], '', 'impDlr'))],
 'mt_exp': [('전체', lambda: customs([str(h) for h in range(8456, 8464)])), ('미국', lambda: customs([str(h) for h in range(8456, 8464)], 'US')), ('중국', lambda: customs([str(h) for h in range(8456, 8464)], 'CN'))],
 'excav_exp': [('전체', lambda: customs(['842952']))],
 'cosme_exp': [('전체', lambda: customs(['3304'])), ('중국', lambda: customs(['3304'], 'CN')), ('미국', lambda: customs(['3304'], 'US')), ('일본', lambda: customs(['3304'], 'JP'))],
 'ramen_exp': [('전체', lambda: customs(['1902301010'])), ('미국', lambda: customs(['1902301010'], 'US')), ('중국', lambda: customs(['1902301010'], 'CN'))],
 'snack_exp': [('전체', lambda: customs(['1704', '1905']))],
 'pulp_imp': [('수입 단가', lambda: customs(['4703'], '', 'unit')), ('수입액', lambda: customs(['4703'], '', 'impDlr'))],
 'fluting': [('수출', lambda: customs(['4805'])), ('수입', lambda: customs(['4805'], '', 'impDlr'))],
}

def build_spec(cat):
    for x in cat['indicators']:
        if x['src'] == 'fred': SPEC[x['id']] = [(x['name'], (lambda r=x['ref']: fred(r)))]
        if x['src'] == 'yahoo': SPEC[x['id']] = [(x['name'], (lambda r=x['ref']: yahoo(r)))]

# ---------------- 계산 ----------------
def shift(d, n):
    y, m = int(d[:4]), int(d[5:7]) + n
    while m <= 0: y, m = y - 1, m + 12
    while m > 12: y, m = y + 1, m - 12
    return f'{y}-{m:02d}'

def yoy_series(s):
    out = {}
    for d, v in s.items():
        p = s.get(shift(d[:7], -12)) if len(d) == 7 else None
        if p not in (None, 0): out[d] = (v / p - 1) * 100
    return out

def monthly(s):  # 일·주별 → 월말값
    m = {}
    for d in sorted(s): m[d[:7]] = s[d]
    return m

def summarize(x, series):
    lab, (s, unit) = series[0]
    tr = x['transform']
    ms = monthly(s) if len(next(iter(s))) == 10 else s
    if tr == 'spread' and len(series) > 1:            # 출하 YoY − 재고 YoY
        a, b = yoy_series(monthly(series[0][1][0])), yoy_series(monthly(series[1][1][0]))
        sig = {d: a[d] - b[d] for d in a if d in b}; basis = '출하 전년비 − 재고 전년비(%p)'
    elif tr == 'sum12_yoy':
        roll = {}
        ks = sorted(ms)
        for i, d in enumerate(ks):
            w = ks[max(0, i - 11): i + 1]
            if len(w) == 12 and w[0] == shift(d, -11): roll[d] = sum(ms[k] for k in w)
        sig = yoy_series(roll); basis = '12개월 합계 전년비(%)'
    elif tr == 'level':
        sig = None; basis = '수준'
    else:
        sig = yoy_series(ms); basis = '전년비(%)' if tr != 'mom' else '전월비(%)'
        if tr == 'mom':
            ks = sorted(ms); sig = {d: (ms[d] / ms[p] - 1) * 100 for p, d in zip(ks, ks[1:]) if ms[p]}
    last_d = max(s); v = s[last_d]
    row = dict(value=round(v, 4), unit=unit, asof=last_d, main=lab, basis=basis)
    if sig:
        ks = sorted(sig); cur = sig[ks[-1]]
        row['signal_value'] = round(cur, 2)
        avg = lambda arr: sum(arr) / len(arr) if arr else None
        a3, p3 = avg([sig[k] for k in ks[-3:]]), avg([sig[k] for k in ks[-6:-3]])
        row['avg3'] = round(a3, 2) if a3 is not None else None
        row['trend'] = None if p3 is None else ('가속' if a3 - p3 > 0.5 else '둔화' if a3 - p3 < -0.5 else '보합')
        row['sign_flip'] = len(ks) >= 2 and (sig[ks[-1]] > 0) != (sig[ks[-2]] > 0)
    else:
        ks = sorted(ms); vals = [ms[k] for k in ks]
        if len(vals) >= 6:
            a3, p3 = sum(vals[-3:]) / 3, sum(vals[-6:-3]) / 3
            row['trend'] = '상승' if a3 > p3 * 1.005 else '하락' if a3 < p3 * 0.995 else '보합'
        if len(vals) >= 13 and vals[-13] and min(vals) > 0: row['signal_value'] = round((vals[-1] / vals[-13] - 1) * 100, 2); row['basis'] = '수준 (전년비 참고)'
    return row, sig

def main():
    cat = json.load(open(os.path.join(HERE, 'catalog.json')))
    build_spec(cat)
    secs = {s['id']: s['name'] for s in cat['sectors']}
    jobs = [(x, lab, f) for x in cat['indicators'] if x['id'] in SPEC for lab, f in SPEC[x['id']]]
    res = {}
    def run(job):
        x, lab, f = job
        try: return x['id'], lab, f(), None
        except Exception as e: return x['id'], lab, None, str(e)[:200]
    with ThreadPoolExecutor(max_workers=6) as ex:
        for iid, lab, val, err in ex.map(run, jobs):
            res.setdefault(iid, []).append((lab, val, err))
    summary, series = [], []
    for x in cat['indicators']:
        base = dict(id=x['id'], sector=x['sector'], sector_name=secs[x['sector']], name=x['name'], src=x['src'], ref=x['ref'], role=x['role'],
                    freq=x['freq'], release=x['release'], transform=x['transform'], why=x['why'])
        if x['id'] not in SPEC:
            base.update(status='보도 기반' if x['src'] == 'news' else '준비 중'); summary.append(base); continue
        order = [lab for lab, _ in SPEC[x['id']]]
        got = sorted([r for r in res.get(x['id'], []) if r[1] is not None], key=lambda r: order.index(r[0]))
        errs = [f'{lab}: {err}' for lab, v, err in res.get(x['id'], []) if err]
        LOG[x['id']] = {'ok': [r[0] for r in got], 'err': errs}
        if not got or got[0][0] != order[0]:
            base.update(status='수집 실패', error=(errs[0] if errs else '대표 시리즈 없음')); summary.append(base); continue
        row, sig = summarize(x, [(lab, v) for lab, v, _ in got])
        base.update(row, status='정상 수집' if not errs else '일부 실패', series=[lab for lab, _, _ in got]); summary.append(base)
        cut = shift(TODAY.strftime('%Y-%m'), -37)
        for lab, (s, unit), _ in got:
            for d, v in sorted(s.items()):
                if d[:7] >= cut: series.append(dict(id=x['id'], label=lab, date=d if len(d) == 10 else d + '-01', value=round(v, 4)))
        if sig:
            for d, v in sorted(sig.items()):
                if d >= cut: series.append(dict(id=x['id'], label='신호', date=d + '-01', value=round(v, 3)))
    json.dump(summary, open(os.path.join(ROOT, 'dash', 'ind_summary.json'), 'w'), ensure_ascii=False, indent=0)
    json.dump(series, open(os.path.join(ROOT, 'dash', 'ind_series.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
    LOG['_run'] = dt.datetime.utcnow().isoformat(timespec='seconds') + 'Z'
    LOG['_hs_leaf'] = {k: sorted(v)[:30] for k, v in HSLOG.items()}
    json.dump(LOG, open(os.path.join(HERE, 'collect_log.json'), 'w'), ensure_ascii=False, indent=1)
    ok = sum(1 for r in summary if r['status'] in ('정상 수집', '일부 실패'))
    print(f'API 지표 {len(SPEC)}개 중 {ok}개 수집 · 시계열 {len(series)}행')
    for k, v in LOG.items():
        if not k.startswith('_') and v['err']: print(' 실패', k, v['err'][:2])

if __name__ == '__main__':
    main()
