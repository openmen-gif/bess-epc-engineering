---
name: bess-standards-romania
description: "BESS EPC 루마니아(RO) 규격·표준·인허가 상세"
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
|--------|--------|---------|------|
| OVR | 1.15 × Un | 400ms | CTR §8.3 |
| UVR | 0.85 × Un | 1,500ms | CTR §8.3 |
| OFR | 51.5 Hz | 200ms | RfG Annex III |
| UFR | 47.5 Hz | 140ms | RfG Annex III |
| ROCOF | 2.5 Hz/s | 500ms | EN 50549-2 |

> ⚠️ [요확인] 실제 정정값은 Transelectrica ATR(연계 기술 승인서)에서 확정

### LVRT 기준 (RfG Annex III — Type C/D, 상세)
```
LVRT 프로파일:
├── 0.0pu → 140ms 유지, 이탈 없이 계속 운전
├── 0.15pu → 625ms 유지
├── 0.50pu → 1,500ms 유지
├── 0.85pu → 연속 운전 복귀
└── 복귀 기울기: ≥ 10% Un / 100ms

HVRT (루마니아 특화):
├── 1.15pu → 400ms 유지 (CTR §8.3 기준)
└── 1.25pu → 100ms 유지 [요확인 — Transelectrica ATR 협의]

FRT 추가 요건:
├── 무효전력 주입 (LVRT 중):
│   ├── ΔV > 10%: 무효전류 ≥ 2% × ΔV
│   ├── 응답: ≤ 30ms
│   └── 우선순위: 무효전력 > 유효전력
├── 복귀 후 유효전력 회복:
│   ├── 0.1pu/s 이상 (기본)
│   └── Transelectrica 강화 가능 [요확인]
├── FRT 시험 방법:
│   ├── EN 50549-2:2019 기반
│   ├── IEC 61400-21 (풍력 준용)
│   └── Transelectrica 입회 시험 (Grid Connection Test)
└── 시험 기관: ICMET (루마니아 전기기술연구소), TÜV, DNV
```

### 통신 · SCADA 규격
```
Transelectrica 연동:
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
│   ├── Transelectrica 중앙 급전소: 발전 제어 신호
│   ├── 응답: ≤ 4초 이내 출력 변경 개시
│   └── 제어 범위: Pmin ~ Pmax (ATR 명시)
├── 계량 (Metering):
│   ├── ANRE 기준 Revenue Meter: ±0.5% 정확도
│   ├── 정산 기간: 15분 (EU 표준 이행)
│   ├── 데이터 전송: ENTSO-E Settlement 연계
│   └── Smart Meter: AMR/AMI (ANRE 의무화 진행 중)
└── 통신 경로:
    ├── Transelectrica 광통신: 전용선 (110kV 이상)
    ├── VPN over Internet: 백업 (이중화)
    └── 가용률: 99.5% 이상

사이버보안 (루마니아):
├── NIS 2 Directive 국내법 전환:
│   ├── CERT-RO: 루마니아 CERT (사이버보안 사고 대응)
│   ├── DNSC (Directoratul Național de Securitate Cibernetică)
│   └── 에너지 부문: Essential Entity 지정
├── ANRE 보안 요건:
│   ├── SCADA 보안: 방화벽, 침입탐지 필수
│   ├── 망분리: OT/IT 물리적 분리 권장
│   └── 접근 제어: RBAC + MFA
├── ISO/IEC 27001: 정보보안 관리 체계 (권장)
└── IEC 62351: 전력 통신 보안 (적용)
```

### 전력시장 참여 (루마니아)
```
OPCOM (Operatorul Pieței de Energie Electrică):
├── DAM (Day-Ahead Market): SDAC 연계, 15분 블록
├── IDM (Intraday Market): SIDC 연계, 연속 거래
├── BM (Balancing Market): Transelectrica 운영
│   ├── aFRR: ≤ 2분 응답 — BESS 최적
│   ├── mFRR: ≤ 12.5분 응답
│   └── 입찰: MW + €/MWh (가격·수량)
├── FCR: ENTSO-E 공동 조달 (루마니아 할당분)
│   └── BESS 참여 가능: Prequalification 필요
└── 정산: Transelectrica (imbalance 정산)

용량 시장 (Capacity Market):
├── Capacity Mechanism: 2024년 도입 [요확인 — 시행 시점]
├── 루마니아 정부 계획: 석탄 퇴출 보완 용량 확보
└── ESS 참여: 예정 (세부 규정 제정 중)

Ancillary Services 계약:
├── Transelectrica 직접 계약
├── 최소 용량: 1MW (aFRR/mFRR)
├── 계약 기간: 월간 또는 분기별 입찰
└── 정산: MW × 시간 × 단가(€/MW/h)

보조금 · 지원:
├── EU 복구기금 (NextGenerationEU): ESS 포함 에너지 투자
├── Innovation Fund: 대규모 ESS 프로젝트
├── Modernisation Fund: 루마니아·동유럽 에너지 현대화
├── PNRR (Plan Național de Redresare și Reziliență):
│   ├── 에너지저장 전용 예산 배정
│   └── 신청: 에너지부 (Ministerul Energiei)
└── Green Certificates (GC): 재에너지 인증서 (ESS 연계 시 [요확인])
```

### ESS 화재 안전 (루마니아)
```
화재 안전 관련 법령:
├── Legea Nr. 307/2006 — 화재 안전법
├── Normativ P118-1999 — 건축물 화재 안전 설계
├── HG 571/2016 — 화재 안전 인가 절차
└── ISU (Inspectoratul pentru Situații de Urgență): 소방 감독

ESS 설치 화재 안전:
├── ISU 승인: Autorizație de Securitate la Incendiu (소방 안전 인가)
│   ├── 설계 단계: 소방 안전 시나리오 (Scenariu de Securitate) 제출
│   ├── 시공 단계: ISU 중간 검사
│   └── 준공 단계: ISU 최종 검사 → 소방 안전 인가 발급
├── 이격 거리 (ISU 가이드라인 + EU 표준 준용):
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
│   ├── Emergency Response Plan (ERP): ISU 제출
│   ├── 비상 차단: 원격 + 현장 (2중)
│   └── 소방대 교육: ESS 특화 위험성 고지
└── 시험:
    ├── UL 9540A: 점차 의무화 추세 (AHJ 재량)
    └── EN 62933-5-2: 시스템 안전 시험

배터리 시험 (루마니아/EU):
├── IEC 62619:2022 — 산업용 배터리 안전 (EN 채택)
├── IEC 63056:2020 — 주거/상업용 배터리 (EN 채택)
├── UN 38.3 — 운송 시험 (ADR/RID 운송 규정)
├── UL 9540A — 화재 전파 시험 (권장 → 의무화 추세)
└── 시험 기관: ICMET Craiova (루마니아), TÜV, DNV, Intertek
```

### 인허가 절차 (상세)
```
1. Certificat de Urbanism (도시계획 인증서)
   ├── 발급: Consiliul Local (지방의회) 또는 Consiliul Județean (군의회)
   ├── 목적: 입지에 대한 법적 요건 확인 (건축 가능 여부)
   ├── 제출: 토지 등기부, 위치도, 사업 개요
   └── 소요: 30일 이내 (법정 기한)

2. Studiu de Racordare (연계 가능성 검토)
   ├── 신청: Transelectrica (110kV+) 또는 DSO (중/저전압)
   ├── 제출: 단선결선도, 설비 사양서, 용량, 입지 정보
   ├── 결과: 연계 가능 여부 + 기술 조건 (접속점, 필요 공사)
   ├── 수수료: 용량·전압별 상이
   └── 소요: 60~90일 (법정 기한)

3. Aviz Tehnic de Racordare (ATR, 연계 기술 승인서)
   ├── 발급: Transelectrica (110kV+) 또는 DSO
   ├── 내용:
   │   ├── 접속점 확정
   │   ├── 보호계전기 정정값 확정
   │   ├── 무효전력 범위 확정
   │   ├── 통신·SCADA 요건
   │   └── 공사비 분담 결정
   ├── 유효기간: 통상 2년 (연장 가능)
   └── 소요: 30~60일

4. 환경 영향 평가 (Evaluare de Impact asupra Mediului)
   ├── Screening: Agenția Națională pentru Protecția Mediului (ANPM)
   │   └── EIA 필요 여부 결정
   ├── Scoping: 평가 범위 결정 (필요 시)
   ├── EIA Report: 생태, 소음, 수질, 시각, 문화유산
   ├── 공공 참여 (Consultare publică): 의무
   ├── Acord de Mediu (환경 허가): ANPM 발급
   └── 소요: 3~6개월 (EIA 필요 시 6~12개월)

5. Autorizație de Construire (건설 허가)
   ├── 발급: Consiliul Local/Județean
   ├── 제출: 건축 도면 (DTAC), 구조 계산서, 소방 시나리오
   ├── ISU 승인: 소방 안전 시나리오 사전 검토
   └── 소요: 30일 (법정 기한) + ISU 검토 별도

6. 전기 공사 + 시운전
   ├── 전기 안전 검사: ISCIR/ISC (해당 기관)
   ├── Grid Connection Test: Transelectrica 입회
   │   ├── 보호계전기 동작 시험
   │   ├── VRT 시험 (또는 시뮬레이션 증빙)
   │   ├── SCADA 통신 시험
   │   └── 계량기 정확도 시험
   └── 소요: 2~4주

7. ANRE 발전 면허 (Licență de Producere)
   ├── 신청: ANRE
   ├── 제출: 준공 서류, 시험 결과, ATR 적합 증빙
   ├── 소요: 30~60일
   └── 유효기간: 25년 (갱신 가능)

8. OPCOM 시장 참여 등록
   ├── Participant Registration: OPCOM 포털
   ├── BM 참여: Transelectrica 등록
   ├── 은행 보증: 시장 참여 보증금
   └── 상업 운전 개시 (COD)

> 총 소요 기간: 일반 6~12개월, 대규모(EIA 필요) 12~18개월
```

---


---

## 라우팅 키워드
RO, 루마니아, ANRE, Transelectrica, CTR, ATR, OPCOM, EN50549, ISU, PNRR, NextGenerationEU
bess-standards-romania
