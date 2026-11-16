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

for t in ['DT_1F02031','DT_1F02016','DT_1F02001']:
    rec('m:'+t, lambda t=t: meta('101', t, ['반도체','제조업','전국','출하','재고','생산','광공업']))
rec('m:1J22001', lambda: meta('101','DT_1J22001',['총지수','전국','식료품']))
print('done')
