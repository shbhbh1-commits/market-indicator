# CNN 공포탐욕 수집·반영
#   python dash/cnn.py fetch  → (GitHub Actions) CNN API를 직접 받아 dash/cnn_raw.json 저장
#   python dash/cnn.py apply  → (일일 갱신) cnn_raw.json을 fg_now.json·summary.json[0]·fg_hist.json에 반영
# CNN API는 날짜 파라미터별 캐시가 달라 오래된 값이 올 수 있으므로, 날짜 없는 주소와 최근 12일 날짜 주소를
# 모두 받아 fear_and_greed.timestamp가 가장 최신인 응답을 쓴다.
import os, sys, json, time, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'cnn_raw.json')
BASE = 'https://production.dataviz.cnn.io/index/fearandgreed/graphdata'
SUBS = [('market_momentum_sp500', '시장 모멘텀(S&P500 vs 125일선)'), ('stock_price_strength', '주가 강도(52주 신고가-신저가)'),
        ('stock_price_breadth', '시장 폭(상승-하락 거래량)'), ('put_call_options', '풋/콜 옵션'),
        ('market_volatility_vix', '변동성(VIX vs 50일선)'), ('junk_bond_demand', '정크본드 수요'),
        ('safe_haven_demand', '안전자산 수요(주식 vs 국채)')]
KO = {'extreme fear': '극단적 공포', 'fear': '공포', 'neutral': '중립', 'greed': '탐욕', 'extreme greed': '극단적 탐욕'}
HDR = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36',
       'Accept': 'application/json, text/plain, */*', 'Accept-Language': 'en-US,en;q=0.9',
       'Origin': 'https://edition.cnn.com', 'Referer': 'https://edition.cnn.com/'}

def fetch():
    import requests
    today = dt.datetime.utcnow().date()
    urls = [BASE] + [f'{BASE}/{(today - dt.timedelta(days=d)).isoformat()}' for d in range(0, 13)]
    best, log = None, []
    for u in urls:
        try:
            r = requests.get(u, headers=HDR, timeout=20)
            if r.status_code != 200:
                log.append({'url': u, 'status': r.status_code}); continue
            j = r.json(); ts = j['fear_and_greed']['timestamp']
            log.append({'url': u, 'status': 200, 'ts': ts})
            if best is None or ts > best['fear_and_greed']['timestamp']: best = j
        except Exception as e:
            log.append({'url': u, 'error': str(e)[:120]})
        time.sleep(0.7)
    if best is None:
        print(json.dumps(log, ensure_ascii=False, indent=1)); sys.exit('CNN 응답 없음')
    fg = best['fear_and_greed']
    hist = best.get('fear_and_greed_historical', {}).get('data', [])
    out = {'fetched_at': dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'), 'fear_and_greed': fg,
           'subs': {k: {'score': best.get(k, {}).get('score'), 'rating': best.get(k, {}).get('rating')} for k, _ in SUBS},
           'hist': [{'d': dt.datetime.utcfromtimestamp(p['x'] / 1000).date().isoformat(), 'y': round(p['y'])} for p in hist[-400:]],
           'log': log}
    json.dump(out, open(RAW, 'w'), ensure_ascii=False, indent=1)
    print('CNN', round(fg['score'], 1), fg['rating'], fg['timestamp'])

def apply():
    x = json.load(open(RAW)); fg = x['fear_and_greed']
    r1 = lambda v: None if v is None else round(float(v), 1)
    now = [{'indicator': '종합 지수', 'score': r1(fg['score']), 'rating': KO.get(fg['rating'], fg['rating'])}]
    for k, name in SUBS:
        s = x['subs'].get(k) or {}
        now.append({'indicator': name, 'score': r1(s.get('score')), 'rating': KO.get(s.get('rating'), s.get('rating'))})
    json.dump(now, open(os.path.join(HERE, 'fg_now.json'), 'w'), ensure_ascii=False, indent=1)
    sp = os.path.join(HERE, 'summary.json'); s = json.load(open(sp))
    s[0].update(cnn_fg=r1(fg['score']), cnn_fg_prev=r1(fg.get('previous_close')), cnn_fg_week=r1(fg.get('previous_1_week')),
                cnn_fg_month=r1(fg.get('previous_1_month')), cnn_fg_year=r1(fg.get('previous_1_year')),
                cnn_fg_rating=KO.get(fg['rating'], fg['rating']), cnn_fg_asof=fg['timestamp'])
    s[0].pop('cnn_fg_note', None)
    json.dump(s, open(sp, 'w'), ensure_ascii=False, indent=1)
    hp = os.path.join(HERE, 'fg_hist.json'); h = json.load(open(hp))
    for p in x.get('hist', []): h[p['d']] = p['y']
    h[fg['timestamp'][:10]] = round(fg['score'])
    json.dump(dict(sorted(h.items())), open(hp, 'w'))
    print('반영', now[0], fg['timestamp'], '수집', x['fetched_at'])

if __name__ == '__main__':
    {'fetch': fetch, 'apply': apply}[sys.argv[1] if len(sys.argv) > 1 else 'fetch']()
