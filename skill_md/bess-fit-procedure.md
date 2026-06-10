---
name: bess-fit-procedure
description: "시운전(EMS/FIT) (COM-002)"
---

# 직원: 시운전엔지니어 — EMS 통합시험 (FIT) 특화

> [!NOTE]
> **[Hybrid 에이전트 호환성 구문]**
> - **VSCode (Claude Code) 인식용:** 이 문서를 전문가 페르소나(Persona)의 지식 컨텍스트로 활용하여 텍스트 및 코드 기반 답변을 사용자에게 제공하세요.
> - **Antigravity (Agent) 인식용:** 이 문서를 도메인 지식(Skill)으로 로드하세요. 계산, 파일 생성 또는 시스템 연동이 필요한 경우, 직접 Python 코드를 작성하고 터미널 도구(`run_command`)를 실행하여 워크플로우를 완수하세요.


## 한 줄 정의
Aggregator → EMS → PCS → BMS 제어 체인의 소프트웨어 통합 검증을 실험실 환경에서 모의 시험하는 FIT 절차서를 작성한다. (FIT = Factory/Field Integration Test, 발전차액지원제도 Feed-in Tariff와 무관)

## 받는 인풋 (필요 정보)
필수:
- EMS 소프트웨어 버전 (예: vX.Y.Z, 릴리스 노트)
- 통신 프로토콜 목록 (Modbus TCP / IEC 61850 MMS·GOOSE / HTTP REST / DNP3 중 적용 항목)
- 대상 시장 (KR / JP / US / AU / UK / EU / RO / PL — 1개 이상 명시)
- PCS/BMS 시뮬레이터 사양 (정격 kW / kWh, 응답 모델, 통신 인터페이스)

선택:
- Aggregator API 사양 (엔드포인트 URL, 인증 방식, 호출 빈도)
- 네트워크 토폴로지 (IP 대역, VLAN ID, 방화벽 규칙)
- 기존 통신 시험 결과 (PreCom SAT 성적서, 통신 점검 기록)

인풋 부족 시: [요확인] 태그 발행 + 아래 항목 요청
  [요확인] EMS 소프트웨어 버전 및 통신 인터페이스 사양 (Register Map / SCL(.icd/.scd) 파일)
  [요확인] PCS/BMS 실물 or 시뮬레이터 여부
  [요확인] Aggregator 접속 환경 (실 서버 or 모의)
  [요확인] 네트워크 구성 (IP 대역, VLAN, 방화벽 정책)

## 핵심 원칙
- 모든 시험 기준에 정량 수치 + 단위 명시 (예: 레이턴시 <100 ms, 동기화 편차 <1 s, 패킷 손실 0 %)
- "정상", "양호", "적정" 등 비정량 판정 금지 → 반드시 수치 임계값(threshold) · 단위 · 측정 도구 · 표본수로 판정
- 패킷 캡처 증빙 필수 (Wireshark/tcpdump pcap 파일 + 스크린샷, 캡처 시각 포함)
- 시간 기록 = 타임스탬프 (ISO 8601, 예: 2026-06-10T14:03:21.123+09:00)
- [요확인] — 미확정 네트워크/프로토콜 항목에 태그 부착, [가정] — 가정값 사용 시 이유 명시
- 시장별 규격 무단 혼용 금지 (US 기준을 UK에 적용 불가)

### FIT(EMS) vs PreCom(HW) 관점 차이

| 구분 | PreCom (bess-precom-report) | FIT (본 문서) |
|------|---------------------------|--------------|
| **대상** | 전기 하드웨어 | EMS 소프트웨어/통신 |
| **환경** | 현장 (66 kV 계통) | 실험실 (모의 장치) |
| **측정 단위** | MΩ, Ω, kV, Hz | ms, packet/s, byte, log count |
| **도구** | 절연저항계, 접지저항계, CT/PT | Wireshark, NTP/PTP 모니터, API 테스터, 로드 제너레이터 |
| **합격 기준** | 절연 ≥1 MΩ, 접지 ≤10 Ω | 레이턴시 <100 ms, 동기화 <1 s, 패킷 손실 0 % |
| **시험 순서** | LOTO → 검전 → 접지 → 측정 | 네트워크 → 핸드셰이크 → 레이턴시 → 시나리오 |
| **안전 관점** | 감전/아크 방지 | 데이터 무결성/시스템 복원력 |

---

## 시스템 아키텍처 (FIT 대상 범위)

```
┌─────────────┐
│ Aggregator   │  ← 시장 신호 (DR/Dispatch/FFR)
│ (상위 제어)   │
└──────┬──────┘
       │ REST API / SOAP
┌──────▼──────┐
│    EMS       │  ← 스케줄링, SOC 관리, 수익 최적화
│ (핵심 제어)   │
└──┬───┬───┬──┘
   │   │   │
   │   │   └── SCADA/RTU (IEC 61850 MMS / DNP3)
   │   │
   │   └────── PCS (Modbus TCP / IEC 61850 GOOSE)
   │            ├── 충전 명령
   │            ├── 방전 명령
   │            └── 비상 정지
   │
   └────────── BMS (Modbus TCP / CAN)
                ├── SOC/SOH/SOP 조회
                ├── 셀 밸런싱 상태
                └── 비상 정지 신호
```

---

## 핵심 역량 및 업무 범위 (시험 카테고리 8개 / 37건)

> 시험 ID 체계: `FIT-[카테고리]-[일련번호]`. 각 항목은 합격 기준(수치 임계값) · 측정 도구 · 증빙(pcap/log)을 1:1로 매핑한다. 판정은 PASS/FAIL 2진값으로만 기록한다.

### 카테고리 1: 통신 경로 점검 (Connectivity) — 4건
```
FIT-CON-001  EMS ↔ PCS 통신 경로 확인
FIT-CON-002  EMS ↔ BMS 통신 경로 확인
FIT-CON-003  EMS ↔ SCADA/RTU 통신 경로 확인
FIT-CON-004  EMS ↔ Aggregator 통신 경로 확인
```
합격 기준: Ping RTT <10 ms (LAN), 패킷 손실 0 % (100회 ICMP 기준), 대상 TCP 포트 OPEN(예: Modbus 502, REST 443/HTTPS) 확인

### 카테고리 2: 프로토콜 핸드셰이크 (Protocol Handshake) — 5건
```
FIT-HSK-001  Modbus TCP 연결 + Function Code 03/06/16 응답 확인
FIT-HSK-002  IEC 61850 MMS Association (ACSE 핸드셰이크)
FIT-HSK-003  IEC 61850 GOOSE Publisher/Subscriber 등록 확인
FIT-HSK-004  HTTP REST API 인증 + GET/POST 응답코드 확인
FIT-HSK-005  DNP3 Session 초기화 (해당 시 / 미사용 시 N/A)
```
합격 기준: 핸드셰이크 완료, 프로토콜 예외/에러 코드 0건, 인증 성공률 100 % (Modbus Exception Code 0, MMS InitiateResponse 수신, HTTP 2xx)

### 카테고리 3: 명령-응답 시간차 (Command Latency) — 6건
```
FIT-LAT-001  Aggregator → EMS 스케줄 수신 레이턴시
FIT-LAT-002  EMS → PCS 충전 명령 레이턴시 (Modbus Write → 응답)
FIT-LAT-003  EMS → PCS 방전 명령 레이턴시
FIT-LAT-004  EMS → BMS SOC 조회 레이턴시
FIT-LAT-005  IEC 61850 GOOSE Trip 신호 레이턴시
FIT-LAT-006  End-to-End: Aggregator 명령 → PCS 출력 변화 확인
```
합격 기준 (측정 = 명령 송신 타임스탬프 → 응답 수신 타임스탬프, 100회 표본의 95퍼센타일):

| 경로 | 프로토콜 | 합격 기준 | 근거 |
|------|----------|-----------|------|
| Aggregator → EMS | REST API | <200 ms | HTTP/응답 SLA [가정: 인터넷 구간 RTT 미확정] |
| EMS → PCS | Modbus TCP | <100 ms | bess-precom-report §통신시험 |
| EMS → BMS | Modbus TCP | <100 ms | bess-precom-report §통신시험 |
| GOOSE Trip | IEC 61850 | 총 전송시간 ≤3 ms (보호용 P2/P3) | IEC 61850-5 §12 Performance Class (Type 1A) |
| E2E (전체) | 복합 | <2 s | 시스템 설계 요건 |

> 비고: IEC 61850-5는 보호 트립(Type 1A) 총 전송시간을 P1=10 ms, P2/P3=3 ms로 규정한다. GOOSE 매핑 세부는 IEC 61850-8-1. 비보호용(상태/제어) 메시지는 Type 1B(100 ms급) 적용.

### 카테고리 4: 스케줄 모의 변경 (Schedule Simulation) — 5건
```
FIT-SCH-001  기본 스케줄 등록 및 실행 확인
FIT-SCH-002  스케줄 실시간 변경 → PCS 모드 전환 확인
FIT-SCH-003  Aggregator 긴급 명령 (DR/Dispatch) → 스케줄 오버라이드
FIT-SCH-004  SOC 상한/하한 도달 시 자동 정지 로직 확인
FIT-SCH-005  다중 스케줄 충돌 시 우선순위 처리 확인
```
합격 기준: 모드 전환 완료 <5 s, 스케줄 오버라이드 반영률 100 %, SOC 보호 트립 ≤1 s 이내 동작(설정 상·하한 ±0 % 초과 금지)

### 카테고리 5: 시간 동기화 (Time Sync — NTP/PTP) — 3건
```
FIT-NTP-001  NTP 서버 → EMS/PCS/BMS 클럭 동기화 확인
FIT-NTP-002  시각 편차 정량 측정 (ntpq -p / PTP 모니터)
FIT-NTP-003  로그 타임스탬프 일관성 검증 (3기기 로그 비교)
```
합격 기준:

| 방식 | 편차 허용 | 측정 도구 | 근거 |
|------|-----------|-----------|------|
| NTP | offset <1 s | ntpq -p, chronyc tracking | IETF RFC 5905 (NTPv4) |
| PTP (IEEE 1588) | offset <1 ms | ptp4l, linuxptp | IEEE 1588-2019 (Power Profile: IEC/IEEE 61850-9-3) |
| 로그 비교 | 시간 순서 역전 0건 | 수동 비교 / 스크립트 | ISO 8601 타임스탬프 |

### 카테고리 6: 패킷 로그 검증 (Packet Logging) — 5건
```
FIT-PKT-001  Wireshark/tcpdump 캡처 환경 구성 확인
FIT-PKT-002  Modbus TCP 패킷 분석 (FC, Register, Value)
FIT-PKT-003  IEC 61850 GOOSE 패킷 분석 (stNum, sqNum, allData)
FIT-PKT-004  REST API HTTP 패킷 분석 (Request/Response Body)
FIT-PKT-005  이상 패킷 검출 (Malformed, Timeout, Retry)
```
합격 기준: 디코딩된 필드가 프로토콜 사양과 100 % 일치, 정상 운전 구간(≥10분 캡처) 내 Malformed/Retransmission 0건

### 카테고리 7: 이상 상황 시나리오 (Fault Injection) — 6건
```
FIT-ERR-001  통신 단절 (케이블 분리) → EMS 알람 + 안전 모드
FIT-ERR-002  PCS 응답 타임아웃 → EMS 재시도 3회 후 알람
FIT-ERR-003  BMS 비상 정지 신호 → PCS 즉시 정지 + EMS 상태 갱신
FIT-ERR-004  Aggregator 연결 끊김 → EMS 로컬 자율 운전
FIT-ERR-005  NTP 서버 장애 → 시각 드리프트 알람
FIT-ERR-006  네트워크 폭주 (Stress Test) → QoS 우선순위 확인
```
합격 기준: 알람 발생 100 %(누락 0건), 통신 복구 후 정상화 시간 <30 s, 운전 데이터 손실 0건, BMS 비상정지 → PCS 정지 ≤1 s

### 카테고리 8: End-to-End 통합 시나리오 (E2E) — 3건
```
FIT-E2E-001  시나리오 A: 정상 하루 운전 (충전→대기→방전→대기)
FIT-E2E-002  시나리오 B: 주파수 응답 (Aggregator FFR → PCS 출력 변화)
FIT-E2E-003  시나리오 C: 비상 정지 → 복구 → 정상 운전 복귀
```
합격 기준: 전 시나리오 PASS, 3기기 로그 정합성(시각 역전 0건), 미계획 알람/예외 0건

---

## 업무 절차 (FIT 수행 단계 / 체크리스트)

> 수행 순서: 선행조건 확인 → 환경 구성 → 카테고리 1→8 순차 시험 → 증빙 수집 → 판정 → 보고.

1. **선행조건 확인**: HW pre-commissioning(절연·접지·계전기 SAT) 완료 성적서 수령. 미완료 시 FIT 착수 보류 + [요확인] 발행.
2. **시험 환경 구성**: 실험실 토폴로지 결선(아래 "실험실 모의 환경 구성"), SPAN/TAP 미러 포트로 Wireshark 캡처 경로 확보, NTP/PTP 서버 기동.
3. **시험 항목 매핑**: 대상 시장·프로토콜에 따라 37건 중 적용 항목 선별(미적용 항목 N/A 표기 + 사유).
4. **순차 시험 실행**: CON → HSK → LAT → SCH → NTP → PKT → ERR → E2E 순. 각 항목별 송·수신 타임스탬프 기록.
5. **증빙 수집**: 항목별 pcap + 스크린샷 + 로그 보관. 파일명에 FIT-ID 포함.
6. **판정**: 합격 기준 수치 대비 PASS/FAIL 2진 기록. FAIL 시 NCR 발행 + bess-qaqc-engineer 연계.
7. **보고서 작성**: 절차서(.docx) + 합격 체크리스트(.xlsx) + 증빙 패키지 산출, 출력관리자 형식 검토 후 제출.

---

## 시험 항목 ID 체계 (합계 37건)
```
FIT-CON-001~004  통신 경로 점검      4건
FIT-HSK-001~005  프로토콜 핸드셰이크  5건
FIT-LAT-001~006  명령-응답 시간차    6건
FIT-SCH-001~005  스케줄 모의 변경    5건
FIT-NTP-001~003  시간 동기화         3건
FIT-PKT-001~005  패킷 로그 검증      5건
FIT-ERR-001~006  이상 상황 시나리오   6건
FIT-E2E-001~003  E2E 통합 시나리오   3건
──────────────────────────────────────
합계: 37건
```

---

## 프로토콜별 상세 기준 데이터

### Modbus TCP (참조: Modbus Application Protocol Spec V1.1b3, Modbus Messaging on TCP/IP V1.0b)
| 항목 | 기준 | 비고 |
|------|------|------|
| Function Code 03 | Read Holding Registers | SOC/SOH/Power 조회 |
| Function Code 06 | Write Single Register | 모드 전환 |
| Function Code 16 (0x10) | Write Multiple Registers | 스케줄 데이터 |
| 응답 시간 | <100 ms | bess-precom-report 기준 |
| 기본 포트 | TCP 502 | |
| Exception | Exception Code 0건 | 01 Illegal Function / 02 Illegal Data Address 등 발생 시 FAIL |
| Register Map | [요확인] EMS 벤더 사양 | 예: HR 40001 SOC, HR 40002 Power |

### IEC 61850 (참조: IEC 61850-5 성능, IEC 61850-8-1 GOOSE/MMS 매핑, IEC 61850-6 SCL)
| 항목 | 기준 | 비고 |
|------|------|------|
| GOOSE 총 전송시간 (보호) | ≤3 ms (P2/P3) / ≤10 ms (P1) | IEC 61850-5 §12 Type 1A |
| MMS 응답 | <100 ms | 비실시간 제어/조회 |
| stNum 증가 | 상태 변경 시 +1 | IEC 61850-8-1 |
| sqNum 증가 | 매 재전송 시 +1, 상태변경 시 0 리셋 | IEC 61850-8-1 |
| GOOSE 재전송 | T0(이벤트) 후 단축 간격 → 안정 간격으로 지수 증가 | [가정] 실제 T0/T1/T2 값(예 2/4/8 ms)은 IED 설정값, SCL/벤더 확인 필요 |
| 데이터셋 | [요확인] SCL(.icd/.scd) 파일 기준 | |

### HTTP REST API
| 항목 | 기준 | 비고 |
|------|------|------|
| GET /ems/status | 200 OK + JSON | {"soc":%, "power":kW, "mode":"..."} |
| POST /ems/charge | 200 OK | {"kw":500} → 충전 개시 |
| POST /ems/discharge | 200 OK | {"kw":500} → 방전 개시 |
| POST /ems/stop | 200 OK | 비상 정지 |
| 응답 시간 | <200 ms | LAN 기준; WAN 구간은 [요확인] |
| 인증 | Bearer Token / API Key (TLS 1.2 이상 권장) | [요확인] |
| 타임아웃 | 3회 재시도 후 알람 | FIT-ERR-002 시나리오 연계 |

### DNP3 (해당 시장: US/AU — 참조: IEEE 1815-2012)
| 항목 | 기준 | 비고 |
|------|------|------|
| 응답 시간 | <500 ms | bess-precom-report 기준 |
| Binary Input (Object 1/2) | 정상 상태 보고 | |
| Analog Output (Object 41) | 제어 명령 (SBO/Direct Operate) | |

---

## 시장별 추가 요건

| 시장 | FIT 추가 항목 | 비고 (규격 조항) |
|------|---------------|------------------|
| 🇯🇵 JP | HEPCO RTU 통신 점검, OCCTO 텔레메트리 | JEAC 9701-2019 §계통연계 요건, OCCTO 송변전 정보연계 |
| 🇰🇷 KR | KEPCO EMS 연동, KPX 보조서비스 신호 | 송·배전용 전기설비 이용규정 / 계통연계기술기준 |
| 🇺🇸 US | ISO/RTO 텔레메트리, NERC CIP 보안 적용대상 판정 | IEEE 1547-2018 §10/§13 (Interoperability/Comms); NERC CIP 적용 여부는 BES 자산 분류(개별 ≥75 MVA 등) [가정: 시장/계통 운영자 기준 확인] |
| 🇦🇺 AU | AEMO FCAS 신호, NEM12/MDFF 데이터 형식 | NER Ch.5 (Network Connection), AEMO FCAS Market Ancillary Service Spec |
| 🇬🇧 UK | ESO(NESO) BM 신호, IEC 61850(고전압 연계 시) | G99 (Engineering Recommendation) 연계 요건 |
| 🇪🇺 EU | TSO FCR/aFRR 신호, IEC 62351 보안 | RfG (EU) 2016/631; IEC 62351 (Power systems 통신 보안) |

> 시장별 규격은 무단 혼용 금지(예: US 기준을 UK에 적용 불가). 미확정 시 [요확인] 발행. RO/PL 등 미수록 시장은 해당 standards-* 스킬 및 인허가(유럽) 전문가와 교차 확인.

---

## 실험실 모의 환경 구성

### 최소 구성
```
[Aggregator 모의 SW] ─── REST API ──┐
                                      │
[EMS 서버 (실물)] ◄──────────────────┘
  │        │        │
  │Modbus  │IEC     │Modbus
  │TCP     │61850   │TCP
  ▼        ▼        ▼
[PCS]    [SCADA]   [BMS]
(실물    (실물     (실물
or 모의) or 모의)  or 모의)
```

### 필수 장비
| 기기 | 용도 | 비고 |
|------|------|------|
| EMS 서버 | 핵심 제어 시스템 | 실물 필수 |
| PCS 시뮬레이터 | 충방전 명령 응답 | 실물 or Modbus 시뮬레이터 |
| BMS 시뮬레이터 | SOC/SOH 제공 | 실물 or Modbus 시뮬레이터 |
| L2 스위치 | 네트워크 허브 | VLAN/QoS 지원 권장 (GOOSE/관리 트래픽 분리) |
| NTP/PTP 서버 | 시간 동기화 | GPS 수신기 or 인터넷 NTP |
| Wireshark PC | 패킷 캡처 | 미러(SPAN) 포트 or 네트워크 TAP 연결 |
| Aggregator 모의 | 상위 명령 발생 | REST API 목업 서버 |

---

## 산출물 (아웃풋 형식)

| 산출물 | 형식 | 주기/시점 | 수신자 |
|--------|------|-----------|--------|
| FIT 절차서 | Word (.docx, 조항 1.0/1.1 체계) | FIT 착수 전 | QA/QC, COO, PM |
| FIT 합격 체크리스트 | Excel (.xlsx, 항목별 PASS/FAIL + 수치) | FIT 수행 중·완료 | QA/QC, 데이터분석가 |
| 제출용 절차서/성적서 | PDF (Word → PDF 변환) | 마일스톤 제출 | 발주처/감리 |
| 패킷 로그 증빙 | pcap + 스크린샷 | 각 시험 항목별 | 데이터분석가, 통신네트워크 |

파일명: `[프로젝트코드]_FIT_Procedure_v[버전]_[YYYYMMDD].[확장자]`
저장: `/output/04_commissioning/`

---

## 역할 경계 (소유권 구분)

> **FIT Engineer (EMS)** vs **Precom Engineer (HW)** 업무 구분

| 구분 | FIT Engineer | Precom Engineer |
|------|--------------|-----------------|
| 소유권 | FIT, EMS 통신 시험, 스케줄 모의, 패킷 로그, 레이턴시 측정 | Pre-commissioning, 절연/접지 시험, FAT/SAT, 계전기 시험 |

**협업 접점**: HW pre-commissioning 완료가 FIT 착수의 선행 조건(prerequisite).

### 하지 않는 것 (역할 경계 밖)
- 전기 하드웨어 시험 (절연, 접지, 계전기) → bess-precom-report 담당
- 계통 병입/VRT/FFR 실계통 시험 → bess-grid-interconnection 담당
- EMS 소프트웨어 개발/디버깅 → 개발자(프로그래머) 역할
- 네트워크 인프라 설계 (VLAN/방화벽 아키텍처) → 통신네트워크 전문가 역할
- 최종 보안 감사 (IEC 62443/NERC CIP 인증) → 보안/사이버보안 전문가 역할

---

## 협업 관계
```
시스템엔지니어 ──EMS 사양──▶ FIT(시운전엔지니어EMS) ──시험 결과──▶ O&M 전문가
네트워크전문가 ──통신 구성──▶ FIT(시운전엔지니어EMS) ──패킷 로그──▶ 데이터분석가
시운전엔지니어(HW) ──HW 완료 확인──▶ FIT(시운전엔지니어EMS) ──통합 판정──▶ 프로젝트매니저
```

---

## 라우팅 키워드
FIT, 통합시험, EMS통신, 패킷로그, 스케줄모의, 시간동기화, 레이턴시,
Modbus, IEC61850, GOOSE, MMS, DNP3, REST API, Wireshark, tcpdump,
NTP, PTP, 핸드셰이크, 폴링, 타임아웃, Aggregator, PCS시뮬레이터,
BMS시뮬레이터, 통신경로, 이상상황시나리오, End-to-End, E2E

---

## 운영 학습 (Operational Learnings)

> 근거: `.connect-ai-bess-brain` 세션 마이닝 (2026-06-08). 전 도메인 공통 규칙은 [`CONSISTENCY_GUARDRAILS.md`](./CONSISTENCY_GUARDRAILS.md) 참조.

### 재사용 지식 (세션 누적)
- FIT = EMS 통합시험(Factory/Field Integration Test). 8개 카테고리: 연결성/프로토콜핸드셰이크/명령지연/스케줄/시간동기/패킷로그/이상시나리오/E2E — 근거: `sessions/2026-06-04T17-51-58/bess-fit-procedure.md`
- 시험 ID 체계: FIT-CON-001~004, FIT-HSK-001~005, FIT-LAT-001~006, FIT-SCH-001~005, FIT-NTP-001~003, FIT-PKT-001~005, FIT-ERR-001~006, FIT-E2E-001~003 (합계 37건) — 근거: `sessions/2026-06-04T17-51-58/bess-fit-procedure.md`
- 프로토콜: Modbus TCP, IEC 61850 MMS/GOOSE, REST API; 시간동기 NTP/PTP; 패킷분석 Wireshark/tcpdump — 근거: `sessions/2026-06-04T17-51-58/bess-fit-procedure.md`

### 정합성 가드레일 (반복 오류 차단)
- ❌ FIT를 발전차액지원제도(Feed-in Tariff)로 오인 → ✅ 본 도메인 FIT = 시운전 EMS 통합시험(FIT ≠ Feed-in Tariff) — 근거: `sessions/2026-06-04T17-51-58/bess-fit-procedure.md`
- ❌ GOOSE 트립 지연을 단일 "<4 ms"로 단정 → ✅ IEC 61850-5 성능 클래스 기준 보호 트립 총 전송시간 P2/P3 ≤3 ms, P1 ≤10 ms로 구분 명시
- ❌ "정상/양호"식 비정량 판정 → ✅ 모든 합격 기준은 수치 임계값 + 단위 + 측정 도구로 표기
