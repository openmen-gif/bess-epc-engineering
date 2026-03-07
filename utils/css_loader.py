import streamlit as st

def apply_custom_css():
    st.markdown(
        """
        <style>
        /* Overall App Background and Default Text Size */
        .stApp {
            background-color: #0d1117;
            color: #e6edf3;
            font-size: 16px;
        }
        
        /* Make all basic markdown text larger */
        .stMarkdown p {
            font-size: 16px !important;
        }
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #161b22;
            border-right: 1px solid #30363d;
        }
        
        /* Sidebar Nav Links Styling */
        [data-testid="stSidebarNav"] span {
            color: #c9d1d9;
            font-weight: 500;
            font-size: 16px !important;
        }
        
        /* Top Header Area */
        header[data-testid="stHeader"] {
            background-color: rgba(13, 17, 23, 0.9) !important;
            border-bottom: 1px solid #30363d;
        }

        /* Buttons Styling */
        .stButton>button {
            background-color: #238636;
            color: #ffffff;
            border: 1px solid rgba(240, 246, 252, 0.1);
            border-radius: 6px;
            font-weight: 600;
            font-size: 16px !important;
            transition: all 0.2s ease-in-out;
        }
        .stButton>button:hover {
            background-color: #2ea043;
            border-color: rgba(240, 246, 252, 0.1);
            color: white;
            box-shadow: 0 0 10px rgba(46, 160, 67, 0.4);
        }
        
        /* Expander/Accordion Styling */
        .streamlit-expanderHeader {
            background-color: #21262d;
            border-radius: 6px;
            color: #e6edf3;
            font-size: 18px !important;
        }
        
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
            color: #58a6ff !important;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-weight: 700;
        }
        h2 { font-size: 2.0rem !important; color: #58a6ff !important; font-weight: 700; }
        h3 { font-size: 1.6rem !important; color: #58a6ff !important; font-weight: 700; }
        h4 { font-size: 1.3rem !important; color: #58a6ff !important; font-weight: 600; }
        
        /* Dataframes & Metrics */
        [data-testid="stMetricValue"] {
            color: #3fb950;
            font-size: 2.2rem !important;
        }
        [data-testid="stMetricLabel"] {
            color: #8b949e;
            font-size: 1rem !important;
        }
        
        /* Info/Success/Warning/Error boxes text size */
        .stAlert p {
            font-size: 16px !important;
        }
        
        /* Hide unnecessary branding */
        footer {visibility: hidden;}
        
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
            
            /* Make headings bold and pure black */
            h1, h2, h3, h4 {
                color: #000000 !important;
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
