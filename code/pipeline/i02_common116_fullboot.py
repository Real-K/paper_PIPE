# -*- coding: utf-8 -*-
"""i02 — common 116-firm 표본의 full-design bootstrap (power-rescue 후속 ②, comment2 §5×§6 교차).

왜. comment2 §6에 따라 common 116 표본을 co-primary로 승격 제안했는데, 가장 엄격한 추론
(full-design: 양측 기업 재표본 + 성향·지지·캘리퍼·K50 매칭 복제별 재추정)은 full 표본(wp15b)에만
적용했다. 승격된 증거는 같은 수준의 추론을 통과해야 Table 1 두 열의 방어 수준이 대칭이 된다.

Panel. wp15b 기계 재사용(head exec) — 처치 재표본 풀만 common 116으로 제한. B=1000 · seed 20260904
(wp15b의 20260903과 별도 스트림 — wp15b 검증·사전계산은 head에서 그대로 재수행되고 결정적).

사전 예측 (실행 전 기입).
  p10 −0.2193(군집 CI [−0.4008, −0.0696])과 sev35 +0.1056([0.0366, 0.1789])은 여유가 있어
  full-design에서도 0 제외 유지 예상 → GO. 하나만 유지 → PARTIAL(해당 통계만 co-primary 문안).
  둘 다 0 포함 → KILL(공동주요 승격 철회, 군집부트 결과로만 서술).
  mean·median·p25는 full 표본과 같이 0 포함 예상(주장에 사용하지 않음).

산출: out/I02.json (집계만).
"""
import os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("HARNESS_OUT", "/mnt/c/obsidian/00 Academic Research/paper014-writing-project/shared/outputs/pipe_wp15_2026-09-03/out")
os.environ.setdefault("PROJECT_BASE", "/mnt/c/obsidian/00 Academic Research/paper014-writing-project")
os.environ.setdefault("HARNESS_SEED", "20260904")
from emit_contract import emit, qci

# wp15b head 재사용: ARM·DC·dvec_fast·stats8·obs_d(검증 포함)까지 실행, 부트 루프 직전에서 절단
src = open(os.path.join(HERE, "wp15b_fullboot.py"), encoding="utf-8").read()
mk = src.find("# ── full-design bootstrap ──")
ns = {"__name__": "i02_reuse", "__file__": os.path.join(HERE, "wp15b_fullboot.py")}
exec(compile(src[:src.rfind("\n", 0, mk)], "wp15b(head)", "exec"), ns)
ARM, dvec_fast, stats8, obs_d, NC = ns["ARM"], ns["dvec_fast"], ns["stats8"], ns["obs_d"], ns["NC"]
SHIFTS = ns["SHIFTS"]
RNG = np.random.default_rng(20260904); B = 1000

common = set(obs_d[0].k)
for s in (18, 24, 30, 36): common &= set(obs_d[s].k)
print(f"common firms = {len(common)}", flush=True)
assert len(common) == 116

a0 = obs_d[0][obs_d[0].k.isin(common)].d2.values
b0 = np.concatenate([obs_d[s][obs_d[s].k.isin(common)].d2.values for s in (18, 24, 30, 36)])
obs = stats8(a0, b0)
print("obs:", {k: round(v, 4) for k, v in obs.items()}, flush=True)

cf = np.array(sorted(common))
arm_by_firm = {s: {k: np.where(ARM[s].k.values == k)[0] for k in common if (ARM[s].k.values == k).any()} for s in SHIFTS}
import time; t0 = time.time(); bs = []; nfail = 0
for rep in range(B):
    fs = cf[RNG.integers(0, len(cf), len(cf))]
    cs = RNG.integers(0, NC, NC)
    dd = {}; ok = True
    for s in SHIFTS:
        rows = [arm_by_firm[s][k] for k in fs if k in arm_by_firm[s]]
        rows = np.concatenate(rows) if rows else np.array([], int)
        if len(rows) < 20: ok = False; break
        d = dvec_fast(ARM[s].iloc[rows].reset_index(drop=True), cs)
        d = d[np.isfinite(d)]
        if len(d) < 20: ok = False; break
        dd[s] = d
    if not ok: nfail += 1; continue
    bs.append(stats8(dd[0], np.concatenate([dd[s] for s in (18, 24, 30, 36)])))
    if (rep + 1) % 250 == 0: print(f"  [{rep+1}/{B}] {(time.time()-t0)/60:.1f}분", flush=True)

est = {}
for k in obs:
    v = [x[k] for x in bs]; ci = qci(v)
    est[k] = dict(obs=round(obs[k], 4), ci=ci, sig=bool(ci[0] > 0 or ci[1] < 0))
est["B_used"] = len(bs); est["n_fail"] = nfail
est["ref_cluster_ci"] = {"p10": [-0.4008, -0.0696], "sev35": [0.0366, 0.1789]}   # wp15 battery common_pooled
for k in ("mean", "median", "p10", "p25", "sev35"):
    print(f"  {k:<7} {est[k]['obs']:+.4f} {est[k]['ci']} {'✓' if est[k]['sig'] else '✗'}", flush=True)

go = est["p10"]["sig"] and est["sev35"]["sig"]
part = est["p10"]["sig"] or est["sev35"]["sig"]
status = "GO" if go else ("PARTIAL" if part else "KILL")
verdict = (f"common116 full-design(B={len(bs)}): p10 {est['p10']['obs']}{est['p10']['ci']}"
           f"{'✓' if est['p10']['sig'] else '✗'} · sev35 {est['sev35']['obs']}{est['sev35']['ci']}"
           f"{'✓' if est['sev35']['sig'] else '✗'} · median {est['median']['obs']}{est['median']['ci']}.")
emit("I-02", "common 116 표본 full-design bootstrap", status, est,
     prediction="p10·sev35 모두 0 제외 유지 → GO. 하나만 → PARTIAL. 둘 다 0 포함 → KILL(공동주요 승격 철회).",
     verdict=verdict, kill_met=(status == "KILL"), n=116)
