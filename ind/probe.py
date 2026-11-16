# 접속 점검 4단계: 남은 KOSIS 코드 찾기 + 표본 조회 형식 확인. 키 내용은 기록하지 않는다.
import requests, json, time, os
out = {}
K = os.environ.get('KOSIS_API_KEY', '').strip()
OUT = 'ind/probe_out.json'
def save(): json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
def rec(k, f):
    for a in range(3):
        try: out[k] = f(); break
        except Exception as e: out[k] = 'ERR ' + repr(e)[:200]; time.sleep(3)
    save()
out['run'] = time.strftime('%Y-%m-%d %H:%M:%S')
def kget(url, **p):
    p.update({'apiKey': K, 'format': 'json', 'jsonVD': 'Y'})
    r = requests.get(url, params=p, timeout=(15, 90))
    try: return r.json()
    except Exception: return r.text[:300]
def meta(org, tbl, kws=None):
    j = kget('https://kosis.kr/openapi/statisticsData.do', method='getMeta', type='ITM', orgId=org, tblId=tbl)
    if not isinstance(j, list): return j
    by = {}
    for x in j:
        o = x.get('OBJ_ID'); b = by.setdefault(o, {'name': x.get('OBJ_NM'), 'n': 0, 'items': []}); b['n'] += 1
        nm = x.get('ITM_NM') or ''
        if (kws is None and len(b['items']) < 40) or (kws and any(k in nm for k in kws)) or o == 'ITEM':
            b['items'].append([x.get('ITM_ID'), nm])
    return by
rec('m:404Y016', lambda: meta('301', 'DT_404Y016', ['시멘트', '레미콘', '콘크리트']))
rec('m:511Y002', lambda: meta('301', 'DT_511Y002', ['소비자심리', '전체']))
rec('m:1KC2020', lambda: meta('101', 'DT_1KC2020', ['소화물', '택배', '육상 운송', '항공']))
rec('m:1KE10041', lambda: meta('101', 'DT_1KE10041'))
rec('m:SEX_DEP', lambda: meta('314', 'DT_SEX_DEP_AGG_MONTH'))
rec('m:403Y002', lambda: meta('301', 'DT_403Y002', ['반도체', '총지수', '컴퓨터전자', '자동차', '선박', '화학', '석유']))
for t in ['DT_1F01501', 'DT_1F01502', 'DT_1F02013', 'DT_1F01001']:
    rec('m:' + t, lambda t=t: meta('101', t, ['반도체', '전산업', '광공업', '제조업', '총지수', '자동차', '화학', '1차금속', '전자부품']))
def search(q):
    j = kget('https://kosis.kr/openapi/statisticsSearch.do', method='getList', searchNm=q, orgId='101', sort='RANK', startCount='1', resultCount='12')
    return [[x.get('TBL_ID'), x.get('TBL_NM'), x.get('END_PRD_DE')] for x in j] if isinstance(j, list) else j
for q in ['산업별 출하지수', '산업별 재고지수', '생산 출하 재고']:
    rec('s:' + q, lambda q=q: search(q))
def sample(org, tbl, itm, n='3', **o):
    p = dict(method='getList', orgId=org, tblId=tbl, itmId=itm, prdSe='M', newEstPrdCnt=n); p.update(o)
    j = kget('https://kosis.kr/openapi/Param/statisticsParameterData.do', **p)
    if not isinstance(j, list): return j
    return {'n': len(j), 'keys': list(j[0].keys()), 'rows': [{k: x.get(k) for k in ('ITM_ID', 'C1', 'C1_NM', 'C2', 'C2_NM', 'C3', 'C3_NM', 'C4_NM', 'PRD_DE', 'DT', 'UNIT_NM')} for x in j[:6]]}
rec('d:1C8015', lambda: sample('101', 'DT_1C8015', 'T1', objL1='A03'))
rec('d:MLTM_1948', lambda: sample('116', 'DT_MLTM_1948', '13103871090T1', objL1='13102871090A.0001', objL2='13102871090B.0002', objL3='ALL', objL4='ALL'))
rec('d:TRD_ENT', lambda: sample('314', 'DT_TRD_SEX_ENT_AGG_MONTH', '13103314421T01', objL1='13102314421A.2002'))
print('done')
