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
