# -*- coding: utf-8 -*-
# =====================================================================
#   국내 시장 지표 분석기  v3.0  (2026-11-06 업데이트)
# ---------------------------------------------------------------------
#   [시장 지표]
#     Fear & Greed Index + EMA + Oscillator / MDD(최대낙폭) / RSI
#     MACD / 볼린저밴드 %B / 투자심리도 / 이동평균 배열(골든·데드크로스)
#     실현변동성 / 추세강도
#   [시장 폭 지표]
#     ETF Breadth(10·20·60·120일선 상회율) / ADR 등락비율
#     52주 신고가·신저가 비율 / 업종 쏠림지수(HHI)
#   [섹터 지표]
#     Mansfield RS / Sortino Ratio + Top20 랭킹 / 이격도·과열도
#   [수급 지표]  ※ 자동수집 모드에서만
#     외국인·기관·개인 순매수 / 지수 PER·PBR
#
#   [v3 신규] 글로벌 심리·과매도 패널
#     지수·관심종목 RSI14 / VIX 기간구조(VIX9D·VIX·VIX3M) / VVIX / SKEW / MOVE
#     HYG/IEF 신용 / 미10년물·달러·원달러·금·비트코인 / CNN Fear&Greed 자동수집 시도
#     SOX 급락일 이후 수익률 통계 / 자동수집 안 되는 지표 바로가기 링크 21개
#     pykrx(KRX)가 막히면 야후 파이낸스로 자동 대체
#
#   ▶ 사용법은 함께 드린 "사용설명서"를 먼저 보세요.
#   ▶ 코딩 지식 없이 사용 가능합니다. 수정할 곳은 "설정" 블록 하나뿐입니다.
# =====================================================================


# ─────────────────────────────────────────────────────────────────────
#  ★ 설정 ★   여기만 고치시면 됩니다
# ─────────────────────────────────────────────────────────────────────
SETTINGS = {
    # ── 데이터를 어디서 가져올지 ──────────────────────────
    #   "auto"  : 인터넷에서 자동 수집   ← 평소에는 이것
    #   "demo"  : 가상 데이터로 연습     ← 처음 한 번은 이것 추천
    #   "excel" : 내가 만든 엑셀 업로드
    "DATA_MODE": "auto",

    # ── [v3] 글로벌 패널 켜기/끄기 ──────────────────────
    "RUN_GLOBAL": True,             # 글로벌 심리·RSI 패널
    "RUN_KOREA": True,              # 국내 지표(기존 v2 기능)

    # ── [v3] KRX 계정 (선택) ─────────────────────────────
    #   2026년부터 KRX 데이터는 로그인이 필요합니다.
    #   data.krx.co.kr 무료 회원 아이디/비번을 넣으면 수급·PER까지 받습니다.
    #   비워두면 야후 파이낸스로 자동 대체(지수·섹터ETF만, 수급 제외).
    #   ※ 노트북을 남과 공유할 때는 꼭 지우세요.
    "KRX_ID": "",
    "KRX_PW": "",

    # ── 분석 기간 ────────────────────────────────────────
    "START_DATE": "2024-11-01",     # 2년 이상 권장
    "END_DATE": None,               # None = 오늘까지

    # ── ETF 선정 ─────────────────────────────────────────
    "ETF_SELECT": "top_amount",     # "top_amount"(거래대금 상위) 또는 "keyword"
    "ETF_TOP_N": 45,
    "ETF_KEYWORDS": [
        "반도체", "코스닥150", "은행", "증권", "자동차", "방산", "조선",
        "화장품", "2차전지", "바이오", "로봇", "태양광", "전력", "건설",
        "보험", "인터넷", "게임", "철강", "운송", "원자력", "미디어",
    ],
    "EXCLUDE_WORDS": ["레버리지", "인버스", "채권", "달러", "금현물", "TR",
                      "선물", "머니마켓", "CD금리", "KOFR", "미국", "차이나",
                      "일본", "인도", "베트남", "글로벌"],

    # ── 지표 설정 ────────────────────────────────────────
    "FG_EMA": 20,
    "BREADTH_MAS": [10, 20, 60, 120],
    "RSI_N": 14,
    "MACD": (12, 26, 9),
    "BB_N": 20,
    "PSY_N": 10,                    # 투자심리도 기간
    "ADR_N": 20,                    # 등락비율 평활 기간
    "CONC_N": 20,                   # 업종쏠림 계산 기간
    "MA_SHORT": 20,                 # 골든크로스 단기선
    "MA_LONG": 60,                  # 골든크로스 장기선
    "SORTINO_N": 60,
    "SORTINO_MA": 60,               # 10주선
    "SORTINO_TOPN": 20,
    "GAP_MA_DAYS": 30,
    "LOOKBACK_DAYS": 247,
    "GAP_QUANTILE": 0.97,


    # ── [v3] 관심종목 (야후 티커: 한국 .KS/.KQ, 일본 .T) ──────
    "WATCHLIST": {
        "NVIDIA": "NVDA", "마이크론": "MU", "AMD": "AMD", "브로드컴": "AVGO",
        "KLA": "KLAC", "램리서치": "LRCX", "AMAT": "AMAT",
        "Onto": "ONTO", "Camtek": "CAMT", "Nova": "NVMI",
        "벤처글로벌": "VG", "블룸에너지": "BE", "컨스텔레이션": "CEG", "네비우스": "NBIS", "다이콤": "DY", "피바디": "BTU",
        "SK하이닉스": "000660.KS", "삼성전자": "005930.KS", "삼성전기": "009150.KS", "SK텔레콤": "017670.KS",
        "펨트론": "168360.KQ", "비나텍": "126340.KQ", "엘티씨": "170920.KQ",
        "도쿄일렉트론": "8035.T", "야마이치": "6941.T",
    },
    "GLOBAL_INDEX": {
        "S&P500": "^GSPC", "나스닥100": "^NDX", "필라델피아반도체": "^SOX", "러셀2000": "^RUT",
        "코스피": "^KS11", "코스닥": "^KQ11", "한국ETF(EWY)": "EWY", "닛케이": "^N225", "대만가권": "^TWII",
    },
    "SENTIMENT_TICKERS": {
        "VIX": "^VIX", "VIX9D": "^VIX9D", "VIX3M": "^VIX3M", "VVIX": "^VVIX", "SKEW": "^SKEW",
        "MOVE": "^MOVE", "HYG": "HYG", "IEF": "IEF", "미10년물": "^TNX", "달러인덱스": "DX-Y.NYB",
        "원달러": "KRW=X", "금": "GC=F", "비트코인": "BTC-USD",
    },
    "EVENT_DROP": -0.08,            # SOX 하루 낙폭 기준 (-8%)

    # ── [v3] pykrx 실패 시 야후로 받을 국내 섹터 ETF ──────
    "KR_SECTOR_ETF": {
        "KODEX 200": "069500.KS", "KODEX 반도체": "091160.KS", "TIGER 반도체": "091230.KS",
        "SOL 반도체소부장": "455850.KS", "KODEX 시스템반도체": "395160.KS", "TIGER 200 IT": "139260.KS",
        "KODEX 은행": "091170.KS", "KODEX 증권": "102970.KS", "KODEX 보험": "140700.KS", "TIGER 200 금융": "139270.KS",
        "KODEX 자동차": "091180.KS", "KODEX 건설": "117700.KS", "KODEX 철강": "117680.KS",
        "KODEX 에너지화학": "117460.KS", "KODEX 운송": "140710.KS", "TIGER 200 중공업": "139230.KS",
        "KODEX 조선": "102960.KS", "SOL 조선TOP3플러스": "466920.KS", "방산(K-Defense)": "449450.KS",
        "KODEX 바이오": "244580.KS", "TIGER 헬스케어": "143860.KS", "KODEX 2차전지산업": "305720.KS",
        "TIGER 화장품": "228790.KS", "KODEX 필수소비재": "266410.KS", "KODEX 경기소비재": "266390.KS",
        "KODEX IT소프트웨어": "266360.KS", "TIGER 인터넷TOP10": "365000.KS", "TIGER K게임": "300610.KS",
        "KODEX K로봇액티브": "445290.KS", "HANARO 원자력": "434730.KS", "TIGER 원자력": "0091P0.KS",
        "태양광ESS": "457990.KS", "KODEX 코스닥150": "229200.KS",
    },

    # ── 신용융자잔고 (선택) ──────────────────────────────
    #   자동 수집이 안 되는 항목입니다.
    #   금융투자협회(freesis.kofia.or.kr)에서 받아 엑셀에 넣으면 함께 분석됩니다.
    #   컬럼명을 "신용잔고_코스피", "신용잔고_코스닥" 으로 하세요.
    "USE_CREDIT_BALANCE": True,

    # ── 출력 ─────────────────────────────────────────────
    "OUT_XLSX": "시장지표_결과.xlsx",
    "MAKE_CHARTS": True,
    "GAP_CHART_COUNT": 5,
    "CHART_MONTHS": 18,
    "RANK_TABLE_DAYS": 12,
}
# ─────────────────────────────────────────────────────────────────────


import os
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec
from matplotlib import font_manager

try:
    from IPython.display import display
    IN_NOTEBOOK = True
except Exception:
    IN_NOTEBOOK = False
    display = print


# =====================================================================
#  0. 한글 폰트
# =====================================================================
def setup_korean_font():
    for p in ["/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
              "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
              "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
              "/home/claude/work/NotoKR-Regular.ttf"]:
        if os.path.exists(p):
            try:
                font_manager.fontManager.addfont(p)
                nm = font_manager.FontProperties(fname=p).get_name()
                plt.rcParams["font.family"] = nm
                plt.rcParams["axes.unicode_minus"] = False
                print(f"[폰트] {nm} 적용")
                return nm
            except Exception:
                continue
    plt.rcParams["axes.unicode_minus"] = False
    print("[폰트] 한글 폰트 미발견 → [1단계] 설치 후 런타임 다시 시작하세요")
    return None


# =====================================================================
#  1. 데이터 수집
# =====================================================================
def load_data_auto(cfg):
    if cfg.get("KRX_ID") and cfg.get("KRX_PW"):
        os.environ["KRX_ID"], os.environ["KRX_PW"] = cfg["KRX_ID"], cfg["KRX_PW"]
    elif not os.environ.get("KRX_ID"):
        raise RuntimeError("KRX 계정 미입력 → 야후로 대체")
    from pykrx import stock
    s = cfg["START_DATE"].replace("-", "")
    e = (cfg["END_DATE"] or pd.Timestamp.today().strftime("%Y-%m-%d")).replace("-", "")
    print(f"[수집] {s} ~ {e}")

    idx = {}
    for nm, code in [("코스피", "1001"), ("코스닥", "2001")]:
        try:
            d = stock.get_index_ohlcv_by_date(s, e, code)
            idx[nm] = d["종가"]
            print(f"  · {nm} {len(d)}일")
        except Exception as ex:
            print(f"  · {nm} 실패 ({type(ex).__name__})")
    if not idx:
        raise RuntimeError("지수 수집 실패")
    idx_df = pd.DataFrame(idx)
    last = idx_df.index[-1].strftime("%Y%m%d")

    # ── 수급 · 밸류 (실패해도 진행) ──
    extra = {}
    try:
        fl = stock.get_market_trading_value_by_date(s, e, "KOSPI")
        for c in ["외국인합계", "기관합계", "개인"]:
            if c in fl.columns:
                extra[f"수급_{c}"] = fl[c] / 1e8      # 억원
        print(f"  · 투자자 수급 {len(fl)}일")
    except Exception as ex:
        print(f"  · 투자자 수급 생략 ({type(ex).__name__})")

    try:
        fd = stock.get_index_fundamental_by_date(s, e, "1001")
        for c in ["PER", "PBR"]:
            if c in fd.columns:
                extra[f"코스피_{c}"] = fd[c]
        print(f"  · 지수 PER/PBR {len(fd)}일")
    except Exception as ex:
        print(f"  · PER/PBR 생략 ({type(ex).__name__})")

    extra_df = pd.DataFrame(extra) if extra else pd.DataFrame(index=idx_df.index)

    # ── ETF ──
    tickers = stock.get_etf_ticker_list(last)
    print(f"  · 전체 ETF {len(tickers)}종목")
    order = list(tickers)
    try:
        snap = stock.get_etf_ohlcv_by_ticker(last)
        col = "거래대금" if "거래대금" in snap.columns else snap.columns[-1]
        order = snap.sort_values(col, ascending=False).index.tolist()
        order += [t for t in tickers if t not in order]
    except Exception:
        pass

    want = cfg["ETF_TOP_N"]
    scan = order if cfg["ETF_SELECT"] == "keyword" else order[:max(want * 3, 130)]
    picked = []
    for t in scan:
        try:
            nm = stock.get_etf_ticker_name(t)
        except Exception:
            continue
        if any(w in nm for w in cfg["EXCLUDE_WORDS"]):
            continue
        if cfg["ETF_SELECT"] == "keyword" and not any(k in nm for k in cfg["ETF_KEYWORDS"]):
            continue
        picked.append((t, nm))
        if cfg["ETF_SELECT"] != "keyword" and len(picked) >= want:
            break
    print(f"  · 선정 {len(picked)}종목")

    series = {}
    for i, (t, nm) in enumerate(picked, 1):
        try:
            d = stock.get_etf_ohlcv_by_date(s, e, t)
            if len(d) < 130:
                continue
            key = nm if nm not in series else f"{nm}({t})"
            series[key] = d["종가"]
        except Exception:
            continue
        if i % 15 == 0:
            print(f"    ...{i}/{len(picked)}")
    if not series:
        raise RuntimeError("ETF 시세 수집 실패")

    etf_df = pd.DataFrame(series)
    print(f"[수집] 완료 — ETF {etf_df.shape[1]}종목 / {etf_df.shape[0]}일")
    return idx_df, etf_df, extra_df


def load_data_excel(cfg):
    try:
        from google.colab import files
        import io
        up = files.upload()
        fn = list(up.keys())[0]
        raw = pd.read_excel(io.BytesIO(up[fn]), sheet_name=0)
    except ImportError:
        raw = pd.read_excel(input("엑셀 경로: ").strip(), sheet_name=0)

    dc = raw.columns[0]
    raw = raw.dropna(subset=[dc])
    raw[dc] = pd.to_datetime(raw[dc])
    raw = raw.set_index(dc).sort_index().apply(pd.to_numeric, errors="coerce")

    icol = [c for c in raw.columns if str(c).strip() in ("코스피", "코스닥", "KOSPI", "KOSDAQ")]
    if not icol:
        raise RuntimeError("'코스피' 컬럼을 찾을 수 없습니다")
    idx_df = raw[icol].rename(columns={"KOSPI": "코스피", "KOSDAQ": "코스닥"})

    ecol = [c for c in raw.columns
            if str(c).startswith(("신용잔고", "수급_", "코스피_P")) or c in icol]
    extra_df = raw[[c for c in ecol if c not in icol]]
    etf_df = raw.drop(columns=ecol)
    print(f"[엑셀] 지수 {idx_df.shape[1]} / ETF {etf_df.shape[1]} / 보조 {extra_df.shape[1]} / {len(raw)}일")
    return idx_df, etf_df, extra_df


def load_data_demo(cfg):
    print("[데모] 가상 데이터입니다. 실제 시장 데이터가 아닙니다.")
    rs = np.random.RandomState(42)
    dates = pd.bdate_range(cfg["START_DATE"],
                           cfg["END_DATE"] or pd.Timestamp.today().strftime("%Y-%m-%d"))
    n = len(dates)

    def gbm(st, mu, sg, sd):
        r = np.random.RandomState(sd).normal(mu / 252, sg / np.sqrt(252), n)
        return st * np.exp(np.cumsum(r))

    kospi = gbm(4200, .60, .22, 1); kospi[int(n * .87):] *= np.linspace(1, .74, n - int(n * .87))
    kosdaq = gbm(800, .40, .28, 2); kosdaq[int(n * .84):] *= np.linspace(1, .64, n - int(n * .84))
    names = ["반도체", "반도체소부장", "코스닥150", "은행", "증권", "자동차", "방산", "조선",
             "화장품", "2차전지", "바이오", "로봇", "태양광", "전력기기", "건설", "보험",
             "인터넷", "게임", "철강", "운송", "원자력", "미디어"]
    etf = {nm: gbm(10000, rs.uniform(-.2, .8), rs.uniform(.2, .45), 100 + i)
           for i, nm in enumerate(names)}

    idx_df = pd.DataFrame({"코스피": kospi, "코스닥": kosdaq}, index=dates)
    etf_df = pd.DataFrame(etf, index=dates)
    cred = pd.Series(np.linspace(11e4, 7e4, n) * (1 + rs.normal(0, .01, n)), index=dates)
    extra_df = pd.DataFrame({
        "신용잔고_코스피": cred * 1.4,
        "신용잔고_코스닥": cred,
        "수급_외국인합계": rs.normal(0, 3000, n).cumsum() / 20,
        "코스피_PER": 11 + rs.normal(0, .4, n).cumsum() / 40,
        "코스피_PBR": 1.05 + rs.normal(0, .02, n).cumsum() / 60,
    }, index=dates)
    return idx_df, etf_df, extra_df


# =====================================================================
#  2. 지표 계산
# =====================================================================
def _mm(s, w):
    lo = s.rolling(w, min_periods=w // 2).min()
    hi = s.rolling(w, min_periods=w // 2).max()
    return ((s - lo) / (hi - lo).replace(0, np.nan) * 100).clip(0, 100)


def calc_rsi(p, n=14):
    d = p.diff()
    g = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    l = (-d).clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    return (100 - 100 / (1 + g / l.replace(0, np.nan))).fillna(50)


def calc_mdd(p, window=None):
    peak = p.rolling(window, min_periods=1).max() if window else p.cummax()
    return (p / peak - 1) * 100


def calc_macd(p, f=12, s=26, sg=9):
    m = p.ewm(span=f, adjust=False).mean() - p.ewm(span=s, adjust=False).mean()
    g = m.ewm(span=sg, adjust=False).mean()
    return m, g, m - g


def calc_bollinger(p, n=20, k=2):
    ma = p.rolling(n).mean(); sd = p.rolling(n).std()
    up, lo = ma + k * sd, ma - k * sd
    return (p - lo) / (up - lo).replace(0, np.nan) * 100, (up - lo) / ma * 100


def calc_psychology(p, n=10):
    return (p.diff() > 0).astype(float).rolling(n).mean() * 100


def calc_adr(df, n=20):
    r = df.pct_change()
    return ((r > 0).sum(axis=1) / (r < 0).sum(axis=1).replace(0, np.nan) * 100).rolling(n).mean()


def calc_concentration(df, n=20):
    ret = df.pct_change(n); pos = ret.clip(lower=0)
    tot = pos.sum(axis=1).replace(0, np.nan)
    hhi = (pos.div(tot, axis=0) ** 2).sum(axis=1)
    k = df.notna().sum(axis=1)
    return ((hhi - 1 / k) / (1 - 1 / k) * 100).clip(0, 100)


def calc_new_high_low(df, n=252):
    hi = df.rolling(n, min_periods=n // 2).max()
    lo = df.rolling(n, min_periods=n // 2).min()
    v = df.notna().sum(axis=1).replace(0, np.nan)
    return (df >= hi * .999).sum(axis=1) / v * 100, (df <= lo * 1.001).sum(axis=1) / v * 100


def calc_breadth(df, cfg=SETTINGS):
    res = pd.DataFrame(index=df.index)
    for n in cfg["BREADTH_MAS"]:
        ma = df.rolling(n, min_periods=max(2, n // 2)).mean()
        v = df.notna() & ma.notna()
        res[f"MA{n}_상회비율"] = (df > ma).where(v).sum(axis=1) / v.sum(axis=1).replace(0, np.nan) * 100
    res["ADR"] = calc_adr(df, cfg["ADR_N"])
    nh, nl = calc_new_high_low(df)
    res["신고가비율"] = nh; res["신저가비율"] = nl
    res["업종쏠림지수"] = calc_concentration(df, cfg["CONC_N"])
    res["집계종목수"] = df.notna().sum(axis=1)
    return res


def calc_market_indicators(price, cfg=SETTINGS):
    """지수 하나에 대한 종합 기술지표"""
    p = price.dropna().astype(float)
    o = pd.DataFrame(index=p.index)
    o["종가"] = p
    o["일간수익률"] = p.pct_change() * 100
    o["MDD_전체"] = calc_mdd(p)
    o["MDD_1년"] = calc_mdd(p, 252)
    o["RSI"] = calc_rsi(p, cfg["RSI_N"])
    f, s, sg = cfg["MACD"]
    o["MACD"], o["MACD_Signal"], o["MACD_Hist"] = calc_macd(p, f, s, sg)
    o["볼린저%B"], o["볼린저밴드폭"] = calc_bollinger(p, cfg["BB_N"])
    o["투자심리도"] = calc_psychology(p, cfg["PSY_N"])
    o[f"MA{cfg['MA_SHORT']}"] = p.rolling(cfg["MA_SHORT"]).mean()
    o[f"MA{cfg['MA_LONG']}"] = p.rolling(cfg["MA_LONG"]).mean()
    o["이평배열"] = np.where(o[f"MA{cfg['MA_SHORT']}"] > o[f"MA{cfg['MA_LONG']}"], "정배열", "역배열")
    o["변동성_연율"] = p.pct_change().rolling(20).std() * np.sqrt(252) * 100
    o["이격도_20일"] = p / p.rolling(20).mean() * 100
    o["이격도_60일"] = p / p.rolling(60).mean() * 100
    return o


def calc_fear_greed(price, breadth=None, cfg=SETTINGS):
    p = price.dropna().astype(float)
    o = pd.DataFrame(index=p.index)
    o["c_모멘텀"] = _mm(p / p.rolling(125, min_periods=60).mean() * 100, 252)
    o["c_RSI"] = calc_rsi(p, 14)
    o["c_변동성"] = 100 - _mm(p.pct_change().rolling(20, min_periods=10).std(), 252)
    lo = p.rolling(252, min_periods=120).min(); hi = p.rolling(252, min_periods=120).max()
    o["c_52주위치"] = ((p - lo) / (hi - lo).replace(0, np.nan) * 100).clip(0, 100)
    if breadth is not None:
        o["c_브레스"] = breadth.reindex(o.index).ffill().clip(0, 100)
    cc = [c for c in o.columns if c.startswith("c_")]
    o["FearGreed"] = o[cc].mean(axis=1)
    o["FG_EMA"] = o["FearGreed"].ewm(span=cfg["FG_EMA"], adjust=False).mean()
    ef = o["FearGreed"].ewm(span=5, adjust=False).mean()
    es = o["FearGreed"].ewm(span=cfg["FG_EMA"], adjust=False).mean()
    o["FG_Oscillator"] = (ef - es) / 100.0
    o["지수"] = p
    return o


def calc_mansfield_rs(df, bm, ma=52):
    b = bm.reindex(df.index).ffill()
    rel = df.div(b, axis=0)
    return (rel / rel.rolling(ma, min_periods=ma // 2).mean() - 1) * 100


def calc_sortino(df, cfg=SETTINGS):
    r = df.pct_change(); n = cfg["SORTINO_N"]
    mu = r.rolling(n, min_periods=n // 2).mean()
    dd = r.where(r < 0).rolling(n, min_periods=max(3, n // 4)).std()
    return mu / dd.replace(0, np.nan) * np.sqrt(252)


def sortino_ranking(sortino, price=None, above_ma=True, extra_ma=None, cfg=SETTINGS):
    sma = sortino.rolling(cfg["SORTINO_MA"], min_periods=cfg["SORTINO_MA"] // 2).mean()
    cand = sortino.where(sortino >= sma) if above_ma else sortino.copy()
    if extra_ma and price is not None:
        pma = price.rolling(extra_ma, min_periods=max(2, extra_ma // 2)).mean()
        cand = cand.where(price >= pma)
    tn = cfg["SORTINO_TOPN"]; rows = {}
    for dt, r in cand.iterrows():
        nm = r.dropna().sort_values(ascending=False).head(tn).index.tolist()
        rows[dt] = nm + [None] * (tn - len(nm))
    return pd.DataFrame.from_dict(rows, orient="index",
                                 columns=[f"Top{i}" for i in range(1, tn + 1)])


def make_gap_summary(price_df, sectors, cfg=SETTINGS):
    gma, look, q = cfg["GAP_MA_DAYS"], cfg["LOOKBACK_DAYS"], cfg["GAP_QUANTILE"]
    qp = int(q * 100); rows = []
    for rank, sec in enumerate(sectors, 1):
        if sec is None or sec not in price_df.columns:
            continue
        p = price_df[sec].dropna()
        if len(p) < gma + 5:
            continue
        ma = p.rolling(gma).mean(); gap = (p / ma * 100).dropna()
        if gap.empty:
            continue
        cur = float(gap.iloc[-1]) - 100
        qx = float(gap.tail(look).quantile(q)) - 100
        rows.append({
            "순위": rank, "섹터": sec,
            "종가": round(float(p.loc[gap.index[-1]]), 1),
            f"MA{gma}": round(float(ma.loc[gap.index[-1]]), 1),
            "현재초과이격도": round(cur, 2),
            f"{qp}분위초과이격도": round(qx, 2),
            "과열도(%)": round(cur / qx * 100, 1) if qx else np.nan,
            "기준일": gap.index[-1].strftime("%Y-%m-%d"),
            "_price": p, "_ma": ma, "_gap": gap,
        })
    return pd.DataFrame(rows)


# =====================================================================
#  3. 대시보드
# =====================================================================
def _judge(v, lo, hi, labels=("낮음", "보통", "높음")):
    if pd.isna(v): return "-"
    return labels[0] if v < lo else (labels[2] if v > hi else labels[1])


def build_dashboard(idx_df, mkt, fg, breadth, extra_df, cfg=SETTINGS):
    rows = []
    for m in idx_df.columns:
        k = mkt[m].iloc[-1]; f = fg[m].iloc[-1]
        rows.append({
            "시장": m,
            "종가": f"{k['종가']:,.1f}",
            "전일대비": f"{k['일간수익률']:+.2f}%",
            "고점대비(MDD)": f"{k['MDD_1년']:.1f}%",
            "Fear&Greed": f"{f['FearGreed']:.1f}",
            "F&G상태": ("극단적공포" if f["FearGreed"] < 25 else "공포" if f["FearGreed"] < 45
                      else "중립" if f["FearGreed"] < 55 else "탐욕" if f["FearGreed"] < 75 else "극단적탐욕"),
            "F&G방향": "개선" if f["FearGreed"] >= f["FG_EMA"] else "악화",
            "RSI": f"{k['RSI']:.1f}",
            "RSI판정": _judge(k["RSI"], 30, 70, ("과매도", "중립", "과매수")),
            "MACD": "상승" if k["MACD_Hist"] > 0 else "하락",
            "볼린저%B": f"{k['볼린저%B']:.0f}",
            "이평배열": k["이평배열"],
            "투자심리도": f"{k['투자심리도']:.0f}%",
            "변동성": f"{k['변동성_연율']:.1f}%",
        })
    dash = pd.DataFrame(rows).set_index("시장")

    b = breadth.iloc[-1]
    mkt_rows = {
        "10일선 상회율": f"{b['MA10_상회비율']:.0f}%",
        "20일선 상회율": f"{b['MA20_상회비율']:.0f}%",
        "60일선 상회율": f"{b['MA60_상회비율']:.0f}%",
        "120일선 상회율": f"{b['MA120_상회비율']:.0f}%",
        "ADR 등락비율": f"{b['ADR']:.0f}",
        "52주 신고가비율": f"{b['신고가비율']:.0f}%",
        "52주 신저가비율": f"{b['신저가비율']:.0f}%",
        "업종 쏠림지수": f"{b['업종쏠림지수']:.0f}",
        "집계 종목수": f"{int(b['집계종목수'])}개",
    }
    if extra_df is not None and len(extra_df.columns):
        e = extra_df.ffill().iloc[-1]
        for c in extra_df.columns:
            if pd.isna(e[c]):
                continue
            if "신용잔고" in c:
                s = extra_df[c].dropna()
                mdd_c = (s.iloc[-1] / s.cummax().iloc[-1] - 1) * 100
                mkt_rows[f"{c}"] = f"{e[c]:,.0f}억  (고점대비 {mdd_c:.0f}%)"
            elif "PER" in c or "PBR" in c:
                mkt_rows[c] = f"{e[c]:.2f}"
            elif "수급" in c:
                mkt_rows[c] = f"{e[c]:,.0f}억"
    breadth_tbl = pd.DataFrame.from_dict(mkt_rows, orient="index", columns=["값"])
    return dash, breadth_tbl


# =====================================================================
#  4. 차트
# =====================================================================
def chart_fear_greed(fg, market, path, months=18, cfg=SETTINGS):
    d = fg.tail(months * 21)
    fig, ax1 = plt.subplots(figsize=(14, 7))
    ax1.plot(d.index, d["FearGreed"], color="#1f6fd0", lw=2, label="Fear & Greed")
    ax1.plot(d.index, d["FG_EMA"], color="#e88a1a", lw=1.8, label=f"EMA{cfg['FG_EMA']}")
    ax1.axhline(50, color="#88c", ls=":", lw=1.2)
    ax1.axhspan(0, 25, color="#c0392b", alpha=.06); ax1.axhspan(75, 100, color="#2e9b57", alpha=.06)
    ax1.set_ylim(0, 100); ax1.set_ylabel("Fear & Greed", color="#1f6fd0")
    ax1.tick_params(axis="y", labelcolor="#1f6fd0"); ax1.grid(alpha=.25)
    ax2 = ax1.twinx()
    ax2.plot(d.index, d["지수"], color="#999", lw=1.3, label="지수")
    ax2.set_ylabel("지수", color="#666"); ax2.tick_params(axis="y", labelcolor="#666")
    ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    ax3 = ax1.twinx(); ax3.spines["right"].set_position(("outward", 58))
    ax3.plot(d.index, d["FG_Oscillator"], color="#6a3fc0", lw=1.6, label="Oscillator")
    ax3.axhline(0, color="#6a3fc0", lw=.6, alpha=.35)
    ax3.set_ylabel("Oscillator", color="#6a3fc0"); ax3.tick_params(axis="y", labelcolor="#6a3fc0")
    L = d.iloc[-1]
    fig.suptitle(f"{market} — Fear & Greed + EMA + Oscillator\n"
                 f"F&G {L['FearGreed']:.1f} | EMA {L['FG_EMA']:.1f} | Osc {L['FG_Oscillator']:.4f}"
                 f"   ({d.index[-1]:%Y-%m-%d})", fontsize=13, fontweight="bold", y=.97)
    h = sum([a.get_legend_handles_labels()[0] for a in (ax1, ax3, ax2)], [])
    l = sum([a.get_legend_handles_labels()[1] for a in (ax1, ax3, ax2)], [])
    ax1.legend(h, l, loc="upper left", fontsize=9)
    plt.tight_layout(rect=[0, 0, 1, .93]); plt.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig); return path


def chart_market_panel(mkt, market, path, months=18):
    """지수 + MDD + RSI + MACD 4단 패널"""
    d = mkt.tail(months * 21)
    fig = plt.figure(figsize=(14, 11))
    gs = gridspec.GridSpec(4, 1, height_ratios=[3, 1.5, 1.5, 1.5], hspace=.28)

    a0 = fig.add_subplot(gs[0])
    a0.plot(d.index, d["종가"], color="#1f6fd0", lw=1.7, label="종가")
    for c, col in [(c, cc) for c, cc in zip([x for x in d.columns if x.startswith("MA")],
                                            ["#e88a1a", "#2e9b57"])]:
        a0.plot(d.index, d[c], lw=1.3, ls="--", color=col, label=c)
    a0.set_ylabel("지수"); a0.grid(alpha=.25); a0.legend(fontsize=9, loc="upper left")
    a0.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    L = d.iloc[-1]
    a0.set_title(f"{market} 종합 패널   종가 {L['종가']:,.1f} ({L['일간수익률']:+.2f}%)  |  "
                 f"MDD {L['MDD_1년']:.1f}%  |  {L['이평배열']}   ({d.index[-1]:%Y-%m-%d})",
                 fontsize=13, fontweight="bold")

    a1 = fig.add_subplot(gs[1], sharex=a0)
    a1.fill_between(d.index, d["MDD_1년"], 0, color="#c0392b", alpha=.3)
    a1.plot(d.index, d["MDD_1년"], color="#c0392b", lw=1.2)
    a1.set_ylabel("MDD (%)"); a1.grid(alpha=.25)
    a1.axhline(-20, color="#888", ls=":", lw=1)

    a2 = fig.add_subplot(gs[2], sharex=a0)
    a2.plot(d.index, d["RSI"], color="#6a3fc0", lw=1.4)
    a2.axhline(70, color="#c0392b", ls="--", lw=1); a2.axhline(30, color="#2e9b57", ls="--", lw=1)
    a2.axhspan(70, 100, color="#c0392b", alpha=.06); a2.axhspan(0, 30, color="#2e9b57", alpha=.06)
    a2.set_ylim(0, 100); a2.set_ylabel("RSI"); a2.grid(alpha=.25)

    a3 = fig.add_subplot(gs[3], sharex=a0)
    colors = ["#2e9b57" if v >= 0 else "#c0392b" for v in d["MACD_Hist"]]
    a3.bar(d.index, d["MACD_Hist"], color=colors, alpha=.5, width=1.0)
    a3.plot(d.index, d["MACD"], color="#1f6fd0", lw=1.3, label="MACD")
    a3.plot(d.index, d["MACD_Signal"], color="#e88a1a", lw=1.2, label="Signal")
    a3.axhline(0, color="#666", lw=.8); a3.set_ylabel("MACD"); a3.grid(alpha=.25)
    a3.legend(fontsize=8, loc="upper left")

    plt.savefig(path, dpi=110, bbox_inches="tight"); plt.close(fig); return path


def chart_breadth(br, path, months=18):
    d = br.tail(months * 21)
    cols = [c for c in d.columns if "상회비율" in c]
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(14, 9), height_ratios=[2, 1], sharex=True)
    pal = ["#1f6fd0", "#e88a1a", "#2e9b57", "#c0392b"]
    for i, c in enumerate(cols):
        ax.plot(d.index, d[c], lw=1.8, label=c.replace("_상회비율", ""), color=pal[i % 4])
    ax.axhline(50, color="#888", ls=":", lw=1.2)
    ax.axhspan(0, 20, color="#c0392b", alpha=.07); ax.axhspan(80, 100, color="#2e9b57", alpha=.07)
    ax.set_ylim(0, 100); ax.set_ylabel("이평선 상회 비율 (%)"); ax.grid(alpha=.25)
    L = d.iloc[-1]
    ax.set_title("시장 폭(Breadth) 지표\n" + "   ".join(
        [f"{c.replace('_상회비율','')} {L[c]:.0f}%" for c in cols]) +
        f"   |  ADR {L['ADR']:.0f}  |  쏠림 {L['업종쏠림지수']:.0f}   ({d.index[-1]:%Y-%m-%d})",
        fontsize=13, fontweight="bold")
    ax.legend(loc="upper right", fontsize=9, ncol=2)

    ax2.plot(d.index, d["업종쏠림지수"], color="#8e44ad", lw=1.6, label="업종 쏠림지수")
    ax2.plot(d.index, d["신고가비율"], color="#2e9b57", lw=1.2, label="52주 신고가 비율")
    ax2.plot(d.index, d["신저가비율"], color="#c0392b", lw=1.2, label="52주 신저가 비율")
    ax2.set_ylabel("%"); ax2.grid(alpha=.25); ax2.legend(fontsize=9, ncol=3)
    plt.tight_layout(); plt.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig); return path


def chart_gap(row, path, months=14, cfg=SETTINGS):
    p = row["_price"].tail(months * 21)
    ma = row["_ma"].reindex(p.index); gap = row["_gap"].reindex(p.index)
    qcol = [c for c in row.index if "분위초과이격도" in str(c)][0]
    fig, ax1 = plt.subplots(figsize=(13, 6))
    ax1.bar(gap.index, gap.values, width=1.0, color="#c0392b", alpha=.16, label="이격도", zorder=0)
    ax1.axhline(100, color="#c0392b", ls="--", lw=1, alpha=.7)
    ax1.axhline(100 + row[qcol], color="#8e44ad", ls="-.", lw=1.3,
                label=f"{cfg['LOOKBACK_DAYS']}일 {int(cfg['GAP_QUANTILE']*100)}분위")
    ax1.set_ylim(min(gap.min(), 97) - 2, max(gap.max(), 100 + row[qcol]) + 3)
    ax1.set_ylabel("이격도 (%)"); ax1.grid(alpha=.22, zorder=0)
    ax2 = ax1.twinx()
    ax2.plot(p.index, p.values, color="#1f6fd0", lw=1.7, label="종가", zorder=3)
    ax2.plot(ma.index, ma.values, color="#e88a1a", lw=1.4, ls="--",
             label=f"MA{cfg['GAP_MA_DAYS']}", zorder=3)
    ax2.set_ylabel("가격"); ax2.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    ax1.set_title(f"[{row['섹터']}]  Sortino #{row['순위']}   "
                  f"현재 초과이격도 {row['현재초과이격도']:+.1f}  |  "
                  f"분위 초과 {row[qcol]:.1f}  |  과열도 {row['과열도(%)']:.0f}%",
                  fontsize=12.5, fontweight="bold")
    h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h2 + h1, l2 + l1, loc="upper center", bbox_to_anchor=(.5, -.09),
               ncol=4, frameon=False, fontsize=9)
    plt.tight_layout(); plt.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig); return path


def chart_credit(extra_df, idx_df, path, months=18):
    cols = [c for c in extra_df.columns if "신용잔고" in c]
    if not cols:
        return None
    d = extra_df[cols].tail(months * 21)
    fig, ax = plt.subplots(figsize=(14, 6))
    pal = ["#1f6fd0", "#c0392b"]
    for i, c in enumerate(cols):
        s = d[c].dropna()
        ax.plot(s.index, s.values, lw=1.8, color=pal[i % 2], label=c)
    ax.set_ylabel("신용융자 잔고 (억원)"); ax.grid(alpha=.25)
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    ax2 = ax.twinx()
    m0 = idx_df.columns[0]
    ax2.plot(idx_df[m0].tail(months * 21).index, idx_df[m0].tail(months * 21).values,
             color="#999", lw=1.2, label=m0)
    ax2.set_ylabel(m0, color="#666"); ax2.tick_params(axis="y", labelcolor="#666")
    txt = "  |  ".join([f"{c} {d[c].dropna().iloc[-1]:,.0f}억 "
                       f"(고점대비 {(d[c].dropna().iloc[-1]/extra_df[c].cummax().iloc[-1]-1)*100:.0f}%)"
                       for c in cols])
    ax.set_title(f"신용융자 잔고 추이\n{txt}", fontsize=13, fontweight="bold")
    h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=9, loc="upper right")
    plt.tight_layout(); plt.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig); return path


# =====================================================================
#  5. 메인
# =====================================================================
# =====================================================================
#  [v3 신규] 6. 야후 파이낸스 수집기 (pykrx 실패 시 대체 + 글로벌 지표)
# =====================================================================
import json as _json
import time as _time
import urllib.request as _ur

def yahoo_close(ticker, start="2015-01-01", end=None, tries=3):
    """야후 차트 API에서 일별 종가(Series)를 가져온다. 실패하면 None."""
    p1 = int(pd.Timestamp(start).timestamp())
    p2 = int((pd.Timestamp(end) if end else pd.Timestamp.today() + pd.Timedelta(days=1)).timestamp())
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
           f"?period1={p1}&period2={p2}&interval=1d")
    for k in range(tries):
        try:
            req = _ur.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            j = _json.loads(_ur.urlopen(req, timeout=20).read())["chart"]["result"][0]
            c = j["indicators"]["quote"][0]["close"]
            idx = pd.to_datetime(j["timestamp"], unit="s").normalize()
            s = pd.Series(c, index=idx, name=ticker, dtype="float64").dropna()
            s = s[~s.index.duplicated(keep="last")]
            # 지수 마지막 봉이 비어 있으면(야후 지연) 현재가로 보충
            m = j.get("meta", {})
            if m.get("regularMarketPrice") and m.get("regularMarketTime"):
                d = pd.to_datetime(m["regularMarketTime"], unit="s").normalize()
                if len(s) and d > s.index[-1] and not end:
                    s.loc[d] = float(m["regularMarketPrice"])
            return s
        except Exception:
            _time.sleep(1 + k)
    return None


def load_data_yahoo(cfg):
    """pykrx(KRX)가 막혔을 때: 코스피·코스닥 지수와 섹터 ETF를 야후에서 받는다.
       수급·PER은 야후에 없어서 이 경로에서는 생략된다."""
    print("[수집-야후] pykrx 대신 야후 파이낸스로 받습니다")
    s = cfg["START_DATE"]
    idx = {}
    for nm, t in [("코스피", "^KS11"), ("코스닥", "^KQ11")]:
        x = yahoo_close(t, s, cfg["END_DATE"])
        if x is not None and len(x):
            idx[nm] = x; print(f"  · {nm} {len(x)}일")
    if not idx:
        raise RuntimeError("야후 지수 수집 실패")
    idx_df = pd.DataFrame(idx).ffill()
    series = {}
    for nm, t in cfg["KR_SECTOR_ETF"].items():
        x = yahoo_close(t, s, cfg["END_DATE"])
        if x is not None and len(x) >= 130:
            series[nm] = x
    if not series:
        raise RuntimeError("야후 ETF 수집 실패")
    etf_df = pd.DataFrame(series).reindex(idx_df.index).ffill()
    print(f"  · 섹터 ETF {etf_df.shape[1]}종목")
    return idx_df, etf_df, pd.DataFrame(index=idx_df.index)


# =====================================================================
#  [v3 신규] 7. 글로벌 심리·과매도 패널
# =====================================================================
def _rsi_last(p, n=14):
    d = p.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


def tech_row(p, n=14):
    """종가 시리즈 → 기술지표 한 줄"""
    p = p.dropna()
    r = _rsi_last(p, n)
    y = p.iloc[-252:]
    pct = lambda k: (p.iloc[-1] / p.iloc[-1 - k] - 1) * 100 if len(p) > k else np.nan
    m50 = p.rolling(50).mean().iloc[-1]
    m200 = p.rolling(200).mean().iloc[-1] if len(p) >= 200 else np.nan
    rv = r.iloc[-1]
    return {
        "기준일": p.index[-1].strftime("%m-%d"),
        "종가": round(p.iloc[-1], 2),
        "1일%": round(pct(1), 1), "5일%": round(pct(5), 1), "1개월%": round(pct(21), 1),
        "RSI14": round(rv, 1),
        "5일전RSI": round(r.iloc[-6], 1) if len(r) > 6 else np.nan,
        "1년최저RSI": round(r.iloc[-252:].min(), 1),
        "50일선%": round((p.iloc[-1] / m50 - 1) * 100, 1),
        "200일선%": round((p.iloc[-1] / m200 - 1) * 100, 1) if m200 == m200 else np.nan,
        "52주고점%": round((p.iloc[-1] / y.max() - 1) * 100, 1),
        "판정": ("극단과매도" if rv < 20 else "과매도" if rv < 30 else "근접" if rv < 35
                 else "과매수" if rv > 70 else "중립"),
    }


def global_panel(cfg):
    print("\n[글로벌] 지수·관심종목·심리 지표 수집")
    start = (pd.Timestamp.today() - pd.Timedelta(days=500)).strftime("%Y-%m-%d")
    data, rows = {}, []
    groups = [("지수", cfg["GLOBAL_INDEX"]), ("관심종목", cfg["WATCHLIST"])]
    for g, dct in groups:
        for nm, t in dct.items():
            x = yahoo_close(t, start)
            if x is None or len(x) < 60:
                print(f"  · {nm}({t}) 실패"); continue
            data[t] = x
            rows.append({"구분": g, "이름": nm, "티커": t, **tech_row(x, cfg["RSI_N"])})
    tech = pd.DataFrame(rows)

    # ── 심리·위험 지표 ──
    sent = {}
    for nm, t in cfg["SENTIMENT_TICKERS"].items():
        x = yahoo_close(t, start)
        if x is not None and len(x):
            sent[nm] = x
    sdf = pd.DataFrame(sent).ffill()
    S = []
    def add(name, val, rule, read):
        S.append({"지표": name, "현재": val, "기준": rule, "해석": read})
    L = sdf.iloc[-1]
    if {"VIX9D", "VIX", "VIX3M"} <= set(sdf.columns):
        r1, r2 = L["VIX9D"] / L["VIX"], L["VIX"] / L["VIX3M"]
        add("VIX", round(L["VIX"], 2), "20↑ 경계 / 30↑ 공포 / 40↑ 패닉",
            "패닉" if L["VIX"] >= 40 else "공포" if L["VIX"] >= 30 else "경계" if L["VIX"] >= 20 else "안정")
        add("VIX9D / VIX", round(r1, 3), ">1 = 단기 패닉(역전)", "역전" if r1 > 1 else "정상")
        add("VIX / VIX3M", round(r2, 3), ">1 = 기간구조 역전(백워데이션)",
            "역전 — 단기 저점 부근에서 자주 출현, 풀릴 때까지 변동성 큼" if r2 > 1 else "정상(콘탱고)")
        sdf["VIX/VIX3M"] = sdf["VIX"] / sdf["VIX3M"]
    if "VVIX" in sdf:
        add("VVIX", round(L["VVIX"], 1), "120↑ 헤지 수요 급증", "급증" if L["VVIX"] >= 120 else "보통")
    if "SKEW" in sdf:
        add("SKEW", round(L["SKEW"], 1), "145↑ 꼬리위험 프리미엄 높음", "높음" if L["SKEW"] >= 145 else "보통")
    if "MOVE" in sdf:
        add("MOVE(채권 변동성)", round(L["MOVE"], 1), "120↑ 금리 발작", "발작" if L["MOVE"] >= 120 else "평온")
    if {"HYG", "IEF"} <= set(sdf.columns):
        ratio = sdf["HYG"] / sdf["IEF"]
        chg = (ratio.iloc[-1] / ratio.iloc[-21] - 1) * 100
        add("HYG/IEF (신용 위험선호)", round(ratio.iloc[-1], 4), "1개월 −3%↓ = 신용 경색 신호",
            f"1개월 {chg:+.1f}% → " + ("경색" if chg <= -3 else "평온"))
        sdf["HYG/IEF"] = ratio
    for k, rule in [("미10년물", "5%↑ 할인율 부담"), ("달러인덱스", "급등 = 위험회피"),
                    ("원달러", "1,400↑ 외국인 이탈 압력"), ("금", "급등 = 안전자산 선호"), ("비트코인", "위험선호 대리")]:
        if k in sdf:
            v = sdf[k].dropna()
            add(k, round(v.iloc[-1], 2), rule, f"1개월 {(v.iloc[-1]/v.iloc[-22]-1)*100:+.1f}%")
    sent_tbl = pd.DataFrame(S)

    # ── CNN Fear & Greed (가능하면 자동) ──
    fg_cnn = None
    try:
        req = _ur.Request("https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
                          headers={"User-Agent": "Mozilla/5.0", "Referer": "https://edition.cnn.com/"})
        j = _json.loads(_ur.urlopen(req, timeout=15).read())
        fg = j["fear_and_greed"]
        fg_cnn = {"점수": round(fg["score"], 1), "등급": fg["rating"],
                  "전일": round(fg.get("previous_close", np.nan), 1),
                  "1주전": round(fg.get("previous_1_week", np.nan), 1),
                  "1달전": round(fg.get("previous_1_month", np.nan), 1)}
        for key, nm in [("put_call_options", "풋콜"), ("junk_bond_demand", "정크본드"),
                        ("safe_haven_demand", "안전자산"), ("market_momentum_sp500", "모멘텀"),
                        ("stock_price_breadth", "브레스"), ("stock_price_strength", "신고가강도"),
                        ("market_volatility_vix", "변동성")]:
            if key in j:
                fg_cnn[nm] = f"{j[key].get('score', 0):.0f} ({j[key].get('rating', '')})"
        print(f"  · CNN Fear&Greed {fg_cnn['점수']} ({fg_cnn['등급']})")
    except Exception:
        print("  · CNN Fear&Greed 자동수집 실패 → 링크로 확인하세요")
    return tech, sent_tbl, sdf, fg_cnn, data


def sox_event_study(cfg):
    """SOX 하루 낙폭이 기준 이하였던 날 이후 수익률 통계"""
    s = yahoo_close("^SOX", "1994-01-01")
    if s is None:
        return None, None
    thr = cfg["EVENT_DROP"]
    r = s.pct_change()
    ev, last = [], -999
    for i in range(1, len(s)):
        if r.iloc[i] <= thr and i - last > 15:
            last = i
            f = lambda k: (s.iloc[i + k] / s.iloc[i] - 1) * 100 if i + k < len(s) else np.nan
            lo = (s.iloc[i:i + 61].min() / s.iloc[i] - 1) * 100 if i + 60 < len(s) else np.nan
            ev.append({"날짜": s.index[i].strftime("%Y-%m-%d"), "당일%": round(r.iloc[i] * 100, 1),
                       "+5일%": f(5), "+20일%": f(20), "+60일%": f(60), "+120일%": f(120),
                       "+250일%": f(250), "60일내추가최대하락%": lo})
    ev = pd.DataFrame(ev).round(1)
    summ = []
    for c in ["+5일%", "+20일%", "+60일%", "+120일%", "+250일%", "60일내추가최대하락%"]:
        v = ev[c].dropna()
        summ.append({"구간": c, "중간값": round(v.median(), 1), "평균": round(v.mean(), 1),
                     "상승확률": f"{(v > 0).sum()}/{len(v)}" if "하락" not in c else f"최악 {v.min():.1f}"})
    return ev, pd.DataFrame(summ)


def link_table():
    L = [
        ("심리", "CNN Fear & Greed", "https://edition.cnn.com/markets/fear-and-greed", "7개 하위지표, 25↓ 극단적 공포"),
        ("심리", "AAII 개인투자자 설문", "https://www.aaii.com/sentimentsurvey", "매주 목 발표, 약세 50%↑ 역발상"),
        ("심리", "NAAIM 운용사 노출지수", "https://naaim.org/programs/naaim-exposure-index/", "매주 수, 기관 주식 노출"),
        ("심리", "CBOE 풋/콜 비율", "https://www.cboe.com/us/options/market_statistics/daily/", "1.0↑ 공포"),
        ("변동성", "VIX 기간구조 (VIX Central)", "http://vixcentral.com/", "선물 곡선, 역전 여부"),
        ("변동성", "CBOE VIX·VIX9D·VIX3M", "https://www.cboe.com/tradable_products/vix/", "현물 VIX 계열"),
        ("변동성", "VKOSPI (인베스팅)", "https://kr.investing.com/indices/kospi-volatility", "한국 공포지수"),
        ("시장폭", "S&P500 50·200일선 상회 비율 ($SPXA200R)", "https://stockcharts.com/h-sc/ui?s=$SPXA200R", "20%↓ 과매도 폭"),
        ("시장폭", "Nasdaq 신고가·신저가", "https://stockcharts.com/h-sc/ui?s=$NAHL", "신저가 급증 = 투매"),
        ("신용", "하이일드 스프레드 (FRED)", "https://fred.stlouisfed.org/series/BAMLH0A0HYM2", "5%↑ 경색"),
        ("신용", "금융스트레스지수 (FRED)", "https://fred.stlouisfed.org/series/STLFSI4", "0↑ 스트레스"),
        ("금리", "미 10년물 (FRED)", "https://fred.stlouisfed.org/series/DGS10", ""),
        ("금리", "FedWatch (CME)", "https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html", "금리 확률"),
        ("한국수급", "KRX 투자자별 매매동향", "http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020101", "외국인·개인"),
        ("한국수급", "금투협 신용융자잔고 (FreeSIS)", "https://freesis.kofia.or.kr/", "빚투 규모"),
        ("한국수급", "금투협 투자자예탁금", "https://freesis.kofia.or.kr/", "대기자금"),
        ("한국수급", "네이버 투자자별 매매", "https://finance.naver.com/sise/sise_trans_style.naver", "당일 속보"),
        ("반도체", "SOX 지수 (야후)", "https://finance.yahoo.com/quote/%5ESOX/", ""),
        ("반도체", "DRAMeXchange 현물가", "https://www.dramexchange.com/", "D램·낸드 가격"),
        ("매크로", "Finviz 히트맵", "https://finviz.com/map.ashx", "업종 쏠림 한눈에"),
        ("매크로", "TradingView 경제 캘린더", "https://www.tradingview.com/economic-calendar/", "고용·CPI·FOMC 일정"),
    ]
    return pd.DataFrame(L, columns=["분류", "지표", "링크", "보는 법"])


def show_links(tbl):
    try:
        from IPython.display import HTML
        h = "<table style='font-size:13px'><tr><th>분류</th><th>지표</th><th>보는 법</th></tr>"
        for _, r in tbl.iterrows():
            h += f"<tr><td>{r['분류']}</td><td><a href='{r['링크']}' target='_blank'>{r['지표']}</a></td><td>{r['보는 법']}</td></tr>"
        display(HTML(h + "</table>"))
    except Exception:
        display(tbl)


def chart_global(tech, sdf, path):
    fig, ax = plt.subplots(1, 2, figsize=(16, 7))
    t = tech.sort_values("RSI14")
    col = ["#c0392b" if v < 30 else "#e67e22" if v < 35 else "#7f8c8d" if v <= 70 else "#27ae60" for v in t["RSI14"]]
    ax[0].barh(t["이름"], t["RSI14"], color=col)
    for v in (30, 70): ax[0].axvline(v, ls="--", c="k", lw=0.8)
    ax[0].set_title(f"RSI14 — 지수·관심종목 ({t['기준일'].iloc[0]})", fontweight="bold")
    ax[0].tick_params(axis="y", labelsize=8)
    if "VIX/VIX3M" in sdf:
        v = sdf["VIX/VIX3M"].dropna().iloc[-260:]
        ax[1].plot(v.index, v.values, c="#2c3e50")
        ax[1].axhline(1, c="r", ls="--", lw=1)
        ax[1].fill_between(v.index, 1, v.values, where=v.values > 1, color="r", alpha=0.25)
        ax[1].set_title(f"VIX/VIX3M 기간구조  현재 {v.iloc[-1]:.2f}  (1 초과 = 역전·패닉)", fontweight="bold")
    plt.tight_layout(); plt.savefig(path, dpi=110); plt.close()
    return path


def run_global(cfg):
    tech, sent_tbl, sdf, fg_cnn, _ = global_panel(cfg)
    ev, ev_sum = sox_event_study(cfg)
    links = link_table()
    n_os = int((tech["RSI14"] < 30).sum()); n_all = len(tech)
    vix_inv = bool(("VIX/VIX3M" in sdf) and sdf["VIX/VIX3M"].iloc[-1] > 1)
    print("\n" + "█" * 70)
    print("   글로벌 심리·과매도 패널")
    print("█" * 70)
    print(f"  · RSI 30 미만: {n_os}/{n_all}개   · VIX 기간구조: {'역전(패닉)' if vix_inv else '정상'}")
    if fg_cnn:
        print("  · CNN F&G: " + ", ".join(f"{k} {v}" for k, v in fg_cnn.items()))
    display(sent_tbl)
    print("\n[지수·관심종목 RSI]  RSI 낮은 순")
    display(tech.sort_values("RSI14").reset_index(drop=True))
    if ev is not None:
        print(f"\n[역사] SOX 하루 {cfg['EVENT_DROP']*100:.0f}% 이하 하락 {len(ev)}회 — 이후 수익률")
        display(ev_sum)
    print("\n[바로가기] 자동수집이 안 되는 지표는 아래 링크에서 확인")
    show_links(links)
    f = None
    if cfg["MAKE_CHARTS"]:
        f = chart_global(tech, sdf, "chart_0_글로벌_RSI_VIX.png")
        if IN_NOTEBOOK:
            from IPython.display import Image as IPImage
            display(IPImage(filename=f))
    return {"tech": tech, "sentiment": sent_tbl, "sent_raw": sdf, "fg_cnn": fg_cnn,
            "events": ev, "event_summary": ev_sum, "links": links, "chart": f}


def run(cfg=SETTINGS):
    print("=" * 70)
    print("   국내 시장 지표 분석기  v3.0")
    print("=" * 70)
    setup_korean_font()
    G = run_global(cfg) if cfg.get("RUN_GLOBAL", True) else None
    if not cfg.get("RUN_KOREA", True):
        _save_global_only(G, cfg)
        return {"global": G}

    try:
        if cfg["DATA_MODE"] == "auto":
            idx_df, etf_df, extra_df = load_data_auto(cfg)
        elif cfg["DATA_MODE"] == "excel":
            idx_df, etf_df, extra_df = load_data_excel(cfg)
        else:
            idx_df, etf_df, extra_df = load_data_demo(cfg)
    except Exception as ex:
        print(f"\n[알림] KRX(pykrx) 수집 실패: {type(ex).__name__} {str(ex)[:80]}")
        try:
            idx_df, etf_df, extra_df = load_data_yahoo(cfg)
        except Exception as ex2:
            print(f"[오류] 야후 대체도 실패: {ex2}")
            print("[대체] 데모 데이터로 진행합니다.\n")
            idx_df, etf_df, extra_df = load_data_demo(cfg)

    etf_df = etf_df.dropna(axis=1, how="all")
    etf_df = etf_df.loc[:, etf_df.notna().sum() >= 130]
    print(f"\n[분석] ETF {etf_df.shape[1]}종목 · {etf_df.shape[0]}거래일 "
          f"({etf_df.index[0]:%Y-%m-%d} ~ {etf_df.index[-1]:%Y-%m-%d})\n")

    breadth = calc_breadth(etf_df, cfg)
    mkt = {m: calc_market_indicators(idx_df[m], cfg) for m in idx_df.columns}
    fg = {m: calc_fear_greed(idx_df[m], breadth["MA20_상회비율"], cfg) for m in idx_df.columns}
    rs = calc_mansfield_rs(etf_df, idx_df[idx_df.columns[0]], cfg["SORTINO_MA"])
    sortino = calc_sortino(etf_df, cfg)
    rank_a = sortino_ranking(sortino, above_ma=True, cfg=cfg)
    rank_b = sortino_ranking(sortino, price=etf_df, above_ma=True, extra_ma=10, cfg=cfg)
    gap = make_gap_summary(etf_df, rank_a.iloc[-1].dropna().tolist(), cfg)
    dash, breadth_tbl = build_dashboard(idx_df, mkt, fg, breadth, extra_df, cfg)

    print("█" * 70)
    print(f"   시장 대시보드     기준일 {idx_df.index[-1]:%Y년 %m월 %d일}")
    print("█" * 70)
    display(dash.T)
    print("\n" + "─" * 70)
    print("   시장 폭 · 수급 지표")
    print("─" * 70)
    display(breadth_tbl)

    print("\n" + "─" * 70)
    print(f"   Mansfield RS 상위 12  (코스피 대비 상대강도)")
    print("─" * 70)
    display(rs.iloc[-1].dropna().sort_values(ascending=False).head(12).round(2).to_frame("RS"))

    print("\n" + "─" * 70)
    print(f"   Sortino 10주선 이상 Top20   (최근 {cfg['RANK_TABLE_DAYS']}일)")
    print("─" * 70)
    display(rank_a.tail(cfg["RANK_TABLE_DAYS"]))

    print("\n" + "─" * 70)
    print(f"   위 조건 + 주가 10일선 이상   (최근 {cfg['RANK_TABLE_DAYS']}일)")
    print("─" * 70)
    display(rank_b.tail(cfg["RANK_TABLE_DAYS"]))

    print("\n" + "─" * 70)
    print("   이격도 · 과열도   (과열도 100% = 247거래일 97분위 수준)")
    print("─" * 70)
    show = [c for c in gap.columns if not c.startswith("_")]
    display(gap[show])

    charts = []
    if cfg["MAKE_CHARTS"]:
        print("\n[차트]")
        for m in idx_df.columns:
            f1 = f"chart_1_FG_{m}.png"; chart_fear_greed(fg[m], m, f1, cfg["CHART_MONTHS"], cfg)
            f2 = f"chart_2_패널_{m}.png"; chart_market_panel(mkt[m], m, f2, cfg["CHART_MONTHS"])
            charts += [f1, f2]; print(f"  · {f1}\n  · {f2}")
        f3 = "chart_3_Breadth.png"; chart_breadth(breadth, f3, cfg["CHART_MONTHS"])
        charts.append(f3); print(f"  · {f3}")
        f4 = chart_credit(extra_df, idx_df, "chart_4_신용잔고.png", cfg["CHART_MONTHS"])
        if f4: charts.append(f4); print(f"  · {f4}")
        for _, r in gap.head(cfg["GAP_CHART_COUNT"]).iterrows():
            f5 = f"chart_5_GAP_{r['순위']:02d}_{r['섹터']}.png"
            chart_gap(r, f5, cfg=cfg); charts.append(f5); print(f"  · {f5}")
        if IN_NOTEBOOK:
            from IPython.display import Image as IPImage
            for f in charts:
                display(IPImage(filename=f))

    out = cfg["OUT_XLSX"]
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        if G: _write_global(w, G)
        dash.T.to_excel(w, sheet_name="① 대시보드")
        breadth_tbl.to_excel(w, sheet_name="② 시장폭_수급")
        gap[show].to_excel(w, sheet_name="③ 이격도_과열도", index=False)
        rank_a.to_excel(w, sheet_name="④ Sortino랭킹")
        rank_b.to_excel(w, sheet_name="⑤ Sortino랭킹_10일선")
        rs.round(2).to_excel(w, sheet_name="⑥ MansfieldRS")
        breadth.round(2).to_excel(w, sheet_name="⑦ Breadth전체")
        for m in idx_df.columns:
            mkt[m].round(3).to_excel(w, sheet_name=f"기술지표_{m}"[:31])
            fg[m].round(4).to_excel(w, sheet_name=f"FearGreed_{m}"[:31])
        sortino.round(3).to_excel(w, sheet_name="Sortino원값")
        if len(extra_df.columns):
            extra_df.round(2).to_excel(w, sheet_name="보조데이터")
        etf_df.to_excel(w, sheet_name="원본_ETF")
        idx_df.to_excel(w, sheet_name="원본_지수")
    print(f"\n[저장] {out}  ({os.path.getsize(out)/1024:.0f} KB)")

    try:
        from google.colab import files as _f
        print("[다운로드] 엑셀을 내려받습니다...")
        _f.download(out)
    except Exception:
        pass

    print("\n" + "=" * 70 + "\n   완료\n" + "=" * 70)
    return {"dashboard": dash, "breadth_table": breadth_tbl, "market": mkt,
            "fear_greed": fg, "breadth": breadth, "rs": rs, "sortino": sortino,
            "rank_a": rank_a, "rank_b": rank_b, "gap": gap,
            "etf": etf_df, "index": idx_df, "extra": extra_df, "charts": charts, "global": G}



def _write_global(w, G):
    G["sentiment"].to_excel(w, sheet_name="⓪ 심리지표", index=False)
    G["tech"].sort_values("RSI14").to_excel(w, sheet_name="⓪ RSI_지수_관심종목", index=False)
    if G["fg_cnn"]:
        pd.Series(G["fg_cnn"]).to_frame("CNN F&G").to_excel(w, sheet_name="⓪ CNN_FearGreed")
    if G["events"] is not None:
        G["event_summary"].to_excel(w, sheet_name="⓪ SOX급락_통계", index=False)
        G["events"].to_excel(w, sheet_name="⓪ SOX급락_사례", index=False)
    lk = G["links"].copy()
    lk.to_excel(w, sheet_name="⓪ 지표링크", index=False)
    ws = w.sheets["⓪ 지표링크"]
    for i, u in enumerate(lk["링크"], start=2):
        c = ws.cell(row=i, column=3); c.hyperlink = u; c.style = "Hyperlink"
    G["sent_raw"].round(4).to_excel(w, sheet_name="원본_글로벌심리")


def _save_global_only(G, cfg):
    out = cfg["OUT_XLSX"].replace(".xlsx", "_글로벌.xlsx")
    with pd.ExcelWriter(out, engine="openpyxl") as w:
        _write_global(w, G)
    print(f"\n[저장] {out}")
    try:
        from google.colab import files as _f; _f.download(out)
    except Exception:
        pass


if __name__ == "__main__":
    RESULT = run(SETTINGS)
