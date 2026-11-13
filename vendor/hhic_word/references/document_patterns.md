# Document Archetypes & Composition Patterns (`hyoword` v2.0)

This guide defines the 6 canonical engineering/contractual document patterns supported by `15_Word-Auto-Skill` across **Global projects (Korea, North America/US, Europe/UK, MENA, APAC/Australia, etc.)**.

---

## 1. Global EPC Client / Consultant RFI Response (`doc_type: "rfi_response"`)

- **Profile & Mode**: `profile: "epc-en"` (or `"global-en"` for English; `"modern"` / `"kr-modern"` for Korean domestic projects), `include_cover: true`, `include_toc: true`, `abbreviations: "auto"`.
- **Recommended Block Sequence**:
  1. `callout` (`kind: "executive_summary"`): Executive summary of technical & contractual position.
  2. `heading` (L1: *Background & Scope of RFI*) + `kv_table` (`columns_mode: 4`) summarizing RFI Reference, Equipment, Baseline Standards (`IEC`, `IEEE`, `KEC/KS`, `AS/NZS`, etc.), and Contract Clauses.
  3. `heading` (L1: *Technical Assessment*) + `clause_list` (`scheme: "alpha"`) separating installation tolerances (`≤ 3 mm` shimming) from long-term geotechnical SLS settlement (`ΔS ≤ 25 mm`).
  4. `table` (Interface Division of Responsibility: OEM vs. Civil BoP vs. Electrical BoP) + `callout` (`kind: "risk_warning"`).
  5. `heading` (L1: *Contractual Risk Allocation & Proposed Redlines*) + `redline_comparison` using `~~del~~` and `++ins++`.
  6. `callout` (`kind: "draft_response"`): Ready-to-send formal response wording for transmittal.
  7. `heading` (L1: *Compliance Matrix, Open Items & Evidence*) + `requirement_matrix` + `open_items` + `evidence_log`.

---

## 2. Korean Domestic Project & HQ Technical / Contractual Review (`doc_type: "internal_technical_review"`)

- **Profile & Mode**: `profile: "modern"` (or `"kr-modern"`, `Pretendard`), `language: "ko"`, `include_cover: false` (Mode B 1-page compact header banner for internal memos) or `include_cover: true` (Mode A formal cover for Korean client/KEPCO/KPX submissions).
- **Recommended Block Sequence**:
  1. `callout` (`kind: "executive_summary"`): 핵심 검토 요약 (결론 우선 3줄 요약).
  2. `heading` (L1: *검토 목적 및 입력 자료 범위*) + `kv_table` (`columns_mode: 4`).
  3. `heading` (L1: *최초 판단과 후속 정정 사항의 정밀 대조*) + `redline_comparison` (최초 검토 판단 vs 후속 확정 대조) + `callout` (`kind: "contract_hold"`).
  4. `heading` (L1: *검토 요약 입장 및 미결 확인 과제*) + `callout` (`kind: "draft_response"`) + `open_items` + `evidence_log`.

---

## 3. Variation / Extension of Time (EOT) / Claim Position Paper (`doc_type: "claim_position_paper"`)

- **Profile & Mode**: `profile: "epc-en"` (or `"modern"` for Korean claims), `include_cover: true`, `include_toc: true`, `abbreviations: "auto"`.
- **Recommended Block Sequence**:
  1. `callout` (`kind: "executive_summary"`): Entitlement basis, delay event summary, and quantum/EOT reservation.
  2. `kv_table`: Contract Baseline, Notice Dates, Relevant FIDIC / EPC Contract Sub-Clauses (`Sub-Clause 8.4`, `Sub-Clause 20.1`, etc.).
  3. `heading` (L1: *Factual Chronology & Cause-and-Effect Analysis*) + `table` (Chronological Event Log with Evidence IDs).
  4. `heading` (L1: *Contractual Entitlement & Risk Allocation*) + `clause_list` (`scheme: "alpha"`).
  5. `open_items` + `evidence_log`.

---

## 4. Contract / Employer's Requirements Redline Review (`doc_type: "contract_redline"`)

- **Profile & Mode**: `profile: "epc-en"` (or `"modern"` for Korean contract review), `include_cover: true` (or `false` for short memo).
- **Recommended Block Sequence**:
  1. `callout` (`kind: "key_takeaway"`): Summary of high-risk commercial/technical deviations.
  2. `section_break` (`orientation: "landscape"`) when wide 5-column clause comparison tables require `262.0 mm` width.
  3. `redline_comparison`: Clause | Baseline Wording (`~~...~~`) | Proposed Markup (`++...++`) | Rationale & Fallback Position.
  4. `section_break` (`orientation: "portrait"`) + `open_items`.

---

## 5. Global & Domestic Technical Specification / Method Statement (`doc_type: "technical_spec"`)

- **Profile & Mode**: `profile: "epc-en"` (or `"modern"` for Korean specs), `include_cover: true`, `include_toc: true`, `abbreviations: "auto"`.
- **Recommended Block Sequence**:
  1. `heading` (L1: *Scope & Applicable Standards*) + `table` (Applicable Global/Regional Standards: e.g., `IEC 62933`, `IEEE 1547 / IEEE 2800`, `UL 9540 / NFPA 855`, `KEC / KS / KGS`, `EN / Grid Code`, `AS/NZS`).
  2. `heading` (L1: *System Architecture & Technical Parameters*) + `spec_table` + `figure` (if diagram provided).
  3. `heading` (L1: *Inspection & Test Plan (ITP) Hold Points*) + `requirement_matrix`.

---

## 6. Fact-Responsibility & Anti-Hallucination Rules (All Patterns)

1. **Preserve Baseline vs. Post-Review Delta**: Never overwrite an initial engineering hypothesis with a subsequent correction without recording the delta in `redline_comparison` when documenting a review history.
2. **Evidence Grading (`E1`–`E4`)**:
   - `E1`: Direct primary project document / executed contract / OEM manual in current package.
   - `E2`: Secondary internal reference such as a prior review note or internal guideline (must carry a scope warning).
   - `E3`: Unverified external assumption (must be tagged `[TO BE CONFIRMED: ...]` or `[확인 필요: ...]`).
   - `E4`: Missing mandatory input (must appear in `open_items`).
3. **Zero Fabricated Metrics**: Never invent cable slack `mm` values, structural settlement limits, or contract dates not grounded in `E1`/`E2` sources.
