---
name: bess-standards-poland
description: "BESS EPC 폴란드(PL) 규격·표준·인허가 상세"
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

## 🇵🇱 폴란드 (Poland)

### 관할 기관
```
URE (Urząd Regulacji Energetyki)
  — 에너지 규제청: 발전 면허(Koncesja), 요금 규제, 시장 감독
PSE (Polskie Sieci Elektroenergetyczne)
  — 폴란드 TSO: 계통 운영, 발란싱, 계통연계 허가
DSO (배전사업자):
  ├── PGE Dystrybucja
  ├── Tauron Dystrybucja
  ├── Energa-Operator
  ├── ENEA Operator
  └── innogy Stoen Operator (바르샤바)
ENTSO-E — EU 기준 최상위
```

### 핵심 법령 · 규격
```
EU 규정 (상위 — 직접 적용)
├── EU RfG 2016/631 (BESS ≥ 50MW: Type D)
└── EU SOGL 2017/1485

폴란드 국내 규정
├── Prawo Energetyczne (에너지법, 1997년 제정, 수시 개정)
│   └── 발전·배전·거래 면허, 계통연계 의무, 요금 규제 근거
├── IRiESP (Instrukcja Ruchu i Eksploatacji Sieci Przesyłowej)
│   └── PSE 계통운영규정: 송전계통 연계·운영·보호 기준
├── IRiESD (Instrukcja Ruchu i Eksploatacji Sieci Dystrybucyjnej)
│   └── 배전계통운영규정: 중/저전압 연계 기준
├── Rozporządzenie w sprawie warunków przyłączenia
│   └── 계통연계 조건 시행령 (에너지부 고시)
├── Ustawa OZE (재생에너지법, 2015)
│   └── 재생에너지 경매, ESS 정의, 하이브리드 설비 규정
└── Ustawa o rynku mocy (용량시장법, 2017)
    └── 용량 경매, ESS 참여 자격, 의무 이행 규정

기술 표준
├── EN 50549-2:2019 — 발전설비 계통 연계 (HV)
├── IEC 62933-5-2 — ESS 안전
├── IEC 61850 — 변전소 통신
├── PN-EN 50160 — 전력품질 (Polish National Standard)
├── PN-EN 62271 series — 고압개폐장치
├── PN-EN 60076 series — 변압기
└── PN-IEC 60364 — 저압 전기설비
```

### 보호계전기 기준 (폴란드 110kV)
| 계전기 | 정정값 | 동작 시간 | 근거 |
|--|--|


---

## 라우팅 키워드
PL, 폴란드, URE, PSE, TGE, IRiESP, IRiESD, PN-EN, PSP, KPO, Capacity Market Poland,
Rynek Mocy, Prawo Energetyczne, Ustawa OZE, NFOŚiGW, Warunki Przyłączenia, RDOŚ
bess-standards-poland

## 운영 학습 (Operational Learnings)

> 근거: `.connect-ai-bess-brain` 세션 마이닝 (2026-06-08). 전 도메인 공통 규칙은 [`CONSISTENCY_GUARDRAILS.md`](./CONSISTENCY_GUARDRAILS.md) 참조.

### 재사용 지식 (세션 누적)
- 기관: URE(에너지규제청, ≥50MW Type D 면허), PSE(TSO, IRiESP), DSO 5사(PGE/Tauron/Energa/ENEA/innogy Stoen) — 근거: `sessions/2026-05-25T04-45-20/bess-standards-poland.md`
- 법령: Prawo Energetyczne, Ustawa OZE(재생에너지·ESS 정의), Ustawa o rynku mocy(용량시장); EU RfG 2016/631, SOGL 2017/1485 — 근거: `sessions/2026-05-25T04-45-20/bess-standards-poland.md`
- 표준: EN 50549-2:2019(HV 연계), PN-EN 50160(전력품질), PN-EN 62271/60076 시리즈, IEC 62933-5-2 — 근거: `sessions/2026-05-25T04-45-20/bess-standards-poland.md`

### 정합성 가드레일 (반복 오류 차단)
- ❌ 세션 1건뿐, 보호계전기 표 미완(110kV 과전압만) → ✅ 추가 세션 누적·검증 후 보호계전기 정정값 확정 — 근거: `sessions/2026-05-25T04-45-20/bess-standards-poland.md`
