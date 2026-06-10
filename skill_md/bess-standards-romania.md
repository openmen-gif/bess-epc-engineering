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
├── ANRE Order No. 11/2023 — ESS 관련 [요확인: 최신 개정 확인]
└── Legea Energiei Nr. 123/2012 — 전기에너지법

기술 표준
├── EN 50549-2:2019 — 발전설비 계통 연계 (LV 이상)
├── IEC 62933-5-2   — ESS 안전
├── IEC 61850       — 변전소 통신
└── EN 50160        — 전력품질
```

### 보호계전기 기준 (루마니아 110kV)
| 계전기 | 정정값 | 동작 시간 | 근거 |
|--|--|


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
