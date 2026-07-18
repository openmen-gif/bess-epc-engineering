import streamlit as st

def apply_custom_css():
    st.markdown(
        """
        <style>
        /* Pretendard — 한국어 최적화 가변 폰트 (@import는 최상단 필수) */
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css');

        /* ── 디자인 토큰 (정본: utils/theme.py PALETTE와 1:1 동기) ── */
        :root {
            --bess-bg:      #0d1117;
            --bess-bg2:     #161b22;
            --bess-bg3:     #21262d;
            --bess-border:  #30363d;
            --bess-text:    #e6edf3;
            --bess-text2:   #c9d1d9;
            --bess-muted:   #8b949e;
            --bess-accent:  #58a6ff;
            --bess-accent2: #79c0ff;
            --bess-ok:      #3fb950;
            --bess-warn:    #e3b341;
            --bess-danger:  #f85149;
            --bess-radius:  10px;
            --bess-font:    'Pretendard Variable', Pretendard, 'Segoe UI', Tahoma, sans-serif;
        }

        /* Overall App Background and Default Text Size */
        .stApp {
            background-color: var(--bess-bg);
            color: var(--bess-text);
            font-size: 16px;
            font-family: var(--bess-font);
        }
        html, body, [class*="css"] { font-family: var(--bess-font); }
        /* Streamlit 헤더 완전 숨김 — 콘텐츠 가림 방지 */
        header[data-testid="stHeader"] { display: none !important; }
        [data-testid="stDecoration"] { display: none !important; }
        /* stMainBlockContainer inline style 강제 오버라이드 (headerHeight 패딩 제거) */
        [data-testid="stMainBlockContainer"] { padding-top: 1rem !important; }
        .block-container { padding-top: 1rem !important; }
        
        /* Make all basic markdown text larger */
        .stMarkdown p {
            font-size: 16px !important;
        }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: var(--bess-bg2);
            border-right: 1px solid var(--bess-border);
        }

        /* Sidebar Nav Links Styling */
        [data-testid="stSidebarNav"] span {
            color: var(--bess-text2);
            font-weight: 500;
            font-size: 16px !important;
        }
        [data-testid="stSidebarNav"] a {
            border-radius: 8px;
            transition: background 0.15s ease;
        }
        [data-testid="stSidebarNav"] a:hover {
            background: rgba(88, 166, 255, 0.08);
        }

        /* Top Header Area — hidden via display:none above */

        /* Buttons Styling */
        .stButton>button {
            background: linear-gradient(180deg, #2ea043 0%, #238636 100%);
            color: #ffffff;
            border: 1px solid rgba(240, 246, 252, 0.1);
            border-radius: 8px;
            font-weight: 600;
            font-size: 16px !important;
            transition: all 0.2s ease-in-out;
        }
        .stButton>button:hover {
            background: linear-gradient(180deg, #34b551 0%, #2ea043 100%);
            border-color: rgba(240, 246, 252, 0.2);
            color: white;
            box-shadow: 0 4px 14px rgba(46, 160, 67, 0.35);
            transform: translateY(-1px);
        }

        /* Expander/Accordion Styling */
        .streamlit-expanderHeader {
            background-color: var(--bess-bg3);
            border-radius: 8px;
            color: var(--bess-text);
            font-size: 18px !important;
        }
        [data-testid="stExpander"] {
            border: 1px solid var(--bess-border) !important;
            border-radius: var(--bess-radius) !important;
            background: var(--bess-bg2);
        }

        /* 탭 — 모던 언더라인 스타일 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            border-bottom: 1px solid var(--bess-border);
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            color: var(--bess-muted);
        }
        .stTabs [aria-selected="true"] {
            color: var(--bess-accent) !important;
        }
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: var(--bess-accent);
        }

        /* 스크롤바 — 얇은 다크 */
        ::-webkit-scrollbar { width: 10px; height: 10px; }
        ::-webkit-scrollbar-track { background: var(--bess-bg); }
        ::-webkit-scrollbar-thumb {
            background: var(--bess-border); border-radius: 5px;
        }
        ::-webkit-scrollbar-thumb:hover { background: #3e4750; }
        
        /* Checkbox Styling - ensure long labels wrap within column */
        .stCheckbox label {
            display: flex !important;
            align-items: flex-start !important;
            overflow: visible !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
        }
        .stCheckbox label p, .stCheckbox label span {
            color: #e6edf3 !important;
            font-size: 15px !important;
            white-space: normal !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            max-width: 100% !important;
        }
        
        /* Selectbox and Input styling */
        .stSelectbox label p, .stTextInput label p, .stNumberInput label p, .stSlider label p {
            font-size: 16px !important;
            font-weight: 600;
        }
        
        /* Markdown / Text Overrides */
        h1 {
            font-size: 2.5rem !important;
            font-family: var(--bess-font);
            font-weight: 800;
            background: linear-gradient(90deg, var(--bess-accent) 0%, var(--bess-accent2) 65%);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.02em;
        }
        h2 { font-size: 2.0rem !important; color: var(--bess-accent) !important; font-weight: 700; letter-spacing: -0.01em; }
        h3 { font-size: 1.6rem !important; color: var(--bess-accent) !important; font-weight: 700; }
        h4 { font-size: 1.3rem !important; color: var(--bess-accent) !important; font-weight: 600; }

        /* Dataframes & Metrics — 카드형 메트릭 */
        [data-testid="stMetric"] {
            background: var(--bess-bg2);
            border: 1px solid var(--bess-border);
            border-radius: var(--bess-radius);
            padding: 12px 16px;
            transition: border-color 0.15s ease, transform 0.15s ease;
        }
        [data-testid="stMetric"]:hover {
            border-color: var(--bess-accent);
            transform: translateY(-1px);
        }
        [data-testid="stMetricValue"] {
            color: var(--bess-ok);
            font-size: 2.0rem !important;
            font-weight: 700;
            font-variant-numeric: tabular-nums;
        }
        [data-testid="stMetricLabel"] {
            color: var(--bess-muted);
            font-size: 0.95rem !important;
        }
        
        /* Info/Success/Warning/Error boxes text size */
        .stAlert p {
            font-size: 16px !important;
        }
        
        /* 워크플로우 카드 내 텍스트 overflow 방지 */
        [data-testid="stVerticalBlockBorderWrapper"] {
            overflow: hidden !important;
        }
        [data-testid="stVerticalBlockBorderWrapper"] p,
        [data-testid="stVerticalBlockBorderWrapper"] a,
        [data-testid="stVerticalBlockBorderWrapper"] span {
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            white-space: normal !important;
            max-width: 100% !important;
        }
        /* page_link 버튼 overflow 방지 */
        [data-testid="stPageLink"] {
            max-width: 100% !important;
            overflow: hidden !important;
        }
        [data-testid="stPageLink"] a {
            white-space: normal !important;
            word-break: break-all !important;
            font-size: 14px !important;
        }

        /* Hide unnecessary branding */
        footer {visibility: hidden;}
        
        /* =========================================
           MOBILE RESPONSIVE (max-width: 768px)
           ========================================= */
        @media (max-width: 768px) {
            /* 사이드바 축소 */
            [data-testid="stSidebar"] {
                min-width: 0 !important;
            }
            /* 패딩 조정 — 상단은 네비 바 높이만큼 확보 */
            [data-testid="stMainBlockContainer"],
            .block-container {
                padding-top: 1rem !important;
                padding-left: 0.8rem !important;
                padding-right: 0.8rem !important;
                padding-bottom: 3rem !important;
                max-width: 100% !important;
            }
            /* 제목 크기 축소 */
            h1 { font-size: 1.4rem !important; }
            h2 { font-size: 1.2rem !important; }
            h3 { font-size: 1.05rem !important; }
            h4 { font-size: 0.95rem !important; }
            /* 본문 텍스트 축소 */
            .stMarkdown p { font-size: 13px !important; }
            .stAlert p { font-size: 13px !important; }
            /* 메트릭 카드 축소 */
            [data-testid="stMetricValue"] {
                font-size: 1.2rem !important;
            }
            [data-testid="stMetricLabel"] {
                font-size: 0.75rem !important;
            }
            [data-testid="stMetricDelta"] {
                font-size: 0.7rem !important;
            }
            /* Columns → 세로 스택 */
            [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
                gap: 0.3rem !important;
            }
            [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
                min-width: 100% !important;
                flex: 1 1 100% !important;
            }
            /* 탭 — 가로 스크롤 허용 + 글자 잘림 방지 (강한 우선순위) */
            .stApp .stTabs [data-baseweb="tab-list"],
            .stApp [role="tablist"] {
                display: flex !important;
                overflow-x: auto !important;
                overflow-y: hidden !important;
                flex-wrap: nowrap !important;
                scrollbar-width: thin !important;
                -webkit-overflow-scrolling: touch !important;
                width: 100% !important;
                max-width: 100% !important;
            }
            .stApp .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar,
            .stApp [role="tablist"]::-webkit-scrollbar {
                height: 4px;
            }
            .stApp .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb,
            .stApp [role="tablist"]::-webkit-scrollbar-thumb {
                background: #30363d;
                border-radius: 2px;
            }
            .stApp .stTabs [data-baseweb="tab-list"] button,
            .stApp [role="tablist"] [role="tab"],
            .stApp [role="tablist"] button {
                font-size: 0.8rem !important;
                padding: 6px 10px !important;
                white-space: nowrap !important;
                word-break: keep-all !important;
                flex: 0 0 auto !important;
                flex-shrink: 0 !important;
                width: auto !important;
                min-width: max-content !important;
                max-width: none !important;
            }
            .stApp .stTabs [data-baseweb="tab-list"] button *,
            .stApp [role="tablist"] [role="tab"] *,
            .stApp [role="tablist"] button * {
                white-space: nowrap !important;
                word-break: keep-all !important;
                overflow: visible !important;
                text-overflow: clip !important;
            }
            /* 탭 컨테이너가 stHorizontalBlock의 flex-wrap 영향 받지 않도록 */
            .stApp .stTabs,
            .stApp .stTabs > div {
                width: 100% !important;
                max-width: 100% !important;
                overflow: visible !important;
            }
            /* 버튼 크기 */
            .stButton > button {
                font-size: 0.8rem !important;
                padding: 6px 12px !important;
            }
            /* iframe 반응형 */
            iframe {
                max-width: 100% !important;
                width: 100% !important;
                height: 350px !important;
            }
            /* 테이블/데이터프레임 가로 스크롤 */
            [data-testid="stDataFrame"] {
                overflow-x: auto !important;
            }
            /* 슬라이더 */
            .stSlider { padding: 0 !important; }
            /* 체크박스 */
            .stCheckbox label p, .stCheckbox label span {
                font-size: 13px !important;
            }
            /* selectbox/input 라벨 */
            .stSelectbox label p, .stTextInput label p,
            .stNumberInput label p, .stSlider label p {
                font-size: 13px !important;
            }
            /* 캡션 / 작은 텍스트 */
            .stCaption, small { font-size: 0.7rem !important; }
            /* expander */
            .streamlit-expanderHeader { font-size: 14px !important; }
        }

        /* =========================================
           SMALL MOBILE (max-width: 480px)
           ========================================= */
        @media (max-width: 480px) {
            .block-container {
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
                padding-bottom: 3rem !important;
            }
            h1 { font-size: 1.2rem !important; }
            h2 { font-size: 1.05rem !important; }
            h3 { font-size: 0.95rem !important; }
            h4 { font-size: 0.85rem !important; }
            .stMarkdown p { font-size: 12px !important; }
            iframe { height: 280px !important; }
            /* 탭 다수 시 가로 스크롤 (강한 우선순위) */
            .stApp .stTabs [data-baseweb="tab-list"],
            .stApp [role="tablist"] {
                overflow-x: auto !important;
                flex-wrap: nowrap !important;
                width: 100% !important;
            }
            .stApp .stTabs [data-baseweb="tab-list"] button,
            .stApp [role="tablist"] [role="tab"],
            .stApp [role="tablist"] button {
                font-size: 0.7rem !important;
                padding: 4px 8px !important;
                white-space: nowrap !important;
                word-break: keep-all !important;
                flex: 0 0 auto !important;
                min-width: max-content !important;
            }
            .stApp .stTabs [data-baseweb="tab-list"] button *,
            .stApp [role="tablist"] [role="tab"] *,
            .stApp [role="tablist"] button * {
                white-space: nowrap !important;
                word-break: keep-all !important;
            }
        }

        /* =========================================
           TABLET (769px ~ 1024px)
           ========================================= */
        @media (min-width: 769px) and (max-width: 1024px) {
            /* 3열 이상 → 2열로 축소 */
            [data-testid="stHorizontalBlock"] {
                flex-wrap: wrap !important;
            }
            [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {
                min-width: 48% !important;
                flex: 1 1 48% !important;
            }
            h1 { font-size: 1.8rem !important; }
            h2 { font-size: 1.5rem !important; }
            h3 { font-size: 1.3rem !important; }
        }

        /* =========================================
           PRINT LAYOUT SPECIFIC CSS
           ========================================= */
        @media print {
            /* Reset body and background to white for ink saving */
            body, .stApp, .main, .block-container {
                background-color: #ffffff !important;
                color: #000000 !important;
                background-image: none !important;
                padding-top: 0 !important;
                padding-bottom: 0 !important;
                padding-left: 0 !important;
                padding-right: 0 !important;
            }
            
            /* Hide Sidebar, Header, and interactive elements */
            [data-testid="stSidebar"], 
            header[data-testid="stHeader"], 
            .stButton, 
            footer,
            .stAudio,
            .stDownloadButton {
                display: none !important;
            }
            
            /* Adjust Main Content Area to take full width */
            .main {
                margin: 0 !important;
                padding: 0 !important;
                width: 100% !important;
                max-width: 100% !important;
            }
            
            /* Typography Adjustments for Print Readability */
            h1, h2, h3, h4, h5, h6, 
            .stMarkdown p, .stMarkdown li, 
            .stMetricLabel, .stMetricValue,
            .stCheckbox label p,
            .stSelectbox label p, .stTextInput label p, .stNumberInput label p, .stSlider label p {
                color: #000000 !important;
                text-shadow: none !important;
            }
            
            /* Make headings bold and pure black (그라디언트 텍스트 해제 포함) */
            h1, h2, h3, h4 {
                color: #000000 !important;
                background: none !important;
                -webkit-text-fill-color: #000000 !important;
                page-break-after: avoid;
                margin-top: 10px !important;
                margin-bottom: 5px !important;
            }
            
            /* Ensure info/success/warning boxes (Alerts) lose their tinted backgrounds */
            .stAlert, .stAlert > div, .stAlert p {
                background-color: transparent !important;
                background: none !important;
                border: none !important;
                border-left: 4px solid #555 !important; /* simple grey accent line instead of full box */
                box-shadow: none !important;
                color: #000000 !important;
            }
            
            /* Fix Metrics (the big green numbers) to be dark and readable */
            [data-testid="stMetric"] {
                background-color: transparent !important;
                border: 1px solid #ccc !important;
                box-shadow: none !important;
                color: #000000 !important;
                padding: 10px !important;
            }
            [data-testid="stMetricValue"], [data-testid="stMetricValue"] > div {
                color: #000000 !important;
                font-weight: bold !important;
            }
            [data-testid="stMetricDelta"] > div {
                color: #333333 !important; /* Darken the small delta text too */
            }
            
            /* Inputs (text, number, select) - simple underline/border */
            .stNumberInput input, .stTextInput input, .stSelectbox > div {
                background-color: transparent !important;
                border: 1px solid #aaa !important;
                color: #000000 !important;
            }
            
            /* Fixing Column Overflow and Overlap */
            .element-container, .stVerticalBlock {
                max-width: 100% !important;
                background-color: transparent !important;
                overflow: visible !important;
            }
            
            /* Keep horizontal layout but allow wrapping when content is too wide */
            [data-testid="stHorizontalBlock"] {
                display: flex !important;
                flex-wrap: wrap !important;
                gap: 6px !important;
                width: 100% !important;
                align-items: flex-start !important;
                page-break-inside: avoid;
            }
            
            /* Columns: each gets at least 45% so 2-col fits, 3+ col wraps cleanly */
            [data-testid="column"] {
                flex: 1 1 45% !important;
                min-width: 0 !important;     /* allow it to shrink below 45% if needed */
                max-width: 100% !important;
                overflow: hidden !important;
                padding: 4px !important;
                box-sizing: border-box !important;
            }
            
            /* All text content wraps within its container */
            p, li, span, label, caption, td, th {
                white-space: normal !important;
                word-wrap: break-word !important;
                overflow-wrap: break-word !important;
                max-width: 100% !important;
            }
            
            /* Scale print font sizes slightly so more fits per line */
            h1 { font-size: 20pt !important; }
            h2 { font-size: 16pt !important; }
            h3 { font-size: 13pt !important; }
            h4, h5, h6 { font-size: 11pt !important; }
            body, p, span, label { font-size: 9pt !important; }
            
            /* Input widgets: force to not overflow column */
            .stNumberInput, .stTextInput, .stSelectbox, .stSlider {
                max-width: 100% !important;
                overflow: hidden !important;
            }
            .stNumberInput input, .stTextInput input {
                width: 100% !important;
                min-width: 0 !important;
            }
            .stSlider > div {
                max-width: 100% !important;
            }
            
            /* Plotly Charts & Heatmaps - Try to force white backgrounds */
            .js-plotly-plot .plotly .bg, 
            .js-plotly-plot .plotly .paper {
                fill: white !important;
            }
            
            /* Prevent page breaks inside cards/metrics/expanders */
            [data-testid="stVerticalBlock"], 
            [data-testid="stMetric"], 
            .streamlit-expanderContent {
                page-break-inside: avoid;
            }
            
            /* General page layout for A4/Letter */
            @page {
                size: A4;
                margin: 10mm; /* Minimal margins for maximum data area */
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

