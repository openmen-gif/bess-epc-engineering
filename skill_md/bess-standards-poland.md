---
name: bess-standards-poland
description: "BESS EPC 폴란드(PL) 규격·표준·인허가 상세"
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
|--------|--------|---------|------|
| OVR | 1.15 × Un | 400ms | RfG Annex III |
| UVR | 0.85 × Un | 1,500ms | IRiESP §연계조건 |
| OFR | 51.5 Hz | 200ms | RfG Annex III |
| UFR | 47.5 Hz | 140ms | RfG Annex III |
| ROCOF | 2.0 Hz/s | 500ms | EN 50549-2 |

> ⚠️ [요확인] 실제 정정값은 PSE Warunki Przyłączenia(연계 기술 조건서)에서 확정.
> 폴란드는 ROCOF 2.0 Hz/s를 적용하며, 루마니아(2.5 Hz/s)보다 보수적임.

### LVRT 기준 (RfG Annex III — Type C/D, 상세)
```
LVRT 프로파일 (PSE 이행 기준):
├── 0.0pu → 150ms 유지, 이탈 없이 계속 운전
├── 0.15pu → 625ms 유지
├── 0.50pu → 1,500ms 유지
├── 0.85pu → 연속 운전 복귀
└── 복귀 기울기: ≥ 10% Un / 100ms

HVRT (폴란드 특화):
├── 1.15pu → 400ms 유지 (IRiESP 기준)
└── 1.25pu → 100ms 유지 [요확인 — PSE 연계 협의]

FRT 추가 요건:
├── 무효전력 주입 (LVRT 중):
│   ├── ΔV > 10%: 무효전류 ≥ 2% × ΔV
│   ├── 응답: ≤ 30ms
│   └── 우선순위: 무효전력 > 유효전력
├── 복귀 후 유효전력 회복:
│   ├── 0.1pu/s 이상 (기본)
│   └── PSE 강화 가능 [요확인]
├── FRT 시험 방법:
│   ├── EN 50549-2:2019 기반
│   ├── IEC 61400-21 (풍력 준용)
│   └── PSE 입회 시험 (Grid Connection Test)
└── 시험 기관: IEn Gdańsk (에너지연구소), TÜV, DNV
```

### 통신 · SCADA 규격
```
PSE 연동:
├── 프로토콜:
│   ├── 110kV 이상: IEC 61850 MMS + IEC 60870-5-104
│   ├── 중전압: IEC 60870-5-104 (주) + Modbus TCP (보조)
│   └── RTU (Remote Terminal Unit): IEC 61850 호환
├── 전송 주기: 4초 (실시간 SCADA)
├── 전송 항목:
│   ├── 필수: P, Q, V, f, SOC, 가용 용량, 충방전 상태
│   ├── 보호: 계전기 동작 상태, 차단기 위치
│   └── 알람: BMS 온도, SOC 한계, 고장 코드
├── AGC (Automatic Generation Control):
│   ├── PSE 중앙 급전소 (KDM — Krajowa Dyspozycja Mocy): 발전 제어 신호
│   ├── 응답: ≤ 4초 이내 출력 변경 개시
│   └── 제어 범위: Pmin ~ Pmax (Warunki Przyłączenia 명시)
├── 계량 (Metering):
│   ├── URE 기준 Revenue Meter: ±0.5% 정확도
│   ├── 정산 기간: 15분 (EU 표준 이행)
│   ├── 데이터 전송: ENTSO-E Settlement 연계
│   └── Smart Meter: AMI 의무화 진행 중 (2026 목표)
└── 통신 경로:
    ├── PSE 광통신: 전용선 (110kV 이상)
    ├── VPN over Internet: 백업 (이중화)
    └── 가용률: 99.5% 이상

사이버보안 (폴란드):
├── NIS 2 Directive 국내법 전환:
│   ├── Ustawa o Krajowym Systemie Cyberbezpieczeństwa (KSC법, 2018)
│   │   └── NIS 2 전환 개정 진행 중 [요확인 — 시행 시점]
│   ├── CSIRT NASK: 국가 CERT (사이버보안 사고 대응)
│   ├── CSIRT GOV (ABW): 정부 CERT
│   └── 에너지 부문: Essential Entity 지정 (KSC법 대상)
├── URE 보안 요건:
│   ├── SCADA 보안: 방화벽, 침입탐지 필수
│   ├── 망분리: OT/IT 물리적 분리 권장
│   └── 접근 제어: RBAC + MFA
├── ISO/IEC 27001: 정보보안 관리 체계 (권장)
└── IEC 62351: 전력 통신 보안 (적용)
```

### 전력시장 참여 (폴란드)
```
TGE (Towarowa Giełda Energii — 폴란드 전력거래소):
├── DAM (Day-Ahead Market): SDAC 연계, 시간대별 블록
├── IDM (Intraday Market): SIDC 연계, 연속 거래
├── Balancing Market: PSE 운영
│   ├── aFRR: ≤ 2분 응답 — BESS 최적
│   ├── mFRR: ≤ 12.5분 응답
│   └── 입찰: MW + PLN/MWh (가격·수량)
├── FCR: ENTSO-E 공동 조달 (폴란드 할당분)
│   └── BESS 참여 가능: Prequalification 필요
└── 정산: PSE (imbalance 정산, PLN 기준)

용량 시장 (Rynek Mocy):
├── Ustawa o rynku mocy (용량시장법, 2017년 제정, 2020년 시행)
├── 경매 유형:
│   ├── T-4: 4년 전 경매 (주 경매, 신규 설비 대상)
│   ├── T-1: 1년 전 경매 (보완 경매, 기존 설비)
│   └── 분기별 경매: 단기 보완
├── ESS 참여: 가능 (Magazyn Energii 자격)
│   ├── 최소 용량: 2MW [요확인 — 경매별 상이]
│   ├── 의무 이행: 지정 시간 가용성 유지
│   └── 페널티: 미이행 시 Kara umowna (위약금)
├── 정산: PLN/MW/rok (연간 용량 대가)
└── 관리: PSE (경매 주관), URE (감독)

Ancillary Services 계약:
├── PSE 직접 계약
├── 최소 용량: 1MW (aFRR/mFRR)
├── 계약 기간: 월간 또는 분기별 입찰
└── 정산: MW × 시간 × 단가(PLN/MW/h)

재생에너지 경매 (Aukcje OZE):
├── 주관: URE
├── 근거: Ustawa OZE (2015)
├── ESS + RE 하이브리드: 참여 가능 (Instalacja hybrydowa)
├── CfD 방식: 15년 보장
└── 경매 주기: 연 1~2회

보조금 · 지원:
├── EU NextGenerationEU / KPO (Krajowy Plan Odbudowy):
│   ├── 에너지저장 전용 예산 배정
│   └── 신청: Ministerstwo Funduszy i Polityki Regionalnej
├── Modernisation Fund: 폴란드·동유럽 에너지 현대화
│   └── 폴란드 최대 수혜국 중 하나
├── Innovation Fund: 대규모 ESS 프로젝트
├── Transformacja Energetyczna (에너지 전환 기금):
│   ├── NFOŚiGW (Narodowy Fundusz Ochrony Środowiska)
│   │   └── 국가환경보호기금: ESS 포함 에너지 투자
│   └── WFOŚiGW: 지역 환경보호기금 (16개 주)
├── Mój Prąd (나의 전기): 가정용 ESS 보조금 프로그램
└── EU ETS Revenue: 배출권 수익 재투자 (에너지 전환)
```

### ESS 화재 안전 (폴란드)
```
화재 안전 관련 법령:
├── Ustawa o ochronie przeciwpożarowej (소방법, 1991)
├── Rozporządzenie MSWiA w sprawie ochrony przeciwpożarowej budynków
│   └── 건축물 소방 기준 시행령
├── Rozporządzenie w sprawie warunków technicznych budynków
│   └── 건축물 기술조건 시행령 (Warunki Techniczne, WT)
└── PSP (Państwowa Straż Pożarna): 소방청 — 소방 허가·감독

ESS 설치 화재 안전:
├── PSP 승인: Uzgodnienie projektu budowlanego pod względem ochrony ppoż.
│   ├── 설계 단계: 소방 안전 시나리오 제출 (Ekspertyza ppoż.)
│   ├── 시공 단계: PSP 중간 검사
│   └── 준공 단계: PSP 최종 검사 → 소방 허가 발급
├── 이격 거리 (PSP 가이드라인 + EU 표준 준용):
│   ├── ESS ↔ 건축물: 6m (가연성 외벽) / 3m (불연 외벽)
│   ├── ESS ↔ ESS: 2m (컨테이너 간)
│   └── 소방대 접근로: 4m 폭
├── 방화 요건:
│   ├── 방화벽: REI 120 (2시간 내화) — 실내 설치 시
│   ├── 배터리 컨테이너: 불연 재료 (Steel 또는 Concrete)
│   ├── 가스 감지: H₂, CO 복합 감지기
│   ├── 자동 소화: 청정 소화약제 또는 Water Mist
│   └── 환기: 기계식 배기 (가연성 가스 LEL 25% 미만)
├── 비상 대응:
│   ├── Emergency Response Plan (ERP): PSP 제출
│   ├── 비상 차단: 원격 + 현장 (2중)
│   └── 소방대 교육: ESS 특화 위험성 고지 (PSP 협의)
└── 시험:
    ├── UL 9540A: 권장 → 의무화 추세 (AHJ 재량)
    └── EN 62933-5-2: 시스템 안전 시험

배터리 시험 (폴란드/EU):
├── IEC 62619:2022 — 산업용 배터리 안전 (EN 채택)
├── IEC 63056:2020 — 주거/상업용 배터리 (EN 채택)
├── UN 38.3 — 운송 시험 (ADR/RID 운송 규정)
├── UL 9540A — 화재 전파 시험 (권장 → 의무화 추세)
└── 시험 기관: IEn Gdańsk (에너지연구소), INiG-PIB, TÜV, DNV, Intertek
```

### 인허가 절차 (상세)
```
1. Warunki Zabudowy / MPZP (도시계획 조건 / 지역 공간 계획)
   ├── 발급: Wójt/Burmistrz/Prezydent Miasta (지자체장)
   ├── MPZP 존재 시: 적합성 확인 (Wypis i wyrys z MPZP)
   ├── MPZP 부재 시: Decyzja o warunkach zabudowy (WZ) 신청
   │   └── WZ 결정: 입지에 대한 건축 가능 여부 및 조건
   ├── 제출: 토지 등기부, 위치도, 사업 개요
   └── 소요: 30~60일 (WZ), MPZP 적합 확인은 14일

2. Warunki Przyłączenia (계통연계 조건)
   ├── 신청: PSE (110kV+) 또는 DSO (중/저전압)
   ├── 제출: 단선결선도, 설비 사양서, 용량, 입지 정보
   ├── 결과:
   │   ├── 접속점 확정
   │   ├── 보호계전기 정정값 확정
   │   ├── 무효전력 범위 확정
   │   ├── 통신·SCADA 요건
   │   └── 공사비 분담 결정 (Opłata za przyłączenie)
   ├── 유효기간: 2년 (연장 가능)
   ├── 수수료: 용량·전압별 상이 (Prawo Energetyczne Art. 7)
   └── 소요: 60~150일 (법정 기한, 용량별 상이)

3. Decyzja Środowiskowa (환경 결정)
   ├── Screening: RDOŚ (Regionalna Dyrekcja Ochrony Środowiska)
   │   └── EIA 필요 여부 결정
   ├── Karta Informacyjna Przedsięwzięcia (KIP): 사업 정보 카드 제출
   ├── EIA Report (필요 시): 생태, 소음, 수질, 시각, 문화유산
   ├── 공공 참여 (Konsultacje społeczne): 의무
   ├── Decyzja środowiskowa: RDOŚ 발급
   └── 소요: 2~4개월 (EIA 불필요), 6~12개월 (EIA 필요)

4. Pozwolenie na Budowę (건설 허가)
   ├── 발급: Starosta (군수) 또는 Prezydent Miasta (시장)
   ├── 제출: Projekt budowlany (건축 설계서), 구조 계산서
   ├── PSP 소방 검토: 소방 안전 시나리오 사전 협의
   ├── 기타 협의: Sanepid (위생), 환경, 도로 관리자 등
   └── 소요: 65일 (법정 기한) + PSP 검토 별도

5. PSP 소방 허가
   ├── Uzgodnienie projektu budowlanego (건축설계 소방 협의)
   ├── 소방 안전 시나리오 검토
   ├── 시공 중 검사
   └── 준공 시 최종 소방 검사 → Odbiór ppoż. (소방 준공 승인)

6. Koncesja na Wytwarzanie Energii Elektrycznej (발전 면허)
   ├── 신청: URE (Urząd Regulacji Energetyki)
   ├── 근거: Prawo Energetyczne Art. 32
   ├── 면제: 50MW 미만 소규모 → Wpis do rejestru (등록제)
   │   └── Magazyn Energii ≥ 10MW: 면허 필요 [요확인]
   ├── 제출: 준공 서류, 시험 결과, 재무 건전성 증빙
   ├── 소요: 30~60일
   └── 유효기간: 10~50년 (신청에 따라)

7. TGE/PSE 시장 참여 등록
   ├── TGE 참여: Towarowa Giełda Energii 회원 등록
   ├── PSE Balancing Market: PSE 등록
   ├── Capacity Market: PSE 경매 참여 등록
   ├── 은행 보증: 시장 참여 보증금 (Zabezpieczenie)
   └── 소요: 30~60일

8. 상업 운전 개시 (COD)
   ├── Grid Connection Test: PSE 또는 DSO 입회
   │   ├── 보호계전기 동작 시험
   │   ├── VRT 시험 (또는 시뮬레이션 증빙)
   │   ├── SCADA 통신 시험
   │   └── 계량기 정확도 시험
   ├── PINB 검사: Powiatowy Inspektorat Nadzoru Budowlanego
   │   └── 건축 준공 검사 (Pozwolenie na użytkowanie)
   ├── PSP 최종 소방 검사
   └── COD 선언

> 총 소요 기간: 일반 6~12개월, 대규모(EIA 필요) 12~18개월
> 참고: 폴란드는 110kV 이상 PSE 연계 시 Queue 대기 발생 가능 (6개월+)
```

---


---

## 라우팅 키워드
PL, 폴란드, URE, PSE, TGE, IRiESP, IRiESD, PN-EN, PSP, KPO, Capacity Market Poland,
Rynek Mocy, Prawo Energetyczne, Ustawa OZE, NFOŚiGW, Warunki Przyłączenia, RDOŚ
bess-standards-poland
