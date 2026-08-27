# -*- coding: utf-8 -*-
"""구(08-23 동결) vs 신(wp13) JSON 수치 전수 비교 — 원고 갱신 대상 식별용."""
import json,os,sys
BASE=os.environ.get("P016_BASE",".") + "/shared/outputs"
NEW=f"{BASE}/pipe_wp13_2026-08-26"
OLD={"wp8b_car.json":"pipe_wp8_2026-08-23","wp8d_trajmatch.json":"pipe_wp8_2026-08-23","wp9c_permutation.json":"pipe_wp9_2026-08-23","wp9e_narrative.json":"pipe_wp9_2026-08-23",
     "wp10c_listed.json":"pipe_wp10_2026-08-23","wp10f.json":"pipe_wp10_2026-08-23","wp10de.json":"pipe_wp10_2026-08-23","wp11d.json":"pipe_wp11_2026-08-23","wp11e.json":"pipe_wp11_2026-08-23",
     "wp11fg.json":"pipe_wp11_2026-08-23","wp7b_quantile.json":"pipe_wp7b_2026-08-23","wp5_main.json":"pipe_wp5_2026-08-22"}
def flat(o,p=""):
    if isinstance(o,dict):
        for k,v in o.items(): yield from flat(v,f"{p}.{k}" if p else k)
    elif isinstance(o,list):
        if len(o)<=12:
            for i,v in enumerate(o): yield from flat(v,f"{p}[{i}]")
        else: yield p+"[len]",len(o)
    else: yield p,o
tol=float(sys.argv[1]) if len(sys.argv)>1 else 1e-9
for f,d in OLD.items():
    po,pn=f"{BASE}/{d}/{f}",f"{NEW}/{f}"
    if not os.path.exists(pn): print(f"## {f}: 신 파일 없음"); continue
    o=dict(flat(json.load(open(po)))); n=dict(flat(json.load(open(pn))))
    ch=[(k,o.get(k),n.get(k)) for k in sorted(set(o)|set(n)) if (k not in o or k not in n or (isinstance(o[k],(int,float)) and isinstance(n[k],(int,float)) and abs(o[k]-n[k])>tol) or (not isinstance(o[k],(int,float)) and o[k]!=n[k]))]
    print(f"## {f}: {len(ch)} 변경 / {len(o)} 항목")
    for k,a,b in ch[:60]: print(f"   {k}: {a} → {b}")
