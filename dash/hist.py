# 3년+ 시계열: S&P500·코스피·VIX(야후) + CNN 공포탐욕(fg_hist.json, 크롬으로 수집)
import json, sys, os, importlib.util
os.chdir(os.path.dirname(os.path.abspath(__file__)))
spec=importlib.util.spec_from_file_location('m',os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','Market_Indicator_Analyzer_v3.py'))
m=importlib.util.module_from_spec(spec); sys.argv=['x']; spec.loader.exec_module(m)
import pandas as pd
S={k:m.yahoo_close(t,'2023-01-01') for k,t in [('spx','^GSPC'),('kospi','^KS11'),('vix','^VIX')]}
df=pd.DataFrame(S)
fg=json.load(open('fg_hist.json'))
fg=pd.Series({pd.Timestamp(k):v for k,v in fg.items()},name='fg')
df=df.join(fg,how='outer').sort_index()
df=df[df.index>='2023-01-01']
rows=[]
for d,r in df.iterrows():
    o={'date':d.strftime('%Y-%m-%d')}
    for k in ['spx','kospi','vix','fg']:
        v=r[k]; o[k]=None if pd.isna(v) else round(float(v),2 if k!='fg' else 0)
    if any(o[k] is not None for k in ['spx','kospi','vix']): rows.append(o)
json.dump(rows,open('history.json','w'),separators=(',',':'))
print(len(rows),rows[0],rows[-2:])
