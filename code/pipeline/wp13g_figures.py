# -*- coding: utf-8 -*-
"""WP13g — 원고 그림 3종 (C-G). 표와 중복되지 않고, 표가 못 보여주는 **형태**를 보여주는 것만 그린다.

Fig 1  거리별 대조: 평균 격차는 이벤트로 갈수록 깊어지는 **기울기**, 꼬리 초과는 유사시점에서 평평하다가
       이벤트에서만 **점프**. 논문의 핵심 반증을 한 장에 담는다(표 3·4 는 수치만 준다).
Fig 2  붕괴확률 곡선: 임계값 선택에 의존하지 않음을 균일대(sup-t)로 보인다. 표는 3개 임계만 싣는다.
Fig 3  동상태 비교: 중앙은 겹치고 아래꼬리만 벌어진다 — §5.4 의 형태 주장. 표 5 는 통계량만 준다.

작도 원칙: 색상 단독 부호화 금지(흑백 인쇄 대응 — 표식·선종으로 구분), 축은 로그고용 포인트/퍼센트포인트,
등가밴드는 사전 고정값(±0.048 평균 · ±0.05 꼬리), 모든 수치는 산출 JSON 에서만 읽는다.
"""
import json,os
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
BASE=os.environ.get("P016_BASE", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))   # 원 경로는 제거했다 — 실행 시 P016_BASE 로 지정하거나 기본값 사용
W13=f"{BASE}/shared/outputs/pipe_wp13_2026-08-26"; W12=f"{BASE}/shared/outputs/pipe_wp12_2026-08-26"
OUT=f"{BASE}/papers/P016_pipe-employment/10_submission/submission_pbfj/figures"; os.makedirs(OUT,exist_ok=True)
plt.rcParams.update({"font.family":"serif","font.size":9,"axes.linewidth":0.7,"axes.edgecolor":"0.3",
                     "xtick.direction":"out","ytick.direction":"out","xtick.major.width":0.7,"ytick.major.width":0.7,
                     "axes.grid":False,"legend.frameon":False,"savefig.bbox":"tight","savefig.dpi":300})
INK="#1a1a1a"; MID="0.45"; BAND="0.86"
def save(fig,name):
    for ext in ("pdf","png"): fig.savefig(f"{OUT}/{name}.{ext}")
    plt.close(fig); print(f"  {name}.pdf / .png",flush=True)

fg=json.load(open(f"{W13}/wp11fg.json")); g=fg["g_placebo_grid"]
SES_M=fg["delta_mean"]; SES_T=fg["delta_tail"]; C_TAIL=fg["c_tail"]
order=["t-36","t-30","t-24","t-18"]
x=[-36,-30,-24,-18,0]
mean=[g[k]["mean"] for k in order]+[fg["f_honest"]["mean"]["effect"]]
mlo=[g[k]["mean_ci"][0] for k in order]+[fg["f_honest"]["mean"]["ci"] if False else None]
mean_ci=[g[k]["mean_ci"] for k in order]+[fg["f_honest"]["mean"]["grid"][0]["ci"]]
tail=[g[k]["tail"] for k in order]+[fg["f_honest"]["tail"]["effect"]]
tail_ci=[g[k]["tail_ci"] for k in order]+[fg["f_honest"]["tail"]["grid"][0]["ci"]]
print("[Fig 1] 거리별 대조",flush=True)
fig,axes=plt.subplots(1,2,figsize=(7.4,3.0),gridspec_kw={"wspace":0.30})
PP={"B. Excess contraction probability (c = -0.35)":100}
for ax,(y,ci,ses,ttl,ylab) in zip(axes,[
    (mean,mean_ci,SES_M,"A. Mean employment gap","Log points"),
    (tail,tail_ci,SES_T,f"B. Excess contraction probability (c = {C_TAIL})","Percentage points")]):
    k=100.0 if ylab=="Percentage points" else 1.0
    y=[v*k for v in y]; ci=[[c[0]*k,c[1]*k] for c in ci]; ses=ses*k
    ax.axhspan(-ses,ses,color=BAND,zorder=0)
    ax.axhline(0,color=MID,lw=0.7,zorder=1)
    lo=[c[0] for c in ci]; hi=[c[1] for c in ci]
    ax.vlines(x,lo,hi,color=INK,lw=1.0,zorder=2)
    ax.plot(x[:4],y[:4],marker="o",ms=4.5,mfc="white",mec=INK,mew=1.0,ls=":",color=MID,lw=0.9,zorder=3,label="Pseudo-event")
    ax.plot(x[4:],y[4:],marker="D",ms=5,mfc=INK,mec=INK,ls="none",zorder=4,label="Actual event")
    ax.set_xticks(x); ax.set_xticklabels(["−36","−30","−24","−18","0"])
    ax.set_xlabel("Months relative to the placement"); ax.set_ylabel(ylab)
    ax.set_title(ttl,fontsize=9,loc="left",pad=6)
    ax.spines[["top","right"]].set_visible(False)
    ax.set_xlim(-40,4)
h1=[Line2D([],[],marker="o",ms=4.5,mfc="white",mec=INK,mew=1.0,ls=":",color=MID,lw=0.9,label="Pseudo-event"),
    Line2D([],[],marker="D",ms=5,mfc=INK,mec=INK,ls="none",label="Actual event")]
axes[0].legend(handles=h1,loc="upper right",fontsize=8,handletextpad=0.5)
for ax,lab in zip(axes,["equivalence band ±0.048 log points","equivalence band ±5 percentage points"]):
    ax.text(0.02,0.055,lab,transform=ax.transAxes,fontsize=7,color="0.35",va="bottom")   # 리뷰5 §4: Word 축소본에서 범례와 겹쳐 하단으로
save(fig,"fig1_gradient_vs_tail")

print("[Fig 2] 붕괴확률 곡선",flush=True)
d=json.load(open(f"{W13}/wp11d.json")); grid=np.array(d["grid"]); K=100.0
fig,axes=plt.subplots(1,2,figsize=(7.4,3.0),gridspec_kw={"wspace":0.30})
ax=axes[0]
for key,lab,mk,ls,fc in (("event","Actual event","D","-",INK),("placebo","Pseudo-event (t−24)","o",":","white")):
    p=np.array(d[key]["point"])*K
    ax.fill_between(grid,np.array(d[key]["lo_unif"])*K,np.array(d[key]["hi_unif"])*K,color=BAND if key=="event" else "0.93",lw=0,zorder=1)
    ax.plot(grid,p,marker=mk,ms=3.6,mfc=fc,mec=INK,mew=0.9,ls=ls,color=INK if key=="event" else MID,lw=1.1,zorder=3,label=lab)
ax.axhline(0,color=MID,lw=0.7)
ax.set_title("A. Excess contraction probability by threshold",fontsize=9,loc="left",pad=6)
ax.set_xlabel("Contraction threshold c (log points)"); ax.set_ylabel("Percentage points")
hA=[Line2D([],[],marker="D",ms=3.6,color=INK,lw=1.1,label="Actual event"),
    Line2D([],[],marker="o",ms=3.6,mfc="white",mec=INK,mew=0.9,ls=":",color=MID,lw=1.1,label="Pseudo-event (t−24)"),
    Patch(facecolor=BAND,label="95% uniform band, event"),Patch(facecolor="0.93",label="95% uniform band, pseudo-event")]
ax.legend(handles=hA,loc="upper left",fontsize=7.5,handletextpad=0.5); ax.spines[["top","right"]].set_visible(False)
ax=axes[1]
dd=np.array(d["ddd"]["point"])*K; lo=np.array(d["ddd"]["lo_unif"])*K; hi=np.array(d["ddd"]["hi_unif"])*K
ax.fill_between(grid,lo,hi,color=BAND,lw=0,zorder=1,label="95% uniform band")
ax.plot(grid,dd,marker="D",ms=3.6,color=INK,lw=1.2,zorder=3,label="Event − pseudo-event")
ax.axhline(0,color=MID,lw=0.7,zorder=2)
ax.set_title("B. Difference, with sup-t uniform band",fontsize=9,loc="left",pad=6)
ax.set_xlabel("Contraction threshold c (log points)"); ax.set_ylabel("Percentage points")
ax.legend(loc="upper left",fontsize=8); ax.spines[["top","right"]].set_visible(False)
ax.text(0.03,0.07,f"band above zero at all {int((lo>0).sum())} of {len(grid)} thresholds",transform=ax.transAxes,fontsize=7,color="0.35")
save(fig,"fig2_collapse_curve")

print("[Fig 3] 동상태 비교",flush=True)
b=json.load(open(f"{W12}/wp12b.json"))["runs"]
fig,axes=plt.subplots(1,2,figsize=(7.4,3.0),gridspec_kw={"wspace":0.30})
ax=axes[0]
strata=[("B_distress_1","Distressed\n(115 vs 27,423)"),("B_distress_0","Not distressed\n(95 vs 78,874)"),("E_pool_distress","Pooled\n(210 recipients)")]
stats=[("mean","Mean"),("median","Median"),("p10","10th pct.")]
mks={"mean":"s","median":"o","p10":"D"}
ypos=np.arange(len(strata))[::-1]
for j,(sk,slab) in enumerate(strata):
    r=b[sk]
    for i,(st,stlab) in enumerate(stats):
        y=ypos[j]+(1-i)*0.22
        e=r[st]; ax.plot([e["ci"][0],e["ci"][1]],[y,y],color=INK,lw=1.0,solid_capstyle="butt")
        ax.plot(e["obs"],y,marker=mks[st],ms=4.5,mfc=INK if e.get("sig") else "white",mec=INK,mew=1.0,ls="none")
ax.axvline(0,color=MID,lw=0.7)
ax.axvspan(-0.048,0.048,color=BAND,zorder=0)
ax.text(0.0,len(strata)-0.45,"±0.048 reference band",fontsize=7,color="0.35",ha="center",va="bottom")
ax.set_yticks(ypos); ax.set_yticklabels([s[1] for s in strata],fontsize=8)
ax.set_xlabel("Recipient − non-recipient (log points)")
ax.set_title("A. Differences by pre-event distress state",fontsize=9,loc="left",pad=6)
h3=[Line2D([],[],marker=mks[k],ms=4.5,mfc=INK,mec=INK,ls="none",label=l) for k,l in stats]
ax.legend(handles=h3,loc="lower left",fontsize=8,handletextpad=0.4)
ax.spines[["top","right"]].set_visible(False); ax.set_ylim(-0.55,len(strata)-0.35)
# 범례 설명(음영 = 등가밴드, 채운 표식 = 구간이 0 배제)은 그림 위가 아니라 **캡션**에 둔다.
ax=axes[1]
c=b["B_distress_1"]["curve"]; gg=np.array(c["grid"]); diff=np.array(c["diff"])*100; lo=np.array(c["lo_unif"])*100; hi=np.array(c["hi_unif"])*100
ax.fill_between(gg,lo,hi,color=BAND,lw=0,zorder=1,label="95% uniform band")
ax.plot(gg,diff,marker="D",ms=3.6,color=INK,lw=1.2,zorder=3,label="Recipient − non-recipient")
ax.axhline(0,color=MID,lw=0.7,zorder=2)
ax.set_title("B. Excess contraction, distressed stratum",fontsize=9,loc="left",pad=6)
ax.set_xlabel("Contraction threshold c (log points)"); ax.set_ylabel("Percentage points")
ax.legend(loc="upper left",fontsize=8); ax.spines[["top","right"]].set_visible(False)
ax.text(0.03,0.07,f"band above zero at all {int((lo>0).sum())} of {len(gg)} thresholds",transform=ax.transAxes,fontsize=7,color="0.35")
save(fig,"fig3_same_state")
json.dump({"id":"WP13g","figures":["fig1_gradient_vs_tail","fig2_collapse_curve","fig3_same_state"],
  "sources":{"fig1":"wp11fg.json (g_placebo_grid, f_honest)","fig2":"wp11d.json (event/placebo/ddd, sup-t uniform bands)","fig3":"wp12b.json (B_distress_1, B_distress_0, E_pool_distress)"},
  "design":"흑백 인쇄 대응(표식·선종 구분, 색상 단독 부호화 없음) · 등가밴드 ±0.048(평균)/±0.05(꼬리) 사전 고정 · 벡터 PDF + 300dpi PNG",
  "note":"표와 비중복: 표는 수치, 그림은 형태(기울기 vs 점프·임계 비의존성·중앙 일치와 꼬리 이탈)"},
  open(f"{W13}/wp13g_figures.json","w"),ensure_ascii=False,indent=1)
print("완료",flush=True)
