# 일일 스냅샷: v3 분석기의 글로벌 패널을 돌려 대시보드용 JSON 생성
import sys, json, importlib.util, datetime as dt, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.argv=['x']
spec=importlib.util.spec_from_file_location('m',os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','Market_Indicator_Analyzer_v3.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
import pandas as pd, numpy as np
cfg=m.SETTINGS
tech,sent,sdf,fg,_=m.global_panel(cfg)
ev,evs=m.sox_event_study(cfg)
def clean(df):
    return json.loads(df.replace({np.nan:None}).to_json(orient='records',force_ascii=False))
ren={'1일%':'d1','5일%':'d5','1개월%':'m1','RSI14':'rsi','5일전RSI':'rsi_prev5','1년최저RSI':'rsi_min1y','50일선%':'vs_ma50','200일선%':'vs_ma200','52주고점%':'vs_high52','기준일':'asof','종가':'close','구분':'group','이름':'name','티커':'ticker','판정':'state'}
t=tech.rename(columns=ren).sort_values('rsi')
json.dump(clean(t),open('rsi.json','w'),ensure_ascii=False)
s=sent.rename(columns={'지표':'indicator','현재':'value','기준':'rule','해석':'reading'}); s['value']=s['value'].astype(float)
json.dump(clean(s),open('sentiment.json','w'),ensure_ascii=False)
v=sdf['VIX/VIX3M'].dropna().iloc[-260:]
json.dump([{'date':d.strftime('%Y-%m-%d'),'ratio':round(float(x),4)} for d,x in v.items()],open('vixts.json','w'))
e=evs.rename(columns={'구간':'window','중간값':'median','평균':'mean','상승확률':'hit'})
json.dump(clean(e),open('sox_events.json','w'),ensure_ascii=False)
idx=t[t.group=='지수'].set_index('ticker')
summ={'asof':dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M KST'),
 'n_oversold':int((t.rsi<30).sum()),'n_total':int(len(t)),
 'vix':round(float(sdf['VIX'].dropna().iloc[-1]),2),'vix_ratio':round(float(v.iloc[-1]),3),
 'vix_state':'역전(패닉)' if v.iloc[-1]>1 else '정상',
 'sox_rsi':float(idx.loc['^SOX','rsi']),'sox_d1':float(idx.loc['^SOX','d1']),
 'spx_rsi':float(idx.loc['^GSPC','rsi']),'kospi_rsi':float(idx.loc['^KS11','rsi']),'kospi_d1':float(idx.loc['^KS11','d1']),
 'n_events':int(len(ev)),
 'cnn_fg':(fg or {}).get('점수')}
json.dump([summ],open('summary.json','w'),ensure_ascii=False)
json.dump(clean(m.link_table().rename(columns={'분류':'category','지표':'name','링크':'url','보는 법':'how'})),open('links.json','w'),ensure_ascii=False)
print(json.dumps(summ,ensure_ascii=False))
