# 아침의 스토아 — 매일 한 구절을 stoic_pool.json에서 순서대로 골라 stoic.json 맨 앞에 붙인다.
# 사용: python3 dash/stoic.py   (같은 날 두 번 돌려도 한 번만 추가)
# 풀(pool)을 다 쓰면 처음부터 다시 돈다. 남은 구절이 10개 미만이면 경고를 출력한다(새 구절 보강 신호).
import os, json, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__))
POOL = os.path.join(HERE, 'stoic_pool.json'); OUT = os.path.join(HERE, 'stoic.json')

def main():
    pool = json.load(open(POOL, encoding='utf-8'))
    hist = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else []
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date().isoformat()
    if hist and hist[0]['date'] == today:
        print('오늘 구절 이미 있음:', hist[0]['author'], hist[0]['ref']); return
    used = [h['id'] for h in hist]
    used_now = set(used[: len(hist) % len(pool)])  # 이번 바퀴에서 이미 쓴 구절
    nxt = next((p for p in pool if p['id'] not in used_now), pool[0])
    row = dict(nxt, date=today, day=len(hist) + 1)
    hist = [row] + hist
    json.dump(hist, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    left = len(pool) - len(used_now) - 1
    print(f'{today} · {row["day"]}일째 · {row["author"]} 『{row["work"]}』 {row["ref"]} · 풀에 남은 구절 {left}개' + (' — 보강 필요' if left < 10 else ''))

if __name__ == '__main__':
    main()
