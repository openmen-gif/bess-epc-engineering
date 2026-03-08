FROM python:3.11-slim

WORKDIR /app

COPY packages.txt .
RUN apt-get update \
    && xargs -a packages.txt apt-get install -y --no-install-recommends \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persistent storage directory for user data (HuggingFace Spaces mounts /data)
RUN mkdir -p /data && chmod 777 /data

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:7860/_stcore/health || exit 1

ENV STREAMLIT_SERVER_PORT=7860
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV BESS_MODE=standalone

CMD ["streamlit", "run", "Dashboard.py", \
     "--server.port=7860", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
