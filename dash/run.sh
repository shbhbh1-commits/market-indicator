#!/usr/bin/env bash
# 시장 심리 대시보드 일일 데이터 생성: 1) 스냅샷 3) 3년+ 시계열
set -e
cd "$(dirname "$0")"
pip install -q --break-system-packages pandas numpy matplotlib requests >/dev/null 2>&1 || true
mkdir -p prev
for f in summary.json rsi.json sentiment.json; do [ -f "$f" ] && cp "$f" prev/; done
python3 snap.py
python3 hist.py
