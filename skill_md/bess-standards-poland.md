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
  └── E.ON Stoen Operator (바르샤바, 구 innogy Stoen — 약 2022년 E.ON으로 리브랜딩)
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

> 아래 값은 IRiESP / PN-EN 50549-2 범위에 기반한 **대표 정정값(예시)**이며, 실제 정정은 PSE 연계조건(Warunki Przyłączenia)·계통해석 결과로 확정해야 한다([요확인 — PSE 연계조건 확정]).

| 계전기 (ANSI) | 대표 정정값 | 동작 시간 | 근거 |
|---|---|---|---|
| 과주파수 (81O) | > 51.5 Hz | ~0.5 s | IRiESP / RfG OF 범위 |
| 저주파수 (81U) | < 47.5 Hz | ~0.3 s | IRiESP / RfG UF 범위 |
| 과전압 (59) | > 1.10 p.u. (121 kV) | ~1.5 s | PN-EN 50549-2 |
| 저전압 (27) | < 0.85 p.u. (93.5 kV) | ~1.5 s | PN-EN 50549-2 / LVRT 협조 |
| ROCOF (81R) | > 1.0 Hz/s (NIP 강화 시 ~2.0) | ~0.15 s | RfG §15 / IRiESP |
| 과전류 (50/51) | 정격의 1.2~1.5배 | TCC 협조 | 계통 단락전류 해석 기반 [요확인] |

> ⚠️ 모든 정정값은 **PSE/DSO 연계조건 + 계통해석(조류·단락·보호협조)** 으로 확정한다. 단일 값 확정 금지, 미확정 항목은 [요확인] 유지.

---

## 받는 인풋 / 필요 정보 (INPUT)

판정·산출물 작성 전에 아래 입력을 확보한다. 미확보 항목은 [요확인] 태그로 발행 후 진행한다.

| 입력 항목 | 단위/형식 | 용도 | 미확보 시 |
|---|---|---|---|
| 연계점 정격 출력 P | MW (AC) | RfG Type 분류(≥50MW Type D) · URE 면허 구분 | 분류 불가 → 판정 보류 |
| 연계 전압 | kV (예: 15.75/110/220/400) | IRiESP(송전)/IRiESD(배전) 적용 분기 | [가정] MV 가정 + 사유 |
| 접속 계통 구분 | 송전(PSE) / 배전(DSO) | 연계조건·관할 기관 결정 | [요확인] |
| 담당 DSO | PGE/Tauron/Energa/ENEA/E.ON Stoen | IRiESD·연계조건 양식 분기 | [요확인] |
| 배터리 화학·정격 에너지 | LFP/NMC, MWh | EN 62619·IEC 62933 적합성 | [요확인] |
| 목표 시장 서비스 | Rynek Mocy(용량)/밸런싱/Arbitrage | 수익모델·자격 매핑 | [가정] 용량시장 기준 |
| 부지 좌표·환경 정보 | 위경도, RDOŚ 보호구역 인접 여부 | 환경 스크리닝 | [요확인] |
| 요청 산출물 형식 | Word/Excel/PDF | bess-output-generator 연계 | 미명시 → output-generator 우선 호출 |

---

## 핵심 역량 및 업무 범위 (PROCESS — 적합성 판정 절차·체크리스트)

폴란드 BESS 규격 적합성 판정을 **수치 + 조항 번호 + 합격/불합격 기준**으로 수행한다.

### 1단계: RfG 분류 및 계통 요건 매핑
- [ ] **Type 분류** — EU RfG 2016/631 + 폴란드 NIP: BESS ≥ 50MW 또는 110kV+ 연계 → Type D. P[MW]·연계전압[kV] 명시.
- [ ] **계통운영규정 적용** — 송전 연계 IRiESP(PSE) / 배전 연계 IRiESD(DSO) 분기. 적용 규정 명시.
- [ ] **주파수·ROCOF 요건** — RfG 범위 + 폴란드 NIP 강화값 대조. 합격: 설계값 ≥ NIP 요구값.

### 2단계: 연계 조건(Warunki Przyłączenia) 및 보호 정정 검증
- [ ] **연계조건 신청** — Rozporządzenie w sprawie warunków przyłączenia 근거, PSE/DSO 연계조건 확보.
- [ ] **보호 정정값 검증** — 위 보호계전기 표 항목별 설계값 vs 연계조건 요구값 대조(Hz·p.u.·Hz/s·s 수치). 비정량 "양호" 금지.

### 3단계: 제품·ESS 안전 적합성
- [ ] **EN 50549-2:2019** (HV 연계), **IEC 62933-5-2**(ESS 안전), **EN 62619**(산업 리튬이온), **PN-EN 50160**(전력품질), **PN-EN 62271/60076**(개폐장치·변압기) 적용 여부 매핑.

### 4단계: 시장 참여·인허가
- [ ] **용량시장(Rynek Mocy)** — Ustawa o rynku mocy(2017) ESS 참여 자격·경매 일정 확인.
- [ ] **면허·인허가** — URE 발전 면허(Koncesja), 환경(RDOŚ), 건설허가 로드맵. 실무 신청은 `bess-permit-europe` 담당.

---

## 산출물 (OUTPUT)

| 산출물 | 형식 | 필수 포함 요소 |
|---|---|---|
| 규격 적합성 매핑표 (PL) | Excel (.xlsx) | EU/국내 규정·표준별 적용 여부·조항·합격·불합격(수치) |
| 보호 적합성 체크리스트 | Excel/Word | 보호계전기 항목별 설계값/연계조건 요구값/판정 |
| 인허가·시장참여 로드맵 (PL) | Word/PDF | URE 면허·연계조건·용량시장·환경 마일스톤 |

> 모든 산출물: 수치+단위(MW/kV/Hz/Hz/s/p.u./%) + 규정 조항 인용 필수. 정정값은 PSE/DSO 연계조건 확정 전 [요확인]. 최종 출력 형식은 bess-output-generator 검토를 거친다.

---

## 라우팅 키워드
PL, 폴란드, URE, PSE, TGE, IRiESP, IRiESD, PN-EN, PSP, KPO, Capacity Market Poland,
Rynek Mocy, Prawo Energetyczne, Ustawa OZE, NFOŚiGW, Warunki Przyłączenia, RDOŚ
bess-standards-poland

## 운영 학습 (Operational Learnings)

> 근거: `.connect-ai-bess-brain` 세션 마이닝 (2026-06-08). 전 도메인 공통 규칙은 [`CONSISTENCY_GUARDRAILS.md`](./CONSISTENCY_GUARDRAILS.md) 참조.

### 재사용 지식 (세션 누적)
- 기관: URE(에너지규제청, ≥50MW Type D 면허), PSE(TSO, IRiESP), DSO 5사(PGE/Tauron/Energa/ENEA/E.ON Stoen[구 innogy Stoen, ~2022 리브랜딩]) — 근거: `sessions/2026-05-25T04-45-20/bess-standards-poland.md`
- 법령: Prawo Energetyczne, Ustawa OZE(재생에너지·ESS 정의), Ustawa o rynku mocy(용량시장); EU RfG 2016/631, SOGL 2017/1485 — 근거: `sessions/2026-05-25T04-45-20/bess-standards-poland.md`
- 표준: EN 50549-2:2019(HV 연계), PN-EN 50160(전력품질), PN-EN 62271/60076 시리즈, IEC 62933-5-2 — 근거: `sessions/2026-05-25T04-45-20/bess-standards-poland.md`

### 정합성 가드레일 (반복 오류 차단)
- ❌ 세션 1건뿐, 보호계전기 표 미완(110kV 과전압만) → ✅ 추가 세션 누적·검증 후 보호계전기 정정값 확정 — 근거: `sessions/2026-05-25T04-45-20/bess-standards-poland.md`
