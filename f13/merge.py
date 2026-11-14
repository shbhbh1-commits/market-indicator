# reasons.json(종목별 매매 사유)·reports.json(매니저별 해설)을 대시보드용 파일에 붙인다.
import os, json
HERE = os.path.dirname(os.path.abspath(__file__)); DASH = os.path.join(HERE, '..', 'dash')
R = json.load(open(os.path.join(HERE, 'reasons.json')))
P = json.load(open(os.path.join(HERE, 'reports.json')))
S = json.load(open(os.path.join(DASH, 'f13_managers.json')))
C = json.load(open(os.path.join(DASH, 'f13_changes.json')))
lab = lambda t, n: t if t and '.' not in t else n
for c in C:
    x = R.get(c['key'])
    ok = x and x.get('period') in ('', c['period'])  # 다른 분기 사유는 붙이지 않음
    c['label'] = lab(c.get('ticker'), c['name'])
    c['reason'] = x['reason'] if ok else ''
    c['basis'] = x['basis'] if ok else ''
    c['reason_src'] = x.get('src', '') if ok else ''
    c['reason_url'] = x.get('url', '') if ok else ''
json.dump(C, open(os.path.join(DASH, 'f13_changes.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
rows = []
for s in S:
    p = P.get(s['id'], {})
    stale = bool(p) and p.get('period') != s.get('period')
    rows.append({'mid': s['id'], 'headline': p.get('headline', ''), 'trend_3y': p.get('trend_3y', ''), 'latest': p.get('latest', ''), 'watch': p.get('watch', ''),
                 'report_period': p.get('period', ''), 'stale': stale, 'sources': p.get('sources', [])})
json.dump(rows, open(os.path.join(DASH, 'f13_reports.json'), 'w'), ensure_ascii=False, indent=0)
# 표시용 라벨을 시계열에도
T = json.load(open(os.path.join(DASH, 'f13_series.json')))
T = [{'mid': t['mid'], 'q': t['q'], 'cusip': t['cusip'], 'label': t.get('label') or lab(t.get('ticker'), t['name']), 'weight': t['weight'], 'value': t['value'] if 'label' in t else round(t['value'] / 1e6, 1)} for t in T]
json.dump(T, open(os.path.join(DASH, 'f13_series.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print('사유 부착', sum(1 for c in C if c['reason']), '/', len(C), '· 해설', sum(1 for r in rows if r['headline']), '/', len(rows))
