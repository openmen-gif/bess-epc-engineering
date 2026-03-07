"""
utils/ipo_en_data.py
English I/P/O content for BESS skill modules.
Used by 07_IPO_Checklists.py when lang == 'EN'.
Key = skill filename (without .md), Value = dict with 'inputs', 'processes', 'outputs' lists.
"""

EN_IPO: dict[str, dict[str, list[str]]] = {

    "bess-project-manager": {
        "inputs": [
            "Project specs (MW/MWh, EPC/EPCM contract type)",
            "Schedule (NTP, PAC, FAC dates) & LD conditions",
            "Budget & financial close conditions",
            "Owner's requirements & approval procedures",
            "WBS baseline & stakeholder register",
            "Existing Lessons Learned database",
        ],
        "processes": [
            "Develop Project Execution Plan (PEP) & Project Charter",
            "Establish WBS (Level 3–4) & RACI matrix",
            "Conduct kick-off meeting & set reporting cadence",
            "Update Weekly & Monthly progress reports",
            "Track SPI / CPI via EVM & S-Curve",
            "Manage Change (MOC) — log Variation Orders",
            "Resolve engineering / procurement / site interfaces",
            "Monitor Risk Register & trigger mitigation actions",
            "Prepare PAC / FAC documentation & punch-list closeout",
        ],
        "outputs": [
            "Project Execution Plan (PEP) (.docx)",
            "Weekly Progress Report (.docx/.pptx)",
            "Monthly Management Report (.pptx)",
            "RACI Matrix (.xlsx)",
            "MOC / Change Log (.xlsx)",
            "Lessons Learned Report (.docx)",
            "Project Close-out Report (.docx)",
        ],
    },

    "bess-scheduler": {
        "inputs": [
            "Project scope (MW/MWh) & target market",
            "Contractual milestones: NTP / PAC / FAC & LD basis",
            "Equipment lead times: Battery / PCS / Transformer",
            "Permit schedule (construction, fire, grid interconnection)",
            "Site construction constraints (weather, access)",
            "Commissioning duration plan",
        ],
        "processes": [
            "Build WBS (7-level) and activity network (FS/FF/SS/SF)",
            "Identify Critical Path and Near-Critical (Float ≤ 5 days)",
            "Set Baseline Schedule in P6 / MS Project",
            "Run 3-week Look-Ahead schedule weekly",
            "Calculate SPI / CPI from earned value data",
            "Plot S-Curve: PV vs EV vs AC",
            "Conduct Delay Analysis (Window / TIA method) on delays",
            "Perform Monte Carlo simulation for P50/P80/P90 completion dates",
            "Issue delay notice & recovery plan to Owner",
        ],
        "outputs": [
            "Baseline Schedule (.xer / .mpp / PDF Gantt)",
            "Weekly Progress Report with S-Curve",
            "3-Week Look-Ahead (Excel)",
            "Delay Analysis Report (.docx)",
            "Monte Carlo Risk Schedule (P50/P80/P90)",
            "Recovery Schedule",
        ],
    },

    "bess-risk-manager": {
        "inputs": [
            "Project scope (MW/MWh) & contract type (FIDIC EPC)",
            "Baseline schedule & cost budget",
            "Target market (KR/US/JP/AU/UK/EU/RO)",
            "Vendor financial assessment & lead time data",
            "Grid interconnection approval timeline",
            "Exchange rate & commodity price data",
        ],
        "processes": [
            "Identify risks using Risk Breakdown Structure (RBS)",
            "Score each risk: P (1–5) × I (1–5) → Risk Score",
            "Grade risks: Critical ≥ 20 / High 12–16 / Medium 5–10 / Low 1–4",
            "Define response strategy: Avoid / Mitigate / Transfer / Accept",
            "Assign risk Owner and response deadline",
            "Update Risk Register weekly; escalate Critical risks to PM",
            "Run Monte Carlo cost risk simulation (N=10,000)",
            "Monitor Early Warning Indicators (SPI < 0.9, CPI < 0.95)",
            "Issue Monthly Risk Report to Owner",
        ],
        "outputs": [
            "Risk Register (.xlsx) — ID, IF-THEN description, P, I, Score, Response",
            "Quantitative Risk Analysis (Monte Carlo P50/P80/P90)",
            "Monthly Risk Report (.docx/.pptx)",
            "Risk Heatmap (5×5)",
            "Early Warning Dashboard",
            "Contingency Usage Log (.xlsx)",
        ],
    },

    "bess-system-engineer": {
        "inputs": [
            "RFP / Client specifications (MW, MWh, grid voltage)",
            "Target market & grid code requirements",
            "C-Rate requirement (0.25C / 0.5C / 1C / 2C)",
            "Site environmental data (temperature, altitude)",
            "Battery chemistry preference (LFP / NMC)",
            "RTE, auxiliary loss, and EPC margin targets",
        ],
        "processes": [
            "Calculate total energy & power scaling (nameplate DC capacity)",
            "Account for RTE, auxiliary loads, and degradation margin",
            "Determine number of battery enclosures & PCS skids",
            "Draft Single Line Diagram (SLD) concept",
            "Select key equipment ratings (PCS, Transformer, MV switchgear)",
            "Coordinate footprint with E-BOP & C-BOP teams",
            "Review regional standards (IEEE 1547, KEC, IEC 62619, etc.)",
        ],
        "outputs": [
            "BESS Conceptual Architecture Diagram",
            "System Sizing Calculation Sheet (.xlsx)",
            "High-level Equipment Schedule / BOM",
            "SLD Base Concept Drawing",
            "System Architecture Report (.txt / .docx)",
        ],
    },

    "bess-ebop-engineer": {
        "inputs": [
            "BESS capacity (MW / MWh) & grid voltage",
            "Grid code & protection relay requirements",
            "Cable routing distances & load currents",
            "Soil resistivity data for grounding design",
            "Target market standards (NEC, KEC, IEC 60364, AS/NZS)",
        ],
        "processes": [
            "Size main & PCS transformers (MVA, impedance, vector group)",
            "Calculate MV/LV cable cross-sections (thermal & voltage drop)",
            "Design protection relay coordination (OVR/UVR, ROCOF, OCEF)",
            "Design grounding grid to IEEE 80 / IEC 60364 standards",
            "Verify arc flash hazard & PPE category",
            "Produce Single Line Diagram (SLD) — IFA / IFC revisions",
            "Review regional E-BOP standards compliance",
        ],
        "outputs": [
            "Transformer Sizing Calculation (.xlsx)",
            "Cable Sizing Schedule (.xlsx)",
            "Protection Relay Setting Sheets (.xlsx)",
            "Grounding Grid Design Calculation",
            "SLD — Issued for Approval (IFA) / Issued for Construction (IFC)",
            "E-BOP Design Report (.docx)",
        ],
    },

    "bess-cbop-engineer": {
        "inputs": [
            "Number and dimensions of battery enclosures & PCS skids",
            "Equipment weights & operating loads",
            "Soil bearing capacity & geotechnical report",
            "Design wind speed & seismic zone",
            "Target market civil standards (IBC/ASCE 7, KDS, Eurocode)",
        ],
        "processes": [
            "Design equipment foundation pads (sizing, rebar, concrete grade)",
            "Calculate pad bearing pressure vs soil capacity",
            "Design cable trench & duct bank routing",
            "Specify HVAC system for enclosures & MV rooms",
            "Design fire protection system layout (suppression, separation)",
            "Verify NFPA 855 / local fire code separation distances",
            "Prepare civil grading & drainage plan",
        ],
        "outputs": [
            "Foundation Pad Design Calculation (.xlsx)",
            "Trench & Duct Bank Layout Drawing",
            "Civil Grading & Drainage Plan",
            "HVAC Equipment Specification",
            "Fire Protection Layout Drawing",
            "C-BOP Design Report (.docx)",
        ],
    },

    "bess-battery-expert": {
        "inputs": [
            "Target capacity (MW / MWh) & C-Rate",
            "Battery chemistry selection (LFP / NMC / Solid-State)",
            "Cycle life requirement & calendar life",
            "Operating temperature range",
            "BMS & thermal management preferences",
        ],
        "processes": [
            "Define cell / module / rack / system hierarchy",
            "Calculate number of cells in series & parallel",
            "Size BMS parameters (SOC window, SOH tracking)",
            "Analyse thermal management: liquid vs air cooling",
            "Review cycle life degradation model (capacity fade curve)",
            "Evaluate LFP vs NMC trade-off for application",
            "Review IEC 62619 / UL 9540 safety certification requirements",
        ],
        "outputs": [
            "Battery System Architecture Design (.docx)",
            "Cell-to-System Sizing Calculation (.xlsx)",
            "Degradation Projection Report (SOH vs EFC)",
            "BMS Parameter Setting Sheet",
            "Safety Certification Requirement Checklist",
        ],
    },

    "bess-data-analyst": {
        "inputs": [
            "Real-time SCADA data (SOC, voltage, current, temperature)",
            "Historical charge/discharge cycle data",
            "Grid metering data (every 5 / 15 min)",
            "Manufacturer SOH degradation curve",
            "Target RTE & auxiliary loss targets",
        ],
        "processes": [
            "Calculate system availability & MTBF",
            "Track Round-Trip Efficiency (RTE) trend vs target",
            "Plot SOH vs EFC degradation curve",
            "Run Isolation Forest anomaly detection on cell temperatures",
            "Build monthly Charge / Discharge profile charts",
            "Generate KPI dashboard (availability, RTE, aux power)",
            "Alert on Early Warning Indicators (T > 35°C, ΔV > 50 mV)",
        ],
        "outputs": [
            "Monthly KPI Dashboard Report (.pptx)",
            "SOH Degradation Trend Chart",
            "Anomaly Detection Alert Log",
            "Efficiency Loss Analysis Report",
            "Data Reporting Package to grid operator",
        ],
    },

    "bess-fire-engineer": {
        "inputs": [
            "BESS capacity & enclosure layout plan",
            "Battery chemistry (LFP / NMC) & thermal runaway data",
            "Building category & occupancy classification",
            "Target market fire codes (NFPA 855, KFS, AS 5139)",
            "Site environmental data (wind direction, slope)",
        ],
        "processes": [
            "Calculate minimum separation distances (NFPA 855 / local code)",
            "Select fire suppression system (clean agent, water mist, CO₂)",
            "Design smoke extraction system & FDS simulation",
            "Specify thermal runaway detection (rack-level BMS + thermal camera)",
            "Review sprinkler system layout vs NFPA 13",
            "Prepare Emergency Response Plan (ERP)",
            "Coordinate authority having jurisdiction (AHJ) review",
        ],
        "outputs": [
            "Fire Protection Design Report (.docx)",
            "Equipment Separation Distance Calculation",
            "Fire Suppression System Specification",
            "Smoke Extraction & FDS Analysis Report",
            "Emergency Response Plan (ERP) (.docx)",
            "AHJ Submission Package",
        ],
    },

    "bess-procurement-expert": {
        "inputs": [
            "Project BOM (Battery, PCS, Transformer, Switchgear, Cable)",
            "Project schedule — required delivery dates by package",
            "Budget & contract form (Turnkey / Supply-only / FIDIC)",
            "Approved vendor list (AVL) & qualification status",
            "Target market import/export regulations",
        ],
        "processes": [
            "Issue RFQ packages to qualified vendors",
            "Evaluate bids: Technical + Commercial + Schedule",
            "Negotiate terms: price, payment, warranty, LD, delivery",
            "Place Purchase Orders and track acknowledgements",
            "Monitor vendor manufacturing progress (MFR reports)",
            "Witness Factory Acceptance Tests (FAT)",
            "Coordinate logistics: sea freight, customs, site delivery",
            "Process vendor invoices vs milestone payment schedule",
        ],
        "outputs": [
            "RFQ Package (Technical Specification + Commercial Terms)",
            "Bid Evaluation Matrix (.xlsx)",
            "Purchase Order (PO) set",
            "Procurement Status Report (PSR) (.xlsx)",
            "FAT Acceptance Certificate",
            "Packing List & Shipping Documents",
        ],
    },

    "bess-financial-analysis": {
        "inputs": [
            "Project CAPEX estimate by package (Battery, EPC, Grid)",
            "Revenue model: market (ERCOT/AEMO), tariff, PPA",
            "Financing structure: equity ratio, loan terms, interest rate",
            "Target IRR / NPV / DSCR thresholds",
            "Battery degradation profile & replacement cost",
            "O&M cost projection ($/MWh-yr)",
        ],
        "processes": [
            "Build 20-year cash flow model in Excel",
            "Calculate project IRR, NPV, Payback Period",
            "Compute DSCR (Debt Service Coverage Ratio) year-by-year",
            "Run sensitivity analysis on CAPEX ±10%, revenue ±15%",
            "Perform scenario analysis: Base / Bull / Bear",
            "Assess IRA tax credit (US) or government incentive eligibility",
            "Prepare financial model for lender / investor review",
        ],
        "outputs": [
            "Financial Model (.xlsx) — 20-year DCF, IRR, NPV, DSCR",
            "Sensitivity Analysis Charts",
            "Investment Memo (.docx)",
            "Lender's Information Memorandum (LIM)",
            "Incentive Eligibility Assessment Report",
        ],
    },

    "bess-structural-analyst": {
        "inputs": [
            "Equipment weights & center of gravity data",
            "Foundation pad dimensions & soil report",
            "Seismic zone & design acceleration (g)",
            "Wind load (design wind speed, m/s)",
            "Snow load (if applicable)",
            "Applicable structural code (ASCE 7, KDS 41, Eurocode 8)",
        ],
        "processes": [
            "Calculate dead, live, wind, and seismic loads per code",
            "Determine governing load combination (1.2D + 1.6L, etc.)",
            "Calculate DCR (Demand / Capacity Ratio) for foundation",
            "Design rebar layout & concrete grade",
            "Perform Von Mises stress analysis for steel frames",
            "Verify anchor bolt capacity against seismic uplift",
            "Check settlement & differential settlement criteria",
        ],
        "outputs": [
            "Structural Calculation Package (.xlsx / .pdf)",
            "Foundation Plan & Detail Drawings",
            "Anchor Bolt Schedule",
            "DCR Summary Table",
            "Structural Analysis Report (.docx)",
        ],
    },

    "bess-qaqc-engineer": {
        "inputs": [
            "Project QA/QC Plan (PQP) & Inspection Test Plan (ITP)",
            "Vendor drawing & datasheet submittals",
            "Factory Acceptance Test (FAT) witness plan",
            "Site Acceptance Test (SAT) procedures",
            "Non-Conformance Report (NCR) register",
        ],
        "processes": [
            "Review & approve vendor submittals (drawings, datasheets, CoC)",
            "Attend FAT at vendor factory — witness key tests",
            "Conduct incoming inspection at site",
            "Perform in-process construction inspection (ITP hold points)",
            "Issue NCRs for non-conformances; track Corrective Action Reports (CAR)",
            "Conduct Pre-Commissioning checks (insulation, continuity, relay)",
            "Complete punch-list & handover to commissioning team",
        ],
        "outputs": [
            "Inspection & Test Plan (ITP)",
            "FAT Witness Report",
            "Incoming Inspection Records",
            "NCR / CAR Log (.xlsx)",
            "Pre-Commissioning Checksheets",
            "Quality Close-out Report (.docx)",
        ],
    },

    "bess-contract-specialist": {
        "inputs": [
            "Contract documents (FIDIC Silver/Gold, NEC, bespoke EPC)",
            "Project schedule (Baseline) & milestone dates",
            "Change event notifications from site or Owner",
            "Variation Order (VO) requests",
            "Dispute records & correspondence log",
        ],
        "processes": [
            "Review contract risk allocation: LD, performance guarantees, indemnities",
            "Track contract milestones & notice periods (FIDIC Clause 20)",
            "Draft & submit Extension of Time (EOT) claims",
            "Prepare Additional Cost claims with substantiation",
            "Manage Variation Orders (VO) — scope, price, time impact",
            "Maintain contemporaneous records for potential disputes",
            "Negotiate settlement agreements with Owner",
        ],
        "outputs": [
            "Contract Risk Register (.xlsx)",
            "EOT Claim Submission (.docx)",
            "Additional Cost Claim Report",
            "Variation Order Log (.xlsx)",
            "Contract Correspondence Log",
            "Settlement Agreement Draft (.docx)",
        ],
    },

    "bess-grid-interconnection": {
        "inputs": [
            "BESS capacity (MW / MWh) & point of interconnection voltage",
            "Grid operator (KEPCO / ERCOT / AEMO / National Grid) requirements",
            "Grid code technical requirements (FRT, reactive power, ROCOF)",
            "Utility interconnection application forms & fees",
            "Power system study report from grid operator",
        ],
        "processes": [
            "Submit grid interconnection application to utility",
            "Provide technical data sheet (TDS) for PCS & BESS",
            "Respond to power system study reports (short circuit, load flow)",
            "Negotiate interconnection agreement commercial terms",
            "Confirm protection relay settings with utility",
            "Conduct grid interconnection test (VRT, FFR, ROCOF test)",
            "Obtain grid interconnection approval certificate",
        ],
        "outputs": [
            "Grid Interconnection Application Package",
            "Technical Data Sheet (TDS) for PCS & BESS",
            "Power System Study Review Comments",
            "Interconnection Agreement (IA)",
            "Protection Relay Setting Confirmation",
            "Grid Interconnection Test Report",
            "Approval Certificate from Utility",
        ],
    },
}
