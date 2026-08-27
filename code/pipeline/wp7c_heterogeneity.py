# -*- coding: utf-8 -*-
"""P-016 WP7c — 좌측꼬리 체계성 규명 (논문 분기점). +12 pair diff d_i를 firm 특성으로 분해:
(1) 꼬리(하위 quintile) vs 나머지 특성 대조. (2) 적자/흑자·자본잠식(재무 병합) subgroup ATT(mean+median).
(3) 규모/사전성장 median split. 재무병합=CORPCODE corp_name→dart_financials(정규화 exact). 이벤트연도 직전 FY.
산출: shared/outputs/pipe_wp7c_2026-08-23/wp7c_hetero.json
"""
import os,json,warnings,re; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
import statsmodels.api as sm
import xml.etree.ElementTree as ET
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp7c_2026-08-23"; os.makedirs(OUT,exist_ok=True)
RNG=np.random.default_rng(20260823)
def norm(s): return re.sub(r'[\s\(\)㈜]|주식회사|\(주\)','',str(s)).lower()
# --- 패널·처치·매칭 (WP7b 재현) ---
nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",columns=["bn10","data_ym","가입자수","업종","시도"])
nps["ym"]=pd.PeriodIndex(nps["data_ym"],freq="M"); nps["le"]=np.log1p(nps["가입자수"].astype(float))
months=pd.period_range(nps.ym.min(),nps.ym.max(),freq="M"); mi={m:j for j,m in enumerate(months)}
LE=nps.pivot_table(index="bn10",columns="ym",values="le",aggfunc="mean").reindex(columns=months).to_numpy(float)
idx=list(nps.pivot_table(index="bn10",columns="ym",values="le",aggfunc="mean").index); firm_ix={b:i for i,b in enumerate(idx)}
firm_ind=nps.groupby("bn10")["업종"].agg(lambda s:str(s.iloc[0])[:2]); firm_sido=nps.groupby("bn10")["시도"].agg(lambda s:str(s.iloc[0]))
firm_med=np.nanmedian(np.where(np.isfinite(LE),LE,np.nan),axis=1)
pb=pd.read_csv(f"{BASE}/shared/data/processed/pitchbook_all_status_v1.csv",dtype=str)
pbbn=set(pb["bn"].astype(str).str.replace(r'\D','',regex=True).str.zfill(10).dropna())
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T["ev"]=pd.to_datetime(T["event_dt"],errors="coerce"); T=T.dropna(subset=["ev"]).drop_duplicates("k"); treated_bn=set(T.k)
def cap(s): return 1.0 if str(s) in ("11","41","28") else 0.0
def man(i):
    try: return 1.0 if 10<=int(i)<=34 else 0.0
    except: return 0.0
def g12(r): d=r[12:]-r[:-12]; return d[np.isfinite(d)]
PRE=3;POST=12;PREW=13; rec=[]
for r in T.itertuples():
    if r.k not in firm_ix: continue
    fi=firm_ix[r.k]; e=mi.get(pd.Period(r.ev,'M'))
    if e is None: continue
    row=LE[fi]; pre=[e-j for j in range(1,PRE+1) if 0<=e-j<len(months)]
    if sum(np.isfinite(row[i]) for i in pre)<3: continue
    if sum(np.isfinite(row[e+j]) for j in range(1,POST+1) if 0<=e+j<len(months))<3: continue
    if not(0<=e-1<len(months) and 0<=e-PREW<len(months) and np.isfinite(row[e-1]) and np.isfinite(row[e-PREW])): continue
    rec.append(dict(k=r.k,cc=r.cc,fi=fi,e=e,evyear=pd.Period(r.ev,'M').year,logsize=np.nanmean([row[i] for i in pre]),pregrowth=row[e-1]-row[e-PREW],cap=cap(firm_sido.get(r.k,"0")),man=man(firm_ind.get(r.k,"99"))))
Tm=pd.DataFrame(rec)
crows=np.array([i for i,b in enumerate(idx) if (b not in pbbn) and (b not in treated_bn)])
cpg=np.array([np.nanmean(g12(LE[r])) if g12(LE[r]).size else np.nan for r in crows]); cls=firm_med[crows]
ok=np.isfinite(cls)&np.isfinite(cpg); crows=crows[ok]; cls=cls[ok]; cpg=cpg[ok]
ccap=np.array([cap(firm_sido.get(idx[r],"0")) for r in crows]); cman=np.array([man(firm_ind.get(idx[r],"99")) for r in crows])
Xt=np.column_stack([Tm.logsize,Tm.logsize**2,Tm.pregrowth,Tm.cap,Tm.man]); Xc=np.column_stack([cls,cls**2,cpg,ccap,cman])
X=np.vstack([Xt,Xc]); y=np.r_[np.ones(len(Xt)),np.zeros(len(Xc))]; Xs=(X-X.mean(0))/X.std(0)
psm=sm.Logit(y,sm.add_constant(Xs)).fit(disp=0); xb=psm.predict(sm.add_constant(Xs),linear=True); xbt=xb[:len(Xt)]; xbc=xb[len(Xt):]
lo,hi=xbt.min(),xbt.max(); supp=(xbc>=lo)&(xbc<=hi); cr=crows[supp]; xbcs=xbc[supp]; calp=0.2*np.std(xb); K=10
o=np.argsort(xbcs); xs=xbcs[o]; cs=cr[o]
def knn(xi):
    pos=np.searchsorted(xs,xi); cand=list(range(max(0,pos-K-2),min(len(xs),pos+K+2))); dd=np.abs(xs[cand]-xi); sel=np.argsort(dd)[:K]
    return [cs[cand[s]] for s in sel if dd[s]<=calp]
di=np.full(len(Tm),np.nan)
for ii,r in enumerate(Tm.itertuples()):
    m=knn(xbt[ii]);
    if not m: continue
    e=r.e; t=e+12
    if not(0<=t<len(months)) or not np.isfinite(LE[r.fi,t]): continue
    bcols=[e-j for j in range(1,PRE+1) if 0<=e-j<len(months)]; Dt=LE[r.fi,t]-np.nanmean([LE[r.fi,b] for b in bcols])
    dc=[np.nanmean([LE[c,b] for b in bcols]) for c in m]; yc=[LE[c,t] for c in m]
    pair=[yc[j]-dc[j] for j in range(len(m)) if np.isfinite(dc[j]) and np.isfinite(yc[j])]
    if len(pair)<3: continue
    di[ii]=Dt-np.mean(pair)
Tm["di"]=di; Tm=Tm.dropna(subset=["di"]); print(f"매칭·d_i {len(Tm)}",flush=True)

# --- 재무 병합 (전체 재무데이터 bn 스트리밍 조인; 49사 panel 아님) ---
import csv as _csv
FIN="PI/drops/재무데이터_2009_2025_통합.csv"
tbn=set(Tm.k)
finmap={}  # bn10 -> {year: dict}
with open(f"{BASE}/{FIN}",encoding='utf-8') as f:
    rd=_csv.reader(f); next(rd)
    for row in rd:
        if len(row)<109: continue
        if row[4].strip()!="결산": continue                 # 연간
        bn=re.sub(r'\D','',row[5]).zfill(10)
        if bn not in tbn: continue
        try: yr=int(row[3])
        except: continue
        def num(x):
            try: return float(x)
            except: return np.nan
        finmap.setdefault(bn,{})[yr]=dict(net=num(row[108]),equity=num(row[82]),rev=num(row[105]))
def get_fin(k,evyear):
    d=finmap.get(k)
    if not d: return None
    for yr in (evyear-1,evyear-2,evyear,evyear-3):
        if yr in d: return d[yr]
    return None
fm=[get_fin(r.k,r.evyear) for r in Tm.itertuples()]
Tm["fin_matched"]=[f is not None for f in fm]
Tm["net_income"]=[f["net"] if f else np.nan for f in fm]
Tm["total_equity"]=[f["equity"] if f else np.nan for f in fm]
Tm["revenue"]=[f["rev"] if f else np.nan for f in fm]
nfin=int(Tm.fin_matched.sum()); print(f"재무 병합(전체·bn조인) {nfin}/{len(Tm)}",flush=True)
Tm[["k","cc","evyear","di","logsize","pregrowth","man","fin_matched","net_income","total_equity","revenue"]].to_csv(f"{OUT}/wp7c_firm_di.csv",index=False,encoding="utf-8-sig")

def stats_of(a):
    a=a[np.isfinite(a)]; n=len(a)
    if n<5: return dict(n=n,note="n<5")
    bs=np.array([np.mean(a[RNG.integers(0,n,n)]) for _ in range(1000)])
    return dict(n=n,mean=round(float(np.mean(a)),4),mean_ci=[round(float(np.percentile(bs,2.5)),4),round(float(np.percentile(bs,97.5)),4)],
                median=round(float(np.median(a)),4),pct_neg=round(float(np.mean(a<0)),3))

# (1) 꼬리(하위 quintile) vs 나머지
q20=np.percentile(Tm.di,20); tail=Tm[Tm.di<=q20]; rest=Tm[Tm.di>q20]
def _pct적자(x):
    xf=x[x.net_income.notna()]; return round(float((xf.net_income<0).mean()),3) if len(xf) else None
tail_profile=dict(q20_cut=round(float(q20),4),
    tail=dict(n=len(tail),mean_logsize=round(float(tail.logsize.mean()),3),mean_pregrowth=round(float(tail.pregrowth.mean()),4),pct_manuf=round(float(tail.man.mean()),3),
              n_fin_income=int(tail.net_income.notna().sum()),pct_적자=_pct적자(tail)),
    rest=dict(n=len(rest),mean_logsize=round(float(rest.logsize.mean()),3),mean_pregrowth=round(float(rest.pregrowth.mean()),4),pct_manuf=round(float(rest.man.mean()),3),
              n_fin_income=int(rest.net_income.notna().sum()),pct_적자=_pct적자(rest)))

# (2) 적자/흑자·자본잠식 subgroup ATT
fmatch=Tm[Tm.fin_matched]
sub={}
sub["적자(net<0)"]=stats_of(fmatch[fmatch.net_income<0].di.values)
sub["흑자(net>=0)"]=stats_of(fmatch[fmatch.net_income>=0].di.values)
sub["자본잠식(equity<0)"]=stats_of(fmatch[fmatch.total_equity<0].di.values)
sub["정상자본(equity>=0)"]=stats_of(fmatch[fmatch.total_equity>=0].di.values)

# (3) 규모/성장 median split
for nm,col in [("소규모","logsize"),("저성장","pregrowth")]:
    med=Tm[col].median()
    sub[f"{nm}(<median)"]=stats_of(Tm[Tm[col]<med].di.values)
    sub[f"{nm}반대(>=median)"]=stats_of(Tm[Tm[col]>=med].di.values)

res=dict(id="P016-WP7c",n_matched=int(len(Tm)),n_fin=nfin,tail_profile=tail_profile,subgroups=sub,
         interpretation="꼬리에 적자·고레버리지·소규모가 과대대표되고 적자 subgroup ATT의 median이 음이면 distress-subset 스토리 성립.")
json.dump(res,open(f"{OUT}/wp7c_hetero.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp7c.done","w").write("done")
print("=== WP7c 완료 ===")
print("꼬리 profile:",json.dumps(tail_profile,ensure_ascii=False))
print("subgroups:",json.dumps(sub,ensure_ascii=False))
