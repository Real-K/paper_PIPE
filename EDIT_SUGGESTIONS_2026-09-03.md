# 수정 제안 — FRL comment2 처분 (2026-09-03)

원고·부록 파일은 수정하지 않았다. 아래는 comment2.md의 제안 전건에 대한 위치별 반영 문구와 표 구조다.
신규 수치는 전부 오늘 실행한 `06_code/wp15*.py` → `shared/outputs/pipe_wp15_2026-09-03/*.json`에서 나오며,
복제 저장소 `Real-K/paper_PIPE`의 `notebooks_FRL/03_comment2_FRL.ipynb`에서 재현·검증된다.
기준 원고: `PIPE_paper_0902.docx` + `PIPE_appendix_0902.docx` + `EDIT_SUGGESTIONS_2026-09-02.md` 반영분.

---

## 0. 신규 분석 결과 요약 (comment2 → 분석 매핑)

| comment2 | 분석 | 핵심 결과 |
|---|---|---|
| §4·§6 파이프라인 통일 | wp15 A_canonical | 단일 파이프라인(wp13c 캐시·군집부트 B=4000)에서 severe(≤−0.35) 초과: full **+10.25pp [4.77, 15.76]**, common 116 **+10.56pp [3.66, 17.89]**. clock별 수준: 4.8→5.3→5.6→9.2→**16.7%** |
| §5 full-design bootstrap | wp15b | 매 복제 양측 기업 재표본+로짓·매칭 재추정(B=1000): p10 **−0.2527 [−0.3466, −0.0627]✓** · sev35 **+10.25pp [3.12, 15.50]✓** · sev25/50도 ✓. mean [−0.1046, +0.0132]·p25 [−0.1573, +0.0122]는 0 포함으로 전환(정직 보고). 곡선 균일하한>0: −0.60~−0.30 구간 7/11 |
| §7 rescue 이질성 | wp15 B_rescue | Actual×Rescue(sev35, common 116): **+0.015 [−0.130, +0.161]** — 방향 판정 불가(구간이 넓음). 분할: non-rescue **+13.7pp [5.7, 21.5]✓**, rescue +6.5pp [−0.8, 14.3]. 꼬리 집중은 rescue 분류에 의존하지 않음 |
| §8 control purity | wp15 C_purity + wp15d | stake≥30% 제외(3건): p10 −0.2492✓. ±3d 최대주주변경·경영권 공시 제외(32건): −0.2232✓. 결과창(+13m) ctrlchg는 severe 35건 중 **25건(71%)** 동반 — 사후 결과로 보고(제외는 과잉조건화) |
| §9 CB 1건 제외 | wp15 C_purity | equity-only 209: p10 −0.2527✓ · sev35 +10.28pp✓ — 사실상 불변 |
| §10 payment anchor | wp15c | 납입일 보유 123건: 납입월 anchor p10 **−0.2435 [−0.3631, −0.0312]✓** · sev35 +7.7pp✓ (같은 123의 공시월 anchor: −0.2332✓·+10.3pp✓). 공시월=납입월 59% |
| §11 window 근거 | wp14a(기존) | +1..+6: p10 −0.1417✓·sev +6.3pp✓·median −0.010 ns → +7..+12: −0.2527✓·+10.3pp✓·median ns |
| §13 same-state 균형 | wp15e | entropy balancing(평균+연도+분산 제약): maxSMD 0.123 → **0.0000**. distressed p10 **−0.3376 [−0.4834, −0.1633]✓** · cprob35 +13.6pp✓ · median −0.002 ns — 완전 균형에서도 유지 |
| §14 entity 재구조화 | wp15d | 결과창(−3d..+13m) DART 스크린: reorg 57·해산 4·ctrlchg 69/210. **reorg 제외 후 p10 −0.1369 [−0.2991, −0.0056]✓ · sev35 +6.6pp✓**. reorg+ctrlchg 제외(97건)면 대조 소멸(+0.067 ns) — 본문 아님, 부록에 보고+해석(아래 §8 블록) |
| §17 FRL 인용 | crossref_verify3 | Han·Xiao 2025(FRL 79, 107308) · Liu·Jin·Xu 2024(FRL 70, 106297) · Takahashi·Takaoka 2026(FRL 100, 110028) 서지 확정 |

경제 환산(§12용): −0.35 log points = **−29.5%** · p10 −0.2527 = **−22.3%** · common −0.2193 = **−19.7%** · same-state −0.3414 = **−28.9%**.

---

## 1. 정체성 재구성 — one-line contribution (comment2 §1)

**위치**: Introduction 첫 문단 마지막 문장("Separating those patterns is the object of this paper.") 교체·확장.

> Separating those components is the object of this paper, and the distinction matters beyond this setting: when financing timing is endogenous, a mean post-financing estimate mixes a pre-existing deterioration with an event-localized tail adjustment, and the two occupy different parts of the outcome distribution.

**Conclusion 첫 문단 끝 추가(한 줄 기여문)**:

> Minority recapitalizations occur late in a deteriorating employment path: average relative employment weakens well before financing, whereas severe downside outcomes become unusually concentrated only around the placement window.

**금지**: comment2 §1이 명시하듯 IV·PSM-DID 추가로 causal paper 화하지 말 것. 현 설계의 지적 명료성이 자산.

## 2. "Two clocks" 개념 문단 + state-revealing 문장 (comment2 §2)

**위치**: §3.2 끝("…so the pattern is not an artifact of the changing pseudo-event sample." 뒤) 새 문단.

> These two facts are naturally read as two clocks of adjustment. Firm condition deteriorates gradually, so the average gap opens well before the transaction. The placement itself, however, tends to occur when latent stress, negotiation, or restructuring need reaches a threshold, and around that threshold a subset of firms enters a discrete adjustment regime. The placement is a state-revealing event rather than an exogenous treatment: it occurs when a subset of already-deteriorating firms enters a nonlinear adjustment region, which moves the lower tail while leaving the median nearly unchanged.

(어휘 주의: "caused restructuring" 금지 — 위 문구는 서술적.)

## 3. 파이프라인 통일 (comment2 §4 — 최우선)

문제: severe 초과가 세 값(12.0/11.0/10.2pp)으로 병존 — 각각 t−24 원구축(wp11d)·prediction-benchmark(wp11fg)·pooled(wp13c계). **정본 = pooled pseudo-event 파이프라인(wp13c 캐시 + 기업군집 부트)**로 통일하고, 나머지 두 구축은 부록의 대안 구축으로 강등한다.

정본 estimand(본문 §2 설계 문단이나 §3.2 앞에 1문장):

> The primary tail estimand is Δ_T(c) = Pr(D_{i,0} ≤ c) − Pr(D_{i,pseudo} ≤ c), the difference between actual-event and pooled pseudo-event probabilities of a matched employment outcome no greater than c, with c = −0.35 featured and the full grid reported in the appendix.

**(a) §3.2 threshold 문단 교체.** 현행 "A threshold grid gives a less quantile-specific view. Using t−24 as the pre-event benchmark, … 12.0 percentage points [5.2, 18.8] … adjusted p-value of 0.006 …" 문단을 다음으로 교체:

> A threshold grid gives a less quantile-specific view. Relative to the pooled pseudo-events, the event-minus-pseudo contraction probability is positive at all eleven cutoffs from −0.60 to −0.10. At c = −0.35 the difference is 10.2 percentage points [4.8, 15.8], and a max-t adjustment across the mean, tenth percentile, twenty-fifth percentile, and median concentrates the joint evidence at the tenth percentile (adjusted p = 0.012). A −0.35 log-point relative outcome corresponds to roughly a 30% employment shortfall against the matched benchmark, and the tenth-percentile contrast of −0.253 log points to roughly 22%.
>
> [근거: sev35 +0.1025 [0.0477, 0.1576] = wp15 A_canonical(정본 부트); 11/11 양수·max-t p10 0.0117 = wp14 B_grid vs_pooled]

**(b) Figure 1 재구성(통일 파이프라인 수준 그림).** Panel A·B 모두 wp13c 캐시의 clock별 **수준**으로 다시 그린다(레거시 prediction-benchmark 그림은 부록 B로 이동, 아래 §12).

| Clock | n | Mean matched gap [95% CI] | Pr(D ≤ −0.35) [95% CI] |
|---|---|---|---|
| t−36 | 125 | −0.0058 [−0.0461, +0.0322] | 4.8% [1.6, 8.8] |
| t−30 | 131 | −0.0115 [−0.0435, +0.0220] | 5.3% [1.5, 9.2] |
| t−24 | 142 | −0.0520 [−0.0927, −0.0169] | 5.6% [2.1, 9.9] |
| t−18 | 163 | −0.0576 [−0.1001, −0.0186] | 9.2% [4.9, 13.5] |
| Actual | 210 | −0.0820 [−0.1289, −0.0363] | 16.7% [11.9, 21.4] |

[근거: wp15 E_clock_levels. Panel A 경로는 현행 그림(−0.006/−0.012/−0.052/−0.058/−0.081)과 최대 0.001 차이 — 시각적으로 동일. Panel B는 "excess vs 예측치"가 아니라 "수준"이 되므로 t−18의 9.2%가 드러난다 — 더 정직하고, +1..+6 창 결과(§9 블록)와 일관: 꼬리는 t−18 무렵 나타나기 시작해 placement 창에서 깊어진다.]

**새 caption**:

> Figure 1. Mean matched employment gap and severe-contraction probability across event clocks.
> Notes. Both panels use the same matched-outcome pipeline held fixed while the event clock changes. Panel A reports the mean recipient-minus-matched-control outcome at four pseudo-events and the actual placement. Panel B reports the probability that the matched outcome is no greater than −0.35 log points. Vertical bars are 95% firm-clustered bootstrap intervals. Relative to the four pooled pseudo-dates, the actual-event excess at −0.35 is 10.2 percentage points [4.8, 15.8], and the common 116-firm sample gives 10.6 points [3.7, 17.9].

**(c) Abstract 문장 교체.** "Severe-contraction excesses remain within a ±5-percentage-point band at each pseudo-date and move outside it only at the placement." →

> The probability of a severe relative contraction is 4.8–5.6% at pseudo-dates 36 to 24 months earlier, begins to rise at 18 months, and reaches 16.7% at the placement — an excess of 10.2 percentage points over the pooled pseudo-dates.

**(d) 부록 B.5 재서술.** 첫 문장 "The threshold-grid and max-t calculations use the actual event versus t−24 comparison…"를 다음으로 교체하고, 표 B5는 pooled 기준 grid(wp14 B_grid vs_pooled: −0.60 +5.5pp…−0.35 +10.2 [3.0, 17.6](균일밴드)…−0.10 +4.2pp)로 갱신, t−24·t−36 grid는 "alternative benchmarks" 행으로 유지:

> The featured threshold-grid and max-t calculations use the pooled pseudo-event benchmark, matching the estimand in Table 1. Grids against each single pseudo-date (t−36, t−24, t−18) are reported as alternative benchmarks; all use the same matched-outcome construction and firm-clustered bootstrap.

**(e) 어휘 삭제**: "original placebo-vector construction", "original construction", "common-pipeline implementation details" 등 이력 서술은 부록에서 제거(연구 이력은 replication package가 보존).

**(f) 수치 병존 정리 원칙**: Table 1·B3·B4의 기존 wp13c 수치는 그대로(동일 파이프라인). 신규로 인쇄되는 severe 행·clock 수준·CI는 전부 wp15 A_canonical/E_clock_levels 한 소스에서만 인용.

## 4. Full-design bootstrap (comment2 §5 — 기술 최우선)

**위치**: 부록 B.4 끝에 새 소절 B.4.1(또는 B.9) 추가 + 본문 §2 추론 문장 1개 교체.

**본문 §2** "Formal event-versus-pseudo contrasts pool the four earlier dates and use 4,000 bootstrap replications clustered by recipient." →

> Formal event-versus-pseudo contrasts pool the four earlier dates. Inference uses two schemes: 4,000 bootstrap replications clustered by recipient, and a full-design bootstrap that re-draws recipient and comparison firms separately and re-estimates the propensity model, common support, and matching within every replication, so that matching and weight-estimation uncertainty and the reuse of comparison firms are reflected in the intervals.

**부록 신규 소절(EN)**:

> B.4.1. Full-design bootstrap
> The firm-clustered bootstrap resamples recipients but holds the estimated propensity model, the common-support boundary, and the matched sets fixed, and it does not reflect the reuse of comparison firms across recipients and pseudo-dates. As a stricter scheme, we re-draw the 210 recipients and the comparison pool separately at the firm level in each of 1,000 replications and re-estimate the propensity model, common support, caliper, and nearest-neighbor sets before recomputing every statistic. The tenth-percentile contrast is −0.253 [−0.347, −0.063] and the severe-contraction excess at −0.35 is 10.2 percentage points [3.1, 15.5]; the excesses at −0.25 and −0.50 remain positive as well ([2.4, 17.8] and [2.0, 11.7]). Two weaker margins move: the mean contrast interval becomes [−0.105, +0.013] and the twenty-fifth-percentile interval [−0.157, +0.012], both now covering zero. In the common 116-firm sample the full-design intervals widen enough to cover zero (tenth percentile [−0.306, +0.066]; severe excess [−0.011, +0.135]), so the balanced-sample result is reported as a composition diagnostic under the firm-clustered scheme rather than as co-primary evidence. The uniform band over the threshold grid remains above zero for all cutoffs from −0.60 through −0.30. The paper's tail statements rest on the full-sample tenth percentile and severe-contraction excess, which survive the stricter scheme.

**표 구조 (Table B7 제안)**:

| Statistic | Firm-clustered bootstrap | Full-design bootstrap |
|---|---|---|
| Mean | −0.0481 [−0.1026, +0.0040] | −0.0481 [−0.1046, +0.0132] |
| Median | −0.0036 [−0.0375, +0.0249] | −0.0036 [−0.0465, +0.0335] |
| Tenth percentile | −0.2527 [−0.3713, −0.0953] | −0.2527 [−0.3466, −0.0627] |
| Twenty-fifth percentile | −0.0641 [−0.1576, −0.0001] | −0.0641 [−0.1573, +0.0122] |
| Severe excess at −0.35 | +0.1025 [+0.0477, +0.1576] | +0.1025 [+0.0312, +0.1550] |

Notes 문구: "The full-design bootstrap re-draws recipient and comparison firms separately and re-estimates the propensity model, support, and matches in each replication (1,000 replications). Point estimates are identical by construction; only the intervals differ."

**정직 보고 의무**: p25가 0을 포함하게 되는 변화를 숨기지 말 것(위 문구에 포함됨). 이에 따라 본문 §3.2의 p25 문장("The twenty-fifth percentile lies between them at −0.064 [−0.158, −0.000].")에 다음 반문장 추가 권고: "…, though this margin does not survive the stricter full-design bootstrap reported in Appendix B."

## 5. Common 116-firm sample — 승격 철회, composition 진단으로 유지 (comment2 §6 · **i02 KILL 반영, 2026-09-04**)

⚠️ **2026-09-04 갱신**: comment2 §6은 common 116을 Table 1 co-primary로 승격하라고 권고했고 초판 제안(09-03)도 그랬으나, **후속 하네스 i02(common 116 full-design bootstrap, B=1000)에서 사전 등록한 기각조건이 발동**했다: p10 −0.2193 [−0.3063, +0.0655] · sev35 +0.1056 [−0.0107, +0.1345] — 둘 다 0 포함. 116개 기업 재표본 + 매칭 재추정 하에서는 공동주요 증거로서의 정밀도가 없다. **따라서 Table 1 열 추가(승격)는 하지 않는다.** 현행 구조(B3 표 + §3.2 한 문장)를 유지하고 아래만 반영한다.

**위치 1 — §3.2 문장 교체(승격 없는 버전).** "Restricting the analysis to the 116 recipients … −0.219 [−0.406, −0.071], so the pattern is not an artifact of the changing pseudo-event sample." →

> The full sample carries the paper's precision; the 116 recipients observed at all five dates provide a composition diagnostic: comparing the same eventual recipients with themselves at four earlier clocks, the pooled tenth-percentile contrast is −0.219 [−0.406, −0.071] with a severe-contraction excess of 10.6 percentage points [3.7, 17.9] under the firm-clustered bootstrap. Composition change across clocks does not generate the tail, although this smaller sample loses precision under the stricter full-design scheme reported in Appendix B.

**위치 2 — B.4.1(full-design 소절, 본 문서 §4)에 정직 문장 추가**:

> In the common 116-firm sample the full-design intervals widen enough to cover zero (tenth percentile [−0.306, +0.066]; severe excess [−0.011, +0.135]), so the balanced-sample result is reported as a composition diagnostic under the firm-clustered scheme rather than as co-primary evidence.

**위치 3 — B3 표에 severe 행만 추가(군집부트, 출처 wp15)**: full +0.1025 [+0.0477, +0.1576] · common +0.1056 [+0.0366, +0.1789].

[근거: `out/I02.json` (prediction 선기입 → KILL; 규칙 11·가드레일 7 — KILL은 표현만 바꿔 되살리지 않는다)]

## 6. Rescue-purpose 이질성 (comment2 §7)

**위치**: §3.3 뒤 새 짧은 소절 §3.4(또는 Table 1 Panel C + 본문 한 문단). comment2 §23에 따라 본문 노출은 최소로.

**본문 문단(EN)**:

> A stated financing purpose provides one transaction-level discriminator. Rescue-type purposes (working capital or debt repayment tied to financial-structure improvement) account for 47.6% of the primary sample. Within a firm and clock fixed-effects design on the common event-clock panel, the actual-date jump in severe-contraction probability is +9.8 percentage points [0.1, 19.5]; the additional jump for rescue-purpose placements is +1.5 points with a wide interval [−13.0, +16.1], and the split samples show a significant jump for non-rescue placements (+13.7 points [5.7, 21.5]) alongside a smaller, imprecise one for rescue placements (+6.5 points [−0.8, +14.3]). The event-localized tail is therefore not an artifact of the narrow stated-rescue classification, and the data do not establish purpose as a moderator.

**Table 1 Panel C 구조(선택)**:

| | Actual-date jump (β) | × Rescue (θ) | n (firms) |
|---|---|---|---|
| 1(D ≤ −0.35), common panel | +0.098 [+0.001, +0.195] | +0.015 [−0.130, +0.161] | 580 (116) |
| 1(D ≤ −0.35), full panel | +0.117 [+0.028, +0.207] | −0.016 [−0.138, +0.106] | 771 (210) |
| D (mean), common panel | −0.075 [−0.166, +0.016] | +0.028 [−0.095, +0.151] | 580 (116) |

Notes: "Firm and event-clock fixed effects; standard errors clustered by firm. Rescue is a firm-level stated-purpose indicator absorbed by the firm effects; θ is identified from within-firm variation across clocks."

**어휘 주의(규칙 11)**: θ의 CI가 넓으므로 "no heterogeneity"라고 쓰지 말 것 — "the data do not establish purpose as a moderator"까지만. 이질성 추가 분할(owner/industry/size/…) 금지 — comment2 §7 자신이 specification mining 경고.

**MDE 병기 (i03, 2026-09-04)** — 위 본문 문단 마지막 문장 뒤에 추가:

> The design's minimum detectable interaction at 80% power is roughly ±21 percentage points in the fixed-effects specification (±16 points for the split contrast) — about twice the actual-date jump itself — so the absence of a detected difference bounds neither direction economically.

[근거: `out/I03.json` — MDE80: FE common116 ±0.2076(β의 2.11배)·full ±0.1751·분할차 ±0.1565]

## 7. Minority purity — equity-only·stake·control (comment2 §8·§9)

**(a) 표본 정의(§9).** 본문 §2 "The sample contains 209 paid-in equity allotments and one convertible-bond placement." 뒤에:

> The featured results use the 209 paid-in equity allotments; including the single convertible-bond placement changes nothing visible (tenth-percentile contrast −0.2527 in both samples), and the inclusive sample is retained in the appendix.

Table 1 Notes에 "estimates are unchanged in the 209 equity-only sample (Appendix B)" 1줄. 부록 B.4 끝에 1문장: "Excluding the single convertible-bond placement leaves the pooled contrasts unchanged (tenth percentile −0.2527 [−0.3644, −0.0943]; severe excess +10.3 points [4.8, 15.8])."
— 제목·제도 서술과 "equity minority recapitalization" 정렬 효과(comment2 §9). 210 표기를 유지할 곳: Table A1(표본 흐름), 부록.

**(b) Stake ≥30% 제외(§8).** 부록 A.3 끝에:

> Among primary-sample transactions with a measured stake (106 of 210), three reach 30% and none reach 50%. Excluding the three, the pooled tenth-percentile contrast is −0.249 [−0.375, −0.092] and the severe-contraction excess 9.6 points [3.9, 15.1].

**(c) Announcement-window control-change 제외(§8).** 부록 B.7(동시공시) 끝에:

> Thirty-two placements coincide with a largest-shareholder-change or management-control filing within three days of the announcement. Excluding them, the tenth-percentile contrast is −0.223 [−0.358, −0.071] and the severe excess 9.8 points [3.9, 16.1]. The "minority recapitalization" label, which Appendix A.3 already scopes to the observed allotment, is therefore not carried by transactions with contemporaneous control activity.

**(d) 결과창 control-change — 새 발견의 보고(과잉조건화 주의).** 아래 §8 블록의 D.3에 함께 서술.

**한계 정직 서술**: allottee의 기존 보유·특수관계 여부는 관측 불가(A.3 현행 문구 유지). PitchBook lead-type은 210 중 31건 NO_DATA — allottee identity 기반 정밀 분류는 이번 회차 범위 밖으로 명시.

## 8. Entity-restructuring 스크린 (comment2 §14) — 신규 부록 D.3

**위치**: 부록 D.2 뒤 새 소절. (09-02 제안의 LOO 소절이 D.3로 들어갔다면 이 소절은 D.4로.)

**EN 초안**:

> D.3. Entity-restructuring screen
> Because NPS employment is recorded at the legal-entity registration number, a merger, division, or business transfer can reduce measured employment without an equivalent economy-wide job loss. A DART screen over each recipient's window from three days before the announcement through thirteen months after flags 57 of 210 recipients with a merger, division, business- or asset-transfer, or share-exchange filing. Excluding all 57, the pooled tenth-percentile contrast is −0.137 [−0.299, −0.006] and the severe-contraction excess 6.6 percentage points [0.7, 13.0]; adding the four dissolution-related filers changes little (−0.138 [−0.304, −0.007]). The excess tail is therefore not an artifact of legal-entity reorganizations alone, although reorganization events account for part of its magnitude: 14 of the 35 severe relative contractions carry such a filing, against 24.6% of non-severe recipients.
> Control-change filings behave differently. Sixty-nine recipients have a largest-shareholder-change or management-control filing in the same window, and these filings concentrate sharply in the severe tail (25 of 35 severe cases, versus 25.1% of the rest). A control change does not move workers off the entity's registration, so it is not a measurement artifact; it is part of the post-placement adjustment the paper measures. Excluding these firms as well removes 97 of 210 recipients and, mechanically, the tail contrast (+0.07 [−0.11, +0.15]). We report this as a conditioning diagnostic rather than a robustness requirement: dropping firms because severe adjustment materialized conditions the sample on the outcome. Read jointly, severe post-placement contractions frequently coincide with subsequent control transitions — consistent with the placement marking entry into a restructuring region — while the measurement-specific screen (reorganization filings) leaves the tail intact.

**타이밍 감사 문장 추가 (i01, 2026-09-04)** — 위 EN 초안 첫 문단의 "…against 24.6% of non-severe recipients." 뒤에:

> A filing-level timing audit sharpens the reading: among the 14 severe cases with a reorganization filing, the first own-firm employment crossing of −0.35 log points precedes the filing in six cases and follows it in seven, so administrative reallocation may contribute to measured severity in up to half of the flagged severe cases — which is why the reorganization-excluded contrast above is the appropriate conservative benchmark. Control-change filings, by contrast, cluster at the placement month itself (16 of 25 within two months of the announcement), well before the employment crossing accumulates.

[근거: `out/I01.json` — reorg drop_first 6/same 1/filing_first 7; ctrl 공시 오프셋 25건 중 16건이 m≤2; own 교차는 중위 +5개월. PARTIAL(예측 선기입: 어느 쪽도 60% 우세 아님)]

**표 구조 (Table D2 제안)**:

| Exclusion (window: −3d to +13m) | Dropped | N | Tenth percentile [95% CI] | Severe excess at −0.35 |
|---|---|---|---|---|
| None (primary) | 0 | 210 | −0.2527 [−0.3647, −0.0923] | +10.2 pp [4.8, 15.8] |
| Reorganization filings | 57 | 153 | −0.1369 [−0.2991, −0.0056] | +6.6 pp [0.7, 13.0] |
| Reorganization + dissolution | 59 | 151 | −0.1380 [−0.3038, −0.0074] | +6.7 pp [0.6, 13.1] |
| + Control-change filings (diagnostic) | 97 | 113 | +0.0674 [−0.1136, +0.1490] | −1.4 pp [−6.6, +4.0] |

Notes: "Firms are removed from both the actual-event and pseudo-event arms. The last row conditions on a post-placement outcome and is reported as a diagnostic, not a robustness check."

**D.2 연결 문장**: D.2 끝에 "Appendix D.3 quantifies this concern with a filing-based reorganization screen." 추가.

**NPS↔DART 종업원수 외부검증(comment2 §14 후반)**: 현재 데이터 빌드에 사업보고서 종업원수 필드가 수집되어 있지 않아 이번 회차에서는 실행하지 않음(선택 항목). 후속 수집 시 검증표 1개(상관·중앙절대편차)로 추가 가능.

## 9. +7..+12 창 근거와 timing decomposition (comment2 §11)

**(a) §2 outcome 정의 문단 끝에 근거 문장**:

> Employment adjustment begins in the first six post-placement months and deepens in the second six; the primary measure averages months +7 to +12 to reduce month-specific payroll noise and to capture the persistent post-placement employment level rather than the transition into it.

**(b) §3.2에 3줄 분해(문단 형태)**:

> The timing decomposition sharpens this: over months +1 to +6 the tenth-percentile contrast is already −0.142 [−0.202, −0.055] with a severe excess of 6.3 points; over months +7 to +12 it deepens to −0.253 with 10.3 points; the median is near zero in both windows. The tail emerges early and deepens, while the center never moves.

**(c) t−18이 가장 가까운 pseudo인 이유(§2 pseudo 문단 끝)**:

> The nearest pseudo-date is t−18 because a t−12 clock would place its +7 to +12 outcome window inside the actual financing window; t−18 is the closest clock whose outcome window ends before the placement.

## 10. 용어 분리 + 경제 환산 (comment2 §12)

- 매칭 설계: **"severe relative contraction"** (또는 "severe employment underperformance") — §3.2·Figure 1·Table 1 Panel A·부록 B.
- 자기(same-state) 설계: **"severe contraction"** — §3.3·부록 C·D.
- 본문 §2 정의 지점에 1문장: "A threshold of −0.35 log points corresponds to roughly a 30% shortfall relative to the matched benchmark."
- §3.2 p10 문장에 환산 병기: "−0.253 [−0.371, −0.095] — roughly a 22% additional relative decline at the tenth percentile."
- 3.3의 "30/210 vs 35/210" 구분 서술은 현행 유지(이미 정확).

## 11. Same-state 균형 강화 (comment2 §13) — 부록 C.2 증보

**위치**: C.2 마지막 문단 앞에 신규 문단 + Table C1에 열 추가(또는 Table C1b).

**EN 초안**:

> As a stricter balance standard, we replace propensity-odds weights with entropy-balancing weights that impose exact balance on every mean (including ROA), on calendar-year indicators, and on the second moments of pre-event growth, leverage, ROA, and cash. All standardized differences are zero by construction (the largest is 0.000, against 0.123 under propensity weighting), with an effective comparison size of 9,303 in the distressed stratum. The distributional contrasts are essentially unchanged: the distressed median difference is −0.002 [−0.033, +0.061], the tenth percentile −0.338 [−0.483, −0.163], and the severe-contraction excess 13.6 percentage points [6.9, 21.0]. The non-distressed stratum behaves the same way (median +0.017 [−0.026, +0.038]; tenth percentile −0.223 [−0.323, −0.055]). Re-estimating the propensity weights inside every bootstrap replication, rather than holding them fixed, gives materially the same intervals (distressed tenth percentile −0.335 [−0.490, −0.167], against −0.341 [−0.496, −0.168] with fixed weights). The same-state tail difference does not depend on the residual imbalance of the baseline weighting or on treating the estimated weights as known.

[구현 주: 가중 재추정 부트의 로짓은 MLE(Newton)로 적합 — wp12b의 distressed 층은 L2 fallback이었으므로 관측 점추정이 미세하게 다르다(−0.3351 vs −0.3414). maxSMD도 0.029로 개선. 노트북 03 §8에 병기.]

**Table C1 추가 열 구조**:

| Covariate | Distressed (PS) | Distressed (EB) | Non-distressed (PS) | Non-distressed (EB) |
|---|---|---|---|---|
| … 기존 8행 … | 기존값 | 0.000 (전 행) | 기존값 | 0.000 (전 행) |
| Maximum absolute difference | 0.123 | 0.000 | 0.009 | 0.000 |

Notes 추가: "EB = entropy balancing on means, calendar-year indicators, and second moments of pre-event growth, leverage, ROA, and cash; effective sizes 9,303 (distressed) and 60,407 (non-distressed). Bootstrap intervals re-solve the weights in each replication."

**본문 §3.3 반문장 추가(선택)**: "…; the pattern is unchanged under entropy-balancing weights that set every measured difference, including ROA, exactly to zero (Appendix C.2)."

## 12. 부록 구조·명칭 정리 (comment2 §18)

- B 표제 "Matching and counterfactual diagnostics" → **"Matching and benchmark diagnostics"**.
- B.2 "Counterfactual-model audit" → **"Pre-event prediction benchmarks"**; 본문 내 "counterfactual model" → "prediction benchmark" 일괄.
- A.2 "Treatment construction and sample flow" → **"Event sample construction and sample flow"**; 본문의 "treatment universe" → "event universe".
- 레거시 Figure 1(prediction-benchmark excess + 등가밴드)은 B.3 뒤로 이동해 "Figure B1. Severe-contraction excess relative to the pre-event prediction benchmark"로 개제(±5pp 등가 판정 서술은 그 estimand에 한정해 유지 — 규칙 11 준수 형태 보존).
- 구조는 comment2 §18 그대로: A setting/sample/measurement · B primary design validation and inference · C same-state benchmark · D measurement/sample-selection robustness · E descriptive flows.

## 13. Caveat 통합 (comment2 §19)

Intro §1 셋째 문단 끝(설계 소개 뒤)에 **한 번만** 정의:

> The design identifies whether employment outcomes are unusually concentrated in the placement-anchored window relative to earlier windows and observed comparison states; it does not identify the counterfactual outcome without financing.

Conclusion 마지막 문단은 현행 유지(두 번째이자 마지막 반복). 그 밖의 반복 제거 대상(각 1회로 축소):
- §3.3 "The comparison remains descriptive because…" — 유지하되 §1의 "does not recover employment in the absence of financing" 문장은 삭제(위 통합문이 대체).
- E.1 "The decomposition is descriptive…does not identify a channel" — 유지(부록은 무방).
사이사이 문장은 적극 해석으로 교체, 예: "Financing timing contains information about a nonlinear transition in downside employment outcomes."

## 14. Introduction problem-first 재배열 (comment2 §16)

첫 문단을 다음 구조로 교체(현행 첫 문단의 인용은 둘째 문단으로 이동):

> Financing events are often endogenous to firm deterioration. A post-financing average can therefore combine two economically different objects: a decline already under way before the transaction, and a discrete adjustment concentrated near the financing date. Whether these components occupy the same part of the outcome distribution is largely unknown. We show that they do not.
>
> The setting is the Korean third-party allotment — a private placement to designated investors that rarely transfers majority ownership. Mandatory dated filings, predominantly minority equity stakes, and monthly administrative employment records make the question answerable: [이후 현행 둘째 문단으로 연결]

한국 = research design enabler로 서술(기여 아님). 현행 첫 문단의 Brown–Floros·Chakraborty–Gantchev 인용은 유지하되 literature 위치로 이동.

## 15. Literature 압축 2축 + FRL 인용 (comment2 §17)

**§1 다섯째 문단("These findings connect two strands…") 교체**:

> These findings connect two strands. The private-placement literature studies financing terms, investor identity, and subsequent performance and real activity (Wruck, 1989; Hertzel and Smith, 1993; Brophy et al., 2009; Brown and Floros, 2012; Chakraborty and Gantchev, 2013; Han and Xiao, 2025; Liu et al., 2024), but has not decomposed endogenous financing timing into outcome distributions across event clocks. The finance-and-labor literature links financing conditions to employment adjustment in buyouts, distress, and bankruptcy (Davis et al., 2014; Agrawal and Matsa, 2013; Graham et al., 2023), but says little about where in a firm's decline a negotiated minority recapitalization is observed — and whether the center and the tail of real adjustment share the same clock. Recent short-format work also studies placements' investor side (Han and Xiao, 2025; Liu et al., 2024) and financing-uncertainty real effects (Takahashi and Takaoka, 2026); our margin is the event-time distribution of downside real adjustment.

**신규 서지(검증 완료 — crossref_verify3.json)**:
- Han, J., and Xiao, C. (2025). Role of private placement targets in shaping long-term corporate performance. *Finance Research Letters*, 79, 107308. https://doi.org/10.1016/j.frl.2025.107308
- Liu, J., Jin, Y., and Xu, C. (2024). The impact of introducing strategic investors on corporate ESG performance—Empirical evidence from private placements in China. *Finance Research Letters*, 70, 106297. https://doi.org/10.1016/j.frl.2024.106297
- Takahashi, K., and Takaoka, S. (2026). When bookbuilding uncertainty hits: Pricing and real effects of primary-market uncertainty. *Finance Research Letters*, 100, 110028. https://doi.org/10.1016/j.frl.2026.110028

(셋 중 지면이 좁으면 Takahashi–Takaoka는 선택. 2,500단어 예산 내 인용 나열 금지 — 위 문단이 상한.)

## 16. Formal hypotheses 대신 competing predictions (comment2 §15)

**위치**: §1 넷째 문단(pseudo-event 설계 소개 "Financing dates are endogenous…") 끝에:

> Two empirical patterns would discriminate between readings. Under continuous deterioration, the downside tail should worsen gradually as the pseudo-event approaches the placement, alongside the mean. Under a threshold or crisis-resolution reading, average deterioration may start early, but severe downside outcomes should concentrate in the actual financing window. The evidence matches the second pattern.

이로써 pseudo-event 설계가 robustness가 아니라 **competing explanations를 구분하는 주 설계**로 승격(comment2 §15). H1/H2 형식 가설은 추가하지 않는다.

## 17. Payment-date anchor (comment2 §10) — 부록 A.1 증보

**위치**: A.1 마지막 문장("We nevertheless refer to the disclosure date as the announcement date…") 뒤:

> As a check, we re-anchor the event month to the month in which funds are paid for the 123 primary-sample placements with a parsed payment date (59% share the announcement month; the median lag is 10 days). The pooled tenth-percentile contrast is −0.244 [−0.363, −0.031] and the severe-contraction excess 7.7 percentage points [0.9, 14.5], against −0.233 [−0.431, −0.084] and 10.3 points [3.3, 18.0] for the announcement anchor in the same 123 firms. The tail is anchored to the financing window, not to the disclosure alone.

**본문(선택, §2 한 문장)**: "Results are similar when the event clock is anchored to the payment month rather than the board announcement (Appendix A.1)."
(규칙 11: "nearly unchanged" 단정 대신 두 anchor 수치 병기 — 위 문구가 그 형태.)

## 18. 제목·초록 (comment2 §21·§22)

**제목 권고(1안)**: *Minority Recapitalizations and the Timing of Employment Downside Risk*
(2안: *Financing in Decline: Employment Tail Risk Around Minority Recapitalizations*. 현행 유지 시에도 무방하나 1안이 economic question을 드러냄.)

**초록 교체안(EN, comment2 §22 로직: problem → result → implication)**:

> Financing events are endogenous to firm deterioration, which makes post-financing averages difficult to interpret. Using monthly administrative employment around Korean third-party equity placements, we compare actual placement windows with matched pseudo-events 18 to 36 months earlier. Average relative employment begins deteriorating well before financing, but the lower tail follows a different clock: relative to pooled pseudo-events, the tenth percentile falls by 0.253 log points while the median is essentially unchanged, and the probability of a severe relative contraction rises from 4.8–5.6% at distant pseudo-dates to 16.7% at the placement. The center–tail distinction survives comparisons with non-recipients in the same measured financial state, a full-design bootstrap, payment-date anchoring, and an entity-restructuring screen. The evidence does not identify the causal effect of financing; it shows that minority recapitalization dates reveal a discrete concentration of downside real adjustment that mean event-study estimates can obscure.

**Highlights 교체(2·5행)**:
- "Severe contractions are concentrated around the financing window." → "Severe relative contractions concentrate in the placement-anchored window."
- "The design establishes timing, not the causal effect of financing." → "Placement dates reveal downside adjustment that mean estimates can obscure."

## 19. Main exhibit 구조 (comment2 §23)

- **Figure 1**: 통일 파이프라인 수준 그림(위 §3(b)) — centerpiece 유지, caption에 common-sample 수치(군집부트, robustness 언급).
- **Table 1 Panel A**: full 표본 단독 + severe 행. common 116 열 추가는 **하지 않음**(i02 KILL — 위 §5); common은 B3 + §3.2 한 문장 유지.
- **Table 1 Panel B**: same-state 현행 유지(+ EB 반문장 참조).
- **Panel C(선택)**: rescue 상호작용(위 §6) — 또는 본문 한 문단으로 대체.
- 부록행: permutation·prediction benchmarks·max-t·동시공시·LOO·flow 분해·full-design bootstrap·EB·restructuring screen·payment anchor. 본문 가시 복잡도는 늘리지 않는다.
- 단어 예산: FRL 2,500 미만. 위 본문 추가(§1·2·5·6·9·10·13·14·16 EN 문장)는 순증 ≈ +290단어; §3(a) 교체(−40)·§13 반복 삭제(−60)·§14 재배열(±0)·§15 압축(−30)을 병행하면 순증 ≈ +160단어. 현행 약 2,450단어이므로 **Panel C를 표로 빼고 §6 본문을 3문장으로 줄이는 것을 기본안**으로 권고(그 경우 순증 ≈ +80단어).

## 20. 예상 질문 → 근거 매핑 (comment2 §20)

| 질문 | 답 근거 |
|---|---|
| "Already failing" | Figure 1 Panel A + §3.1 (mean은 t−24부터) · "the tail does not" = E_clock_levels |
| "What does financing have to do with it?" | §6 rescue(비의존) + D.3 control-transition 공행(71%) + two-clocks 문단 |
| "Tail cutoff arbitrary" | 11-cutoff grid(균일밴드) + p10 + sev25/50 (wp15b) |
| "A few extreme firms" | D.3(LOO, 09-02 반영분) |
| "SEs ignore reused controls" | B.4.1 full-design bootstrap |
| "Not actually balanced" | C.2 EB(maxSMD 0.000) |
| "Acquisitions/control changes" | equity-only 209 · stake≥30 제외 · ±3d ctrl 제외 · D.3 진단 |
| "Announcement is not funding" | A.1 payment anchor |
| "Legal entity changes" | D.3 reorg 스크린 |
| "Why Korea?" | §14 재배열 문단(enabler 서술) |

## 21. 반영하지 않기를 권고 (comment2 자체 지침과 일치)

- IV·PSM-DID·추가 outcome(CEO turnover 등) 확장 — 금지(§1·§24).
- rescue 외 이질성 분할 추가 — 금지(§7).
- t−12 pseudo-event 추가 — 오염(§9 블록 (c)의 논리).
- 부록 신규 소절 남설 — B.4.1, C.2 증보, D.3, A.1 증보 4건으로 한정. "we tried everything" 인상 방지(§18).

---

### 산출물·검증 체인

| 파일 | 내용 |
|---|---|
| `shared/outputs/pipe_wp15_2026-09-03/wp15_comment2_battery.json` | 정본 통일 세트(A_canonical·E_clock_levels)·rescue·purity·환산 |
| `…/wp15b_fullboot.json` | full-design bootstrap (B=1000, 재구현≡캐시 검증 max|Δ|<1e-10) |
| `…/wp15c_payment.json` | payment anchor (123, 양 anchor 나란히) |
| `…/wp15d_restruct.json` | 결과창 재구조화 스크린 + tail 겹침 (플래그 CSV는 로컬 전용) |
| `…/wp15e_samestate_eb.json` | entropy balancing + 가중 재추정 부트 |
| `…/crossref_verify3.json` | FRL 인용 3건 서지 검증 |
| repo `notebooks_FRL/03_comment2_FRL.ipynb` | 위 전부 저장출력 + 인쇄수치 assert |
| `…/out/I01.json` (2026-09-04) | 타이밍 감사: reorg∩severe 14 = drop_first 6·filing_first 7 (PARTIAL) · ctrl 공시는 placement월 군집 |
| `…/out/I02.json` (2026-09-04) | common116 full-design 부트 **KILL** — p10 [−0.306, +0.066]·sev35 [−0.011, +0.135] 0 포함 → §5 승격 철회 |
| `…/out/I03.json` (2026-09-04) | rescue θ MDE80: FE ±20.8pp(β의 2.1배)·분할 ±15.7pp → §6 MDE 병기 |
