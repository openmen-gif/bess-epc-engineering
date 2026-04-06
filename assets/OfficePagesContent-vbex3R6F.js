import{a as e,t}from"./jsx-runtime-DCka7677.js";var n=t(),r=e.div`
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: 100%;
  overflow-y: auto;
  box-sizing: border-box;

  @media (max-width: 768px) {
    padding: 16px;
    gap: 16px;
  }
`,i=e.div`
  h1 { 
    font-size: 22px; font-weight: 700; margin: 0; 
    @media (max-width: 768px) { font-size: 18px; }
  }
  p  { 
    font-size: 13px; color: #6B7280; margin-top: 6px; 
    @media (max-width: 768px) { font-size: 11px; }
  }
`,a=e.hr`
  border: none;
  border-top: 1px solid rgba(255,255,255,0.08);
  margin: 0;
`,o=e.h2`
  font-size: 14px;
  font-weight: 700;
  color: #9CA3AF;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  margin: 0;
`,s=e.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;

  @media (max-width: 480px) {
    grid-template-columns: 1fr;
  }
`,c=e.div`
  background: rgba(255,255,255,0.03);
  border: 1px solid ${({$color:e})=>e?`${e}30`:`rgba(255,255,255,0.08)`};
  border-left: 3px solid ${({$color:e})=>e??`#3B82F6`};
  border-radius: 10px;
  padding: 16px;
  
  .name  { font-size: 14px; font-weight: 600; color: #F9FAFB; }
  .id    { font-size: 11px; color: #6B7280; margin-top: 3px; }
  .role  { font-size: 12px; color: #9CA3AF; margin-top: 10px; line-height: 1.6; }
`,l=e.div`
  background: rgba(59,130,246,0.06);
  border: 1px solid rgba(59,130,246,0.2);
  border-radius: 10px;
  padding: 18px;
  font-size: 13px;
  color: #9CA3AF;
  line-height: 1.8;
  
  strong { color: #F9FAFB; }
`,u=e.div`
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
`,d=e.span`
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 11px;
  color: #9CA3AF;
`,f=[{id:`CEO-001`,name:`BESS Orchestrator`,role:`프로젝트 전체를 총괄합니다. 업무를 직접 수행하지 않고 분류, 위임, 통합, 승인하는 역할을 합니다. 8개 시장(KR/JP/US/AU/UK/EU/RO/PL) 프로젝트를 조율합니다.`},{id:`CEO-010`,name:`전략기획 전문가`,role:`시장 진입 전략 수립 및 포트폴리오 관리를 담당합니다. 글로벌 BESS 시장 동향 분석 및 기회 발굴을 수행합니다.`},{id:`CEO-011`,name:`사업개발 전문가`,role:`BESS EPC 사업의 초기 단계(개발, 입찰)를 지원합니다. 고객사와의 협상 및 계약 체결 전 전략을 수립합니다.`}],p=[`🇰🇷 KR(KPX)`,`🇯🇵 JP(HEPCO)`,`🇺🇸 US(CAISO/PJM/ERCOT)`,`🇦🇺 AU(AEMO)`,`🇬🇧 UK(NGESO)`,`🇪🇺 EU(ENTSO-E)`,`🇷🇴 RO(Transelectrica)`,`🇵🇱 PL(PSE)`],m=[{id:`CTO-100`,name:`설계 총괄 컨설턴트`,role:`BESS EPC 기술 아키텍처를 총괄 설계합니다. v6.1 프레임워크 유지 및 에이전트 설계 표준을 수호합니다.`},{id:`SYS-101`,name:`시스템 엔지니어`,role:`BESS 시스템 전체 아키텍처(MW/MWh, kV) 설계. EMS 사양 및 SLD(단선결선도) 작성을 담당합니다.`},{id:`PWR-102`,name:`E-BOP 전문가`,role:`전기 BOP(Balance of Plant) 설계. 변압기, 개폐기, 계통연계장치(PCC)를 담당합니다.`},{id:`CIV-103`,name:`C-BOP 전문가`,role:`토목·건축 BOP 설계. 컨테이너 기초, 도로, 방재 시설 등을 담당합니다.`},{id:`BAT-104`,name:`배터리 전문가`,role:`LFP/NMC 배터리 셀·모듈·랙 사양. SOH/RTE 계산 및 BMS 연동 설계를 수행합니다.`},{id:`PCS-105`,name:`PCS 전문가`,role:`PCS(전력변환장치) 사양 및 제어 파라미터 설계. IEEE 1547, IEC 62477 규격 적용을 담당합니다.`},{id:`COM-106`,name:`통신네트워크 전문가`,role:`IEC 61850(GOOSE/MMS), Modbus TCP, DNP3, OPC-UA 기반 통신 아키텍처를 설계합니다.`},{id:`STD-107`,name:`규격·표준 전문가`,role:`각국 규격(IEC, IEEE, KEC, JEAC 등) 교차 검증 및 준수 여부를 검토합니다.`}],h=[`IEC 62619`,`IEC 62477`,`IEEE 1547-2018`,`IEC 61850`,`UL 9540`,`NFPA 855`,`KEC 제241조`,`JEAC 9701`,`G99`,`AS 4777`],g=[{id:`CFO-300`,name:`재무분석가`,role:`15년 IRR/NPV 재무모델 작성. CAPEX/OPEX 추정 및 시장별 수익 시뮬레이션을 수행합니다.`},{id:`CFO-301`,name:`계약전문가`,role:`EPC 계약, O&M 계약, PPA 계약 등 BESS 사업 관련 계약서 작성 및 리스크 분석을 담당합니다.`},{id:`CFO-302`,name:`법률전문가`,role:`각국 에너지법, 인허가 규정, 사이버보안법(NIS2, NERC CIP) 등 법률 리스크를 검토합니다.`},{id:`CFO-303`,name:`견적·문서 전문가`,role:`BQ(물량산출서), 견적서, 기술 제안서를 작성합니다. Word/Excel/PDF 형식으로 산출물을 제공합니다.`}],_=[{name:`🇰🇷 KR(KPX)`,services:`FR 예비력, REC 5.0, CBP`},{name:`🇯🇵 JP(HEPCO)`,services:`調整力, 容量市場, 需給調整市場`},{name:`🇺🇸 US(CAISO)`,services:`Regulation, Capacity, Energy`},{name:`🇦🇺 AU(AEMO)`,services:`FCAS 6개, NEM 5분 정산`},{name:`🇬🇧 UK(NGESO)`,services:`DC/DR/DM, Capacity Market, BM`},{name:`🇪🇺 EU(ENTSO-E)`,services:`FCR, aFRR, mFRR, Balancing Market`}],v=[{id:`COO-400`,name:`공정관리 전문가`,role:`EPC 프로젝트 WBS 수립 및 전체 공정표(MS Project/Primavera) 관리를 담당합니다.`},{id:`COO-401`,name:`구매·조달 전문가`,role:`배터리, PCS, 변압기 등 주요 기자재 조달 계획 수립 및 공급업체 관리를 수행합니다.`},{id:`COO-402`,name:`보안·HSE 전문가`,role:`LOTO 절차, 비상정지 시스템, IEC 62443(사이버보안) 등 안전/보안 계획을 수립합니다.`},{id:`COO-403`,name:`시운전 전문가`,role:`FAT/SAT/FIT 시험 절차 수립, EMS 통합 시험, 계통연계 VRT 시험을 전담합니다.`},{id:`COO-404`,name:`O&M 전문가`,role:`BESS 운영·유지보수 계획(예방정비, 성능 모니터링) 수립 및 장기 운영 전략을 담당합니다.`}],y=[{phase:`개발`,tasks:`법률·인허가 검토, 재무 타당성 분석`},{phase:`입찰`,tasks:`견적서, BQ, 기술 제안서 작성`},{phase:`시공`,tasks:`조달, 공정관리, 안전관리`},{phase:`시운전`,tasks:`FAT/SAT/FIT, 계통연계 VRT 시험`},{phase:`운영`,tasks:`O&M 계획, 성능 모니터링, 수익 최적화`}];function b(){return(0,n.jsxs)(r,{children:[(0,n.jsxs)(i,{children:[(0,n.jsx)(`h1`,{children:`🎯 CEO Office — 전략 오케스트레이션`}),(0,n.jsx)(`p`,{children:`프로젝트 총괄 지휘 및 68인 에이전트 업무 배분 허브`})]}),(0,n.jsx)(a,{}),(0,n.jsxs)(l,{children:[(0,n.jsx)(`strong`,{children:`[핵심 원칙]`}),(0,n.jsx)(`br`,{}),`• 한 번에 질문 하나만 한다 · 단계를 건너뛰지 않는다`,(0,n.jsx)(`br`,{}),`• 수치는 계산 근거와 단위를 항상 포함한다`,(0,n.jsx)(`br`,{}),`• 불확실 항목은 [요확인] 태그로 명시한다`,(0,n.jsx)(`br`,{}),(0,n.jsx)(`br`,{}),(0,n.jsx)(`strong`,{children:`[위임 체계]`}),` 0단계(업무 파악) → 1단계(작업 분해) → 2단계(조직 설계) → 3단계(설계서) → 4단계(리뷰)`]}),(0,n.jsx)(o,{children:`소속 에이전트`}),(0,n.jsx)(s,{children:f.map(e=>(0,n.jsxs)(c,{$color:`#3B82F6`,children:[(0,n.jsx)(`div`,{className:`name`,children:e.name}),(0,n.jsx)(`div`,{className:`id`,children:e.id}),(0,n.jsx)(`div`,{className:`role`,children:e.role})]},e.id))}),(0,n.jsx)(o,{children:`담당 시장`}),(0,n.jsx)(u,{children:p.map(e=>(0,n.jsx)(d,{children:e},e))})]})}function x(){return(0,n.jsxs)(r,{children:[(0,n.jsxs)(i,{children:[(0,n.jsx)(`h1`,{children:`🔩 CTO Office — 기술 설계 총괄`}),(0,n.jsx)(`p`,{children:`BESS 시스템 엔지니어링 · 설계 · 규격 검토 전담`})]}),(0,n.jsx)(a,{}),(0,n.jsxs)(l,{children:[(0,n.jsx)(`strong`,{children:`[설계 검증 분야]`}),(0,n.jsx)(`br`,{}),`• 구조해석(FEM) · 열유동해석(CFD) · 계통해석(조류/단락)`,(0,n.jsx)(`br`,{}),`• BESS 설치 유형: Type1(Standalone) / Type2(Solar+BESS) / Type3(Wind+BESS) / Type4(변전소) / Type5(Hybrid)`,(0,n.jsx)(`br`,{}),`• 핵심 공식: RTE = 방전에너지/충전에너지 × 100% | E_avail = (SOC - SOC_min) × E_nom × SOH`]}),(0,n.jsxs)(o,{children:[`소속 에이전트 (`,m.length,`명)`]}),(0,n.jsx)(s,{children:m.map(e=>(0,n.jsxs)(c,{$color:`#8B5CF6`,children:[(0,n.jsx)(`div`,{className:`name`,children:e.name}),(0,n.jsx)(`div`,{className:`id`,children:e.id}),(0,n.jsx)(`div`,{className:`role`,children:e.role})]},e.id))}),(0,n.jsx)(o,{children:`적용 규격`}),(0,n.jsx)(u,{children:h.map(e=>(0,n.jsx)(d,{children:e},e))})]})}function S(){return(0,n.jsxs)(r,{children:[(0,n.jsxs)(i,{children:[(0,n.jsx)(`h1`,{children:`💰 CFO Office — 재무 분석 · 계약 · 법무`}),(0,n.jsx)(`p`,{children:`BESS 사업 수익성 검토 · EPC 계약 · 국가별 법률 리스크 관리`})]}),(0,n.jsx)(a,{}),(0,n.jsxs)(o,{children:[`소속 에이전트 (`,g.length,`명)`]}),(0,n.jsx)(s,{children:g.map(e=>(0,n.jsxs)(c,{$color:`#F59E0B`,children:[(0,n.jsx)(`div`,{className:`name`,children:e.name}),(0,n.jsx)(`div`,{className:`id`,children:e.id}),(0,n.jsx)(`div`,{className:`role`,children:e.role})]},e.id))}),(0,n.jsx)(o,{children:`시장별 그리드 서비스`}),(0,n.jsx)(s,{children:_.map(e=>(0,n.jsxs)(c,{$color:`#F59E0B`,children:[(0,n.jsx)(`div`,{className:`name`,children:e.name}),(0,n.jsx)(`div`,{className:`role`,children:e.services})]},e.name))})]})}function C(){return(0,n.jsxs)(r,{children:[(0,n.jsxs)(i,{children:[(0,n.jsx)(`h1`,{children:`⚙️ COO Office — 운영 관리`}),(0,n.jsx)(`p`,{children:`EPC 공정 · 조달 · 안전(HSE) · 시운전 · O&M 전담`})]}),(0,n.jsx)(a,{}),(0,n.jsxs)(o,{children:[`소속 에이전트 (`,v.length,`명)`]}),(0,n.jsx)(s,{children:v.map(e=>(0,n.jsxs)(c,{$color:`#10B981`,children:[(0,n.jsx)(`div`,{className:`name`,children:e.name}),(0,n.jsx)(`div`,{className:`id`,children:e.id}),(0,n.jsx)(`div`,{className:`role`,children:e.role})]},e.id))}),(0,n.jsx)(o,{children:`프로젝트 단계별 역할`}),(0,n.jsx)(s,{children:y.map(e=>(0,n.jsxs)(c,{$color:`#10B981`,children:[(0,n.jsxs)(`div`,{className:`name`,children:[e.phase,` 단계`]}),(0,n.jsx)(`div`,{className:`role`,children:e.tasks})]},e.phase))})]})}export{b as CeoOfficePage,S as CfoOfficePage,C as CooOfficePage,x as CtoOfficePage};