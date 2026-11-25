# 2000년~ 시계열: S&P500·나스닥100·코스피·VIX(야후) + CNN 공포탐욕(fg_hist.json, 2023년 6월~)
# 산출: history.json(일별), vix_events.json(VIX 종가 30 이상 구간별 이벤트·최대 VIX·낙폭·회복일)
import json, sys, os, importlib.util
os.chdir(os.path.dirname(os.path.abspath(__file__)))
spec=importlib.util.spec_from_file_location('m',os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','Market_Indicator_Analyzer_v3.py'))
m=importlib.util.module_from_spec(spec); sys.argv=['x']; spec.loader.exec_module(m)
import pandas as pd
START='2000-01-01'
T=[('spx','^GSPC'),('ndx','^NDX'),('kospi','^KS11'),('vix','^VIX')]
S={k:m.yahoo_close(t,'1999-01-01') for k,t in T}
df=pd.DataFrame(S)
fg=json.load(open('fg_hist.json'))
fg=pd.Series({pd.Timestamp(k):v for k,v in fg.items()},name='fg')
df=df.join(fg,how='outer').sort_index()
full=df.copy()
df=df[df.index>=START]
rows=[]
for d,r in df.iterrows():
    o={'date':d.strftime('%Y-%m-%d')}
    for k in ['spx','ndx','kospi','vix','fg']:
        v=r[k]; o[k]=None if pd.isna(v) else round(float(v),2 if k!='fg' else 0)
    if any(o[k] is not None for k in ['spx','ndx','kospi','vix']): rows.append(o)
json.dump(rows,open('history.json','w'),separators=(',',':'))
print(len(rows),rows[0],rows[-1])

# ── VIX 30 이상 구간 이벤트 ──
LABEL={  # 구간 시작일(YYYY-MM) → 이벤트 이름. 새 구간은 '분류 전'으로 나오며 일일 작업이 채운다
 '2000-04':'닷컴 버블 붕괴 시작(나스닥 고점 이탈)','2000-10':'닷컴 2차 하락','2000-12':'닷컴 하락·경기 둔화','2001-03':'닷컴 바닥권·미국 경기침체',
 '2001-09':'9·11 테러','2002-07':'엔론·월드컴 회계부정, 닷컴 최종 바닥','2003-01':'이라크전 개전 직전','2007-08':'서브프라임 1차(퀀트펀드 청산)',
 '2007-11':'서브프라임 손실 확대','2008-01':'소시에테제네랄 사태·연준 긴급 인하','2008-03':'베어스턴스 붕괴','2008-09':'리먼 파산·글로벌 금융위기',
 '2009-10':'금융위기 후 조정','2010-05':'플래시 크래시·그리스 재정위기','2011-08':'미국 신용등급 강등·유럽 재정위기','2015-08':'위안화 절하·차이나 쇼크',
 '2018-02':'볼마겟돈(VIX 상품 붕괴)','2018-12':'연준 긴축·미중 무역분쟁','2020-02':'코로나 팬데믹','2020-09':'미국 기술주 급락',
 '2020-10':'미국 대선 불확실성·코로나 재확산','2021-01':'게임스톱 숏스퀴즈','2021-12':'오미크론·연준 긴축 전환','2022-01':'연준 긴축·러시아 우크라이나 침공',
 '2022-04':'연준 75bp·인플레이션 쇼크','2022-09':'영국 LDI 사태·CPI 쇼크','2024-08':'엔 캐리 청산·미국 고용 쇼크','2025-04':'‘해방의 날’ 상호관세',
 '2026-03':'이란 전쟁·유가·금리 급등','2026-11':'SEC 엔비디아 회계조사 보도·AI 반도체 투매'}
v=full['vix'].dropna(); v=v[v.index>=START]
hi=v[v>=30].index; eps=[]
if len(hi):
    cur=[hi[0]]
    for d in hi[1:]:
        if (d-cur[-1]).days<=35: cur.append(d)
        else: eps.append(cur); cur=[d]
    eps.append(cur)
def stat(k,start,vpk):
    c=full[k].dropna(); pre=c[(c.index<start)&(c.index>=start-pd.Timedelta(days=365))]
    if pre.empty: return {}
    pk=pre.max(); pkd=pre.idxmax(); win=c[(c.index>=pkd)&(c.index<=vpk+pd.Timedelta(days=120))]
    tr=win.min(); trd=win.idxmin(); rec=c[c.index>trd]; rec=rec[rec>=pk]
    base=c[c.index>=vpk]
    f12=c[c.index>=vpk+pd.Timedelta(days=365)]
    return {k+'_dd':round((tr/pk-1)*100,1),k+'_trough':trd.strftime('%Y-%m-%d'),
            k+'_rec_days':int((rec.index[0]-trd).days) if len(rec) else None,
            k+'_f12':round((f12.iloc[0]/base.iloc[0]-1)*100,1) if len(f12) and len(base) else None}
out=[]
for e in eps:
    seg=v.loc[e[0]:e[-1]]; vpk=seg.idxmax()
    o={'start':e[0].strftime('%Y-%m-%d'),'end':e[-1].strftime('%Y-%m-%d'),'days30':len(e),'vix_max':round(float(seg.max()),1),'vix_peak':vpk.strftime('%Y-%m-%d'),
       'event':LABEL.get(e[0].strftime('%Y-%m'),'분류 전')}
    for k in ['spx','ndx','kospi']: o.update(stat(k,e[0],vpk))
    out.append(o)
out.reverse()
json.dump(out,open('vix_events.json','w'),ensure_ascii=False,separators=(',',':'))
print('vix_events',len(out),out[0])

# ── 한국 증권시장안정펀드(증안펀드) 타임라인 ── 날짜는 공개 보도·금융위 발표 기준, 수치는 야후 코스피 종가로 계산
FUND=[
 dict(id='1990',short='1990.5 증시안정기금 4조 출범·매입',vix='',crisis='3저 호황 붕괴 후 장기 하락',ann='1990-05',exec_='실제 매입(증시안정기금 4조원 → 4.85조원, 은행·증권·보험·상장사 출자)',
      steps='1989.4 코스피 1,007 고점 → 1990.5 증시안정기금 출범 → 수년간 매입',base=None,note='야후 코스피 자료가 1996년부터라 수치 비교 불가'),
 dict(id='2003',short='2003.2 공동펀드 4,000억 조성·투입',vix='2003-01',crisis='카드사태·이라크전·북핵',ann='2003-02-03',exec_='실제 투입(증권유관기관 공동펀드 4,000억원, 2003.2~2007.8 운용)',
      steps='2002.4 고점 938 → 2003.2 공동펀드 조성 → 2003.3.17 바닥 515 → 반등',note='조성 월(2월) 첫 거래일 기준'),
 dict(id='2008',short='10.10 공동펀드 제안 → 11.21 5,150억 투입 시작',vix='2008-09',crisis='리먼 파산·글로벌 금융위기',ann='2008-10-10',exec_='실제 투입 5,150억원(거래소 2,500·예탁원 2,100·증협 500·운용협회 50억), 2008.11.21부터 5개월간 매월 1,030억원',
      steps='2007.10 고점 2,065 → 10.10 증권업계 공동펀드 제안 → 10.24 바닥 939 → 11.20 2차 저점 949 → 11.21 첫 투입 → 2009 반등',exe='2008-11-21',note='발표 후 2주간 −24% 추가 하락. 투입은 바닥 4주 뒤'),
 dict(id='2020',short='3.24 10.7조 발표(바닥 5일 뒤), 미집행',vix='2020-02',crisis='코로나 팬데믹',ann='2020-03-24',exec_='미집행(10.76조원 약정: 5대 금융지주 5조·국책은행 2조·선도 금융사 3조·유관기관 7,600억)',
      steps='2020.1 고점 2,267 → 3.19 바닥 1,458 → 3.24 10.7조 발표 → 4월 조성 → 집행 없이 반등',note='발표가 바닥 5일 뒤'),
 dict(id='2022',short='9.29 재가동 검토(다음 날 바닥), 미집행',vix='2022-09',crisis='연준 긴축·레고랜드',ann='2022-09-29',exec_='미집행(10.76조원 재약정, 10월 중순)',
      steps='2021.7 고점 3,305 → 9.29 재가동 검토 → 9.30 바닥 2,155 → 10월 재약정 → 집행 없이 반등',note='검토 다음 날이 바닥'),
 dict(id='2024',short='12.4 10조 즉시 가동 준비, 미집행',vix='',crisis='12·3 비상계엄',ann='2024-12-04',exec_='미집행(10조원 "언제든 즉시 가동" 준비)',
      steps='2024.7 고점 2,891 → 12.4 즉시 가동 준비 발표 → 12.9 국지 저점 2,361 → 2025.4 관세로 2,294 재하락 → 반등',note='국지 바닥은 5일 뒤, 진짜 바닥은 4개월 뒤(관세)'),
 dict(id='2026-03',short='3.5 거론, 당국 신중',vix='2026-03',crisis='이란 전쟁·유가·금리 급등',ann='2026-03-05',exec_='미가동(거론만, 당국 신중)',
      steps='2026.2 고점 6,307 → 3.5 증안펀드 거론 → 3.31 저점 5,052 → 반등',note=''),
 dict(id='2026-11',short='11.22 가동 준비 착수(18년 만) → 11.25 확대 추진, 투입 미정',vix='2026-11',crisis='AI 반도체 투매(SEC 엔비디아 회계조사 보도)',ann='2026-11-23',exec_='가동 준비 착수(11.22 F4 긴급회의, 18년 만). 10.76조원 약정, 투입 시기 미정. 11.25 산은, 금융사에 추가 출자 가능액 조회 공문(확대 추진, 납입 요청 아님·한경 11.25 보도)',
      steps='2026.6.22 고점 9,115 → 11.20 −5.2% → 11.22 가동 준비 착수 → 11.23 4,709(장중 4,587) → 11.24 +6.3% 5,006 → 11.25 −6.2% 4,698(삼성 −9.9%·하이닉스 −11.1%) → 11.25 확대 추진 공문(한경 보도)',note='동반: 자사주 매수한도 완화(11.24~, 3개월)·불법 공매도 특별감시·신용 담보비율 완화. 11.25 박현주 회장 100조 확대 제안(재경일보 보도, 정부 결정 아님)'),
]
kc=full['kospi'].dropna(); kf=[]
for f in FUND:
    o={k:v for k,v in f.items() if k not in ('exec_','base')}; o['exec']=f['exec_']
    if len(f['ann'])==10 and pd.Timestamp(f['ann'])>=kc.index[0]:
        d=pd.Timestamp(f['ann']); a=kc[kc.index>=d]; b0=a.iloc[0]
        w=kc[d-pd.Timedelta(days=30):d+pd.Timedelta(days=60)]
        o.update(k_ann=round(float(b0)),bottom=w.idxmin().strftime('%Y-%m-%d'),k_bottom=round(float(w.min())),to_bottom=int((w.idxmin()-a.index[0]).days),
                 more_drop=round(float(a[:d+pd.Timedelta(days=60)].min()/b0-1)*100,1))
        for n,lab in [(30,'f1m'),(91,'f3m'),(182,'f6m'),(365,'f12m')]:
            x=kc[kc.index>=d+pd.Timedelta(days=n)]; o[lab]=round(float(x.iloc[0]/b0-1)*100,1) if len(x) else None
    kf.append(o)
json.dump(kf,open('kr_fund.json','w'),ensure_ascii=False,separators=(',',':'))
print('kr_fund',len(kf),kf[-1])
