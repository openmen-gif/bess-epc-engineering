---
name: bess-standards-uk
description: "BESS EPC 영국(UK) 규격·표준·인허가 상세"
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
|--------|--------|---------|------|
| OVR | 1.14 × Un | 0.5s | G99 §6, Table 3 |
| UVR | 0.87 × Un | 2.5s | G99 §6, Table 3 |
| OFR | 51.0 Hz | 0.5s | G99 §7 |
| UFR | 47.5 Hz | 20s | G99 §7 |
| ROCOF | 1.0 Hz/s | 0.5s | G99 §8 (벡터 이동 포함) |

> ⚠️ [요확인] DNO별로 정정값 상이. 해당 DNO의 Distribution Code 확인 필수

### LVRT / HVRT 기준 (G99 §12)
```
LVRT:
├── 전압 0.0pu → 140ms 유지, 이탈 없이 운전
├── 복귀 후 무효전력 주입: 유효전력 회복 속도 0.1pu/s 이상
└── 무효전력 지원: ΔQ = 2% × ΔV (전압 오차당)

HVRT:
└── 전압 1.2pu → 100ms 유지
```

### 계통 보조 서비스 시장 (National Grid ESO)
```
주파수 조정 서비스:
├── DC (Dynamic Containment)   — FFR 대체, ±0.5Hz 이내 유지
│   응답: ≤ 1초, 지속: 30분, 입찰: 매일 EFA Block
├── DR (Dynamic Regulation)    — ±0.2Hz 유지
├── DM (Dynamic Moderation)    — ±0.5Hz 초과 시
├── BM (Balancing Mechanism)   — 실시간 발전량 조정
└── FFR (Firm Frequency Response) — 구형 서비스, DC로 대체 중

용량 시장 (Capacity Market):
├── T-4 Auction (4년 선도): 매년 12월
├── T-1 Auction (1년 선도): 매년 3월
├── EFR (Enhanced Frequency Response) — 별도 조달
└── CM 참가 BESS: Generating Unit 또는 DSR로 등록

BSC (Balancing and Settlement Code):
├── BM Unit 등록 (Elexon)
├── Settlement Period: 30분 단위
└── Imbalance Charge 노출 위험 관리 필요
```

### 통신 · SCADA 규격
```
National Grid ESO / NESO 연동:
├── BM Unit 통신:
│   ├── 프로토콜: IEC 61850 (132kV 이상) + ICCP/TASE.2
│   ├── DNP3 over TCP/IP: 일부 DNO 연동
│   ├── EDL (Electronic Data Logging): 30분 정산 데이터
│   └── 전송 주기: 4초 (AGC), 30분 (Settlement)
├── Balancing Mechanism (BM) 통신:
│   ├── BM Unit Registration: Elexon (BSC 체계)
│   ├── FPN (Final Physical Notification): 실시간 출력 계획
│   ├── BOA (Bid-Offer Acceptance): ESO 지시 수신
│   └── REMIT 보고: ACER (EU 시장 남용 규제)
├── DC/DR/DM 서비스 통신:
│   ├── Low-frequency relay: 실시간 주파수 감시
│   ├── 응답 검증: 4초 단위 출력 데이터 전송
│   └── Pre-qualification Test: 주파수 주입 시험
├── 계량 (Metering):
│   ├── BSC Metering: CoP (Code of Practice) 준수
│   ├── CoP1/2: 100MW 이상 (최고 정밀도)
│   ├── CoP3: 10~100MW
│   ├── CoP5: 소규모 (<10MW)
│   ├── Settlement Period: 30분 단위
│   └── Data Collector (DC) + Data Aggregator (DA) 지정
└── 통신 경로:
    ├── ESO 전용 통신: BT 전용선 또는 VPN
    ├── 이중화: 주/백업 물리적 분리
    └── 가용률: 99.5% 이상

사이버보안:
├── NIS Regulations 2018 (Network and Information Systems):
│   ├── 전력 부문: OES (Operators of Essential Services) 지정
│   ├── Competent Authority: Ofgem
│   ├── NCSC CAF (Cyber Assessment Framework) 준수
│   └── 사이버 사고 보고: 72시간 이내 Ofgem 보고
├── NCSC (National Cyber Security Centre) 가이드라인:
│   ├── Cyber Essentials: 기본 보안 인증 (정부 계약 시 필수)
│   ├── Cyber Essentials Plus: 외부 검증 포함
│   └── 10 Steps to Cyber Security
├── ENA Cyber Security Best Practice:
│   ├── DNO/IDNO 연결 시 보안 요건
│   ├── SCADA 암호화: TLS 1.2+ 필수
│   └── 네트워크 세그먼테이션
└── 200MW+ BESS:
    └── CNI (Critical National Infrastructure) 지정 가능 → 추가 보안 의무
```

### 인증 요건 (UKCA / CE)
```
UKCA 마킹 (UK Conformity Assessment):
├── 브렉시트 후 CE → UKCA 전환
│   └── 전환 기한: 2025년 12월 31일까지 CE 인정 [요확인 — 연장 여부]
├── 적용 지침:
│   ├── Supply of Machinery (Safety) Regulations
│   ├── Electromagnetic Compatibility Regulations 2016
│   ├── Electrical Equipment (Safety) Regulations 2016
│   └── RoHS (Restriction of Hazardous Substances)
├── 적합성 평가 기관: UK Approved Bodies
├── 적합 선언서 (DoC): 제조사 또는 UK Authorised Representative
└── 기술 문서: 영어 — UK 시장 보관 의무

배터리 / ESS 시험:
├── BS EN 62933-5-2:2020 — ESS 안전 요건
├── IEC 62619:2022 — 배터리 안전 (BS EN 동등)
├── BS EN 62477-1 — 전력변환장치 안전
├── UL 9540A — 화재 전파 시험 (AHJ 요구 증가 중)
└── 시험 기관: BSI, Intertek, TÜV UK, LRQA

인버터 인증:
├── G99 Type Test Certificate: 필수
│   ├── 시험 항목: 전압/주파수 응답, 단독운전, 전력품질
│   ├── G99 Issue 6 (2024): 최신 기준
│   └── Type Tested = DNO 개별 시험 면제
├── G99 Unit Test: Type Test 미보유 시 현장 시험
└── Engineering Recommendation G5/5: 고조파 기준
    ├── Individual: 각 차수 THD 한도
    └── Planning Level: 계통 누적 기준
```

### ESS 화재 안전 (영국)
```
화재 안전 관련 법령:
├── Regulatory Reform (Fire Safety) Order 2005
├── Building Regulations Part B: 방화 요건
├── BS 9999: 화재 안전 설계 코드
└── HSE (Health & Safety Executive): 위험물 관리

ESS 설치 화재 안전 (현행 가이드라인):
├── NFCC (National Fire Chiefs Council) 가이드라인:
│   ├── ESS 설치 시 소방서 사전 협의 권장
│   ├── Emergency Response Plan (ERP) 제출
│   └── 소방대 접근: 4m 폭 접근로 확보
├── 이격 거리 (권장):
│   ├── ESS ↔ 건축물: 6m (가연성 외벽) / 3m (불연 외벽)
│   ├── ESS ↔ ESS: 1.5~3m (규모별)
│   └── ESS ↔ 부지 경계: 3m 이상
├── 방화 요건:
│   ├── 방화벽: REI 60 이상 (60분 내화)
│   ├── 배터리 컨테이너: 불연 재료 또는 내화 처리
│   ├── 가스 감지: H₂, CO 감지기 설치
│   └── 자동 소화: 청정 소화약제 또는 스프링클러
├── 열 폭주 관리:
│   ├── UL 9540A 시험 결과 제출 (점차 의무화 추세)
│   ├── 환기 설계: 가연성 가스 배출 (LEL 25% 미만 유지)
│   └── Cell-to-cell propagation 방지 설계
└── 보험:
    ├── Property Insurance: 화재 리스크 평가서 제출
    ├── Public Liability Insurance: 최소 £5M
    └── Business Interruption Insurance: 권장

> ⚠️ UK ESS 화재 안전 기준은 현재 NFCC 가이드라인 수준
> BS EN 등 공식 표준 제정 진행 중 [요확인 — 제정 시점]
```

### 인허가 절차 (상세)
```
1. Ofgem 발전 면허 (Electricity Generation Licence)
   ├── ≥ 50MW: 발전 면허 필수
   ├── < 50MW: 면허 면제 (Exemption)
   ├── Energy Act 2023: ESS 전용 라이선스 검토 중 [요확인]
   ├── 제출: Ofgem 온라인 포털
   └── 소요: 2~4주 (면허) / 1주 (면제 확인)

2. Planning Permission (계획 허가)
   ├── NSIP (Nationally Significant Infrastructure Project):
   │   ├── ≥ 350MW (육상): Planning Inspectorate (PINS) 심사
   │   ├── DCO (Development Consent Order) 신청
   │   ├── 절차: Pre-application → Acceptance → Examination → Decision
   │   └── 소요: 18~30개월
   ├── Town & Country Planning Act (< 350MW):
   │   ├── Local Planning Authority (LPA) 신청
   │   ├── Full Planning Application 또는 Outline
   │   └── 소요: 3~12개월
   ├── 환경 영향 평가 (EIA):
   │   ├── Screening: EIA 필요 여부 판단 (LPA/PINS)
   │   ├── Scoping: 평가 범위 결정
   │   ├── ES (Environmental Statement) 작성
   │   └── 항목: 생태, 소음, 시각, 교통, 홍수, 문화유산
   └── 환경 허가:
       ├── Environment Agency: Flood Risk Assessment (홍수 위험 지역)
       ├── Natural England: 생태계 영향 (SSSI 인접 시)
       ├── Historic England: 문화유산 영향
       └── Noise Assessment: BS 4142:2014 기준

3. Grid Connection (계통 연계)
   ├── DNO Connection Offer 요청:
   │   ├── UK Power Networks, Western Power Distribution 등
   │   ├── 소규모 (<1MW): 11kV, 약 3~6개월
   │   ├── 중규모 (1~50MW): 33kV, 약 6~12개월
   │   ├── 대규모 (≥50MW): 132kV, 약 12~24개월
   │   └── Queue 관리: Connection Offer Acceptance
   ├── TNSP Connection (132kV 이상):
   │   ├── National Grid ESO (또는 NESO): TO Build Process
   │   ├── CUSC (Connection and Use of System Code) 적용
   │   └── 소요: 12~36개월
   └── Connection Agreement 체결

4. G99 시험 · 인증
   ├── Type Test: 인버터 제조사 제공 (G99 Issue 6)
   ├── Unit Test: Type Test 미보유 시 현장 시험
   ├── Commissioning Test: DNO 입회 하 실시
   │   ├── 보호계전기 동작 시험
   │   ├── 주파수 응답 시험
   │   └── Anti-islanding 시험
   └── G99 Compliance Certificate 발급

5. BSC 등록 · 시장 참여
   ├── Elexon: BM Unit 등록
   ├── ESO: DC/DR/DM Pre-qualification
   ├── Capacity Market: CM Registration (해당 시)
   └── REMIT Registration: ACER 등록

6. 상업 운전 개시 (COD)
```

---


---

## 라우팅 키워드
UK, 영국, G99, UKCA, Ofgem, NationalGrid, ESO, NESO, DNO, DC, DR, DM, CapacityMarket, BSC, Elexon, NIS, NFCC
bess-standards-uk
