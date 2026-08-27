# -*- coding: utf-8 -*-
"""원고 절·부록 참조 검사 — 수치 검증기(wp13_verify_draft.py)가 못 잡는 축을 막는다.

절 재번호는 수치를 바꾸지 않으므로 수치 검증기를 통과한다. 그래서 별도 검사가 필요하다:
본문·보충자료의 모든 `Section N(.M)` / `Appendix X` 참조가 **실제로 존재하는 제목**을 가리키는지 확인한다.
종료코드 1 = 미해결 참조 존재.
"""
import re,sys,os
BASE=os.environ.get("P016_BASE",".") + "/papers/P016_pipe-employment/10_submission/submission_pbfj"
M=f"{BASE}/PBFJ_manuscript_anonymized.md"; S=f"{BASE}/PBFJ_online_supplement.md"
ms=open(M,encoding="utf-8").read(); ss=open(S,encoding="utf-8").read()
secs=set(); 
for m in re.finditer(r"^#{2,3} (\d+(?:\.\d+)?)\.? ",ms,flags=re.M):
    secs.add(m.group(1))
    if "." in m.group(1): secs.add(m.group(1).split(".")[0])
apps={m.group(1) for m in re.finditer(r"^## Appendix ([A-Z])\.",ss,flags=re.M)}
print(f"정의된 절 {sorted(secs, key=lambda x:[int(p) for p in x.split('.')])}")
print(f"정의된 부록 {sorted(apps)}")
bad=0
for path,txt in ((M,ms),(S,ss)):
    ln={}; 
    for i,l in enumerate(txt.split("\n"),1): ln[i]=l
    for i,l in ln.items():
        if l.startswith("#"): continue
        for m in re.finditer(r"Sections?\s+(\d+(?:\.\d+)?)(?:\s+and\s+(\d+(?:\.\d+)?))?",l):
            for g in (m.group(1),m.group(2)):
                if g and g not in secs:
                    print(f"  ⛔ {os.path.basename(path)} L{i}: Section {g} — 해당 제목 없음"); bad+=1
        for m in re.finditer(r"Appendix ([A-Z])\b",l):
            if m.group(1) not in apps:
                print(f"  ⛔ {os.path.basename(path)} L{i}: Appendix {m.group(1)} — 해당 제목 없음"); bad+=1
print(f"\n미해결 참조 {bad}")
sys.exit(1 if bad else 0)
