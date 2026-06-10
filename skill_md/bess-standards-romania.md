---
name: bess-standards-romania
description: "BESS EPC 루마니아(RO) 규격·표준·인허가 상세"
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

## 🇷🇴 루마니아 (Romania)

### 관할 기관
```
ANRE (Autoritatea Națională de Reglementare în domeniul Energiei)
  — 전력 규제, 계통 연계 인허가 주관
Transelectrica — 루마니아 TSO
Distribuție    — 지역 DSO
ENTSO-E        — EU 기준 최상위
```

### 핵심 법령 · 규격
```
EU 규정 (상위 — 직접 적용)
├── EU RfG 2016/631 (BESS ≥ 50MW: Type D)
└── EU SOGL 2017/1485

루마니아 국내 규정
├── ANRE Order No. 30/2013 — Codul Tehnic al Rețelei (CTR)
├── ANRE Order No. 59/2013 — 계통 연계 허가 절차
├── ANRE Order No. 11/2023 — ESS 관련 [요확인 — 미검증] (오더 번호·연도 1차출처 미확인)
└── Legea Energiei Nr. 123/2012 — 전기에너지법

기술 표준
├── EN 50549-2:2019 — 발전설비 계통 연계 (HV)
├── IEC 62933-5-2   — ESS 안전
├── IEC 61850       — 변전소 통신
└── EN 50160        — 전력품질
```

### 보호계전기 기준 (루마니아 110kV)

> 아래 값은 ANRE CTR(Codul Tehnic al Rețelei) / EN 50549-2 범위에 기반한 **대표 정정값(예시)**이며, 실제 정정은 Transelectrica/DSO 연계조건(ATR)·계통해석 결과로 확정해야 한다([요확인 — ATR 연계조건 확정]).

| 계전기 (ANSI) | 대표 정정값 | 동작 시간 | 근거 |
|---|---|---|---|
| 과주파수 (81O) | > 51.5 Hz | ~0.5 s | CTR / RfG OF 범위 |
| 저주파수 (81U) | < 47.5 Hz | ~0.3 s | CTR / RfG UF 범위 |
| 과전압 (59) | > 1.10 p.u. (121 kV) | ~1.5 s | EN 50549-2 |
| 저전압 (27) | < 0.85 p.u. (93.5 kV) | ~1.5 s | EN 50549-2 / LVRT 협조 |
| ROCOF (81R) | > 1.0 Hz/s (NIP 강화 시 ~2.0) | ~0.15 s | RfG §15 / CTR |
| 과전류 (50/51) | 정격의 1.2~1.5배 | TCC 협조 | 계통 단락전류 해석 기반 [요확인] |

> ⚠️ 모든 정정값은 **Transelectrica/DSO 연계조건(ATR) + 계통해석(조류·단락·보호협조)** 으로 확정한다. 단일 값 확정 금지, 미확정 항목은 [요확인] 유지.

---

## 받는 인풋 / 필요 정보 (INPUT)

판정·산출물 작성 전에 아래 입력을 확보한다. 미확보 항목은 [요확인] 태그로 발행 후 진행한다.

| 입력 항목 | 단위/형식 | 용도 | 미확보 시 |
|---|---|---|---|
| 연계점 정격 출력 P | MW (AC) | RfG Type 분류(≥50MW Type D) · ANRE 면허 구분 | 분류 불가 → 판정 보류 |
| 연계 전압 | kV (예: 20/110/220/400) | 송전(Transelectrica)/배전(DSO) 적용 분기 | [가정] MV 가정 + 사유 |
| 접속 계통 구분 | 송전 / 배전 | 연계조건(ATR)·관할 기관 결정 | [요확인] |
| 배터리 화학·정격 에너지 | LFP/NMC, MWh | EN 62619·IEC 62933 적합성 | [요확인] |
| 목표 시장 서비스 | OPCOM/밸런싱/Arbitrage | 수익모델·자격 매핑 | [가정] 밸런싱 기준 |
| 부지 좌표·환경 정보 | 위경도, 보호구역 인접 여부 | 환경 스크리닝(ISU 소방 포함) | [요확인] |
| 요청 산출물 형식 | Word/Excel/PDF | bess-output-generator 연계 | 미명시 → output-generator 우선 호출 |

---

## 핵심 역량 및 업무 범위 (PROCESS — 적합성 판정 절차·체크리스트)

루마니아 BESS 규격 적합성 판정을 **수치 + 조항 번호 + 합격/불합격 기준**으로 수행한다.

### 1단계: RfG 분류 및 계통 요건 매핑
- [ ] **Type 분류** — EU RfG 2016/631 + 루마니아 NIP: BESS ≥ 50MW 또는 110kV+ 연계 → Type D. P[MW]·연계전압[kV] 명시.
- [ ] **CTR 적용** — ANRE Order 30/2013 Codul Tehnic al Rețelei 송전계통 연계·운영·보호 기준 적용.
- [ ] **주파수·ROCOF 요건** — RfG 범위 + 루마니아 NIP 강화값 대조. 합격: 설계값 ≥ NIP 요구값.

### 2단계: 연계 인허가(ATR/CTR) 및 보호 정정 검증
- [ ] **연계 절차** — ANRE Order 59/2013(연계 허가 절차) 근거, Transelectrica/DSO ATR 확보.
- [ ] **보호 정정값 검증** — 위 보호계전기 표 항목별 설계값 vs ATR 요구값 대조(Hz·p.u.·Hz/s·s 수치). 비정량 "양호" 금지.

### 3단계: 제품·ESS 안전 적합성
- [ ] **EN 50549-2:2019**(HV 연계), **IEC 62933-5-2**(ESS 안전), **IEC 61850**(통신), **EN 50160**(전력품질) 적용 여부 매핑.

### 4단계: 시장 참여·인허가
- [ ] **시장 참여** — OPCOM/밸런싱 시장 참여 자격, ANRE Order 11/2023(ESS) 적용 여부 [요확인 — 미검증].
- [ ] **인허가** — ANRE 면허, ISU 소방, 건설허가, PNRR/NextGenerationEU 자금 연계. 실무 신청은 `bess-permit-europe` 담당.

---

## 산출물 (OUTPUT)

| 산출물 | 형식 | 필수 포함 요소 |
|---|---|---|
| 규격 적합성 매핑표 (RO) | Excel (.xlsx) | EU/국내 규정·표준별 적용 여부·조항·합격·불합격(수치) |
| 보호 적합성 체크리스트 | Excel/Word | 보호계전기 항목별 설계값/ATR 요구값/판정 |
| 인허가·시장참여 로드맵 (RO) | Word/PDF | ANRE 면허·ATR·OPCOM·ISU·PNRR 마일스톤 |

> 모든 산출물: 수치+단위(MW/kV/Hz/Hz/s/p.u./%) + 규정 조항 인용 필수. 정정값은 Transelectrica/DSO ATR 확정 전 [요확인]. 최종 출력 형식은 bess-output-generator 검토를 거친다.

---

## 라우팅 키워드
RO, 루마니아, ANRE, Transelectrica, CTR, ATR, OPCOM, EN50549, ISU, PNRR, NextGenerationEU
bess-standards-romania

## 운영 학습 (Operational Learnings)

> 근거: `.connect-ai-bess-brain` 세션 마이닝 (2026-06-08). 전 도메인 공통 규칙은 [`CONSISTENCY_GUARDRAILS.md`](./CONSISTENCY_GUARDRAILS.md) 참조.

### 재사용 지식 (세션 누적)
- 기관: ANRE(규제, Order 59/2013 연계허가, Order 11/2023 ESS), Transelectrica(TSO), 지역 DSO — 근거: `sessions/2026-05-25T04-45-20/bess-standards-romania.md`
- 표준: EN 50549-2:2019, IEC 62933-5-2, IEC 61850, EN 50160 (PL과 동일 EU 표준 계열) — 근거: `sessions/2026-05-25T04-45-20/bess-standards-romania.md`

### 정합성 가드레일 (반복 오류 차단)
- ❌ 세션 1건, Order 11/2023 최신 개정 [요확인] 미해소·보호계전기 정정값 미기재 → ✅ 추가 세션 누적·검증 후 확정 — 근거: `sessions/2026-05-25T04-45-20/bess-standards-romania.md`
