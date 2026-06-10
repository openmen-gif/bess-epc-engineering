---
name: bess-standards-uk
description: "BESS EPC 영국(UK) 규격·표준·인허가 상세"
---

> [!NOTE]
> **[Hybrid 에이전트 호환성 구문]**
> - **VSCode (Claude Code) 인식용:** 이 문서를 전문가 페르소나(Persona)의 지식 컨텍스트로 활용하여 텍스트 및 코드 기반 답변을 사용자에게 제공하세요.
> - **Antigravity (Agent) 인식용:** 이 문서를 도메인 지식(Skill)으로 로드하세요. 계산, 파일 생성 또는 시스템 연동이 필요한 경우, 직접 Python 코드를 작성하고 터미널 도구(`run_command`)를 실행하여 워크플로우를 완수하세요.

> **규격 스킬 체계**: 본 문서는 bess-standards-analyst 시장별 상세 중 하나이다.
> - 공통: bess-standards-analyst (비교표·산출물·원칙)
> - 한국: bess-standards-korea (KR)
> - 일본: bess-standards-japan (JP)
> - 미국: bess-standards-usa (US)
> - 호주: bess-standards-australia (AU)
> - 영국: bess-standards-uk (UK)
> - 유럽: bess-standards-eu (EU)
> - 루마니아: bess-standards-romania (RO)
> - 폴란드: bess-standards-poland (PL)

## 🇬🇧 영국 (United Kingdom)

### 관할 기관
```
Ofgem (Office of Gas and Electricity Markets) — 전력 규제
National Grid ESO (Electricity System Operator) — 계통 운영 (2024~: NESO로 전환)
  → NESO (National Energy System Operator) 2024년 10월 설립
DNOs (Distribution Network Operators)         — 지역 배전 운영자
  (UK Power Networks / Western Power / Northern Powergrid 등)
Elexon                                        — BSC (Balancing and Settlement Code) 운영
```

### 핵심 법령 · 규격
```
1차 법령
├── Electricity Act 1989
├── Energy Act 2023 — ESS 독립 라이선스 도입
│   → 기존: 발전/공급 면허 내 포함
│   → 신규: ESS 전용 라이선스 (2025년 이후 시행 예정) [요확인]
└── Climate Change Act 2008 — 넷제로 법적 의무

기술 규정
├── G99 (ENA Engineering Recommendation G99)
│   — 발전설비 계통 연계 기준 (최신: Issue 6, 2024)
│   ├── §6   — 전압 범위
│   ├── §7   — 주파수 범위
│   ├── §8   — ROCOF 및 벡터 이동
│   ├── §12  — LVRT / HVRT
│   └── §16  — 계량 및 원격 통신
├── G100 — 소규모 ESS (≤ 50kW) 연계 기준
├── ER P2/8 — 계통 보안 기준
├── BS EN 62933-5-2 — ESS 안전 요건
└── IEC 61850       — 통신 (132kV 이상)
```

### 보호계전기 기준 (G99 기준, 132kV)

> 아래 값은 ENA G99(Issue 6, 2024) 표준 보호 정정 범위에 기반한 **대표 정정값(예시)**이며, 실제 정정은 NESO/DNO 연계협의(Connection Offer)·계통해석 결과로 확정해야 한다([요확인 — DNO/NESO 연계협의 확정]).

| 계전기 (ANSI) | 대표 정정값 | 동작 시간 | 근거 |
|---|---|---|---|
| 과주파수 (81O) | > 51.5 Hz | ~0.5 s | G99 §7 (주파수 범위) |
| 저주파수 (81U) | < 47.5 Hz | ~20 s (지연), <47.0 Hz 즉시 | G99 §7 |
| 과전압 (59) | > 1.10 p.u. (≈145 kV) | ~1.0 s | G99 §6 (전압 범위) |
| 저전압 (27) | < 0.80 p.u. | LVRT 프로파일 협조 | G99 §12 (LVRT/HVRT) |
| ROCOF (81R) | 1.0 Hz/s (G99 권고, 최대 ~1.0) | ~0.5 s | G99 §8 (ROCOF·벡터이동) |
| 과전류 (50/51) | 정격의 1.2~1.5배 | TCC 협조 | ER P2/8 / 단락전류 해석 [요확인] |

> ⚠️ 모든 정정값은 **NESO/DNO 연계협의 + 계통해석(조류·단락·보호협조)** 으로 확정한다. 단일 값 확정 금지, 미확정 항목은 [요확인] 유지.

---

## 받는 인풋 / 필요 정보 (INPUT)

판정·산출물 작성 전에 아래 입력을 확보한다. 미확보 항목은 [요확인] 태그로 발행 후 진행한다.

| 입력 항목 | 단위/형식 | 용도 | 미확보 시 |
|---|---|---|---|
| 연계점 정격 출력 P | MW (AC) | G99 Type(A~D) 분류 · 연계 경로 결정 | 분류 불가 → 판정 보류 |
| 연계 전압 | kV (예: 11/33/132/275/400) | DNO(배전) vs NESO(송전) 분기 | [가정] MV 가정 + 사유 |
| 접속 계통 구분 | 배전(DNO) / 송전(NESO) | 연계협의 경로·양식 결정 | [요확인] |
| 담당 DNO | UK Power Networks/Western Power/Northern Powergrid 등 | 지역 연계협의 분기 | [요확인] |
| 배터리 화학·정격 에너지 | LFP/NMC, MWh | BS EN 62933·EN 62619 적합성 | [요확인] |
| 목표 시장 서비스 | Capacity Market/밸런싱/Arbitrage | 수익모델·BSC 정산 매핑 | [가정] 밸런싱 기준 |
| ESS 라이선스 구분 | 발전·공급 면허 내 / ESS 전용 | Energy Act 2023 적용 | [요확인] (2025 이후 시행 예정) |
| 요청 산출물 형식 | Word/Excel/PDF | bess-output-generator 연계 | 미명시 → output-generator 우선 호출 |

---

## 핵심 역량 및 업무 범위 (PROCESS — 적합성 판정 절차·체크리스트)

영국 BESS 규격 적합성 판정을 **수치 + 조항 번호 + 합격/불합격 기준**으로 수행한다.

### 1단계: G99 분류 및 계통 요건 매핑
- [ ] **연계 경로** — 배전(≤132kV, DNO) vs 송전(NESO) 구분. 연계전압[kV]·정격[MW] 명시.
- [ ] **G99 적용** — ENA G99 Issue 6(2024) [요확인 — 최신 Issue 연도 확인]: §6 전압·§7 주파수·§8 ROCOF·§12 LVRT/HVRT·§16 계량·통신.
- [ ] **소규모 예외** — ≤50kW는 G100 적용(BESS 대형은 비해당).

### 2단계: 연계협의 및 보호 정정 검증
- [ ] **연계협의** — DNO/NESO Connection Offer 확보, 보호 정정 요구값 수령.
- [ ] **보호 정정값 검증** — 위 보호계전기 표 항목별 설계값 vs 연계협의 요구값 대조(Hz·p.u.·Hz/s·s 수치). 비정량 "양호" 금지.

### 3단계: 제품·ESS 안전 적합성
- [ ] **BS EN 62933-5-2**(ESS 안전, EN의 BS 채택본), **IEC 61850**(132kV+ 통신), **UKCA 마킹** 적용 여부 매핑.

### 4단계: 시장 참여·라이선스
- [ ] **Capacity Market·밸런싱** — Elexon BSC 정산, 보조서비스 참여 자격 확인.
- [ ] **라이선스** — Energy Act 2023 ESS 전용 라이선스(2025 이후 시행 예정) [요확인] vs 기존 발전/공급 면허. 실무 인허가는 `bess-permit-english` 담당.

---

## 산출물 (OUTPUT)

| 산출물 | 형식 | 필수 포함 요소 |
|---|---|---|
| 규격 적합성 매핑표 (UK) | Excel (.xlsx) | G99/법령/표준별 적용 여부·조항·합격·불합격(수치) |
| 보호 적합성 체크리스트 | Excel/Word | 보호계전기 항목별 설계값/연계협의 요구값/판정 |
| 인허가·시장참여 로드맵 (UK) | Word/PDF | 라이선스·연계협의·Capacity Market·BSC 마일스톤 |

> 모든 산출물: 수치+단위(MW/kV/Hz/Hz/s/p.u./%) + 규정 조항 인용 필수. 정정값은 DNO/NESO 연계협의 확정 전 [요확인]. 최종 출력 형식은 bess-output-generator 검토를 거친다.

---

## 라우팅 키워드
UK, 영국, G99, UKCA, Ofgem, NationalGrid, ESO, NESO, DNO, DC, DR, DM, CapacityMarket, BSC, Elexon, NIS, NFCC
bess-standards-uk

## 운영 학습 (Operational Learnings)

> 근거: `.connect-ai-bess-brain` 세션 마이닝 (2026-06-08). 전 도메인 공통 규칙은 [`CONSISTENCY_GUARDRAILS.md`](./CONSISTENCY_GUARDRAILS.md) 참조.

### 재사용 지식 (세션 누적)
- ENA G99 Issue 6(2024): §6 전압, §7 주파수 ±0.5Hz, §12 LVRT/HVRT, §16 계량·통신; G100(≤50kW 소규모); ER P2/8 보안 — 근거: `sessions/2026-05-25T04-45-20/bess-standards-uk.md`
- Energy Act 2023: ESS 독립 라이선스 도입(2025 이후 예정, [요확인]); Electricity Act 1989 기본틀 — 근거: `sessions/2026-05-25T04-45-20/bess-standards-uk.md`
- 기관: Ofgem(라이선스), NESO(구 National Grid ESO, 연계·용량시장), DNO(UK Power Networks 등), Elexon(BSC 정산) — 근거: `sessions/2026-05-25T04-45-20/bess-standards-uk.md`

### 정합성 가드레일 (반복 오류 차단)
- ❌ BS EN 62933-5-2를 UK 고유 표준으로 서술 → ✅ EN(유럽)의 BS 채택본, EU와 동일 표준 계열 — 근거: `sessions/2026-05-25T04-45-20/bess-standards-uk.md`
