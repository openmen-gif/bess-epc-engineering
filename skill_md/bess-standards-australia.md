---
name: bess-standards-australia
description: "BESS EPC 호주(AU) 규격·표준·인허가 상세"
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

## 🇦🇺 호주 (Australia)

### 관할 기관
```
AEMO (Australian Energy Market Operator) — NEM 운영, FCAS 시장
AER  (Australian Energy Regulator)       — 시장 규제
AEMC (Australian Energy Market Commission) — 규정 수립
각 주 규제기관 — SA (ESCOSA), VIC (ESC), NSW (IPART) 등
CEC  (Clean Energy Council)             — 인증 목록 (보조금 연계)
```

### 핵심 법령 · 규격
```
National Electricity Law (NEL)
National Electricity Rules (NER)
├── Chapter 5    — 발전기·ESS 등록
├── Chapter 5A   — 분산형 자원
└── Schedule 5.2 — 기술 연계 요건 (Technical Performance Standards)

기술 표준
├── AS 4777-2020 — Grid connection of energy systems
│   ├── Part 1: 설치 요건
│   ├── Part 2: 인버터 요건 (전압·주파수 응답)
│   └── Part 3: 계통 보호
├── AS/NZS 5139:2019 — ESS 설치 (화재 안전)
├── AS/NZS 3000:2018 — 배선 규정 (Wiring Rules)
└── IEC 62933-5-2    — ESS 계통 통합 안전
```

### 보호계전기 기준 (AS 4777-2020 / NER Schedule 5.2)
| 계전기 | 정정값 범위 | 기본 동작 시간 |
|--------|-----------|------------|
| OVR-1 | 110~120% × Un | 60s |
| OVR-2 | 120~130% × Un | 0.5s |
| UVR-1 | 85~90% × Un | 2s |
| UVR-2 | 70~80% × Un | 0.5s |
| OFR | 51.0~52.0 Hz | 1s |
| UFR | 47.5~49.0 Hz | 1s |
| ROCOF | 1.5~4.0 Hz/s | 0.5s |

> ⚠️ [요확인] 주(SA, VIC 등)별로 정정값 범위 상이. AEMO Connection Agreement에서 확정

### FCAS 참여 요건 (AEMO)
```
6개 FCAS 서비스:
┌──────────────┬────────────┬──────────┬──────┐
│ 서비스        │ 응답 시간  │ 지속 시간 │ 방향 │
├──────────────┼────────────┼──────────┼──────┤
│ Raise 6-sec  │ 6초        │ 5분      │ 방전 │
│ Raise 60-sec │ 60초       │ 5분      │ 방전 │
│ Raise 5-min  │ 5분        │ 5분      │ 방전 │
│ Lower 6-sec  │ 6초        │ 5분      │ 충전 │
│ Lower 60-sec │ 60초       │ 5분      │ 충전 │
│ Lower 5-min  │ 5분        │ 5분      │ 충전 │
└──────────────┴────────────┴──────────┴──────┘

참여 등록:
├── AEMO 시장 참여자 등록
├── MNSP/TNSP 네트워크 접속 협의
├── Technical Performance Standards 충족
└── 계량기: NEM12 포맷 데이터 전송

수익 구조:
├── FCAS: 낙찰 용량[MW] × [AUD/MW]
├── NEM 에너지: 방전 에너지[MWh] × [AUD/MWh] (5분 정산)
├── LGC (Large-scale Generation Certificate) — 재생에너지 연계 시
└── ARENA / CEFC 보조금 — 프로젝트별
```

### 주(State)별 규제 차이
```
┌────────┬───────────────────────────────────────────────────────┐
│ 주     │ 규제 기관 / 특이 사항                                  │
├────────┼───────────────────────────────────────────────────────┤
│ SA     │ ESCOSA — 가장 선진적 ESS 시장, 전체 재생비율 70%+     │
│ (남호주)│ AEMO 주도 빅배터리 (Hornsdale 150MW), FCAS 활성       │
│        │ Planning Consent: SA Planning Commission              │
├────────┼───────────────────────────────────────────────────────┤
│ VIC    │ ESC (Essential Services Commission)                   │
│ (빅토리아)│ Victorian Big Battery (300MW/450MWh)               │
│        │ Environment Effects Statement (EES): ≥ 임계값 시      │
│        │ Planning Permit: 지자체 (Local Council)               │
├────────┼───────────────────────────────────────────────────────┤
│ NSW    │ IPART + NSW DPE (Department of Planning)             │
│ (뉴사우스│ State Significant Development (SSD): ≥ 30MW          │
│  웨일즈)│ Development Application (DA): < 30MW                  │
│        │ Waratah Super Battery (850MW) 진행 중                 │
├────────┼───────────────────────────────────────────────────────┤
│ QLD    │ QCA (Queensland Competition Authority)                │
│(퀸즐랜드)│ Development Assessment: SARA 프로세스                │
│        │ 재생에너지 존 (REZ) 지정 — ESS 집중 입지              │
├────────┼───────────────────────────────────────────────────────┤
│ WA     │ ERA (Economic Regulation Authority)                   │
│ (서호주)│ SWIS (South West Interconnected System) — NEM 비참여  │
│        │ WEM (Wholesale Electricity Market) 독자 운영           │
│        │ Synergy 주정부 전력회사 주도                           │
└────────┴───────────────────────────────────────────────────────┘

> ⚠️ [요확인] WA(서호주)는 NEM 비참여 → AEMO 규정이 아닌 WEM 규정 적용
```

### 통신 · SCADA 규격
```
AEMO 연동:
├── 프로토콜:
│   ├── 대규모 (≥30MW): IEC 61850 + DNP3 over TCP/IP
│   ├── 중규모 (5~30MW): DNP3 over TCP/IP
│   └── 소규모 (<5MW): Modbus TCP (DNSP 연동)
├── AGC (Automatic Generation Control):
│   ├── 전송 주기: 4초
│   ├── 응답: ≤ 4초 이내 출력 변경
│   └── FCAS 제어 신호: 실시간
├── 전송 항목:
│   ├── 필수: P, Q, V, f, SOC, 가용 용량, 운전 상태
│   ├── FCAS: 응답 속도, 드룹 설정값, 가용 MW
│   └── 선택: 온도, BMS 알람, 고장 정보
├── 계량 (Metering):
│   ├── NEM12 포맷: 5분 간격 데이터 (NMI 기반)
│   ├── Revenue Meter: ±0.5% 정확도 (CT/PT 포함)
│   ├── Metering Coordinator (MC) 지정 필수
│   └── MSATS (Market Settlement and Transfer Solution) 등록
└── 통신 경로:
    ├── AEMO 전용 VPN (주) + 공공 인터넷 VPN (백업)
    ├── 이중화 필수: 주/백업 경로 물리적 분리
    └── 가용률: 99.5% 이상

사이버보안:
├── Australian Energy Sector Cyber Security Framework (AESCSF)
│   ├── AEMO 주도 자발적 프레임워크
│   ├── C2M2 (Capability Maturity Model) 기반
│   └── 연간 자가 평가 + 외부 검증 (대규모)
├── Critical Infrastructure Act 2018 (SOCI Act):
│   ├── 에너지 부문: Critical Infrastructure 지정
│   ├── Risk Management Program 수립 의무
│   └── 사이버 사고 보고: ASD (Australian Signals Directorate)
├── ISM (Information Security Manual): ASD 발행
│   └── Essential Eight: 패치 관리, MFA, 백업 등 8대 기준
└── AEMO 보안 요건:
    ├── Market Participant 접속: TLS 1.2+ 암호화
    ├── 인증: 공인 인증서 (PKI)
    └── 접근 제어: 역할 기반 (RBAC)
```

### AS/NZS 5139 ESS 화재 안전 (상세)
```
AS/NZS 5139:2019 — 전기 에너지 저장 시스템 설치:
├── 위험 등급 분류:
│   ├── Low Risk: ≤ 2.4kWh 또는 비위험 화학물질
│   ├── Medium Risk: 2.4kWh ~ 200kWh (리튬이온)
│   └── High Risk: > 200kWh (리튬이온) — 대부분 BESS 해당
├── 이격 거리 (High Risk):
│   ├── ESS ↔ 거주 건물: ≥ 1,000mm (외부) 또는 방화벽
│   ├── ESS ↔ 개구부 (창문/문): ≥ 1,000mm
│   ├── ESS ↔ 가연성 재료: ≥ 600mm
│   ├── ESS ↔ 부지 경계: ≥ 600mm
│   └── ESS ↔ ESS: ≥ 600mm (컨테이너 간)
├── 방화 요건:
│   ├── 방화벽: FRL 60/60/60 이상 (비연소/차열/차단)
│   ├── 바닥: 불연 재료, 배수 시설 (소화수 수집)
│   ├── 환기: 자연 또는 기계식, 0.3 ACH 이상
│   └── 비상 접근: 소방대 접근 가능 경로 확보
├── 전기 안전:
│   ├── DC 차단: 각 배터리 스트링 단위
│   ├── 비상 차단 버튼: 접근 가능 위치
│   ├── 접지: AS/NZS 3000 기준
│   └── 과전류 보호: 각 스트링 단위
└── 보호 시스템:
    ├── 열 폭주 감지: 가스 감지 (CO, H₂) 또는 온도 감지
    ├── 자동 소화: 스프링클러 또는 에어로졸 (AHJ 협의)
    ├── 자동 화재 탐지: 연기감지 + 열감지 조합
    └── 비상 대응 계획 (ERP): 소방서 제출 의무

CEC (Clean Energy Council) 인증:
├── CEC 승인 배터리 목록:
│   ├── 호주 보조금 (SRES, 주정부 프로그램) 수령 시 필수
│   ├── 승인 기준: IEC 62619, UL 1973, 또는 UN 38.3 + IEC 63056
│   └── 목록 갱신: 분기별
├── CEC 승인 인버터 목록:
│   ├── AS 4777.2-2020 적합성 시험 통과 필수
│   └── DER Register 등록 요건
├── CEC Accredited Installer:
│   ├── 설치 자격: CEC 인정 설치자
│   ├── 설계 자격: CEC 인정 설계자 (Grid Connect 또는 Stand-alone)
│   └── 자격 갱신: 연간 CPD (Continuing Professional Development)
└── DER Register (Distributed Energy Resources):
    ├── AEMO 운영, 2020년 시작
    ├── 모든 DER (태양광+ESS) 등록 의무
    └── DNSP (Distribution NSP) 통해 등록

배터리 시험 요건:
├── IEC 62619:2022 — 산업용 리튬이온 배터리 안전
├── IEC 63056:2020 — 리튬이온 배터리 안전 (주거/상업용)
├── UN 38.3 — 운송 시험 (위험물 운송)
├── UL 9540A — 화재 전파 시험 (임의이나 AHJ 요구 증가)
└── 시험 기관: SAI Global, TÜV SÜD Australia, CSIRO
```

### 인허가 절차 (상세)
```
1. AEMO 시장 참여자 등록 (Market Participant Registration)
   ├── Generator (Scheduled/Semi-Scheduled): ≥ 30MW
   ├── Non-Scheduled: 5~30MW (또는 자발적 등록)
   ├── Small Generation Aggregator: < 5MW 집합
   ├── 제출: Registration Application (AEMO 포털)
   ├── 수수료: AUD 5,000~50,000 (규모별)
   └── 소요: 4~8주

2. Network Service Provider (NSP) 연결 신청
   ├── TNSP (Transmission): ≥ 30MW 또는 고전압 연결
   │   ├── TransGrid (NSW), AusNet (VIC), ElectraNet (SA) 등
   │   ├── Connection Enquiry → Detailed Response → Application
   │   └── 소요: 6~18개월 (Network Augmentation 포함 시 더 소요)
   ├── DNSP (Distribution): < 30MW 또는 중/저전압 연결
   │   ├── Ausgrid, Endeavour, Essential Energy (NSW) 등
   │   ├── Basic Connection → Standard Connection → Negotiated Connection
   │   └── 소요: 2~6개월
   └── Technical Performance Standards 협의:
       ├── NER Schedule 5.2 요건 충족 증빙
       ├── GPS (Generator Performance Standards) 합의
       └── AEMO 기술 검토 (≥ 30MW)

3. 환경 영향 평가 (주별)
   ├── SA: Development Approval (State Commission Assessment Panel)
   ├── NSW: State Significant Development (SSD) EIS — ≥ 30MW
   │   └── SSD 절차: Scoping → EIS 작성 → 공공 의견수렴 → 결정
   ├── VIC: Planning Permit + Environment Effects Statement (필요 시)
   ├── QLD: Development Assessment (SARA 프로세스)
   └── 소요: 3~12개월 (SSD/EES 필요 시 12~24개월)

4. 건설 허가
   ├── Development Application (DA) 또는 Planning Permit
   ├── Building Approval: National Construction Code (NCC) 기준
   ├── 전기 안전: AS/NZS 3000 기반 Electrical Contractor 라이선스
   └── 소요: 1~3개월

5. 연결 계약 (Connection Agreement) 체결
   ├── NSP와 정식 연결 계약
   ├── Metering 설정: NMI 할당, MC/MP/MDP 지정
   └── SCADA 연동 시험

6. 시운전 · AEMO 등록 완료
   ├── Generator Compliance Test: 보호계전기, VRT, FCAS 응답
   ├── AEMO 기술 승인
   ├── 시장 등록 최종 확인
   └── COD (Commercial Operation Date)
```

### 환경 · 입지 허가 (상세)
```
연방 환경법:
├── EPBC Act (Environment Protection and Biodiversity Conservation):
│   ├── Matters of National Environmental Significance (MNES) 해당 시
│   ├── 멸종위기종, 습지(Ramsar), 세계유산, 핵 활동 등
│   ├── 자발적 Referral → DAWE (Department) 결정
│   └── 소요: 3~6개월 (Controlled Action 결정 시 12개월+)
└── Native Title Act: 원주민 토지 권리 확인 필수

주별 환경 요건:
├── SA: Development Act 1993 → Planning, Development and Infrastructure Act 2016
├── NSW: EP&A Act, Biodiversity Conservation Act, Water Management Act
├── VIC: Planning and Environment Act, Flora and Fauna Guarantee Act
├── QLD: Planning Act 2016, Environmental Protection Act 1994
└── WA: EP Act 1986, Environmental Protection (Clearing of Native Vegetation) Regulations

소음 규제:
├── SA: Environment Protection (Noise) Policy 2007
│   └── 산업 소음: 주간 52 dB(A), 야간 45 dB(A) (거주지 경계)
├── NSW: Noise Policy for Industry (EPA)
│   └── Intrusive criteria + Amenity criteria 중 낮은 값
├── VIC: SEPP N-1 (State Environment Protection Policy)
│   └── 주간 55 dB(A), 야간 45 dB(A) (거주지)
└── 주요 소음원: HVAC, 변압기, 인버터 냉각팬

토지 이용:
├── 일반 산업 구역: 허용 (Permitted Use)
├── 농업 구역: Conditional Use (주별 상이)
├── 보전 구역: 원칙적 불허
├── Bush fire prone area: 추가 방화 요건 (AS 3959)
└── Aboriginal Heritage: 원주민 문화유산 조사 (필요 시)
```

---


---

## 라우팅 키워드
AU, 호주, AS4777, AS5139, AEMO, FCAS, NER, CEC, NEM, EPBC, SOCI, AESCSF
bess-standards-australia
