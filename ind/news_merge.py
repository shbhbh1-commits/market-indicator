# 보도 기반 지표 병합기 — ind/news_data.json(보도·협회 발표에서 Claude가 채운 값)을
# dash/ind_summary.json · dash/ind_series.json 의 '보도 기반' 행에 합친다. API 키가 필요 없다.
# 사용: python3 ind/news_merge.py   (collect.py 끝에서도 자동 호출)
#
# news_data.json 형식 (지표 id별):
# { "<id>": { "unit": "억달러", "main": "수출액",
#             "levels": {"<라벨>": {"YYYY-MM" 또는 "YYYY-MM-DD": 값, ...}, ...},   # 첫 라벨이 대표값
#             "signal": {"YYYY-MM(-DD)": 값, ...},  "signal_basis": "전년비(%)",
#             "updated": "YYYY-MM-DD", "next_release": "YYYY-MM-DD",
#             "src": [{"title": "...", "url": "...", "date": "YYYY-MM-DD"}], "note": "..." } }
import os, json, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SUM = os.path.join(ROOT, 'dash', 'ind_summary.json'); SER = os.path.join(ROOT, 'dash', 'ind_series.json')
ND = os.path.join(HERE, 'news_data.json')

def d10(k): return k if len(k) == 10 else k + '-01'

def main():
    if not os.path.exists(ND): print('news_data.json 없음'); return
    news = json.load(open(ND, encoding='utf-8'))
    summ = json.load(open(SUM, encoding='utf-8')); ser = json.load(open(SER, encoding='utf-8'))
    today = dt.date.today().isoformat(); n = 0
    for row in summ:
        x = news.get(row['id'])
        if row.get('src') != 'news' or not x: continue
        levels = x.get('levels') or {}; sig = x.get('signal') or {}
        if not levels and not sig: continue
        ser = [s for s in ser if s['id'] != row['id']]
        for lab, s in levels.items():
            for k, v in sorted(s.items()):
                if v is not None: ser.append(dict(id=row['id'], label=lab, date=d10(k), value=round(float(v), 4)))
        for k, v in sorted(sig.items()):
            if v is not None: ser.append(dict(id=row['id'], label='신호', date=d10(k), value=round(float(v), 3)))
        main_lab = next(iter(levels), None)
        if main_lab:
            s = levels[main_lab]; last = max(s); val = s[last]
        else:
            last = max(sig); val = sig[last]
        row.update(value=round(float(val), 4), unit=x.get('unit', ''), asof=last, main=main_lab or (x.get('signal_basis') or '신호'),
                   basis=x.get('signal_basis', '전년비(%)'), status='보도 수집', series=list(levels) or ['신호'],
                   news_updated=x.get('updated'), next_release=x.get('next_release'), news_src=x.get('src', [])[:3], note=x.get('note', ''))
        if sig:
            ks = sorted(sig); row['signal_value'] = round(float(sig[ks[-1]]), 2)
            a3 = [sig[k] for k in ks[-3:]]; p3 = [sig[k] for k in ks[-6:-3]]
            row['avg3'] = round(sum(a3) / len(a3), 2)
            row['trend'] = None if not p3 else ('가속' if sum(a3)/len(a3) - sum(p3)/len(p3) > 0.5 else '둔화' if sum(a3)/len(a3) - sum(p3)/len(p3) < -0.5 else '보합')
            if row['trend'] is None and len(ks) >= 2: row['trend'] = '가속' if sig[ks[-1]] > sig[ks[-2]] + 0.5 else '둔화' if sig[ks[-1]] < sig[ks[-2]] - 0.5 else '보합'
            row['sign_flip'] = len(ks) >= 2 and (sig[ks[-1]] > 0) != (sig[ks[-2]] > 0)
        nr = x.get('next_release')
        if nr and nr < today: row['status'] = '보도 수집 · 갱신 필요'
        n += 1
    json.dump(summ, open(SUM, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    json.dump(ser, open(SER, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    left = [r['id'] for r in summ if r.get('src') == 'news' and r.get('status') == '보도 기반']
    print(f'보도 지표 {n}개 병합 · 아직 빈 보도 지표 {len(left)}개: {", ".join(left)}')

if __name__ == '__main__':
    main()
