# P016 원고 개정 마스터 가이드 (2026-09-04)

**용도**: PI가 원고를 직접 개정할 때 이 한 파일만 보면 되도록, 세 문서(EDIT_SUGGESTIONS 09-02 10블록 · 09-03 21블록 · i01–i03 개정분)를 위치 순서로 통합·정리한 실행 가이드. 모든 수치는 아티팩트에서 재검증했고(소스 맵 §17), 복제 저장소 `Real-K/paper_PIPE`의 `notebooks_FRL/01–03` 노트북이 인쇄값을 assert한다.

**기준 원고**: `PIPE_paper_0902.docx` + `PIPE_appendix_0902.docx`.

**세 문서 간 충돌 해소 (이 가이드가 정본)**:
1. **Grid featured 벤치마크**: 09-02 §5는 t−24를 featured로 유지했으나, comment2 §4(파이프라인 통일)에 따라 **pooled가 featured** — 09-03 §3이 09-02 §5를 대체한다. t−24·t−36·t−18 grid는 부록 B.5의 alternative benchmarks로 강등.
2. **common 116 승격**: 09-03 초판의 Table 1 열 추가는 **철회**(i02 사전등록 KILL) — composition 진단으로 유지.
3. 09-02 §0 요약표의 "t−36 재현 p 0.0057 · [3.7, 20.1]"은 **오기** — 정본은 max-t p10 **0.0032**, 균일밴드 **[3.5, 20.2]** (wp14 B_grid.vs_t36_replic 재확인).

---

## §0. CI 표기 규약 (혼용 금지 — 리뷰어 신뢰의 핵심)

같은 severe-excess 수치에 세 가지 구간이 존재한다. **어느 문장에 어느 구간을 쓰는지 고정**:

| 구간 유형 | 값 (c=−0.35, full) | 쓰는 곳 |
|---|---|---|
| 기업군집 percentile CI (B=4,000) | +10.2pp **[4.8, 15.8]** | 본문 §3.2 · Table 1 severe 행 · Figure 1 caption · 초록 |
| sup-t 균일밴드 (11-cutoff grid) | +10.2pp **[3.0, 17.6]** | 부록 B.5 grid 표에서만 ("uniform band" 라벨 필수) |
| full-design bootstrap CI (B=1,000) | +10.2pp **[3.1, 15.5]** | 부록 B.4.1에서만 |

동일 규칙이 p10에도 적용: 본문/Table 1 = [−0.371, −0.095](군집) · B.4.1 = [−0.347, −0.063](full-design). **한 문장 안에서 두 유형을 병기할 때는 반드시 유형을 명시한다.**

---

## §1. 정본 수치 카드

원고에 인쇄될 수 있는 모든 수치. ★ = 신규(이번 회차), 나머지는 기존 인쇄값 유지.

### 1a. Table 1 Panel A — actual vs pooled pseudo (210 vs 561, 169 firms; 군집부트 B=4,000)

| 통계 | 값 [95% CI] | 상태 |
|---|---|---|
| Mean | −0.0481 [−0.1026, +0.0040] | 기존 유지 (wp13c) |
| Tenth percentile | −0.2527 [−0.3713, −0.0953] | 기존 유지 |
| Twenty-fifth percentile | −0.0641 [−0.1576, −0.0001] | 기존 유지 + full-design 각주(§7 참조) |
| Median | −0.0036 [−0.0375, +0.0249] | 기존 유지 |
| ★ Severe excess at −0.35 | **+0.1025 [+0.0477, +0.1576]** | 신규 행 (wp15 A_canonical) |

주의: wp15 재부트(seed 20260903)의 mean~median CI는 MC 오차만큼 다르다(예: mean [−0.1015, +0.0034]). **기존 인쇄된 wp13c CI를 유지**하고, 신규 severe 행만 wp15에서 가져온다. 두 소스를 섞어 재인쇄하지 말 것.

### 1b. Clock별 수준 (★ 신규 Figure 1 데이터; wp15 E_clock_levels, 기업부트 B=4,000)

| Clock | n | Mean matched gap [CI] | Pr(D ≤ −0.35) [CI] |
|---|---|---|---|
| t−36 | 125 | −0.0058 [−0.0461, +0.0322] | 4.8% [1.6, 8.8] |
| t−30 | 131 | −0.0115 [−0.0435, +0.0220] | 5.3% [1.5, 9.2] |
| t−24 | 142 | −0.0520 [−0.0927, −0.0169] | 5.6% [2.1, 9.9] |
| t−18 | 163 | −0.0576 [−0.1001, −0.0186] | 9.2% [4.9, 13.5] |
| Actual | 210 | −0.0820 [−0.1289, −0.0363] | 16.7% [11.9, 21.4] |
| (pooled pseudo 참조) | 561 | −0.0339 [−0.0541, −0.0150] | 6.4% [4.5, 8.6] |

Panel A 경로는 현행 그림(−0.006/−0.012/−0.052/−0.058/−0.081)과 최대 0.001 차이. severe 산식 확인: 35/210 = 16.67% 대 pooled 6.42% → 초과 10.25pp.

### 1c. Clock별 event-minus-single-pseudo 대조

| 벤치마크 | p10 대조 [CI] (기존 B4 유지) | ★ sev35 대조 [CI] (wp15) |
|---|---|---|
| vs t−18 | −0.2035 [−0.3286, −0.0047] | +0.0746 [+0.0097, +0.1362] |
| vs t−24 | −0.2647 [−0.3922, −0.0882] | +0.1103 [+0.0447, +0.1719] |
| vs t−30 | −0.2969 [−0.4279, −0.1234] | +0.1132 [+0.0453, +0.1784] |
| vs t−36 | −0.3060 [−0.4249, −0.1018] | +0.1187 [+0.0556, +0.1818] |

### 1d. Common 116-firm (기존 B3 유지 + ★ severe 행)

Mean −0.0616 [−0.1261, −0.0006] · p10 −0.2193 [−0.4062, −0.0709] · p25 −0.0816 [−0.2063, −0.0038] · median −0.0207 [−0.0569, +0.0163] · ★ sev35 +0.1056 [+0.0366, +0.1789].
★ **full-design에서는 유의 상실**(i02, 사전등록 KILL): p10 [−0.3063, +0.0655] · sev35 [−0.0107, +0.1345] — B.4.1에 정직 보고, **co-primary 승격 금지**.

### 1e. Full-design bootstrap (★ 신규 B.4.1; wp15b, B=1,000, 검증: 재구현≡캐시 max|Δ|<1e-10)

| 통계 | 군집 CI (기존) | full-design CI |
|---|---|---|
| Mean | [−0.1026, +0.0040] | **[−0.1046, +0.0132]** (0 포함 전환) |
| Median | [−0.0375, +0.0249] | [−0.0465, +0.0335] |
| p10 | [−0.3713, −0.0953] | **[−0.3466, −0.0627]** ✓ |
| p25 | [−0.1576, −0.0001] | **[−0.1573, +0.0122]** (0 포함 전환) |
| Sev35 | [+0.0477, +0.1576] | **[+0.0312, +0.1550]** ✓ |

sev25 [+0.0243, +0.1779]✓ · sev50 [+0.0195, +0.1174]✓. Grid 균일하한>0: −0.60~−0.30의 7/11 (pointwise는 −0.60~−0.20의 9/11).

### 1f. Threshold grid — pooled 벤치마크 (★ B.5 featured; wp14 B_grid.vs_pooled, 균일밴드)

| Cutoff | Diff | 95% uniform band |
|---|---|---|
| −0.60 | +5.5pp | [+0.5, +10.6] |
| −0.55 | +7.7pp | [+2.1, +13.4] |
| −0.50 | +8.5pp | [+2.5, +14.4] |
| −0.45 | +7.9pp | [+1.8, +13.9] |
| −0.40 | +9.2pp | [+2.9, +15.6] |
| −0.35 | +10.2pp | [+3.0, +17.6] |
| −0.30 | +10.5pp | [+2.6, +18.4] |
| −0.25 | +8.7pp | [+0.5, +17.0] |
| −0.20 | +8.6pp | [−0.0, +17.2] |
| −0.15 | +7.2pp | [−2.1, +16.4] |
| −0.10 | +4.2pp | [−5.7, +14.0] |

11/11 점추정 양수 · 균일하한>0 8/11 · max-t 조정 p: p10 **0.0117**, mean 0.18, p25 0.23, median 1.00.
대안 벤치마크(각주·표 행): t−24(원구축 wp11d) 12.0 [5.2, 18.8]·p 0.006 (재추정 시 11.0 [2.4, 19.7]·p 0.0132); t−36 11.9 [3.5, 20.2]·p 0.0032; t−18 7.5 [−0.9, 15.9]·p 0.056(균일밴드 0 포함, 최소 placebo 표본).

### 1g. Sub-window (기존 09-02 §2; wp14a)

+1..+6: p10 −0.1417 [−0.2017, −0.0549] · sev +6.3pp [+2.5, +10.3] · median −0.0099 ns.
+7..+12: p10 −0.2527 [−0.3659, −0.0966] · sev +10.3pp [+4.9, +15.9] · median −0.0036 ns.

### 1h. Same-state (기존 C3/C4 유지 + ★ EB/재추정)

기존(성향가중): distressed median −0.002 [−0.036, +0.069] · p10 −0.341 [−0.496, −0.168] · sev 18.26% vs 4.42% (13.84pp [4.79, 22.89]) · maxSMD 0.123(ROA) · ESS 14,566.5.
★ EB(평균+연도더미+pg·lev·roa·cash 2차모멘트; 복제마다 re-solve, B=500): **maxSMD 0.0000** · ESS 9,303 · median −0.0023 [−0.0328, +0.0608] · p10 **−0.3376 [−0.4834, −0.1633]** · cprob35 **+0.1362 [+0.0690, +0.2095]**. Non-distressed: maxSMD 0.0000 · ESS 60,407 · median +0.0174 [−0.0258, +0.0381] · p10 −0.2227 [−0.3230, −0.0545] · cprob35 +0.0769 [+0.0258, +0.1318].
★ 성향가중 복제별 재추정(Newton MLE): distressed p10 −0.3351 [−0.4896, −0.1671] · cprob35 +0.1355 [+0.0706, +0.2074] · maxSMD 0.029 — 고정가중과 실질 동일 구간. (점추정 −0.3351 vs 논문 −0.3414는 논문의 distressed 로짓이 ridge fallback였던 데서 오는 미세차 — 재추정 행을 인쇄한다면 이 사실을 각주로.)

### 1i. Purity 제외 (★; wp15 C_purity — 기업을 양팔에서 제거, 군집부트)

| 제외 | drop | n | p10 [CI] | sev35 [CI] |
|---|---|---|---|---|
| CB 1건 (equity-only 209) | 1 | 209 | −0.2527 [−0.3644, −0.0943] | +0.1028 [+0.0477, +0.1579] |
| stake ≥30% | 3 | 207 | −0.2492 [−0.3746, −0.0920] | +0.0961 [+0.0394, +0.1511] |
| ±3d 최대주주변경·경영권 공시 | 32 | 178 | −0.2232 [−0.3575, −0.0705] | +0.0979 [+0.0391, +0.1609] |
| ±3d 구조조정 공시 | 5 | 205 | −0.2569 [−0.3800, −0.0920] | +0.1008 [+0.0460, +0.1572] |

stake 커버리지: 210 중 106 관측 · ≥30% 3건 · ≥50% 0건.

### 1j. Entity-restructuring 스크린 (★ 신규 D절; wp15d, 창 = 공시일−3d..+13m)

플래그: reorg(합병·분할·영업/자산양수도·주식교환) **57** · 해산 4 · 최대주주변경·경영권 **69** / 210.

| 제외 | drop | n | p10 [CI] | sev35 [CI] |
|---|---|---|---|---|
| Reorg | 57 | 153 | **−0.1369 [−0.2991, −0.0056]** ✓ | +0.0664 [+0.0069, +0.1304] ✓ |
| Reorg + 해산 | 59 | 151 | −0.1380 [−0.3038, −0.0074] ✓ | +0.0668 [+0.0061, +0.1311] ✓ |
| + Control-change (진단) | 97 | 113 | +0.0674 [−0.1136, +0.1490] ✗ | −0.0140 [−0.0655, +0.0399] ✗ |

꼬리 겹침: severe 35건 중 reorg 14 (40.0% vs 비-severe 24.6%) · ctrlchg **25 (71.4% vs 25.1%)** · 해산 1.
★ 타이밍 감사(i01): reorg∩severe 14건 = 하락 교차 선행 6 · 동월 1 · 공시 선행 7. ctrl 공시는 placement월 군집(**15/25가 m≤2**)인 반면 자기 고용의 −0.35 교차는 중위 **+5개월** — ctrl "공시 선행"의 상당 부분은 기계적.

### 1k. Payment anchor (★ A.1 증보; wp15c — 같은 123개 기업 나란히)

커버리지: 210 중 123 납입일 관측 · 공시월=납입월 59% · lag 중위 10일 IQR [8, 15].

| Anchor | Mean [CI] | Median | p10 [CI] | sev35 [CI] |
|---|---|---|---|---|
| 공시월 (123) | −0.0840 [−0.1508, −0.0223] | −0.0043 | −0.2332 [−0.4307, −0.0837] | +0.1030 [+0.0326, +0.1799] |
| 납입월 (123) | −0.0616 [−0.1304, +0.0002] | +0.0040 | **−0.2435 [−0.3631, −0.0312]** | **+0.0767 [+0.0092, +0.1446]** |

### 1l. Rescue 이질성 + MDE (★ 선택 Panel C; wp15 B_rescue + I03)

FE 회귀(firm FE + clock FE, 기업군집 SE):

| 사양 | Actual 점프 β [CI] | ×Rescue θ [CI] | n (firms) |
|---|---|---|---|
| 1(D≤−0.35), common 116 | +0.0984 [+0.0013, +0.1954] | +0.0153 [−0.1300, +0.1605] | 580 (116) |
| 1(D≤−0.35), full | +0.1174 [+0.0281, +0.2067] | −0.0160 [−0.1384, +0.1064] | 771 (210) |
| D (mean), common 116 | −0.0747 [−0.1658, +0.0164] | +0.0276 [−0.0953, +0.1506] | 580 (116) |

분할: rescue(100/210=47.6%) sev35 +0.0651 [−0.0075, +0.1425] ns · non-rescue +0.1365 [+0.0572, +0.2150] ✓ · 층간차 −0.0714 [−0.1809, +0.0381] ns.
★ MDE80(=2.4865×SE): FE common ±**0.2076**(β의 2.11배) · FE full ±0.1751 · 분할차 ±0.1565.

### 1m. 경제 환산 · 기타 고정값

expm1(−0.35) = **−29.5%** · expm1(−0.2527) = **−22.3%** · expm1(−0.2193) = −19.7% · expm1(−0.3414) = −28.9%.
LOO(기존 09-02 §4): p10 대조 전체 −0.2527 → 하위 5 제거 −0.1551 → 10 제거 −0.1152 → 15 제거(7.1%) −0.0757, 단독 제거 15종 전부 음수. 카운트: 매칭 d≤−0.35 **35/210** · 자기 outcome ≤−0.35 **30/210**(14.29%).
표본선택(09-02 §7): feasible 260 = 210 + 50; leverage만 차이(중위 0.73 vs 0.78 · 평균 1.31 vs 2.07 · MWU p=0.027), 나머지 p≥0.13.
표본 흐름 정본(09-02 §10, v3): **415**(389 equity + 26 CB) → 382(357 structured + 25 parsed) → 360 → 321 → 260 → 210(209+1) → 208 완결.

---

## §2. 제목 · Highlights · 초록

**제목(권고 1안)**: *Minority Recapitalizations and the Timing of Employment Downside Risk*
(2안: *Financing in Decline: Employment Tail Risk Around Minority Recapitalizations*; 현행 유지도 가능하나 1안이 economic question을 드러냄.)

**Highlights (5행 전체 교체안)**:
> - Average employment deterioration begins about two years before minority recapitalizations.
> - Severe relative contractions concentrate in the placement-anchored outcome window.
> - The probability of a severe contraction triples at the placement relative to earlier clocks.
> - Recipients and non-recipients in the same measured state differ only in the lower tail.
> - Placement dates reveal downside adjustment that mean estimates can obscure.

**초록 (전체 교체안 — problem → result → implication)**:
> Financing events are endogenous to firm deterioration, which makes post-financing averages difficult to interpret. Using monthly administrative employment around Korean third-party equity placements, we compare actual placement windows with matched pseudo-events 18 to 36 months earlier. Average relative employment begins deteriorating well before financing, but the lower tail follows a different clock: relative to pooled pseudo-events, the tenth percentile falls by 0.253 log points while the median is essentially unchanged, and the probability of a severe relative contraction rises from 4.8–5.6% at distant pseudo-dates to 16.7% at the placement. The center–tail distinction survives comparisons with non-recipients in the same measured financial state, a bootstrap that re-estimates the matching in every replication, payment-date anchoring, and an entity-restructuring screen. The evidence does not identify the causal effect of financing; it shows that minority recapitalization dates reveal a discrete concentration of downside real adjustment that mean event-study estimates can obscure.

(주의: "excess of 10.2 percentage points" 문장을 초록에 넣을 경우 군집 CI [4.8, 15.8]과 짝지을 것.)

---

## §3. §1 Introduction — 문단별 재구성

**문단 1 (problem-first 교체)** — 현행 첫 문단("Private placements give public firms…") 대체:
> Financing events are often endogenous to firm deterioration. A post-financing average can therefore combine two economically different objects: a decline already under way before the transaction, and a discrete adjustment concentrated near the financing date. Whether these components occupy the same part of the outcome distribution is largely unknown. We show that they do not — and the distinction matters beyond our setting, because when financing timing is endogenous, a mean post-financing estimate mixes a pre-existing deterioration with an event-localized tail adjustment.

**문단 2 (한국 = design enabler)** — 현행 둘째 문단을 아래 도입문으로 연결:
> The setting is the Korean third-party allotment — a private placement to designated investors that rarely transfers majority ownership. Mandatory dated filings, predominantly minority equity stakes, and monthly administrative employment records make the question answerable. [이후 현행 "Among the 201 equity placements… 1,321 listed firms" 문장 유지]

**문단 3 (KKW 포지셔닝, 09-02 §1)** — 문단 2 끝 또는 문단 4 앞:
> Korean equity issues are a canonical setting for distressed recapitalization: Kim, Ko, and Wang (2019) show that more than a third of follow-on issue proceeds retire debt and that issuers are frequently loss-making. We take this association as the starting point rather than the finding. The question here is not whether placements select distressed firms — they do — but how real adjustment is distributed in event time around the financing.

**문단 4 (설계 + competing predictions)** — 현행 "Financing dates are endogenous…" 문단 유지 후 끝에 추가:
> Two empirical patterns would discriminate between readings. Under continuous deterioration, the downside tail should worsen gradually as the pseudo-event approaches the placement, alongside the mean. Under a threshold or crisis-resolution reading, average deterioration may start early, but severe downside outcomes should concentrate in the actual financing window. The evidence matches the second pattern.

그리고 caveat 통합문(1회만; 현행 "This design locates outcomes in event time; it does not recover employment in the absence of financing."를 다음으로 확장 교체):
> The design identifies whether employment outcomes are unusually concentrated in the placement-anchored window relative to earlier windows and observed comparison states; it does not identify the counterfactual outcome without financing.

**문단 5 (결과 요약)** — 현행 유지하되 severe 문장을 통일 파이프라인 수치로: "At a −0.35-log-point threshold, …"를:
> At a −0.35 log-point threshold — roughly a 30% shortfall against the matched benchmark — the probability of a severe relative contraction is 4.8–5.6% at pseudo-dates 36 to 24 months out, begins to rise at 18 months, and reaches 16.7% at the placement, an excess of 10.2 percentage points [4.8, 15.8] over the pooled pseudo-dates.

**문단 6 (문헌 2축, 09-03 §15)** — 현행 "These findings connect two strands…" 교체:
> These findings connect two strands. The private-placement literature studies financing terms, investor identity, and subsequent performance and real activity (Wruck, 1989; Hertzel and Smith, 1993; Hertzel et al., 2002; Brophy et al., 2009; Chaplinsky and Haushalter, 2010; Brown and Floros, 2012; Chakraborty and Gantchev, 2013; Lim et al., 2021; Liu et al., 2024; Han and Xiao, 2025), but has not decomposed endogenous financing timing into outcome distributions across event clocks. The finance-and-labor literature links financing conditions to employment adjustment in buyouts, distress, and bankruptcy (Hotchkiss, 1995; Agrawal and Matsa, 2013; Davis et al., 2014; Brown and Matsa, 2016; Falato and Liang, 2016; Caggese et al., 2019; Baghai et al., 2021; Benmelech et al., 2021; Graham et al., 2023), but says little about where in a firm's decline a negotiated minority recapitalization is observed — and whether the center and the tail of real adjustment share the same clock. Minority recapitalizations sit between those settings: they inject outside capital without usually changing majority control, often after deterioration has begun.

---

## §4. §2 Setting, data, and design — 앵커별 수정

1. **표본 정의(§9 CB)** — "The sample contains 209 paid-in equity allotments and one convertible-bond placement." 뒤에:
> The featured results use the 209 paid-in equity allotments; including the single convertible-bond placement leaves every reported contrast unchanged (Appendix B), and the inclusive sample is retained there.

2. **Estimand 1문장** — outcome 정의 수식 문단 뒤:
> The primary tail estimand is the difference between actual-event and pooled pseudo-event probabilities of a matched outcome no greater than a threshold c, with c = −0.35 featured — roughly a 30% shortfall against the matched benchmark — and a full threshold grid in the appendix.

3. **Window 근거(§11)** — outcome 정의 문단 끝:
> Employment adjustment begins in the first six post-placement months and deepens in the second six; the primary measure averages months +7 to +12 to reduce month-specific payroll noise and to capture the persistent post-placement employment level rather than the transition into it.

4. **t−18 근거** — pseudo-event 문단 끝:
> The nearest pseudo-date is t−18 because a t−12 clock would place its +7 to +12 outcome window inside the actual financing window; t−18 is the closest clock whose outcome window ends before the placement.

5. **추론 서술(full-design 예고)** — "Formal event-versus-pseudo contrasts pool the four earlier dates and use 4,000 bootstrap replications clustered by recipient." →
> Formal event-versus-pseudo contrasts pool the four earlier dates. Inference uses two schemes: 4,000 bootstrap replications clustered by recipient, and a full-design bootstrap that re-draws recipient and comparison firms separately and re-estimates the propensity model, common support, and matching within every replication (Appendix B).

6. **Payment anchor 예고(선택 1문장)**:
> Results are similar when the event clock is anchored to the payment month rather than the board announcement (Appendix A).

7. **용어**: 본문 전체에서 매칭 설계의 꼬리는 "severe **relative** contraction", same-state(자기 outcome)는 "severe contraction"으로 분리. "treatment universe" → "event universe".

---

## §5. §3 Results — 3.1 / 3.2 / 3.3 (+ 선택 3.4)

### 3.1 — 한 곳만
"The actual-event estimate is −0.081 [−0.101, −0.061]." → 통일 파이프라인 수치로 교체:
> The actual-event estimate is −0.082 [−0.129, −0.036].
(구 값은 prediction-benchmark(wp11fg) 산출 — Figure 1을 수준 그림으로 바꾸면 함께 교체. CI가 넓어지는 이유는 모델 벤치마크가 아니라 기업부트 수준 CI이기 때문 — 정직한 변화.)

### 3.2 — 전면 개정 (아래 5문단 전체 교체안)

**문단 1 (분위수 + 환산 + p25 정직)**:
> The center of the distribution barely changes between the actual event and the pooled pseudo-events. The median difference is −0.004 log points [−0.038, 0.025]. At the tenth percentile, however, the difference is −0.253 [−0.371, −0.095] — roughly a 22% additional relative employment decline. The twenty-fifth percentile lies between them at −0.064 [−0.158, −0.000], though this margin does not survive the stricter full-design bootstrap reported in Appendix B. These pooled comparisons place the event-window change below the earlier distribution without implying that the same firms occupy a given quantile at every date.

**문단 2 (grid — pooled featured)**:
> A threshold grid gives a less quantile-specific view. Relative to the pooled pseudo-events — the same benchmark as the quantile contrasts — the event-minus-pseudo contraction probability is positive at all eleven cutoffs from −0.60 to −0.10, and the difference at c = −0.35 is 10.2 percentage points [4.8, 15.8]. A max-t adjustment across the mean, tenth percentile, twenty-fifth percentile, and median concentrates the joint evidence at the tenth percentile (adjusted p = 0.012). Appendix B reports the full grid with uniform bands and three alternative pseudo-date benchmarks.

**문단 3 (Figure 1 Panel B — 수준 + common 진단)**:
> Panel B of Figure 1 traces the severe-contraction probability itself across event clocks: 4.8% at t−36, 5.3% at t−30, 5.6% at t−24, 9.2% at t−18, and 16.7% at the placement. The tail is quiet at distant clocks, stirs at t−18, and concentrates at the placement. Composition change across clocks does not generate this pattern: restricting every clock to the 116 recipients observed at all five dates, the pooled tenth-percentile contrast is −0.219 [−0.406, −0.071] with a severe-contraction excess of 10.6 percentage points [3.7, 17.9] under the firm-clustered bootstrap, although this smaller sample loses precision under the full-design scheme in Appendix B.

**문단 4 (timing decomposition)**:
> The dynamics within the first post-placement year sharpen the picture. Over months +1 to +6 the tenth-percentile contrast relative to the pooled pseudo-dates is already −0.142 [−0.202, −0.055] with a severe-contraction excess of 6.3 percentage points; over months +7 to +12 it deepens to −0.253 with 10.3 points; the median is near zero in both windows. The excess lower tail emerges soon after the placement and widens over the year, while the center never moves.

**문단 5 (two clocks 개념 + state-revealing)**:
> These facts are naturally read as two clocks of adjustment. Firm condition deteriorates gradually, so the average gap opens well before the transaction. The placement itself, however, tends to occur when latent stress, negotiation, or restructuring need reaches a threshold, and around that threshold a subset of firms enters a discrete adjustment regime. The placement is a state-revealing event rather than an exogenous treatment: it occurs when a subset of already-deteriorating firms enters a nonlinear adjustment region, which moves the lower tail while leaving the median nearly unchanged.

(삭제되는 것: 현행 "Using t−24 as the pre-event benchmark… 12.0 [5.2, 18.8]… 0.006…" 문단과 "Panel B… −0.1, −1.4, −0.5, 0.9pp… 11.0 [9.1, 12.9]" 문단 — 전자는 B.5 대안 벤치마크로, 후자는 Figure B1(prediction-benchmark 등가성 그림)로 이동.)

### 3.3 — 두 곳만
1. 끝에 EB 반문장: "…cannot account for both the matched centers and the lower-tail gap." →
> …cannot account for both the matched centers and the lower-tail gap; the pattern is unchanged under entropy-balancing weights that set every measured difference, including ROA, exactly to zero (Appendix C).
2. 카운트 문장(09-02 §3) — §3.3 첫 문단 앞 또는 §3.2 문단 3 뒤:
> In counts rather than rates, 30 of the 210 recipients experience an own-firm employment outcome of at least −0.35 log points, and 35 of 210 do so in the matched recipient-minus-control outcome; the tail is not the product of two or three extreme firms.

### 3.4 (선택 — 지면 있으면 문단 1개, 없으면 생략하고 부록으로)
> A stated financing purpose provides one transaction-level discriminator. Rescue-type purposes account for 47.6% of the primary sample. Within a firm and clock fixed-effects design, the actual-date jump in severe-contraction probability is 9.8 percentage points [0.1, 19.5]; the additional jump for rescue-purpose placements is 1.5 points with a wide interval [−13.0, +16.1], and the split samples show a significant jump for non-rescue placements (13.7 points [5.7, 21.5]) alongside a smaller, imprecise one for rescue placements (6.5 points [−0.8, 14.3]). The event-localized tail is therefore not an artifact of the narrow stated-rescue classification. The data do not establish purpose as a moderator: the minimum detectable interaction at 80% power is roughly ±21 percentage points — about twice the actual-date jump — so the absence of a detected difference bounds neither direction economically.

---

## §6. §4 Conclusion

1. 첫 문단 끝에 one-line contribution:
> Minority recapitalizations occur late in a deteriorating employment path: average relative employment weakens well before financing, whereas severe downside outcomes become unusually concentrated only around the placement window.
2. 마지막 문단(비인과 한계)은 현행 유지 — intro 통합문과 함께 정확히 2회 반복 구조. 그 사이 본문에서는 "descriptive/not causal" 반복 삭제, 필요하면 적극 문장으로:
> Financing timing contains information about a nonlinear transition in downside employment outcomes.

---

## §7. Figure 1 · Table 1 스펙

**Figure 1 (통일 수준 그림)** — 데이터는 §1b 표 그대로. Panel A: mean matched gap 수준(오차막대 = 기업부트 CI). Panel B: Pr(D≤−0.35) 수준. 등가밴드 음영은 제거(레거시 그림 Figure B1로 이동).
**Caption**:
> Figure 1. Mean matched employment gap and severe-contraction probability across event clocks.
> Notes. Both panels use the same matched-outcome pipeline held fixed while the event clock changes. Panel A reports the mean recipient-minus-matched-control outcome at four pseudo-events and at the actual placement; Panel B reports the probability that the matched outcome is no greater than −0.35 log points. Vertical bars are 95% firm-clustered bootstrap intervals. Relative to the four pooled pseudo-dates, the actual-event excess at −0.35 is 10.2 percentage points [4.8, 15.8]; in the common 116-firm sample it is 10.6 points [3.7, 17.9].

**Table 1 Panel A** — 기존 4행 유지 + Severe 행 추가(§1a). 노트에 추가:
> Severe relative contraction denotes a matched outcome no greater than −0.35 log points (35 of 210 actual-event observations); its interval is the firm-clustered bootstrap percentile interval. Estimates are unchanged in the 209 equity-only sample, and the twenty-fifth-percentile margin does not survive the full-design bootstrap (Appendix B).
**Panel B** — 현행 유지. **Panel C(선택)** — §1l 표 3행 + 노트("Firm and event-clock fixed effects; standard errors clustered by firm. Rescue is a firm-level stated-purpose indicator absorbed by the firm effects.").

---

## §8. Appendix A

**A.1 끝 (payment anchor)**:
> As a check, we re-anchor the event month to the month in which funds are paid for the 123 primary-sample placements with a parsed payment date (59% share the announcement month; the median lag is 10 days). The pooled tenth-percentile contrast is −0.244 [−0.363, −0.031] and the severe-contraction excess 7.7 percentage points [0.9, 14.5], against −0.233 [−0.431, −0.084] and 10.3 points [3.3, 18.0] for the announcement anchor in the same 123 firms. The tail is anchored to the financing window, not to the disclosure alone.
(주의: "nearly unchanged" 단정 금지 — 두 anchor 수치 병기가 규칙 11 준수 형태.)

**A.2 — v3 정본 수치 교체(09-02 §10)**: 첫 문단과 Table A1 상단 3행:
> The extraction retains the first completed third-party allotment for each firm. It contains 415 transactions—389 paid-in equity increases and 26 convertible-bond placements. Of these, 382 have an identifiable event date (357 from the structured extraction and 25 recovered from the filing documents), and 360 fall inside the 2015–2025 analysis window.
Table A1: 415 → 382 → 360 → 321 → 260 → 210 → 209 → 208 → 201 → 196(→123 primary와 구분 주의: 196은 360 기준, 123은 210 기준 — A.1 문구는 123 사용) → 1,321 → 1,250.

**A.2 끝 (표본선택, 09-02 §7)**:
> Of the 260 calendar-feasible transactions, the 50 that fail the primary observation rule resemble the analysis sample in event year, allottee stake, purpose composition, ROA, and loss incidence (Mann-Whitney and proportion tests, p ≥ 0.13), but they are more levered (median 0.78 versus 0.73; mean 2.07 versus 1.31; p = 0.027). Exclusion therefore tilts the estimating sample, if anything, away from the most levered issuers. Because the observation-window bound in Appendix D codes early record cessations as extreme contractions and strengthens the tail result, this selection margin is unlikely to manufacture the excess lower tail.
(+ Table A3: included 210 / excluded 50 / p — 행: event year, stake, rescue purpose, equity, leverage, ROA, cash, loss, impairment.)

**A.3 끝 (stake 제외)**:
> Among primary-sample transactions with a measured stake (106 of 210), three reach 30% and none reach 50%. Excluding the three, the pooled tenth-percentile contrast is −0.249 [−0.375, −0.092] and the severe-contraction excess 9.6 points [3.9, 15.1].

---

## §9. Appendix B

**표제·명칭**: "Matching and counterfactual diagnostics" → **"Matching and benchmark diagnostics"**. B.2 "Counterfactual-model audit" → **"Pre-event prediction benchmarks"**; 본문 "counterfactual model" → "prediction benchmark" 일괄.

**B.3 뒤 — Figure B1 이동**: 현행 Figure 1(prediction-benchmark excess + ±5pp 등가밴드)을 "Figure B1. Severe-contraction excess relative to the pre-event prediction benchmark"로 이동. Table B2도 그 estimand 라벨로 유지(등가 판정 서술은 이 estimand에 한정 — −0.1/−1.4/−0.5/+0.9pp, actual +11.0 [9.1, 12.9]).

**B.4** — 기존 B3(pooled/common 4행) 유지 + severe 행 추가(full +0.1025 [+0.0477, +0.1576] · common +0.1056 [+0.0366, +0.1789]) + B4(clock별 p10) 유지 + ★ sev35 열 추가(§1c). 대조군 재사용 명시 문장(09-02 §6 위치2):
> Comparison firms can serve several recipients and pseudo-dates; the firm-clustered inference accounts for a recipient's repeated appearance across event clocks but not for reuse of the same comparison firm across recipients — the full-design bootstrap below addresses this.

**B.4.1 (신설 — full-design bootstrap)**:
> B.4.1. Full-design bootstrap
> The firm-clustered bootstrap resamples recipients but holds the estimated propensity model, the common-support boundary, and the matched sets fixed. As a stricter scheme, we re-draw the 210 recipients and the comparison pool separately at the firm level in each of 1,000 replications and re-estimate the propensity model, common support, caliper, and nearest-neighbor sets before recomputing every statistic. The tenth-percentile contrast is −0.253 [−0.347, −0.063] and the severe-contraction excess at −0.35 is 10.2 percentage points [3.1, 15.5]; the excesses at −0.25 and −0.50 remain positive as well ([2.4, 17.8] and [2.0, 11.7]). Two weaker margins move: the mean interval becomes [−0.105, +0.013] and the twenty-fifth-percentile interval [−0.157, +0.012], both now covering zero. In the common 116-firm sample the full-design intervals widen enough to cover zero (tenth percentile [−0.306, +0.066]; severe excess [−0.011, +0.135]), so the balanced-sample result is a composition diagnostic under the firm-clustered scheme rather than co-primary evidence. The uniform band over the threshold grid remains above zero for all cutoffs from −0.60 through −0.30. The paper's tail statements rest on the full-sample tenth percentile and severe-contraction excess, which survive the stricter scheme.
(+ Table: §1e 5행 × {군집 CI, full-design CI}; Notes: "Point estimates are identical by construction; only the intervals differ.")

**B.5 (재작업 — pooled featured + 대안 벤치마크)**: 첫 문단 교체:
> The featured threshold-grid and max-t calculations use the pooled pseudo-event benchmark, matching the estimand in Table 1. The event-minus-pooled contraction probability is positive at all eleven thresholds; the uniform lower bound is above zero from −0.60 through −0.25, and the max-t adjusted p-value across the four featured summaries is 0.012 for the tenth percentile (0.18 for the mean, 0.23 for the twenty-fifth percentile, 1.00 for the median). Grids against single pseudo-dates behave the same way: the t−24 benchmark gives 12.0 percentage points [5.2, 18.8] at −0.35 under its original construction (11.0 [2.4, 19.7] when re-estimated in the pooled-contrast pipeline; adjusted tenth-percentile p = 0.013), the most distant t−36 benchmark gives 11.9 points [3.5, 20.2] (adjusted p = 0.003), and the nearest t−18 benchmark keeps positive point estimates at every threshold (7.5 points at −0.35) while its uniform band includes zero at most cutoffs, reflecting the smallest single-date placebo sample. The grid evidence does not depend on the choice of pseudo-date benchmark.
Table B5 데이터는 §1f(cutoff·diff·uniform band — "95% uniform band" 열 라벨 필수). "original placebo-vector construction"류 이력 서술은 삭제 — 위 문구의 "under its original construction / re-estimated in the pooled-contrast pipeline"이 허용 상한.

**B.7 끝 (±3d control 제외)**:
> Thirty-two placements coincide with a largest-shareholder-change or management-control filing within three days of the announcement. Excluding them, the tenth-percentile contrast is −0.223 [−0.358, −0.071] and the severe excess 9.8 points [3.9, 16.1].

**B.8 (신설 — sub-window; 본문 §3.2 문단 4의 표 버전)**: Table — 두 창 × {p10 diff, severe excess, median}; §1g 수치.

---

## §10. Appendix C

**C.1 — 부트 서술 정정(09-02 §6)**: "…and use 2,000 bootstrap replications, resampling non-recipient observations at the firm level." →
> …and use 2,000 bootstrap replications that resample both sides: recipients are resampled with replacement (each recipient contributes one observation per stratum, so this is firm-level resampling on the treated side), and non-recipient observations are resampled by firm cluster. Propensity-odds weights are estimated once on the original sample and held fixed within replications; Section C.2 reports schemes that re-estimate the weights in every replication.

**C.2 — EB 증보(신규 문단 + Table C1 열 추가)**:
> As a stricter balance standard, we replace propensity-odds weights with entropy-balancing weights that impose exact balance on every mean (including ROA), on calendar-year indicators, and on the second moments of pre-event growth, leverage, ROA, and cash. All standardized differences are zero by construction (against a maximum of 0.123 under propensity weighting), with an effective comparison size of 9,303 in the distressed stratum. The distributional contrasts are essentially unchanged: the distressed median difference is −0.002 [−0.033, +0.061], the tenth percentile −0.338 [−0.483, −0.163], and the severe-contraction excess 13.6 percentage points [6.9, 21.0]; the non-distressed stratum behaves the same way (median +0.017 [−0.026, +0.038]; tenth percentile −0.223 [−0.323, −0.055]). Re-estimating the propensity weights inside every bootstrap replication rather than holding them fixed also leaves the intervals materially unchanged (distressed tenth percentile −0.335 [−0.490, −0.167]). The same-state tail difference depends on neither the residual imbalance of the baseline weighting nor on treating the estimated weights as known.
Table C1: 열 추가(PS/EB × 층) — EB 열은 전 행 0.000, Max |SMD| 행 0.123→0.000, 0.009→0.000. Notes: "EB = entropy balancing on means, calendar-year indicators, and second moments of pre-event growth, leverage, ROA, and cash; weights are re-solved in each bootstrap replication; effective sizes 9,303 (distressed) and 60,407 (non-distressed)."

---

## §11. Appendix D

**D.2 끝**: "Appendix D.3–D.4 quantify this concern." 연결문.

**D.3 (신설 — LOO; 09-02 §4)**:
> D.3. Influence of the most extreme recipients
> Removing the m most negative matched outcomes one at a time and cumulatively, the pooled event-minus-pseudo tenth-percentile contrast declines in magnitude but keeps its sign throughout: −0.253 in the full sample, −0.155 after removing the five most extreme recipients, −0.115 after ten, and −0.076 after fifteen (7.1% of the sample). Each of the fifteen single-firm deletions leaves the contrast negative. Attenuation is expected mechanically — the statistic is a lower-tail contrast — but the pattern shows an order-statistic artifact of a handful of firms is not driving the result.

**D.4 (신설 — entity-restructuring 스크린 + 타이밍 감사)**:
> D.4. Entity-restructuring screen
> Because NPS employment is recorded at the legal-entity registration number, a merger, division, or business transfer can reduce measured employment without an equivalent economy-wide job loss. A DART screen over each recipient's window from three days before the announcement through thirteen months after flags 57 of 210 recipients with a merger, division, business- or asset-transfer, or share-exchange filing. Excluding all 57, the pooled tenth-percentile contrast is −0.137 [−0.299, −0.006] and the severe-contraction excess 6.6 percentage points [0.7, 13.0]; adding the four dissolution-related filers changes little (−0.138 [−0.304, −0.007]). The excess tail is therefore not an artifact of legal-entity reorganizations alone, although reorganization events account for part of its magnitude: 14 of the 35 severe relative contractions carry such a filing, against 24.6% of the other recipients. A filing-level timing audit sharpens the reading: among those 14 cases, the first own-firm employment crossing of −0.35 log points precedes the filing in six and follows it in seven, so administrative reallocation may contribute to measured severity in up to half of the flagged severe cases — which is why the reorganization-excluded contrast above is the appropriate conservative benchmark.
> Control-change filings behave differently. Sixty-nine recipients have a largest-shareholder-change or management-control filing in the same window, and these filings concentrate sharply in the severe tail (25 of 35 severe cases, versus 25.1% of the rest); they cluster at the placement month itself (15 of 25 within two months of the announcement), well before the employment crossing accumulates at a median of five months after the event. A control change does not move workers off the entity's registration, so it is not a measurement artifact; it is part of the post-placement adjustment the paper measures. Excluding these firms as well removes 97 of 210 recipients and, mechanically, the tail contrast (+0.07 [−0.11, +0.15]). We report this as a conditioning diagnostic rather than a robustness requirement: dropping firms because severe adjustment materialized conditions the sample on the outcome. Read jointly, severe post-placement contractions frequently coincide with subsequent control transitions — consistent with the placement marking entry into a restructuring region — while the measurement-specific screen leaves the tail intact.
(+ Table: §1j — 마지막 행 라벨 "diagnostic" 명시; Notes: "Firms are removed from both the actual-event and pseudo-event arms. The last two rows condition on a post-placement outcome and are reported as diagnostics, not robustness checks.")

**NPS↔DART 종업원수 외부검증**: 현 데이터 빌드에 사업보고서 종업원수 필드가 없어 이번 회차 제외(수집 시 상관·중앙절대편차 1표로 추가 가능) — 원고에는 쓰지 않는다.

---

## §12. References — 최종 구성 (총 20, 전건 Crossref 검증 완료)

기존 4 + 신규 16. 인용 위치는 §3 문단 6과 KKW 문단. Takahashi–Takaoka는 선택(+1 → 21).

기존: Brown & Floros (2012, JCF 18, 151–165) · Chakraborty & Gantchev (2013, JFE 108, 213–230) · Davis et al. (2014, AER 104, 3956–3990) · Graham et al. (2023, JF 78, 2087–2137).

신규 — private placement/PIPE:
> Wruck, K. H. (1989). Equity ownership concentration and firm value: Evidence from private equity financings. Journal of Financial Economics, 23(1), 3–28. https://doi.org/10.1016/0304-405X(89)90003-2
> Hertzel, M., and Smith, R. L. (1993). Market discounts and shareholder gains for placing equity privately. Journal of Finance, 48(2), 459–485. https://doi.org/10.1111/j.1540-6261.1993.tb04723.x
> Hertzel, M., Lemmon, M., Linck, J. S., and Rees, L. (2002). Long-run performance following private placements of equity. Journal of Finance, 57(6), 2595–2617. https://doi.org/10.1111/1540-6261.00507
> Brophy, D. J., Ouimet, P. P., and Sialm, C. (2009). Hedge funds as investors of last resort? Review of Financial Studies, 22(2), 541–574. https://doi.org/10.1093/rfs/hhl045  [Crossref 연도 2006은 advance access — 인쇄본 2009로 인용]
> Chaplinsky, S., and Haushalter, D. (2010). Financing under extreme risk: Contract terms and returns to private investments in public equity. Review of Financial Studies, 23(7), 2789–2820. https://doi.org/10.1093/rfs/hhq035
> Lim, J., Schwert, M., and Weisbach, M. S. (2021). The economics of PIPEs. Journal of Financial Intermediation, 45, 100832. https://doi.org/10.1016/j.jfi.2019.100832

신규 — 한국 포지셔닝:
> Kim, W., Ko, Y., and Wang, S.-F. (2019). Debt restructuring through equity issues. Journal of Banking & Finance, 106, 341–356. https://doi.org/10.1016/j.jbankfin.2019.07.002

신규 — finance & labor:
> Hotchkiss, E. S. (1995). Postbankruptcy performance and management turnover. Journal of Finance, 50(1), 3–21. https://doi.org/10.1111/j.1540-6261.1995.tb05165.x
> Agrawal, A. K., and Matsa, D. A. (2013). Labor unemployment risk and corporate financing decisions. Journal of Financial Economics, 108(2), 449–470. https://doi.org/10.1016/j.jfineco.2012.11.006
> Brown, J., and Matsa, D. A. (2016). Boarding a sinking ship? An investigation of job applications to distressed firms. Journal of Finance, 71(2), 507–550. https://doi.org/10.1111/jofi.12367
> Falato, A., and Liang, N. (2016). Do creditor rights increase employment risk? Evidence from loan covenants. Journal of Finance, 71(6), 2545–2590. https://doi.org/10.1111/jofi.12435
> Caggese, A., Cuñat, V., and Metzger, D. (2019). Firing the wrong workers: Financing constraints and labor misallocation. Journal of Financial Economics, 133(3), 589–607. https://doi.org/10.1016/j.jfineco.2017.10.008
> Baghai, R. P., Silva, R. C., Thell, V., and Vig, V. (2021). Talent in distressed firms: Investigating the labor costs of financial distress. Journal of Finance, 76(6), 2907–2961. https://doi.org/10.1111/jofi.13077
> Benmelech, E., Bergman, N., and Seru, A. (2021). Financing labor. Review of Finance, 25(5), 1365–1393. https://doi.org/10.1093/rof/rfab013

신규 — 최근 FRL (comment2 §17 필수 1–2건):
> Liu, J., Jin, Y., and Xu, C. (2024). The impact of introducing strategic investors on corporate ESG performance—Empirical evidence from private placements in China. Finance Research Letters, 70, 106297. https://doi.org/10.1016/j.frl.2024.106297
> Han, J., and Xiao, C. (2025). Role of private placement targets in shaping long-term corporate performance. Finance Research Letters, 79, 107308. https://doi.org/10.1016/j.frl.2025.107308
> (선택) Takahashi, K., and Takaoka, S. (2026). When bookbuilding uncertainty hits: Pricing and real effects of primary-market uncertainty. Finance Research Letters, 100, 110028. https://doi.org/10.1016/j.frl.2026.110028

claim-인용 연결(rule 01): 할인·정보비대칭 Hertzel-Smith · 사후 저성과 Hertzel et al. · last-resort Brophy·Lim · 계약조건 Chaplinsky-Haushalter · 소유구조 Wruck · 부실 recap Korea KKW · 고용×부실 Hotchkiss/Brown-Matsa/Baghai · 금융마찰→노동 Agrawal-Matsa/Falato-Liang/Caggese/Benmelech · FRL 근접 Liu/Han-Xiao. FRL 관행: 150편 실측 중위 24·하위10% 16 — 20개는 관행 내.

---

## §13. 쓰지 말 것 (규칙 10·11 + 이번 회차 확정분)

1. **"no heterogeneity" / "purpose does not matter"** — MDE ±21pp라 배제 불가. 상한: "the data do not establish purpose as a moderator" + MDE 병기.
2. **common 116을 co-primary/headline으로** — i02 KILL. "composition diagnostic"까지만.
3. **"results are nearly unchanged under the payment anchor"** 단정 — 두 anchor 수치 병기 형태만.
4. **"the placement causes/triggers restructuring"** — state-revealing 서술만.
5. **p25를 유의 결과로 인용** — full-design에서 0 포함. 본문 문단 1의 정직 반문장 필수.
6. **preregistration 어휘** (preregistered·pre-analysis plan·frozen·outcome-blind 등) — 원고 금지(규칙 10).
7. **"original construction" 이력 서술** — B.5의 최소 표현("under its original construction")만 허용.
8. **±5pp 등가밴드 서술을 raw 수준에 적용** — 등가 판정은 prediction-benchmark estimand(Figure B1/Table B2)에 한정. raw 수준에서 t−18은 9.2%로 이미 상승.
9. **ctrl-change 제외 후 소멸을 robustness 실패로 서술** — post-treatment conditioning 진단으로만.
10. **IV·PSM-DID·outcome 확장·추가 이질성 분할·t−12 clock** — 하지 않는다(comment2 자체 지침).

---

## §14. 단어 예산 (FRL < 2,500)

현행 본문 ≈ 2,450단어. 순증 요인: §3.2 재작성(+~120) · intro 재구성(+~80) · §2 문장들(+~90) · 3.3 추가(+~50) · 결론(+~40) = +380. 절감 요인: §3.2 구 문단 2개 삭제(−~160) · caveat 반복 삭제(−~60) · intro 문단 정리(−~60) · §3.4 본문 생략 시(−~120). **권고 기본안: §3.4(rescue)는 본문 생략(Table 1 Panel C도 생략), 부록 신설 절(가칭 C.6 또는 B.9)로 — 순증 ≈ +100 이내로 관리.** 최종 카운트 후 2,400 미만 목표.

---

## §15. 부록 구조 최종안

A setting/sample/measurement (A.1 payment anchor 증보 · A.2 v3 수치+선택표 · A.3 stake · A.4 유지)
B primary design validation and inference — "Matching and **benchmark** diagnostics" (B.1 · B.2 prediction benchmarks(개칭) · B.3 pseudo-event 구성 + Figure B1(구 Fig1) · B.4 대조 + B.4.1 full-design · B.5 grid(pooled featured) · B.6 permutation · B.7 concurrent + ctrl 제외 · B.8 sub-window)
C same-state benchmark (C.1 부트 서술 정정 · C.2 EB 증보 · C.3–C.5 유지 · (선택) C.6 rescue)
D measurement/sample-selection robustness (D.1 · D.2 · D.3 LOO · D.4 restructuring 스크린+타이밍)
E descriptive flows (유지)

---

## §16. 반영 후 검증 절차 (순서 고정)

1. 원고·부록 개정 → md/docx 저장.
2. **검증기 입력 확장**: `wp13_verify_draft.py`의 아티팩트 풀에 `shared/outputs/pipe_wp15_2026-09-03/*.json`과 `…/out/I0{1,2,3}.json` 추가 (신규 수치가 미매칭으로 뜨지 않게).
3. `python3 papers/P016_pipe-employment/06_code/wp13_verify_draft.py` — 미매칭 0(오탐 제외)·철회문자열 0 확인.
4. 교차 일관성 수동 4점: ① severe 10.2pp가 초록·§3.2·Table 1·Fig1 caption에서 전부 [4.8, 15.8]와 짝인지 ② 16.7%·4.8–5.6%·9.2%가 초록↔§3.2↔Fig1 일치 ③ 209/210 표기가 §2 정의와 Table A1 흐름에 맞는지 ④ B.5 표가 "uniform band" 라벨을 달고 있는지.
5. docx 재생성(`10_submission/md2docx.sh`) → 단어 수 확인(<2,500).
6. 노트북 대조: repo `notebooks_FRL/01–03`이 개정 후 수치와 일치하는지 — 특히 01은 구 Figure 1(wp11fg) 기준이므로 **개정 채택 시 01 노트북의 Fig1 셀을 수준 그림으로 갱신 필요**(가이드 반영 후 요청 시 실행).

---

## §17. 산출물 소스 맵 (수치 → 아티팩트)

| 수치 블록 | 아티팩트 (repo `artifacts/`) | 로컬 소스 |
|---|---|---|
| Table 1 기존 4행·B3·B4 | `wp13c_pooled_placebo.json` | pipe_wp13_2026-08-26 |
| severe 행·clock 수준·per-clock sev·purity·rescue | `wp15_comment2_battery.json` | pipe_wp15_2026-09-03 |
| full-design(B.4.1) | `wp15b_fullboot.json` | 〃 |
| payment anchor(A.1) | `wp15c_payment.json` | 〃 |
| restructuring(D.4) | `wp15d_restruct.json` | 〃 |
| same-state EB(C.2) | `wp15e_samestate_eb.json` | 〃 |
| grid(B.5)·LOO(D.3)·선택(A.2) | `wp14_comment_battery.json` | pipe_wp14_2026-09-02 |
| sub-window(B.8·§3.2) | `wp14a_subwindow.json` | 〃 |
| 타이밍 감사(D.4) | `I01.json` | pipe_wp15_2026-09-03/out |
| common116 full-design KILL | `I02.json` | 〃 |
| rescue MDE | `I03.json` | 〃 |
| FRL 서지 | `crossref_verify3.json` | 〃 |
| same-state 기존(C1–C4) | `wp12b.json` · `wp12c_balance.json` | pipe_wp12_2026-08-26 |
| prediction benchmark(B.2·Fig B1) | `wp11e.json` · `wp11fg.json` | pipe_wp11_2026-08-23 |
| t−24 원구축 grid | `wp11d.json` | 〃 |
| permutation(B.6) | `wp9c_permutation.json` | pipe_wp9_2026-08-23 |

재현 노트북: `notebooks_FRL/01_paper_FRL` (현행 인쇄값) · `02_appendix_FRL` (부록) · `03_comment2_FRL` (이번 회차 신규 — 27셀, 위 표의 신규 수치 전수 assert).
