# WP13 재실행 사본 (2026-08-26): 정규화 마스터(382 dated)로 동일 코드 재실행. 원본 wp10de_falsification.py · 출력 폴더만 pipe_wp13_2026-08-26 으로 치환.
# -*- coding: utf-8 -*-
"""P-016 WP10de — 식별 referee fix 2·3 잔여.
(d1) placebo-in-time: 처치기업 pseudo-event(e−24)에서 동일 추정기(avg7-12/base12/k50, 상장풀) → mean·p10/p25가 null 범위인지.
(d2) 사전 downside-dispersion 진단: 처치 vs 매칭대조의 pre 12m 월간 log변화 p10 대조(distress-선택 스토리 검사).
(e) CAR 통제회귀: car11 ~ survival + stake + log(1+dealsize) + logsize + kosdaq + yearFE (HC1).
산출: shared/outputs/pipe_wp13_2026-08-26/wp10de.json
"""
import os,json,csv,re,warnings; warnings.filterwarnings("ignore")
import numpy as np,pandas as pd
from scipy import stats
import statsmodels.api as sm
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
RE=f"{BASE}/shared/outputs/pipe_r1_reextract_2026-08-22"
OUT=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"
RNG=np.random.default_rng(20260823)
# ---- 상장 풀 (wp10c와 동일 구축) ----
listed=set()
with open(f"{BASE}/PI/drops/재무데이터_2009_2025_통합.csv",encoding='utf-8') as f:
    rd=csv.reader(f); next(rd)
    for row in rd:
        if len(row)<6: continue
        if re.match(r'^A\d{6}$',row[0].lstrip('﻿')):
            bn=re.sub(r'\D','',row[5]).zfill(10)
            if len(bn)==10 and bn!="0000000000": listed.add(bn)
nps=pd.read_parquet(f"{BASE}/shared/data/processed/nps_monthly_matched_v2.parquet",columns=["bn10","data_ym","가입자수","업종","시도"])
nps["ym"]=pd.PeriodIndex(nps["data_ym"],freq="M"); nps["le"]=np.log1p(nps["가입자수"].astype(float))
months=pd.period_range(nps.ym.min(),nps.ym.max(),freq="M"); mi={m:j for j,m in enumerate(months)}; NM=len(months)
piv=nps.pivot_table(index="bn10",columns="ym",values="le",aggfunc="mean").reindex(columns=months)
idx=list(piv.index); firm_ix={b:i for i,b in enumerate(idx)}; LE=piv.to_numpy(float)
firm_ind=nps.groupby("bn10")["업종"].agg(lambda s:str(s.iloc[0])[:2]); firm_sido=nps.groupby("bn10")["시도"].agg(lambda s:str(s.iloc[0]))
firm_med=np.nanmedian(np.where(np.isfinite(LE),LE,np.nan),axis=1)
pb=pd.read_csv(f"{BASE}/shared/data/processed/pitchbook_all_status_v1.csv",dtype=str)
pb["k"]=pb["bn"].astype(str).str.replace(r'\D','',regex=True).str.zfill(10)
pbbn=set(pb["k"].dropna())
T=pd.read_csv(f"{RE}/treatment_master_v2.csv",dtype=str); T["k"]=T["k"].str.replace(r'\D','',regex=True).str.zfill(10)
T=T[pd.to_numeric(T.event_dt.astype(str).str[:4],errors="coerce").between(2015,2025)]   # 표본기간 2015–2025(원고 명시). 날짜 정규화로 유입된 2010–2014·2026 이벤트 제외 — WP13, 2026-08-27
T["ev"]=pd.to_datetime(T["event_dt"],errors="coerce").dt.to_period("M"); T=T.dropna(subset=["ev"]).drop_duplicates("k"); tb=set(T.k)
T=T[T.k.isin({l.strip() for l in open(f"{BASE}/shared/outputs/pipe_wp13_2026-08-26/emp_primary_k.txt") if l.strip()})]  # WP13: 고정 1차표본(210)
def cap(s): return 1.0 if str(s) in ("11","41","28") else 0.0
def man(i):
    try: return 1.0 if 10<=int(i)<=34 else 0.0
    except: return 0.0
def g12(r): d=r[12:]-r[:-12]; return d[np.isfinite(d)]
_cl=set(pd.read_csv(f"{BASE}/shared/outputs/pipe_wp13_2026-08-26/controls_clean.csv",dtype=str).query("third_hist=='False'").bn.str.replace(r"\D","",regex=True).str.zfill(10))  # WP13: clean pool 통일(C-A5)
ctrl_bn=[b for b in idx if (b in listed) and (b not in pbbn) and (b not in tb)]
ctrl_bn=[b for b in ctrl_bn if b in _cl]
crows=np.array([firm_ix[b] for b in ctrl_bn])
cpg=np.array([np.nanmean(g12(LE[r])) if g12(LE[r]).size else np.nan for r in crows]); cls=firm_med[crows]
okc=np.isfinite(cls)&np.isfinite(cpg); crows=crows[okc]; cls=cls[okc]; cpg=cpg[okc]
ccap=np.array([cap(firm_sido.get(idx[r],"0")) for r in crows]); cman=np.array([man(firm_ind.get(idx[r],"99")) for r in crows])
Xc=np.column_stack([cls,cls**2,cpg,ccap,cman])
def build(df,shift):
    rec=[]
    for r in df.itertuples():
        if r.k not in firm_ix: continue
        fi=firm_ix[r.k]; e0=mi.get(r.ev)
        if e0 is None: continue
        e=e0-shift
        if e-13<0 or e+12>=NM: continue
        row=LE[fi]
        if not(np.isfinite(row[e-1]) and np.isfinite(row[e-13])): continue
        pre=[e-j for j in range(1,4)]
        if sum(np.isfinite(row[i]) for i in pre)<3: continue
        if sum(np.isfinite(row[e+j]) for j in range(1,13))<3: continue
        rec.append(dict(k=r.k,fi=fi,e=e,logsize=np.nanmean([row[i] for i in pre]),pregrowth=row[e-1]-row[e-13],cap=cap(firm_sido.get(r.k,"0")),man=man(firm_ind.get(r.k,"99"))))
    return pd.DataFrame(rec)
def run_att(Tm):
    Xt=np.column_stack([Tm.logsize,Tm.logsize**2,Tm.pregrowth,Tm.cap,Tm.man])
    X=np.vstack([Xt,Xc]); y=np.r_[np.ones(len(Xt)),np.zeros(len(Xc))]; Xs=(X-X.mean(0))/X.std(0)
    lgt=sm.Logit(y,sm.add_constant(Xs)).fit(disp=0); xb=np.asarray(lgt.predict(sm.add_constant(Xs),linear=True))
    xbt=xb[:len(Xt)]; xbc=xb[len(Xt):]
    lo,hi=xbt.min(),xbt.max(); supp=(xbc>=lo)&(xbc<=hi); CSr=crows[supp]; xbcs=xbc[supp]; calp=0.2*np.std(xb); K=50
    o=np.argsort(xbcs); XS=xbcs[o]; CS=CSr[o]
    def knn(xi):
        p=np.searchsorted(XS,xi); cand=list(range(max(0,p-K-2),min(len(XS),p+K+2))); dd=np.abs(XS[cand]-xi); sel=np.argsort(dd)[:K]
        return [CS[cand[s]] for s in sel if dd[s]<=calp]
    D=np.full(len(Tm),np.nan); PRE_CH=[[],[]]  # treated, control 월간변화 pre 풀
    for ii,r in enumerate(Tm.itertuples()):
        m=knn(xbt[ii])
        if not m: continue
        e=r.e; bc=list(range(e-12,e)); bt_=np.nanmean(LE[r.fi,bc])
        if np.sum(np.isfinite(LE[r.fi,bc]))<6 or not np.isfinite(bt_): continue
        # pre 월간 변화 수집 (d2)
        ch=np.diff(LE[r.fi,bc]); PRE_CH[0].extend(ch[np.isfinite(ch)])
        pj=list(range(e+7,e+13)); v=LE[r.fi,pj]
        if np.sum(np.isfinite(v))<3: continue
        dc=[]
        for c in m:
            cb=np.nanmean(LE[c,bc]); cv=LE[c,pj]
            if np.isfinite(cb) and np.sum(np.isfinite(cv))>=3:
                dc.append(np.nanmean(cv)-cb)
                cch=np.diff(LE[c,bc]); PRE_CH[1].extend(cch[np.isfinite(cch)])
        if len(dc)<3: continue
        D[ii]=(np.nanmean(v)-bt_)-np.mean(dc)
    return D,PRE_CH
def bci(vec,fn=np.nanmean,B=2000):
    v=vec[np.isfinite(vec)]; n=len(v)
    bs=np.array([fn(v[RNG.integers(0,n,n)]) for _ in range(B)])
    return round(float(fn(v)),4),[round(float(np.percentile(bs,2.5)),4),round(float(np.percentile(bs,97.5)),4)],n
res={}
# (d1) placebo-in-time
Tp=build(T,24); Dp,_=run_att(Tp)
pm,pci,pn=bci(Dp)
qp={q:round(float(np.percentile(Dp[np.isfinite(Dp)],q)),4) for q in (10,25,50)}
res["d1_placebo_t24"]=dict(n=pn,mean=pm,ci=pci,p10=qp[10],p25=qp[25],p50=qp[50],
    note="wp10c null 대비: null p10 −0.214[−0.276,−0.165]·p25 −0.102[−0.129,−0.075]. placebo가 null 범위면 통과.")
print("(d1) placebo t−24:",res["d1_placebo_t24"],flush=True)
# (d2) 사전 downside-dispersion: 실제 이벤트 표본
Ta=build(T,0); Da,PRE=run_att(Ta)
tch=np.array(PRE[0]); cch=np.array(PRE[1])
res["d2_pre_downside"]=dict(treated_p10=round(float(np.percentile(tch,10)),4),control_p10=round(float(np.percentile(cch,10)),4),
    treated_p90=round(float(np.percentile(tch,90)),4),control_p90=round(float(np.percentile(cch,90)),4),
    treated_sd=round(float(tch.std()),4),control_sd=round(float(cch.std()),4),
    levene_p=round(float(stats.levene(tch,cch).pvalue),4),
    note="pre 12m 월간 log고용변화 분포 — 처치가 사전부터 좌측꼬리 두꺼우면 distress-선택 신호.")
print("(d2) pre downside:",res["d2_pre_downside"],flush=True)
# (e) CAR 통제회귀
car=pd.read_csv(f"{OUT}/wp10b_car_vw.csv",dtype={"k":str})
stk=pd.read_csv(f"{OUT}/wp10a_stake.csv",dtype={"k":str})
fdp=pd.read_csv(f"{BASE}/shared/outputs/pipe_wp13_2026-08-26/treatment_fdpp.csv",dtype={"k":str})
fdp["k"]=fdp["k"].str.replace(r'\D','',regex=True).str.zfill(10)
pbz=pb[["k","Deal Size"]].copy(); pbz["sz"]=pd.to_numeric(pbz["Deal Size"],errors="coerce"); pbz=pbz.groupby("k",as_index=False).sz.max()
Tsz=T[["k","cc","ev"]].merge(car,on="k").merge(stk[["k","stake"]],on="k",how="left").merge(pbz,on="k",how="left")
Tsz["survival"]=Tsz.get("survival")
# logsize·kosdaq·year 부착
Tsz["fi"]=Tsz.k.map(firm_ix)
Tsz=Tsz.dropna(subset=["fi"]); Tsz["fi"]=Tsz.fi.astype(int)
Tsz["logsize"]=[firm_med[f] for f in Tsz.fi]
import xml.etree.ElementTree as ET
root=ET.parse(f"{BASE}/shared/data/external/dart_auditcover/CORPCODE.xml").getroot()
cc2cls={(li.findtext("corp_code") or "").strip():"" for li in root.iter("list")}
Tsz["year"]=Tsz.ev.astype(str).str[:4].astype(int)
E=Tsz.dropna(subset=["car11"]).copy()
E["survival"]=E["survival"].astype(float) if "survival" in E else np.nan
E=E[np.isfinite(E["survival"])] if E["survival"].notna().any() else E
E["lsz"]=np.log1p(E.sz.fillna(E.sz.median())); E["stake_f"]=E.stake.fillna(E.stake.median())
ydum=pd.get_dummies(E.year,prefix="y",drop_first=True).astype(float)
Xe=sm.add_constant(np.column_stack([E.survival,E.stake_f,E.lsz,E.logsize]+[ydum[c].values for c in ydum.columns]))
ols=sm.OLS(np.asarray(E.car11,float),Xe).fit(cov_type="HC1")
P_=np.asarray(ols.params); SE_=np.asarray(ols.bse); PV_=np.asarray(ols.pvalues)
res["e_car_controls"]=dict(n=int(len(E)),survival_coef=round(float(P_[1]),4),se=round(float(SE_[1]),4),p=round(float(PV_[1]),4),
    controls="stake, log(1+dealsize), logsize(firm), year FE. (mktcap·discount 미보유→한계 명시; kosdaq은 지수프록시에 이미 반영)")
print("(e) CAR 통제회귀 survival coef:",res["e_car_controls"],flush=True)
json.dump(res,open(f"{OUT}/wp10de.json","w"),ensure_ascii=False,indent=1)
open(f"{OUT}/wp10de.done","w").write("done")
print("\n=== WP10de 완료 ===")
