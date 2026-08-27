# WP13 재실행 사본 (2026-08-26): 정규화 마스터(382 dated)로 동일 코드 재실행. 원본 wp9e_narrative.py · 출력 폴더만 pipe_wp13_2026-08-26 으로 치환.
# -*- coding: utf-8 -*-
"""P-016 WP9e — 서사 업그레이드 배터리.
(a) CAR ~ 조달목적(생존 vs 투자): 시장이 공시된 목적에 차등 반응하는가 (이진검정, 검정력 OK)
(b) 좌측꼬리 ~ 목적 + 사전관측치 예측(LPM·AUC): econometrician은 꼬리를 예측하는가
(c) 개선 CAR→d 검정: CAR[0,+5]·5분위 포트폴리오·정밀 d(avg7-12/base12/k50)·CI/MDE 병기(rule11)
(d) 12개월 BHAR(시장조정): 꼬리·생존목적 기업의 장기 수익률 — 시장은 결국 배우는가
산출: shared/outputs/pipe_wp13_2026-08-26/wp9e_narrative.json + wp9e_firm_d_v2.csv
"""
import os,json,warnings; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
from scipy import stats
import statsmodels.api as sm
import xml.etree.ElementTree as ET
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
RNG=np.random.default_rng(20260823)
# ---------- 정밀 d (avg7-12/base12/k50) firm-level 재구축 ----------
nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",columns=["bn10","data_ym","가입자수","업종","시도"])
nps["ym"]=pd.PeriodIndex(nps["data_ym"],freq="M"); nps["le"]=np.log1p(nps["가입자수"].astype(float))
months=pd.period_range(nps.ym.min(),nps.ym.max(),freq="M"); mi={m:j for j,m in enumerate(months)}; NM=len(months)
piv=nps.pivot_table(index="bn10",columns="ym",values="le",aggfunc="mean").reindex(columns=months)
idx=list(piv.index); firm_ix={b:i for i,b in enumerate(idx)}; LE=piv.to_numpy(float)
firm_ind=nps.groupby("bn10")["업종"].agg(lambda s:str(s.iloc[0])[:2]); firm_sido=nps.groupby("bn10")["시도"].agg(lambda s:str(s.iloc[0]))
firm_med=np.nanmedian(np.where(np.isfinite(LE),LE,np.nan),axis=1)
pb=pd.read_csv(f"{BASE}/shared/data/processed/pitchbook_all_status_v1.csv",dtype=str)
pbbn=set(pb["bn"].astype(str).str.replace(r'\D','',regex=True).str.zfill(10).dropna())
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T=T[pd.to_numeric(T.event_dt.astype(str).str[:4],errors="coerce").between(2015,2025)]   # 표본기간 2015–2025(원고 명시). 날짜 정규화로 유입된 2010–2014·2026 이벤트 제외 — WP13, 2026-08-27
T["evd"]=pd.to_datetime(T["event_dt"],errors="coerce"); T["ev"]=T.evd.dt.to_period("M"); T=T.dropna(subset=["ev"]).drop_duplicates("k"); tb=set(T.k)
T=T[T.k.isin({l.strip() for l in open(f"{BASE}/shared/outputs/pipe_wp13_2026-08-26/emp_primary_k.txt") if l.strip()})]  # WP13: 고정 1차표본(210)
def cap(s): return 1.0 if str(s) in ("11","41","28") else 0.0
def man(i):
    try: return 1.0 if 10<=int(i)<=34 else 0.0
    except: return 0.0
def g12(r): d=r[12:]-r[:-12]; return d[np.isfinite(d)]
rec=[]
for r in T.itertuples():
    if r.k not in firm_ix: continue
    fi=firm_ix[r.k]; e=mi.get(r.ev)
    if e is None: continue
    row=LE[fi]; pre=[e-j for j in range(1,4) if 0<=e-j<NM]
    if sum(np.isfinite(row[i]) for i in pre)<3: continue
    if sum(np.isfinite(row[e+j]) for j in range(1,13) if 0<=e+j<NM)<3: continue
    if not(0<=e-1<NM and 0<=e-13<NM and np.isfinite(row[e-1]) and np.isfinite(row[e-13])): continue
    rec.append(dict(k=r.k,cc=r.cc,fi=fi,e=e,evd=r.evd,logsize=np.nanmean([row[i] for i in pre]),pregrowth=row[e-1]-row[e-13],cap=cap(firm_sido.get(r.k,"0")),man=man(firm_ind.get(r.k,"99"))))
Tm=pd.DataFrame(rec)
crows=np.array([i for i,b in enumerate(idx) if (b not in pbbn) and (b not in tb)])
cpg=np.array([np.nanmean(g12(LE[r])) if g12(LE[r]).size else np.nan for r in crows]); cls=firm_med[crows]
ok=np.isfinite(cls)&np.isfinite(cpg); crows=crows[ok]; cls=cls[ok]; cpg=cpg[ok]
ccap=np.array([cap(firm_sido.get(idx[r],"0")) for r in crows]); cman=np.array([man(firm_ind.get(idx[r],"99")) for r in crows])
Xt=np.column_stack([Tm.logsize,Tm.logsize**2,Tm.pregrowth,Tm.cap,Tm.man]); Xc=np.column_stack([cls,cls**2,cpg,ccap,cman])
X=np.vstack([Xt,Xc]); y=np.r_[np.ones(len(Xt)),np.zeros(len(Xc))]; Xs=(X-X.mean(0))/X.std(0)
psm=sm.Logit(y,sm.add_constant(Xs)).fit(disp=0); xb=np.asarray(psm.predict(sm.add_constant(Xs),linear=True)); xbt=xb[:len(Xt)]; xbc=xb[len(Xt):]
lo,hi=xbt.min(),xbt.max(); supp=(xbc>=lo)&(xbc<=hi); cr=crows[supp]; xbcs=xbc[supp]; calp=0.2*np.std(xb); K=50
o=np.argsort(xbcs); XS=xbcs[o]; CS=cr[o]
def knn(xi):
    p=np.searchsorted(XS,xi); cand=list(range(max(0,p-K-2),min(len(XS),p+K+2))); dd=np.abs(XS[cand]-xi); sel=np.argsort(dd)[:K]
    return [CS[cand[s]] for s in sel if dd[s]<=calp]
dv=np.full(len(Tm),np.nan)
for ii,r in enumerate(Tm.itertuples()):
    e=r.e
    if e-12<0 or e+12>=NM: continue
    pre=LE[:,e-12:e]; post=LE[:,e+7:e+13]
    own_pre=np.nanmean(pre[r.fi]); own_post=np.nanmean(post[r.fi])
    if np.sum(np.isfinite(pre[r.fi]))<6 or np.sum(np.isfinite(post[r.fi]))<3: continue
    nb=knn(xbt[ii]); vals=[]
    for c in nb:
        cp=np.nanmean(pre[c]); cq=np.nanmean(post[c])
        if np.sum(np.isfinite(pre[c]))>=6 and np.sum(np.isfinite(post[c]))>=3: vals.append(cq-cp)
    if len(vals)<3: continue
    dv[ii]=(own_post-own_pre)-np.mean(vals)
Tm["d2"]=dv; Tm2=Tm.dropna(subset=["d2"]).copy()
print(f"정밀 d(avg7-12/b12/k50) n={len(Tm2)}",flush=True)
# ---------- merge: CAR + 목적 ----------
car=pd.read_csv(f"{BASE}/shared/outputs/pipe_wp13_2026-08-26/wp8b_car_firm.csv",dtype={"k":str})
fd=pd.read_csv(f"{BASE}/shared/outputs/pipe_wp13_2026-08-26/treatment_fdpp.csv",dtype={"k":str})
fd["k"]=fd["k"].str.replace(r'\D','',regex=True).str.zfill(10)
M=Tm2.merge(car,on="k",how="left").merge(fd[["k","fdpp_found","dom_purpose"]],on="k",how="left")
M["survival"]=M.dom_purpose.isin(["운영","채무상환"]).astype(float)
M["growth_p"]=M.dom_purpose.isin(["시설","타법인증권","영업양수"]).astype(float)
M.to_csv(f"{OUT}/wp9e_firm_d_v2.csv",index=False,encoding="utf-8-sig")
q25=M.d2.quantile(.25); M["tl"]=(M.d2<=q25).astype(float)
res={}
def mci(a,B=2000):
    a=np.asarray(a,float); a=a[np.isfinite(a)]; n=len(a)
    if n<5: return dict(n=n)
    bs=np.array([np.mean(a[RNG.integers(0,n,n)]) for _ in range(B)])
    return dict(n=n,mean=round(float(a.mean()),4),ci=[round(float(np.percentile(bs,2.5)),4),round(float(np.percentile(bs,97.5)),4)])
# (a) CAR ~ 목적 (공시된 정보에 시장 차등반응?)
sub=M[(M.fdpp_found==True)&((M.survival==1)|(M.growth_p==1))].dropna(subset=["m1_p1"])
a_s=sub[sub.survival==1]; a_g=sub[sub.growth_p==1]
for w in ("m1_p1","e0_p5"):
    s_=mci(a_s[w]); g_=mci(a_g[w])
    tt=stats.ttest_ind(a_s[w].dropna(),a_g[w].dropna(),equal_var=False)
    res[f"a_CAR_{w}"]=dict(survival=s_,growth=g_,diff=round(float(np.nanmean(a_s[w])-np.nanmean(a_g[w])),4),welch_p=round(float(tt.pvalue),4))
print("(a) CAR~목적:",res["a_CAR_m1_p1"],flush=True)
# (b) 꼬리 ~ 목적 + 예측(LPM/AUC)
sb=M[(M.fdpp_found==True)&((M.survival==1)|(M.growth_p==1))]
t_s=float(sb[sb.survival==1]["tl"].mean()); t_g=float(sb[sb.growth_p==1]["tl"].mean())
ct=np.array([[int(sb[(sb.survival==1)&(sb["tl"]==1)].shape[0]),int(sb[(sb.survival==1)&(sb["tl"]==0)].shape[0])],
             [int(sb[(sb.growth_p==1)&(sb["tl"]==1)].shape[0]),int(sb[(sb.growth_p==1)&(sb["tl"]==0)].shape[0])]])
fis=stats.fisher_exact(ct)
res["b_tail_by_purpose"]=dict(tail_rate_survival=round(t_s,3),tail_rate_growth=round(t_g,3),fisher_p=round(float(fis.pvalue),4),table=ct.tolist())
# 예측 logit: tail ~ logsize+pregrowth+survival+man (in-sample AUC, 수동 계산)
P=M.dropna(subset=["d2"]).copy(); P["survival"]=P["survival"].fillna(0)
Xp=sm.add_constant(np.column_stack([P.logsize,P.pregrowth,P.survival,P.man]))
lg=sm.Logit(np.asarray(P["tl"]),Xp).fit(disp=0)
ph=np.asarray(lg.predict(Xp)); yv=np.asarray(P["tl"])
r1=stats.rankdata(ph); auc=(r1[yv==1].sum()-yv.sum()*(yv.sum()+1)/2)/(yv.sum()*(len(yv)-yv.sum()))
res["b_tail_predict"]=dict(auc_insample=round(float(auc),3),coefs={k_:round(float(v),4) for k_,v in zip(["const","logsize","pregrowth","survival","manuf"],np.asarray(lg.params))},
                           pvals={k_:round(float(v),4) for k_,v in zip(["const","logsize","pregrowth","survival","manuf"],np.asarray(lg.pvalues))})
print("(b) 꼬리~목적:",res["b_tail_by_purpose"],"| AUC:",res["b_tail_predict"]["auc_insample"],flush=True)
# (c) 개선 CAR→d: CAR[0,+5] 예측변수 + 5분위 포트폴리오 + CI 병기
cc_=M.dropna(subset=["d2","e0_p5"])
Xr=sm.add_constant(np.column_stack([cc_.e0_p5,cc_.logsize,cc_.pregrowth]))
ols=sm.OLS(np.asarray(cc_.d2,float),Xr).fit(cov_type="HC1")
Pm=np.asarray(ols.params); Tv=np.asarray(ols.tvalues); Pv=np.asarray(ols.pvalues); Se=np.asarray(ols.bse)
res["c_ols_d2_car05"]=dict(coef=round(float(Pm[1]),4),se=round(float(Se[1]),4),t=round(float(Tv[1]),2),p=round(float(Pv[1]),4),
                            ci=[round(float(Pm[1]-1.96*Se[1]),4),round(float(Pm[1]+1.96*Se[1]),4)],n=int(len(cc_)))
cc_["q5"]=pd.qcut(cc_.e0_p5,5,labels=False)
top=cc_[cc_.q5==4].d2; bot=cc_[cc_.q5==0].d2
tt=stats.ttest_ind(top.dropna(),bot.dropna(),equal_var=False)
res["c_portfolio_q5"]=dict(top_mean=round(float(top.mean()),4),bottom_mean=round(float(bot.mean()),4),diff=round(float(top.mean()-bot.mean()),4),welch_p=round(float(tt.pvalue),4))
print("(c) CAR[0,5]→d2:",res["c_ols_d2_car05"],"| Q5-Q1:",res["c_portfolio_q5"],flush=True)
# (d) 12개월 BHAR (시장조정 buy-and-hold)
root=ET.parse(f"{BASE}/shared/data/external/dart_auditcover/CORPCODE.xml").getroot()
cc2sc={}
for li in root.iter("list"):
    c=(li.findtext("corp_code") or "").strip(); sc=(li.findtext("stock_code") or "").strip()
    if c and sc and len(sc)==6: cc2sc[c]=sc
def load_sheet(sh):
    d=pd.read_excel(f"{BASE}/PI/drops/kospi, kosdaq 종목 수정주가.xlsx",sheet_name=sh)
    d=d.rename(columns={d.columns[0]:"date"}); d["date"]=pd.to_datetime(d["date"],errors="coerce"); d=d.dropna(subset=["date"]).set_index("date").sort_index()
    d.columns=[str(c).replace("A","",1) if str(c).startswith("A") else str(c) for c in d.columns]
    return d.apply(pd.to_numeric,errors="coerce")
px=pd.concat([load_sheet("kospi"),load_sheet("kosdaq")],axis=1); px=px.loc[:,~px.columns.duplicated()]
ret=px/px.shift(1)-1.0; mkt=ret.mean(axis=1); dates=ret.index
print(f"주가 로드 {px.shape}",flush=True)
def bhar12(sc,evd):
    if sc not in ret.columns: return np.nan
    p0=dates.searchsorted(evd)
    if p0+252>=len(dates) or p0<1: return np.nan
    ri=ret[sc].iloc[p0+1:p0+253]; rm=mkt.iloc[p0+1:p0+253]
    okm=np.isfinite(ri.values)&np.isfinite(rm.values)
    if okm.sum()<200: return np.nan
    return float(np.prod(1+ri.values[okm])-np.prod(1+rm.values[okm]))
M["sc"]=M.cc.map(cc2sc)
M["bhar12"]=[bhar12(r.sc,r.evd) if pd.notna(r.sc) else np.nan for r in M.itertuples()]
bt=M[(M["tl"]==1)].bhar12; br=M[(M["tl"]==0)].bhar12
res["d_bhar"]=dict(all=mci(M.bhar12),tail=mci(bt),rest=mci(br),
                   welch_p=round(float(stats.ttest_ind(bt.dropna(),br.dropna(),equal_var=False).pvalue),4))
bs_=M[M.survival==1].bhar12; bg=M[M.growth_p==1].bhar12
res["d_bhar_purpose"]=dict(survival=mci(bs_),growth=mci(bg),
                           welch_p=round(float(stats.ttest_ind(bs_.dropna(),bg.dropna(),equal_var=False).pvalue),4))
print("(d) BHAR12 전체:",res["d_bhar"]["all"],"| tail vs rest:",res["d_bhar"]["tail"],res["d_bhar"]["rest"],"p=",res["d_bhar"]["welch_p"],flush=True)
print("(d) BHAR12 목적: surv",res["d_bhar_purpose"]["survival"],"grow",res["d_bhar_purpose"]["growth"],"p=",res["d_bhar_purpose"]["welch_p"],flush=True)
json.dump(res,open(f"{OUT}/wp9e_narrative.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp9e.done","w").write("done")
print("\n=== WP9e 완료 ===")
