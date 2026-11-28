# 턴 지시등 — 산업 지표마다 '턴 상태'를 계산하고, ind/playbook.json의 산업 연쇄 규칙으로 지시등을 켠다.
# 사용: python3 ind/turns.py   (ind_summary·ind_series 갱신 후. dash/ind_turns.json, dash/ind_tstate.json 생성)
#
# 지표 턴 상태 (신호 = 전년비 등 지표별 신호, 수준형은 원계열 3개월 변화)
#   상승 턴: 신호가 −→+ 로 바뀌었고 최근 3개월 평균도 직전 3개월보다 좋아짐 (확인된 전환)
#   상승 조짐: 아직 −지만 하락 폭이 줄며 3개월 평균이 개선 / 또는 +전환이지만 평균 확인 전
#   하락 조짐: 아직 +지만 상승 폭이 줄며 3개월 평균이 악화 / 또는 −전환이지만 평균 확인 전
#   하락 턴: 신호가 +→− 로 바뀌었고 3개월 평균도 악화
#   상승 지속 / 하락 지속 / 판단 보류(자료 3개 미만)
# 규칙의 지시등: 핵심 지표 중 하나라도 '턴'이면 점등, '조짐'이면 주의. invert=true 지표는 방향을 뒤집어 읽는다
# (예: 폐지값 하락 = 골판지에 좋음).
import os, json, datetime as dt
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
D = os.path.join(ROOT, 'dash')
UP_T, UP_H, DN_H, DN_T, UP_C, DN_C, NA = '상승 턴', '상승 조짐', '하락 조짐', '하락 턴', '상승 지속', '하락 지속', '판단 보류'
FLIP = {UP_T: DN_T, UP_H: DN_H, DN_H: UP_H, DN_T: UP_T, UP_C: DN_C, DN_C: UP_C, NA: NA}

def mean(a): return sum(a) / len(a) if a else None

def monthly(points):
    """(date, value) → 월말 값 목록 (일별·주별 계열을 월 단위로)."""
    m = {}
    for d, v in sorted(points): m[d[:7]] = v
    return [m[k] for k in sorted(m)], sorted(m)

def state_of(vals, dates, is_level):
    if is_level:
        if len(vals) < 5: return NA, None, None
        ch = [vals[i] - vals[i - 1] for i in range(1, len(vals))]
        s = ch  # 월간 변화량을 신호처럼 쓴다
    else:
        s = vals
    if len(s) < 3: return NA, (s[-1] if s else None), None
    cur, prev = s[-1], s[-2]
    a3 = mean(s[-3:]); p3 = mean(s[-6:-3]) if len(s) >= 6 else mean(s[:-3]) if len(s) > 3 else None
    better = p3 is not None and a3 > p3; worse = p3 is not None and a3 < p3
    if is_level:  # 수준형: 최근 2개월 연속 상승(하락) 전환 + 그 전 3개월은 반대 방향
        r2 = s[-2:]; before = s[-5:-2]
        if all(x > 0 for x in r2) and mean(before) < 0: st = UP_T
        elif all(x < 0 for x in r2) and mean(before) > 0: st = DN_T
        elif cur > 0 and mean(before) <= 0: st = UP_H
        elif cur < 0 and mean(before) >= 0: st = DN_H
        else: st = UP_C if mean(s[-3:]) > 0 else DN_C
        return st, cur, dates[-1] if dates else None
    if prev <= 0 < cur: st = UP_T if better else UP_H
    elif prev >= 0 > cur: st = DN_T if worse else DN_H
    elif cur < 0 and cur > prev and better: st = UP_H
    elif cur > 0 and cur < prev and worse: st = DN_H
    else: st = UP_C if cur > 0 else DN_C
    return st, cur, dates[-1] if dates else None

def main():
    summ = json.load(open(os.path.join(D, 'ind_summary.json'), encoding='utf-8'))
    ser = json.load(open(os.path.join(D, 'ind_series.json'), encoding='utf-8'))
    book = json.load(open(os.path.join(HERE, 'playbook.json'), encoding='utf-8'))
    newsp = os.path.join(D, 'ind_turn_news.json')
    news = json.load(open(newsp, encoding='utf-8')) if os.path.exists(newsp) else {}
    sig, lev = defaultdict(list), defaultdict(lambda: defaultdict(list))
    for p in ser:
        if p['label'] == '신호': sig[p['id']].append((p['date'], p['value']))
        else: lev[p['id']][p['label']].append((p['date'], p['value']))
    byid = {r['id']: r for r in summ}
    states = {}
    FLOW = {'mortgage'}  # 수준 자체가 '월간 증감'인 지표는 수준을 신호처럼 읽는다
    for r in summ:
        i = r['id']
        if i in FLOW and lev.get(i):
            lab = next(iter(lev[i])); vals, dates = monthly(lev[i][lab]); st, cur, asof = state_of(vals, dates, False); kind = '월간 증감'
        elif len(sig.get(i, [])) >= 3:
            vals, dates = monthly(sig[i]); st, cur, asof = state_of(vals, dates, False); kind = '신호'
        else:
            main_lab = r.get('main') if r.get('main') in lev.get(i, {}) else next(iter(lev.get(i, {})), None)
            if main_lab and len(lev[i][main_lab]) >= 5:
                vals, dates = monthly(lev[i][main_lab]); st, cur, asof = state_of(vals, dates, True); kind = '수준 변화'
            else:
                pts = sig.get(i, []); st, cur, asof, kind = NA, (pts[-1][1] if pts else None), (pts[-1][0][:7] if pts else None), '자료 부족'
        states[i] = dict(id=i, name=r['name'], sector_name=r.get('sector_name'), state=st, kind=kind,
                         cur=None if cur is None else round(cur, 2), asof=asof, basis=r.get('basis'), chains=[])
    rows = []
    for c in book:
        trig = []; up_t = up_h = dn_t = dn_h = 0
        for t in c['triggers']:
            s = states.get(t['ind'])
            if not s: continue
            st = FLIP[s['state']] if t.get('invert') else s['state']
            s['chains'].append(c['title'])
            core = t['role'] == '핵심'
            if core:
                up_t += st == UP_T; up_h += st == UP_H; dn_t += st == DN_T; dn_h += st == DN_H
            trig.append(dict(ind=t['ind'], name=s['name'], role=t['role'], invert=bool(t.get('invert')), raw=s['state'], read=st,
                             cur=s['cur'], asof=s['asof'], basis=s['basis'], kind=s['kind']))
        conf_up = sum(1 for x in trig if x['role'] == '확인' and x['read'] in (UP_T, UP_H, UP_C))
        conf_dn = sum(1 for x in trig if x['role'] == '확인' and x['read'] in (DN_T, DN_H, DN_C))
        n_conf = sum(1 for x in trig if x['role'] == '확인' and x['read'] != NA)
        if up_t and not dn_t: lamp, side = '상승 점등', 'up'
        elif dn_t and not up_t: lamp, side = '하락 점등', 'down'
        elif up_t and dn_t: lamp, side = '엇갈림', 'up' if conf_up >= conf_dn else 'down'
        elif up_h and not dn_h: lamp, side = '상승 조짐', 'up'
        elif dn_h and not up_h: lamp, side = '하락 조짐', 'down'
        elif up_h and dn_h: lamp, side = '엇갈림', 'up' if conf_up >= conf_dn else 'down'
        else:
            core_reads = [x['read'] for x in trig if x['role'] == '핵심']
            if core_reads and all(x == NA for x in core_reads): lamp, side = '자료 부족', 'up'
            else:
                lamp = '꺼짐'; side = 'up' if sum(x in (UP_C,) for x in core_reads) >= sum(x in (DN_C,) for x in core_reads) else 'down'
        play = c[side]
        rows.append(dict(id=c['id'], sector=c['sector'], title=c['title'], lamp=lamp, side='상승' if side == 'up' else '하락',
                         look=play['look'], action=play['action'], lag=play['lag'], why=c['why'],
                         confirm=f'확인 지표 {conf_up if side == "up" else conf_dn}/{n_conf}개 같은 방향',
                         triggers=trig, case=c.get('case'), news=news.get(c['id'], [])[:3], news_q=c.get('news_q', [])))
    order = {'상승 점등': 0, '하락 점등': 0, '엇갈림': 1, '상승 조짐': 2, '하락 조짐': 2, '꺼짐': 3, '자료 부족': 4}
    rows.sort(key=lambda r: (order[r['lamp']], r['sector']))
    prevp = os.path.join(D, 'prev', 'ind_turns.json')
    prev = {r['id']: r['lamp'] for r in json.load(open(prevp, encoding='utf-8'))} if os.path.exists(prevp) else {}
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date().isoformat()
    for r in rows:
        p = prev.get(r['id']); r['prev_lamp'] = p
        r['new'] = p is not None and p != r['lamp'] and r['lamp'] in ('상승 점등', '하락 점등', '상승 조짐', '하락 조짐', '엇갈림')
        r['asof'] = today
    json.dump(rows, open(os.path.join(D, 'ind_turns.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    st_rows = [dict(s, chains=' · '.join(s['chains'])) for s in states.values()]
    json.dump(st_rows, open(os.path.join(D, 'ind_tstate.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    lit = [r for r in rows if r['lamp'] in ('상승 점등', '하락 점등', '엇갈림')]
    hint = [r for r in rows if r['lamp'] in ('상승 조짐', '하락 조짐')]
    print(f'지시등: 점등 {len(lit)} · 조짐 {len(hint)} · 전체 {len(rows)}')
    for r in rows: print(('★' if r['new'] else ' '), r['lamp'], '|', r['title'], '|', ', '.join(f"{t['name']}={t['read']}" for t in r['triggers'] if t['role'] == '핵심'))

if __name__ == '__main__':
    main()
