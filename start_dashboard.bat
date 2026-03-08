@echo off
echo Starting BESS EPC Platform Dashboard...
cd /d "%~dp0"
streamlit run Dashboard.py
pause
