# 접속 점검 3단계: KOSIS 통계표 메타(항목·분류 코드)와 표본 데이터, 관세청 12개월 조회. 키 내용은 기록하지 않는다.
import requests, json, time, os, re
out = {}
K = os.environ.get('KOSIS_API_KEY', '').strip(); D = os.environ.get('DATA_GO_KR_KEY', '').strip()
OUT = 'ind/probe_out.json'
def save(): json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
def rec(k, f):
    try: out[k] = f()
    except Exception as e: out[k] = 'ERR ' + repr(e)[:250]
    save()
out['run'] = time.strftime('%Y-%m-%d %H:%M:%S')
def kget(url, **p):
    p.update({'apiKey': K, 'format': 'json', 'jsonVD': 'Y'})
    r = requests.get(url, params=p, timeout=(10, 60))
    try: return r.json()
    except Exception: return r.text[:300]
def meta(org, tbl):
    j = kget('https://kosis.kr/openapi/statisticsData.do', method='getMeta', type='ITM', orgId=org, tblId=tbl)
    if not isinstance(j, list): return j
    by = {}
    for x in j:
        o = x.get('OBJ_ID'); by.setdefault(o, {'name': x.get('OBJ_NM'), 'n': 0, 'items': []})
        by[o]['n'] += 1
        if len(by[o]['items']) < 60: by[o]['items'].append([x.get('ITM_ID'), x.get('ITM_NM'), x.get('UP_ITM_ID')])
    return by
def sample(org, tbl, **objs):
    p = dict(method='getList', orgId=org, tblId=tbl, itmId=objs.pop('itm', 'ALL'), prdSe='M', newEstPrdCnt='2')
    for i, (k, v) in enumerate(objs.items()): p[k] = v
    j = kget('https://kosis.kr/openapi/Param/statisticsParameterData.do', **p)
    if not isinstance(j, list): return j
    return {'n': len(j), 'rows': [{k: x.get(k) for k in ('ITM_ID', 'ITM_NM', 'C1', 'C1_NM', 'C2', 'C2_NM', 'PRD_DE', 'DT', 'UNIT_NM')} for x in j[:12]]}
T = [('301', 'DT_403Y002'), ('101', 'DT_1C8015'), ('116', 'DT_MLTM_1948'), ('116', 'DT_MLTM_5386'), ('101', 'DT_1YL202004E'), ('116', 'DT_MLTM_5328'),
     ('101', 'DT_1G1B002'), ('301', 'DT_404Y016'), ('301', 'DT_511Y002'), ('101', 'DT_1K41013'), ('101', 'DT_1KC2020'), ('101', 'DT_1J22001'),
     ('101', 'DT_1J22009'), ('314', 'DT_TRD_SEX_ENT_AGG_MONTH'), ('314', 'DT_SEX_DEP_AGG_MONTH')]
for org, tbl in T: rec(f'meta:{org}:{tbl}', lambda org=org, tbl=tbl: meta(org, tbl))
# 아직 표를 못 찾은 것: 업종별 생산·출하·재고지수, 온라인쇼핑 상품군별(최신)
def search(q):
    j = kget('https://kosis.kr/openapi/statisticsSearch.do', method='getList', searchNm=q, orgId='', sort='RANK', startCount='1', resultCount='10')
    if not isinstance(j, list): return j
    return [[x.get('ORG_ID'), x.get('TBL_ID'), x.get('TBL_NM'), x.get('END_PRD_DE')] for x in j]
for q in ['광업제조업 생산 출하 재고지수 산업별', '제조업 재고지수', '온라인쇼핑몰 취급상품범위별 상품군별 거래액', '반도체 재고지수']:
    rec('search:' + q, lambda q=q: search(q))
# 관세청: 12개월 이내 조회
def cust(hs, c=''):
    r = requests.get('https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList', params={'serviceKey': D, 'strtYymm': '202510', 'endYymm': '202609', 'cntyCd': c, 'hsSgn': hs}, timeout=(10, 60))
    items = re.findall(r'<item>(.*?)</item>', r.text, re.S)
    return {'st': r.status_code, 'n': len(items), 'first': items[0][:700] if items else r.text[:300], 'last': items[-1][:500] if items else ''}
for hs, c in [('8504', 'US'), ('854232', ''), ('89', ''), ('1902301010', ''), ('3304', 'CN'), ('8456', '')]:
    rec(f'cust:{hs}:{c}', lambda hs=hs, c=c: cust(hs, c))
print('done')
