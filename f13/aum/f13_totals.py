import sys, json, re
sys.path.insert(0,'f13')
import fetch
from fetch import get
def allf(cik):
    d=get(f'https://data.sec.gov/submissions/CIK{cik:010d}.json').json()
    rows=[]
    def add(r):
        for i,f in enumerate(r['form']):
            if f=='13F-HR': rows.append((r['reportDate'][i], r['filingDate'][i], r['accessionNumber'][i]))
    add(d['filings']['recent'])
    for f in d['filings'].get('files',[]): add(get('https://data.sec.gov/submissions/'+f['name']).json())
    return rows
out={}
for name,cik in [('baupost',1061768),('fundsmith',1569205)]:
    rows=allf(cik); best={}
    for p,fd,acc in rows:
        if p not in best or fd>best[p][0]: best[p]=(fd,acc)
    res=[]
    for p in sorted(best):
        if p<'2018-12-31': continue
        if not (p[5:]=='12-31' or p>='2026-01-01'): continue
        fd,acc=best[p]
        base=f'https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace("-","")}/'
        idx=get(base+'index.json').json()['directory']['item']
        prim=[x['name'] for x in idx if x['name'].lower().endswith('.xml') and 'primary' in x['name'].lower()]
        x=get(base+prim[0]).text
        tv=float(re.search(r'tableValueTotal>([\d.]+)<',x).group(1)); n=int(re.search(r'tableEntryTotal>(\d+)<',x).group(1))
        raw=tv
        if p<='2022-09-30' or cik==1061768: tv*=1000
        res.append({'period':p,'filed':fd,'value_usd_bn':round(tv/1e9,3),'entries':n,'raw_total':raw,'url':base})
        print(name,p,round(tv/1e9,2),n)
    out[name]=res
json.dump(out,open(sys.argv[1],'w'),indent=1)
