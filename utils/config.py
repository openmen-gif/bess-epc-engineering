"""
BESS Dashboard runtime configuration.

Environment variable BESS_MODE controls execution mode:
  - "api"        : route heavy computation to FastAPI backend (default for local)
  - "standalone" : run everything in-process (default for cloud / HF Space)

Auto-detection: if BESS_MODE is not set, the code checks for HF Space
indicators (SPACE_ID env var) and falls back to "api" otherwise.
"""
import os

_space = os.getenv("SPACE_ID")  # set automatically on Hugging Face Spaces
_explicit = os.getenv("BESS_MODE")

if _explicit:
    MODE = _explicit.lower()
elif _space:
    MODE = "standalone"
else:
    MODE = "api"

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
IS_API_MODE = (MODE == "api")
