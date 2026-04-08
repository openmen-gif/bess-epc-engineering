FROM python:3.11-slim

WORKDIR /app

# Python 패키지 설치 (레이어 캐시)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 스킬 MD 파일 (변경 빈도 낮음)
COPY skill_md/ skill_md/

# API 서버
COPY api/ api/

# 프론트엔드 정적 빌드
COPY static/ static/

# README (HF Spaces 설정)
COPY README.md .

ENV SKILL_MD_DIR=/app/skill_md

EXPOSE 7860

CMD ["uvicorn", "api.agent_api:app", "--host", "0.0.0.0", "--port", "7860"]
