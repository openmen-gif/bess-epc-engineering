---
name: bess-standards-eu
description: "BESS EPC EU(일반) 규격·표준·인허가 상세"
---

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

## 🇪🇺 EU 일반 (European Union)

### EU 규정 체계 (ENTSO-E 기반)
```
EU 규정 (직접 적용 — 회원국 추가 입법 불필요)
├── Regulation (EU) 2016/631 — RfG (Requirements for Generators)
│   발전 유형별 분류:
│   ├── Type A: P < 0.8kW~1MW (국가별 상이)
│   ├── Type B: 1MW ≤ P < 50MW
│   ├── Type C: 50MW ≤ P < 75MW
│   └── Type D: P ≥ 75MW (또는 국가별 임계값)
│
├── Regulation (EU) 2016/1388 — DCC (Demand Connection Code)
│   → 수요 측 연결 요건 (ESS 충전 모드 시 적용)
│
├── Regulation (EU) 2017/1485 — SOGL (System Operation Guidelines)
│   → 계통 운영자 운영 지침
│
└── Regulation (EU) 2016/1447 — NC HVDC
    → 고압직류(HVDC) 연계 요건

EU 지침 (Directive — 회원국 입법 필요)
├── Electricity Directive 2019/944 — 전력 시장 통합
├── RED II 2018/2001             — 재생에너지 (보조금 체계)
└── EU Battery Regulation 2023/1542 — 배터리 규제 (순환경제)
    → 2025년부터 배터리 여권(Battery Passport) 도입 예정 [요확인]
```

### RfG 발전기 유형별 요건 (Type C/D — 대형 BESS)
```
Type C/D 공통 필수 요건:
├── 주파수 응답 (FSM: Frequency Sensitive Mode) 의무
├── ROCOF 내성: ≥ 2 Hz/s (국가별 강화 가능)
├── LVRT: 전압 0.0pu → 150ms (국가별 상이)
├── 무효전력 능력: 역률 0.95 leading ~ 0.95 lagging
├── 원격 제어: TSO 직접 제어 인터페이스
└── 실제 발전량 모니터링: TSO에 실시간 전송

Type D 추가:
├── 전압 제어 능력 (Voltage Control) 필수
├── 계통 보호 협조: TSO 요건 적용
└── 재동기화 능력 (Re-synchronization)
```

### EU 공통 보호 기준 (RfG Annex III — Type C/D)
| 항목 | 기준값 | 비고 |
|------|--------|------|
| UFR 이탈 | 47.5 Hz | 20초 유지 후 이탈 허용 |
| OFR 이탈 | 51.5 Hz | 즉시 이탈 허용 |
| LVRT (0.0pu) | 140ms 유지 | 이탈 없이 운전 |
| ROCOF 내성 | ≥ 2 Hz/s | 국가별 강화 가능 |

> ⚠️ 각 회원국 TSO는 RfG 기준을 강화할 수 있음 (완화 불가)
> 실제 적용값은 해당국 National Implementation Plan (NIP) 확인 필수

### CE 인증 요건 (상세)
```
필수 CE 마킹 지침:
├── 기계류 규정 (EU) 2023/1230 — Machinery Regulation (2027년 적용)
│   ├── 기존 Machinery Directive 2006/42/EC 대체
│   ├── 디지털 적합성 선언 (Digital DoC) 허용
│   ├── 소프트웨어 안전 요건 강화
│   └── Notified Body 심사: Annex IV 해당 시 필수
├── 저전압 지침 2014/35/EU (LVD):
│   ├── 적용: 50~1000V AC, 75~1500V DC 전기 설비
│   ├── 적합성 평가: 제조사 자기 선언 (Module A)
│   └── 적용 표준: EN 62477-1 (전력변환장치)
├── 전자기 적합성 2014/30/EU (EMC):
│   ├── 고조파 방출: EN 61000-3-12 (16A 초과)
│   ├── 플리커: EN 61000-3-11
│   ├── 내성: EN 61000-6-2 (산업용)
│   └── 방출: EN 61000-6-4 (산업용)
├── RoHS 2011/65/EU — 유해물질 제한:
│   ├── 납, 수은, 카드뮴, 6가 크롬, PBB, PBDE
│   └── 면제: 대형 고정 산업 설비 (BESS 면제 가능 [요확인])
├── ATEX 2014/34/EU — 폭발 위험 구역:
│   ├── 배터리실 가스 방출 시 Zone 2 해당 가능
│   └── 환기 설계로 Zone 해제 일반적
└── Radio Equipment Directive (RED) 2014/53/EU:
    └── 무선 통신 모듈 내장 시 적용

ESS 특화 표준:
├── EN 62933-5-2:2020 — ESS 안전 요건
│   ├── 시스템 레벨 안전 시험
│   └── Harmonised Standard (CE 적합성 추정 근거)
├── EN 62619:2022 — 산업용 리튬이온 배터리 안전
├── EN 63056:2020 — 주거/상업용 리튬이온 배터리
└── EN 62477-1:2012+A11:2014 — 전력변환장치 안전

적합성 선언 (DoC — Declaration of Conformity):
├── 제조사 또는 EU Authorised Representative 발행
├── 적용 지침·규정 목록 명시
├── 적용 Harmonised Standards 목록
├── Notified Body 번호 (해당 시)
├── 기술 문서 (Technical File): EU 내 10년 보관 의무
└── 언어: 해당 회원국 공용어 번역 필요
```

### EU Battery Regulation 2023/1542 (상세)
```
적용 시기 (단계별 시행):
├── 2024년 2월: 규정 발효
├── 2025년 2월: 탄소발자국 선언 의무 (EV/산업용)
├── 2026년 8월: 배터리 여권 (Battery Passport) 도입
├── 2027년: 탄소발자국 성능 등급 라벨
├── 2028년: 재활용 함량 최소 비율 (코발트 16%, 리튬 6%, 니켈 6%)
└── 2031년: 재활용 함량 강화 (코발트 26%, 리튬 12%, 니켈 15%)

산업용 배터리 (BESS 해당) 주요 요건:
├── 탄소발자국 (Carbon Footprint):
│   ├── 제조사: 제품 수명 주기 탄소발자국 산출·선언 의무
│   ├── 방법론: Commission Delegated Act (상세 방법론 제정 중)
│   └── 최대 한도: 2027년 이후 탄소발자국 상한선 설정 예정 [요확인]
├── 배터리 여권 (Battery Passport):
│   ├── QR 코드 기반 디지털 제품 여권
│   ├── 정보: 제조자, 재료 구성, 탄소발자국, 재활용 함량, 성능, 내구성
│   ├── 접근 수준: 공개(일반) + 제한(규제기관/재활용업자)
│   └── ESPR (Ecodesign for Sustainable Products Regulation)과 연계
├── 듀 딜리전스 (Due Diligence):
│   ├── 원자재 공급망 실사 의무 (코발트, 리튬, 니켈, 흑연 등)
│   ├── OECD Due Diligence Guidance 준수
│   └── 분쟁광물 · 아동노동 리스크 평가
├── 성능 · 내구성 요건:
│   ├── 용량 유지율: 80% @2,000 사이클 (권장 — 위임 법령 제정 중)
│   ├── 에너지 효율: Round-trip efficiency 선언
│   ├── 수명: 기대 수명 (年 또는 사이클) 명시
│   └── State of Health (SOH) 데이터: BMS 통해 제공 의무
├── 수거 · 재활용:
│   ├── 생산자 책임 (EPR): 수명 종료 배터리 수거 의무
│   ├── 재활용 효율:
│   │   ├── 2025년: 리튬 50%, 코발트/니켈/구리 90%
│   │   └── 2030년: 리튬 80%, 코발트/니켈/구리 95%
│   └── Second Life: 재사용 시 SOH 데이터 의무 제공
├── 라벨링:
│   ├── 용량 (Ah/kWh), 전압, 제조일, 제조국
│   ├── 분리수거 심볼 (Crossed-out Wheeled Bin)
│   ├── 위험 물질 함유 표시
│   └── CE 마킹 + 배터리 규정 적합 표시
└── Notified Body:
    ├── EU Module B (형식 검사) + Module C (생산 적합)
    └── 대형 산업용 배터리: Notified Body 심사 필수

> ⚠️ [요확인] 배터리 여권 상세 데이터 항목 — Commission Delegated Act 제정 대기 중
> ⚠️ BESS 프로젝트에서 배터리 벤더 선정 시 Battery Regulation 대응 여부 필수 확인
```

### EU 에너지저장 시장 참여 (상세)
```
Electricity Directive 2019/944 §36:
├── TSO/DSO는 에너지저장을 비차별적으로 시장 접근 허용 의무
├── 독립 저장 사업자: TSO/DSO 소유 금지 원칙 (예외 있음)
├── 집합 자원 (Aggregator): 분산형 ESS 집합 참여 허용
└── 비차별적 네트워크 요금 — 충전 시 이중 과금 금지 (점진적 이행)

Balancing Market (ENTSO-E 통합 플랫폼):
┌──────────────────┬───────────┬──────────┬────────────────────────┐
│ 서비스            │ 응답 시간 │ 지속     │ 플랫폼                  │
├──────────────────┼───────────┼──────────┼────────────────────────┤
│ FCR              │ 30초      │ 15분+    │ PICASSO 통합 (2024~)   │
│ aFRR             │ 2분       │ 가변     │ MARI 통합 (2024~)      │
│ mFRR             │ 12.5분    │ 가변     │ TERRE → MARI 통합      │
│ RR (Replacement) │ 30분      │ 가변     │ TERRE 플랫폼           │
└──────────────────┴───────────┴──────────┴────────────────────────┘

├── BESS 적합 서비스: FCR (최적), aFRR (적합)
├── FCR 시장 규모: ~3,000MW (EU 전체)
├── FCR 가격: €3~15/MW/h (국가·시기별 변동)
└── 입찰: 통합 플랫폼 또는 국가 TSO 직접

용량 시장 (국가별 운영):
├── 독일: Strategic Reserve (비시장 기반)
├── 프랑스: Mécanisme de Capacité (용량 의무)
├── 이탈리아: Capacity Market (T-4, T-1 경매)
├── 폴란드: Capacity Market (2025년 ESS 참여 확대)
├── 아일랜드: CRM (Capacity Remuneration Mechanism)
└── 벨기에: CRM (2025년 시작)

에너지 시장:
├── DAM (Day-Ahead Market): SDAC (Single DAM Coupling) 통합
├── IDM (Intraday Market): SIDC (Single IDM Coupling) 연속 거래
├── 정산 기간: 15분 (EU 표준, 2025년 완전 이행)
└── 가격: Zonal Pricing → 각국 Bidding Zone별

EU Taxonomy — ESS 적격 여부:
├── Climate Change Mitigation: ESS 적격 활동
├── 기술 기준: "do no significant harm" 원칙 충족
├── 그린 파이낸싱: EU Green Bond Standard 활용 가능
└── 실질적 기여 기준: 재에너지 통합 지원 입증
```

### 통신 · SCADA 규격 (EU 공통)
```
ENTSO-E 통신 표준:
├── IEC 61850: 변전소 통신 (MMS, GOOSE, SV)
│   ├── IEC 61850-7-420: DER 연계 (ESS 포함)
│   ├── IEC 61850-90-7: DER 기능 모델 (Inverter)
│   └── IEC 61850-8-2: XMPP 기반 (광역 통신)
├── IEC 60870-5-104: 원격 제어 (TCP/IP 기반)
│   ├── TSO → BESS: 제어 명령 (출력/충방전)
│   └── BESS → TSO: 실시간 데이터 (P, Q, V, f, SOC)
├── ICCP/TASE.2: 제어센터 간 통신
├── CIM (Common Information Model): IEC 61968/61970
│   └── 계통 모델 데이터 교환 표준
└── Metering: IEC 62056 (DLMS/COSEM) — 스마트 미터링

EU 사이버보안:
├── NIS 2 Directive (EU) 2022/2555 (2024년 10월 시행):
│   ├── 에너지 부문: "Essential Entity" 지정
│   ├── 사이버 사고 보고: 24시간 이내 초기 보고, 72시간 상세 보고
│   ├── 공급망 보안: 벤더 리스크 평가 의무
│   ├── 과징금: 최대 €10M 또는 매출 2% (중 큰 금액)
│   └── 회원국 국내법 전환 의무
├── Cyber Resilience Act (CRA) 2024:
│   ├── 디지털 제품 보안: CE 마킹 요건에 사이버보안 포함
│   ├── 소프트웨어 업데이트: 수명 주기 동안 보안 패치 제공 의무
│   ├── 취약점 보고: ENISA에 24시간 이내
│   └── 2027년 완전 시행 예정
├── ENISA (EU Agency for Cybersecurity):
│   ├── EU Cybersecurity Certification Framework
│   └── 에너지 부문 위협 분석 보고서 발행
├── IEC 62351: 전력 시스템 통신 보안
│   ├── Part 3: TCP/IP 보안 (TLS 1.2+)
│   ├── Part 4: MMS 보안
│   ├── Part 5: IEC 60870-5 보안
│   └── Part 6: IEC 61850 보안
└── ISO/IEC 27001: 정보보안 관리 체계 (ISMS) — 권장
```

### 환경 · 입지 (EU 공통)
```
EU 환경 지침:
├── EIA Directive 2014/52/EU:
│   ├── Annex I: 필수 환경 영향 평가 (대규모 에너지 설비)
│   ├── Annex II: 회원국 판단 (대부분 ESS는 Annex II)
│   └── Screening → Scoping → EIS → 공공 참여 → 결정
├── Habitats Directive 92/43/EEC:
│   ├── Natura 2000 보호구역 영향 평가
│   └── Appropriate Assessment (AA): 보호구역 인접 시
├── Birds Directive 2009/147/EC:
│   └── 특별보호구역 (SPA) 영향 검토
├── Water Framework Directive 2000/60/EC:
│   └── 수질 영향 평가 (냉각수·소화수 배출)
├── Industrial Emissions Directive (IED):
│   └── 대형 연소 시설 — ESS 일반적 비해당
└── REACH Regulation (EC) 1907/2006:
    └── 배터리 화학물질 등록 (제조사 의무)

EU Taxonomy 환경 기준:
├── 기후변화 완화 기여 입증
├── DNSH (Do No Significant Harm): 6개 환경 목표
│   ├── 기후변화 적응
│   ├── 수자원·해양자원
│   ├── 순환경제 (배터리 재활용)
│   ├── 오염 예방 (유해물질)
│   ├── 생물다양성
│   └── 기후변화 완화
└── 최소 사회적 보호 조치 (인권, 노동권)
```

---


---

## 라우팅 키워드
EU, 유럽, RfG, ENTSO-E, CE마킹, BatteryRegulation, NIS2, EUTaxonomy, SOGL, NCHVDC, PICASSO, MARI, FCR, aFRR
bess-standards-eu
