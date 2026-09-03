# -*- coding: utf-8 -*-
"""하네스 산출 계약. 모든 분석 스크립트가 같은 모양의 JSON 을 남기게 한다 — 원장·검증기·복제 저장소가 이 모양을 전제한다.
사용: from emit_contract import emit, sha16, qci
      emit("I-12", "제목", "GO|PARTIAL|KILL|OK", {...estimates...}, prediction="검정 전 예측", verdict="한 줄 판정", kill_met=False, n=286)
"""
import os, json, time, hashlib, inspect
import numpy as np
_T0 = time.time()
OUT = os.environ.get("HARNESS_OUT", os.path.join(os.getcwd(), "out"))
BASE = os.environ.get("PROJECT_BASE", os.getcwd())
SEED = int(os.environ.get("HARNESS_SEED", "42"))
def sha16(path):
    with open(path, "rb") as f: return hashlib.sha256(f.read()).hexdigest()[:16]
def qci(x, lo=2.5, hi=97.5):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    return [round(float(np.percentile(x, lo)), 4), round(float(np.percentile(x, hi)), 4)]
def emit(iid, title, status, estimates, prediction, verdict, kill_met, n=None, extra=None):
    """표준 산출: out/<ID>.json. 예측(prediction)은 결과를 보기 전에 쓴 문장이어야 한다 — 사후 합리화 방지."""
    src = os.path.abspath(inspect.stack()[1].filename)
    rec = {"id": iid, "title": title, "status": status, "n": n, "estimates": estimates, "prediction": prediction,
           "verdict": verdict, "kill_met": kill_met, "code": os.path.relpath(src, BASE), "sha256_16": sha16(src),
           "seed": SEED, "runtime_s": round(time.time() - _T0, 1), "date": time.strftime("%Y-%m-%d")}
    if extra: rec.update(extra)
    os.makedirs(OUT, exist_ok=True); p = os.path.join(OUT, iid.replace("-", "") + ".json")
    json.dump(rec, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n{'='*70}\n[{iid}] {status} — {verdict}\n  → {p}\n{'='*70}"); return rec
