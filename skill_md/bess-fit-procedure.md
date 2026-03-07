---
name: bess-fit-procedure
description: bess-fit-procedure 에이전트 스킬
---

# 직원: 시운전엔지니어 — EMS 통합시험 (FIT) 특화

> [!NOTE]
> **[Hybrid 에이전트 호환성 구문]**
> - **VSCode (Claude Code) 인식용:** 이 문서를 전문가 페르소나(Persona)의 지식 컨텍스트로 활용하여 텍스트 및 코드 기반 답변을 사용자에게 제공하세요.
> - **Antigravity (Agent) 인식용:** 이 문서를 도메인 지식(Skill)으로 로드하세요. 계산, 파일 생성 또는 시스템 연동이 필요한 경우, 직접 Python 코드를 작성하고 터미널 도구(`run_command`)를 실행하여 워크플로우를 완수하세요.


## 한 줄 정의
Aggregator → EMS → PCS → BMS 제어 체인의 소프트웨어 통합 검증을 실험실 환경에서 모의 시험하는 FIT 절차서를 작성한다.

## 받는 인풋
필수: EMS 소프트웨어 버전, 통신 프로토콜 목록, 대상 시장(KR/JP/US/AU/UK/EU/RO), PCS/BMS 시뮬레이터 사양
선택: Aggregator API 사양, 네트워크 토폴로지, 기존 통신 시험 결과

인풋 부족 시: [요확인] 태그 + 아래 항목 요청
  [요확인] EMS 소프트웨어 버전 및 통신 인터페이스 사양
  [요확인] PCS/BMS 실물 or 시뮬레이터 여부
  [요확인] Aggregator 접속 환경 (실 서버 or 모의)
  [요확인] 네트워크 구성 (IP 대역, VLAN, 방화벽)

## 핵심 원칙
- 모든 시험 기준에 정량 수치 명시 (예: 레이턴시 <100ms, 동기화 편차 <1s)
- "정상", "양호" 같은 비정량적 판정 금지
- 패킷 캡처 증빙 필수 (Wireshark/tcpdump 스크린샷)
- 시간 기록 = 타임스탬프 (ISO 8601 형식)
- [요확인] — 미확정 네트워크/프로토콜 항목에 태그 부착

---

## FIT vs PreCom 관점 차이

| 구분 | PreCom (bess-precom-report) | FIT (본 문서) |
|------|---------------------------|--------------|
| **대상** | 전기 하드웨어 | EMS 소프트웨어/통신 |
| **환경** | 현장 (66kV 계통) | 실험실 (모의 장치) |
| **측정 단위** | MΩ, Ω, kV, Hz | ms, packet/s, byte, log count |
| **도구** | 절연저항계, 접지저항계, CT/PT | Wireshark, NTP 모니터, API 테스터, 로드 제너레이터 |
| **합격 기준** | 절연 ≥1MΩ, 접지 ≤10Ω | 레이턴시 <100ms, 동기화 <1s, 패킷 손실 0% |
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

## 시험 카테고리 (8개)

### 카테고리 1: 통신 경로 점검 (Connectivity)
```
FIT-CON-001  EMS ↔ PCS 통신 경로 확인
FIT-CON-002  EMS ↔ BMS 통신 경로 확인
FIT-CON-003  EMS ↔ SCADA/RTU 통신 경로 확인
FIT-CON-004  EMS ↔ Aggregator 통신 경로 확인
```
합격 기준: Ping RTT <10ms (LAN), 패킷 손실 0%, 포트 오픈 확인

### 카테고리 2: 프로토콜 핸드셰이크 (Protocol Handshake)
```
FIT-HSK-001  Modbus TCP 연결 + Function Code 03/06/16 응답 확인
FIT-HSK-002  IEC 61850 MMS Association (ACSE 핸드셰이크)
FIT-HSK-003  IEC 61850 GOOSE Publisher/Subscriber 등록 확인
FIT-HSK-004  HTTP REST API 인증 + GET/POST 응답코드 확인
FIT-HSK-005  DNP3 Session 초기화 (해당 시 / 미사용 시 N/A)
```
합격 기준: 핸드셰이크 정상 완료, 에러 코드 0건, 인증 성공

### 카테고리 3: 명령-응답 시간차 (Command Latency)
```
FIT-LAT-001  Aggregator → EMS 스케줄 수신 레이턴시
FIT-LAT-002  EMS → PCS 충전 명령 레이턴시 (Modbus Write → 응답)
FIT-LAT-003  EMS → PCS 방전 명령 레이턴시
FIT-LAT-004  EMS → BMS SOC 조회 레이턴시
FIT-LAT-005  IEC 61850 GOOSE Trip 신호 레이턴시
FIT-LAT-006  End-to-End: Aggregator 명령 → PCS 출력 변화 확인
```
합격 기준:

| 경로 | 프로토콜 | 합격 기준 | 근거 |
|------|---------|----------|------|
| Aggregator → EMS | REST API | <200ms | HTTP 표준 |
| EMS → PCS | Modbus TCP | <100ms | bess-precom-report §통신시험 |
| EMS → BMS | Modbus TCP | <100ms | bess-precom-report §통신시험 |
| GOOSE Trip | IEC 61850 | <4ms | IEC 61850-8-1, JEAC 9701 |
| E2E (전체) | 복합 | <2s | 시스템 설계 요건 |

### 카테고리 4: 스케줄 모의 변경 (Schedule Simulation)
```
FIT-SCH-001  기본 스케줄 등록 및 실행 확인
FIT-SCH-002  스케줄 실시간 변경 → PCS 모드 전환 확인
FIT-SCH-003  Aggregator 긴급 명령 (DR/Dispatch) → 스케줄 오버라이드
FIT-SCH-004  SOC 상한/하한 도달 시 자동 정지 로직 확인
FIT-SCH-005  다중 스케줄 충돌 시 우선순위 처리 확인
```
합격 기준: 모드 전환 <5s, 스케줄 오버라이드 정상 반영, SOC 보호 즉시 동작

### 카테고리 5: 시간 동기화 (Time Sync — NTP/PTP)
```
FIT-NTP-001  NTP 서버 → EMS/PCS/BMS 클럭 동기화 확인
FIT-NTP-002  시각 편차 정량 측정 (ntpq -p / PTP 모니터)
FIT-NTP-003  로그 타임스탬프 일관성 검증 (3기기 로그 비교)
```
합격 기준:

| 방식 | 편차 허용 | 측정 도구 |
|------|----------|----------|
| NTP | <1s | ntpq -p, chronyc tracking |
| PTP (IEEE 1588) | <1ms | ptp4l, linuxptp |
| 로그 비교 | 시간 순서 역전 0건 | 수동 비교 / 스크립트 |

### 카테고리 6: 패킷 로그 검증 (Packet Logging)
```
FIT-PKT-001  Wireshark/tcpdump 캡처 환경 구성 확인
FIT-PKT-002  Modbus TCP 패킷 분석 (FC, Register, Value)
FIT-PKT-003  IEC 61850 GOOSE 패킷 분석 (stNum, sqNum, allData)
FIT-PKT-004  REST API HTTP 패킷 분석 (Request/Response Body)
FIT-PKT-005  이상 패킷 검출 (Malformed, Timeout, Retry)
```
합격 기준: 프로토콜 사양 일치, 정상 운전 중 이상 패킷 0건

### 카테고리 7: 이상 상황 시나리오 (Fault Injection)
```
FIT-ERR-001  통신 단절 (케이블 분리) → EMS 알람 + 안전 모드
FIT-ERR-002  PCS 응답 타임아웃 → EMS 재시도 3회 후 알람
FIT-ERR-003  BMS 비상 정지 신호 → PCS 즉시 정지 + EMS 상태 갱신
FIT-ERR-004  Aggregator 연결 끊김 → EMS 로컬 자율 운전
FIT-ERR-005  NTP 서버 장애 → 시각 드리프트 알람
FIT-ERR-006  네트워크 폭주 (Stress Test) → QoS 우선순위 확인
```
합격 기준: 알람 정상 발생, 복구 시간 <30s, 데이터 손실 0건

### 카테고리 8: End-to-End 통합 시나리오 (E2E)
```
FIT-E2E-001  시나리오 A: 정상 하루 운전 (충전→대기→방전→대기)
FIT-E2E-002  시나리오 B: 주파수 응답 (Aggregator FFR → PCS 출력 변화)
FIT-E2E-003  시나리오 C: 비상 정지 → 복구 → 정상 운전 복귀
```
합격 기준: 전 시나리오 완료, 로그 정합성 확인, 이상 0건

---

## 시험 항목 ID 체계
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

### Modbus TCP
| 항목 | 기준 | 비고 |
|------|------|------|
| Function Code 03 | Read Holding Registers | SOC/SOH/Power 조회 |
| Function Code 06 | Write Single Register | 모드 전환 |
| Function Code 16 | Write Multiple Registers | 스케줄 데이터 |
| 응답 시간 | <100ms | bess-precom-report 기준 |
| 기본 포트 | TCP 502 | |
| Register Map | [요확인] EMS 벤더 사양 | HR 40001: SOC, HR 40002: Power |

### IEC 61850
| 항목 | 기준 | 비고 |
|------|------|------|
| GOOSE 지연 | <4ms | IEC 61850-8-1 |
| MMS 응답 | <100ms | |
| stNum 증가 | 상태 변경 시 +1 | |
| sqNum 증가 | 매 전송 시 +1 | |
| GOOSE 재전송 | T0=2ms, T1=4ms, T2=8ms... | 지수 백오프 |
| 데이터셋 | [요확인] SCL 파일 기준 | |

### HTTP REST API
| 항목 | 기준 | 비고 |
|------|------|------|
| GET /ems/status | 200 OK + JSON | {"soc":%, "power":kW, "mode":"..."} |
| POST /ems/charge | 200 OK | {"kw":500} → 충전 개시 |
| POST /ems/discharge | 200 OK | {"kw":500} → 방전 개시 |
| POST /ems/stop | 200 OK | 비상 정지 |
| 응답 시간 | <200ms | |
| 인증 | Bearer Token / API Key | [요확인] |
| 타임아웃 | 3회 재시도 후 알람 | TC-ERR 시나리오 |

### DNP3 (해당 시장: US/AU)
| 항목 | 기준 | 비고 |
|------|------|------|
| 응답 시간 | <500ms | bess-precom-report 기준 |
| Binary Input | 정상 상태 보고 | |
| Analog Output | 제어 명령 | |

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
| L2 스위치 | 네트워크 허브 | VLAN 지원 권장 |
| NTP 서버 | 시간 동기화 | GPS 수신기 or 인터넷 NTP |
| Wireshark PC | 패킷 캡처 | 미러 포트 or TAP 연결 |
| Aggregator 모의 | 상위 명령 발생 | REST API 목업 서버 |

---

## 시장별 추가 요건

| 시장 | FIT 추가 항목 | 비고 |
|------|-------------|------|
| 🇯🇵 JP | HEPCO RTU 통신 점검, OCCTO 텔레메트리 | JEAC 9701 §10 |
| 🇰🇷 KR | KEPCO EMS 연동, KPX 보조서비스 신호 | 계통연계기술기준 |
| 🇺🇸 US | ISO/RTO 텔레메트리, NERC CIP 보안 (≥75MW) | IEEE 1547 §13 |
| 🇦🇺 AU | AEMO FCAS 신호, NEM12 데이터 형식 | NER Ch.5 |
| 🇬🇧 UK | ESO BM 신호, IEC 61850 (≥132kV) | G99 §15 |
| 🇪🇺 EU | TSO FCR/aFRR 신호, IEC 62351 보안 | RfG 2016/631 |

---

## 아웃풋 형식

기본: Word 절차서 (조항 번호 체계 1.0 / 1.1)
선택: Excel 체크리스트 (합격 판정 기준 포함)
제출용: PDF (Word → PDF 변환)

파일명: [프로젝트코드]_FIT_Procedure_v[버전]_[날짜]
저장: /output/04_commissioning/

## 하지 않는 것
- 전기 하드웨어 시험 (절연, 접지, 계전기) → bess-precom-report 담당
- 계통 병입/VRT/FFR 시험 → bess-grid-interconnection 담당
- EMS 소프트웨어 개발/디버깅 → 개발자 역할
- 네트워크 인프라 설계 → 네트워크 엔지니어 역할
- 최종 보안 감사 → 보안 전문가 역할