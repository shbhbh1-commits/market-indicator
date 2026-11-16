# 접속 점검 2단계: KOSIS 통계표 검색 + 관세청 응답 형식 확인. 키 내용은 절대 기록하지 않는다.
import requests, json, time, os
out = {}
K = os.environ.get('KOSIS_API_KEY', '').strip(); D = os.environ.get('DATA_GO_KR_KEY', '').strip()
OUT = 'ind/probe_out.json'
def save(): json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
def rec(k, f):
    try: out[k] = f()
    except Exception as e: out[k] = 'ERR ' + repr(e)[:250]
    save()
out['run'] = time.strftime('%Y-%m-%d %H:%M:%S')
# 1) KOSIS 통합검색: 키워드별 상위 통계표(orgId, tblId, 표 이름, 최근 시점)
KW = ['수출물량지수', '경기종합지수 순환변동치', '광업제조업동향조사 생산 출하 재고지수', '반도체 생산 출하 재고지수', '주택건설실적 인허가',
      '주택건설실적 착공', '미분양주택현황', '건설경기동향조사 건설수주', '생산자물가지수 품목별', '소비자동향조사 소비자심리지수',
      '소매업태별 판매액지수', '온라인쇼핑동향 상품군별 거래액', '서비스업생산지수 소화물', '소비자물가지수 품목별', '국적별 입국자',
      '내국인 출국자', '목적별 국적별 입국']
def search(q):
    r = requests.get('https://kosis.kr/openapi/statisticsSearch.do', params={'method': 'getList', 'apiKey': K, 'searchNm': q, 'orgId': '', 'sort': 'RANK',
                     'startCount': '1', 'resultCount': '8', 'format': 'json', 'jsonVD': 'Y'}, timeout=(10, 40))
    try: j = r.json()
    except Exception: return r.text[:300]
    if isinstance(j, dict): return j
    return [{k: x.get(k) for k in ('ORG_ID', 'ORG_NM', 'TBL_ID', 'TBL_NM', 'END_PRD_DE', 'STAT_PRD_SE', 'CONTENTS') if x.get(k)} for x in j]
for q in KW: rec('kosis_s:' + q, lambda q=q: search(q))
# 2) 관세청 품목별·국가별 수출입: 응답 필드와 HS 자릿수 허용 범위
def cust(hs, c=''):
    r = requests.get('https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList', params={'serviceKey': D, 'strtYymm': '202509', 'endYymm': '202609', 'cntyCd': c, 'hsSgn': hs}, timeout=(10, 60))
    t = r.text
    import re
    items = re.findall(r'<item>(.*?)</item>', t, re.S)
    return {'st': r.status_code, 'n': len(items), 'first': items[0][:600] if items else t[:400], 'last': items[-1][:400] if items else ''}
for hs, c in [('8504', 'US'), ('854232', ''), ('89', ''), ('1902301010', ''), ('3304', 'CN')]:
    rec(f'cust:{hs}:{c}', lambda hs=hs, c=c: cust(hs, c))
print('done')
