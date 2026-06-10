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
| 계전기 | 정정값 | 동작 시간 | 근거 |
|--|--|


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
