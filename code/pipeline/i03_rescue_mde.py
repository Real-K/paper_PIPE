# -*- coding: utf-8 -*-
"""i03 — rescue 상호작용 θ의 MDE(80%) (power-rescue 후속 ③, 레버 F22).

왜. wp15 B_rescue에서 θ(Actual×Rescue)는 전 사양에서 CI가 0을 포함했다. 규칙 11에 따라
이것을 "이질성 없음"으로 쓸 수 없고, "not detected"와 "absent"를 구분하려면 이 설계가
어느 크기의 목적별 차이까지 볼 수 있는지(MDE)를 병기해야 한다.

Panel. MDE80 = (z_{0.975}+z_{0.80})·SE(θ) = 2.4865·SE — 양측 5%·검정력 80%.
  FE 사양 4종(공통116/전체 × sev35/sev25)과 분할차(정규근사 SD) 각각.
  기준화: 기저 actual 점프(β)와 대비한 배율.

사전 예측 (실행 전 기입 — 2026-09-04 답변에서 ±14~15pp로 예측했음. 그 예측은 분할차 SD
기준이었고, FE 사양의 SE(≈0.074)로는 ±18~19pp가 나올 것으로 정정 예상).

산출: out/I03.json. 결정적(신규 추정 없음 — wp15 부트 SD/SE 재사용). status=OK(진단).
"""
import os, sys, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("HARNESS_OUT", "/mnt/c/obsidian/00 Academic Research/paper014-writing-project/shared/outputs/pipe_wp15_2026-09-03/out")
os.environ.setdefault("PROJECT_BASE", "/mnt/c/obsidian/00 Academic Research/paper014-writing-project")
from emit_contract import emit

O15 = "/mnt/c/obsidian/00 Academic Research/paper014-writing-project/shared/outputs/pipe_wp15_2026-09-03"
B = json.load(open(f"{O15}/wp15_comment2_battery.json"))["runs"]["B_rescue"]
Z = 1.959964 + 0.841621                      # 2.4865 — 양측 5% · 80% 검정력

est = {}
for k in ("common116_sev35", "common116_sev25", "full_unbal_sev35", "full_unbal_sev25"):
    th = B[k]["act_x_rescue"]; be = B[k]["actual"]
    mde = Z * th["se"]
    est[k] = dict(theta=th["b"], se=th["se"], mde80=round(mde, 4),
                  beta_actual=be["b"], mde_over_beta=round(mde / abs(be["b"]), 2))
# 분할차(정규근사): CI 폭에서 SD 복원
d = B["split_diff_sev35"]; sd = (d["ci"][1] - d["ci"][0]) / (2 * 1.959964)
est["split_diff_sev35"] = dict(diff=d["diff"], sd=round(sd, 4), mde80=round(Z * sd, 4))

for k, v in est.items():
    print(f"  {k:<22} MDE80 ±{v['mde80']:.4f}" + (f" (기저 점프의 {v['mde_over_beta']}배)" if "mde_over_beta" in v else ""))

m_fe = est["common116_sev35"]["mde80"]; m_sp = est["split_diff_sev35"]["mde80"]
verdict = (f"sev35 기준 감지가능 최소 이질성: FE 사양 ±{m_fe:.3f}({m_fe*100:.1f}pp, 기저 점프 "
           f"{est['common116_sev35']['beta_actual']:+.3f}의 {est['common116_sev35']['mde_over_beta']}배) · "
           f"분할차 ±{m_sp:.3f}({m_sp*100:.1f}pp). 이 설계는 목적별 차이가 기저 점프 크기 수준이어도 "
           f"검출을 보장하지 못한다 — 'purpose는 moderator로 판정 불가'가 정확한 서술이며 '무이질성'은 금지.")
emit("I-03", "rescue 상호작용 θ의 MDE(80%)", "OK", est,
     prediction="±14~15pp(분할차 기준, 09-04 답변)로 예측했으나 FE SE(0.074)로는 ±18~19pp 정정 예상.",
     verdict=verdict, kill_met=False, n=B["rescue_coverage"]["n_primary"])
