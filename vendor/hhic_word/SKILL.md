---
name: hhic-word-generator
description: Builds editable native Microsoft Word (.docx) and verified PDF documents using the Hyosung Heavy Industries (HHIC / 효성중공업) Editorial Design System v2.0 from a declarative JSON file via build_doc.py. Supports Mode A (formal engineering & EPC contractual reports with cover page, approvals, revision history, auto TOC, abbreviations, numbered clauses, spec tables, redline comparisons, compliance matrices, and open items) and Mode B (compact 1-page header technical review memos). Use when the user asks for an MS Word document, .docx report, EPC technical review, RFI response, contract review, specification, or 사내 기술 검토서.
---

# HHIC (효성) MS Word 문서 생성 엔진 (`15_Word-Auto-Skill` v2.0)

## 반드시 지킬 핵심 규칙
1. **일회성 `python-docx` 스크립트 직접 작성 금지**: 문서를 만들 때 개별 파이썬 스크립트를 짜지 않는다. 오직 선언형 JSON 파일(`docs_json/<날짜>_<주제>.json`)을 작성하고 `skill/scripts/build_doc.py`만 실행한다.
2. **아웃라인 & 미결사항(Open Items) 승인 게이트**: 본문 JSON을 작성하기 전에 **문서 모드(표지 포함 여부), 장/절(Heading 1~3) 구조, 주요 표 구성, 근거 등급(E1~E4) 및 미확인 항목(`[TO BE CONFIRMED]` / `[확인 필요]`)**을 표로 제시하고 사용자 승인을 받는다.
3. **사실 규율 (Fact Discipline)**:
   - 원문 URL이나 프로젝트 정본(E1)이 확인되지 않은 수치·책임·기간은 문구 끝에 영문은 `[TO BE CONFIRMED: ...]`(또는 `[TBD]`), 국문은 `[확인 필요: ...]`를 반드시 붙인다.
   - 임의로 수치(`mm`, `MW`, 기간 등)나 계약 조항 책임을 지어내지 않는다.
   - `"완벽히 보장"`, `"원천 차단"`, `"100% 보장"`, `"unconditionally guaranteed"` 같은 단정적 표현은 빌더가 자동 거부한다.
4. **글쓰기 규칙**: JSON 본문을 쓰기 전에 [references/writing_style.md](references/writing_style.md)를 읽는다. 대시와 가운뎃점, 작업 흔적 단어(세션, 사용자, 스킬), 본문 속 근거 등급 `(E1)`, 백틱, 한영 병기 라벨, 미리 채운 서명을 쓰지 않는다. 빌드 때 나오는 `[STYLE]` 경고는 인계 전에 0건으로 만든다.
5. **정본 템플릿 보존**: `templates/Word Template_Empty_No Project Data.docx`는 읽기 전용 도너(Donor) 정본이다. 빌더가 SHA-256 해시(`4ec89b04...`)를 검증하며, 다르면 즉시 중단한다.

---

## 작업 순서 (6단계 게이트)
```markdown
- [ ] 1. 입력 확인 및 문서 모드/프로필 결정
- [ ] 2. 근거 조사 및 미확인 항목(TBC) 식별 (E1~E4 등급)
- [ ] 3. 아웃라인 및 표 구성 승인 (게이트)
- [ ] 4. 선언형 doc JSON 작성 (`docs_json/`, `references/writing_style.md` 준수)
- [ ] 5. 빌드 및 자동 검수 (`build_doc.py --strict --render-pdf --render-png`, `[STYLE]` 경고 0건까지 수정)
- [ ] 6. 산출물(.docx, .pdf, .validation.json) 및 육안 검수 결과 인계
```

### 1) 두 가지 레이아웃 모드 (`meta.include_cover`) — 글로벌 전 권역(한국 포함) 및 한·영 공통 지원
| 모드 | 설정 | 구성 및 적합 용도 |
|---|---|---|
| **Mode A (공식 보고서·계약/기술문서, 기본값)** | `"include_cover": true`, `"include_toc": true` | **Page 1 (표지)**: 효성 로고 + 문서 상태 배지 + 히어로 타이틀(`24.5pt`) & 서브타이틀 + 4열 4행 문서 식별 메타데이터 카드<br>**Page 2 (문서관리 시트)**: 러닝 머리글 시작 + 결재란(`APPROVALS & SIGN-OFF`) + 개정이력(`DOCUMENT CONTROL & REVISION HISTORY`)<br>**Page 3 (목차·약어)**: 자동 목차(`CONTENTS`) + 약어표(`ABBREVIATIONS & DEFINITIONS`)<br>**Page 4+ (본문)**: 다단계 조항 본문 + 바닥글(`Page X of Y`) |
| **Mode B (컴팩트 실무 검토서·RFI·메모)** | `"include_cover": false`, `"include_toc": false` | **Page 1 상단**: 효성 로고 + 문서 상태 배지 + 제목 + 2x4 컴팩트 메타데이터 요약표 직후 **1페이지부터 즉시 Executive Summary 및 본문 시작** (사내 기술 검토서·실무 메모 스타일, 1페이지부터 쪽수 표시 및 2페이지부터 러닝 머리글 자동 적용) |

### 2) 세 가지 폰트 프로필 (`meta.profile` / `--profile`)
- **`epc-en` (또는 `global-en`, 영문 글로벌 문서 기본값)**: `Arial` (영문) + `맑은 고딕` (국문 병기 보조) + `Consolas` (코드/식별자). **글로벌 전 권역(북미·유럽·중동·아태·호주·한국 해외사업 등)** 영문 EPC 기술사양서·클레임·RFI·계약 검토서 전용.
- **`modern` (또는 `kr-modern`, 한국 프로젝트 및 국문 문서 기본값)**: `Pretendard` 단일 패밀리 + `Consolas`. **한국 국내 프로젝트(한전·거래소·발전사·민자 대외 제출물 포함) 및 본사/연구소 국문 기술 검토서·경영진 보고서** 전용 (Mode A 정식 표지 및 Mode B 컴팩트 헤더 모두 지원).
- **`safe`**: `Arial` + `맑은 고딕` + `Courier New`. 외부 발주처·타 PC 배포 시 폰트 누락이 없는 범용 호환 프로필.

### 3) 지원 블록 타입 (`blocks[]` 14종 요약)
상세 필드는 [references/doc_schema.md](references/doc_schema.md)를 참조한다.

| 블록 `type` | 용도 및 특징 |
|---|---|
| `heading` | `level` (1~4), 자동 조항 번호(`1.`, `1.1`, `1.1.1`), `keepNext` 강제 적용 |
| `paragraph` | 일반 본문(`body`), 도입 강조(`lead`), 주석(`note`). 인라인 `**굵게**`, `` `코드` ``, `~~취소선~~`, `++밑줄추가++`, `[TO BE CONFIRMED: ...]` 배지 자동 변환 |
| `clause_list` | `scheme: "alpha"` (`(a)` → `(i)` 계약 조항식), `"bullet"` (`•` → `▪` 기술 불릿), `"numbered"` (`1)` 절차식) |
| `callout` | 5종 시맨틱 요약/경고 박스 (`executive_summary`, `key_takeaway`, `risk_warning`, `contract_hold`, `draft_response`) |
| `kv_table` | 2열 또는 4열(`columns_mode: 4`) Key-Value 제원/개요 요약표 |
| `table` | 엔지니어링 사양표·비교표 (`tblHeader` 페이지 넘김 헤더 반복, `cantSplit` 행 분할 방지, `COMPLIANT`/`TBC`/`OPEN ISSUE` 상태 셀 자동 배지 컬러링) |
| `redline_comparison` | 계약 조항 원문 vs 수정안(Redline Markup), 또는 당초 판단 vs 후속 정정(TF-1) 4열 대조표 |
| `requirement_matrix` | EPC 규격/요건 준수성 매트릭스 (`Req ID` \| `Clause` \| `Requirement` \| `Compliance` \| `Position`) |
| `open_items` | 미결 확인 필요 사항 및 질의 목록 표 (`No.` \| `Subject` \| `Clarification` \| `Impact` \| `Status`) |
| `evidence_log` | 출처 및 근거 등급(`E1`~`E4`) 추적 표 |
| `abbreviations` | 약어 및 용어 정의 표 (`meta.abbreviations: "auto"` 설정 시 본문 약어 자동 추출 가능) |
| `figure` | 도면/이미지 삽입 (`path`, `caption`, `width_mm`) |
| `page_break` | 명시적 페이지 나눔 |
| `section_break` | `orientation: "landscape" \| "portrait"` (광폭 표를 위한 A4 가로/세로 섹션 전환) |

---

## 빌드 및 검증 명령
```bash
# 표준 빌드 + Word COM 목차/필드 자동 갱신 + PDF 변환 + PNG 렌더링 + 엄격 검수
python skill/scripts/build_doc.py docs_json/<파일명>.json --strict --render-pdf --render-png

# 스키마 및 팩트/수식 사전 점검 (파일 생성 없이 검증만 수행)
python skill/scripts/build_doc.py docs_json/<파일명>.json --check-only

# Claude.ai 웹 업로드용 스킬 패키지(.zip) 생성
python skill/scripts/build_doc.py --package-claude
```
- 빌드 완료 후 `output/<파일명>_png/page_01.png` ... 이미지를 `view_file`로 직접 열어 표 정렬, 페이지 넘김, 목차 번호를 육안으로 최종 확인한다.
