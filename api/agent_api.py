"""
BESS AI Agent API Server
- 00_Skill_MD 폴더의 에이전트 MD 파일을 파싱하여
- 명령어 키워드에 맞는 에이전트 지식 기반 응답을 생성한다
"""
import os
import re
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List

app = FastAPI(title="BESS Agent Knowledge API", version="1.0")

# CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── MD 파일 경로 (환경변수 우선, 없으면 로컬 상대 경로) ───────────────────────
SKILL_MD_DIR = Path(os.getenv("SKILL_MD_DIR", Path(__file__).resolve().parent.parent / "skill_md"))

# ── 에이전트 인덱스 (MD 파일 로드 시 캐시) ────────────────────────────────────
_agent_index: dict = {}

def parse_md_frontmatter(content: str) -> dict:
    """YAML frontmatter 파싱 (--- ... --- 구문)"""
    meta = {}
    lines = content.split("\n")
    if len(lines) > 0 and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                break
            if ":" in line:
                key, _, val = line.partition(":")
                meta[key.strip()] = val.strip().strip('"')
    return meta

def extract_sections(content: str) -> dict:
    """MD 내 주요 섹션 추출 (## 헤더 기준)"""
    sections = {}
    current = "intro"
    buf = []
    for line in content.split("\n"):
        if line.startswith("## "):
            if buf:
                sections[current] = "\n".join(buf).strip()
            current = line[3:].strip()
            buf = []
        else:
            buf.append(line)
    if buf:
        sections[current] = "\n".join(buf).strip()
    return sections

def extract_agent_prompt(content: str) -> str:
    """<Process_Context> 블록에서 실제 에이전트 지침 추출"""
    match = re.search(r"<Process_Context>(.*?)</Process_Context>", content, re.DOTALL)
    # <Agent_Prompt> 블록도 검색 (구버전 대응)
    if not match:
        match = re.search(r"<Agent_Prompt>(.*?)</Agent_Prompt>", content, re.DOTALL)
    return match.group(1).strip() if match else ""

def build_index():
    """모든 MD 파일 파싱 → 인덱스 구축"""
    global _agent_index
    _agent_index.clear()
    if not SKILL_MD_DIR.exists():
        print(f"[ERROR] MD Directory NOT FOUND: {SKILL_MD_DIR}")
        return
    
    for md_path in SKILL_MD_DIR.glob("bess-*.md"):
        try:
            content = md_path.read_text(encoding="utf-8", errors="ignore")
            meta     = parse_md_frontmatter(content)
            sections = extract_sections(content)
            prompt   = extract_agent_prompt(content)
            
            agent_id = meta.get("id", "") or md_path.stem.upper()
            name     = meta.get("name", "") or md_path.stem
            dept     = meta.get("department", "BESS Experts")
            desc     = meta.get("description", "")
            
            # 라우팅 키워드 추출 (소문자 집합)
            keywords = set()
            keywords.update(re.split(r"[,/·、\s]+", desc.lower()))
            keywords.update(re.split(r"[,/·、\s]+", name.lower().replace("-", " ")))
            # 파일명에서 핵심 키워드 추출
            stem_core = md_path.stem.replace("bess-", "").replace("-", " ")
            keywords.update(stem_core.split())
            keywords.discard("")
            
            _agent_index[md_path.stem] = {
                "id":       agent_id,
                "name":     name,
                "dept":     dept,
                "desc":     desc,
                "keywords": keywords,
                "sections": sections,
                "prompt":   prompt[:3000],
                "filename": md_path.name
            }
        except Exception as e:
            print(f"[WARN] Failed to parse {md_path.name}: {e}")
    print(f"[INFO] Successfully loaded {len(_agent_index)} agent MD files from {SKILL_MD_DIR}")

# 서버 시작 시 인덱스 구축 (startup 이벤트로 비동기 실행)
@app.on_event("startup")
def startup_build_index():
    build_index()

# ── 요청/응답 스키마 ──────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    command: str

class LogEntry(BaseModel):
    type: str  # '', 'success', 'warn', 'error', 'cmd'
    text: str

class QueryResponse(BaseModel):
    logs: List[LogEntry]
    matched_agents: List[dict] # 에이전트 상세 정보 포함

# ── 키워드 매칭 함수 ──────────────────────────────────────────────────────────
# 한글 키워드 -> 영어 키워드 확장 맵 (모듈 상수)
_KR_MAP = {
    "배터리": ["battery"], "시스템": ["system"], "재무": ["financial", "finance"],
    "계산": ["analysis", "calculate"], "설계": ["engineer", "design"],
    "시뮬": ["simulation", "emtsim"], "비용": ["cost"], "계수": ["parameter"],
    "규격": ["standard"], "표준": ["standard"], "전문가": ["expert"],
    "오케": ["orchestrator"], "ceo": ["ceo"], "cto": ["cto"], "cfo": ["cfo"],
    "coo": ["coo"], "통신": ["network", "communication"], "전기": ["ebop"],
    "토목": ["cbop"], "인허가": ["permit"], "법률": ["legal"], "계약": ["contract"],
    "시운전": ["commissioning"], "공정": ["scheduler"], "안전": ["hse", "security"],
    "사업": ["dev", "business"], "마케팅": ["marketer"], "로지": ["logistics"],
    "품질": ["qaqc"], "검수": ["qaqc"], "환경": ["env", "hse"],
}

def match_agents(query: str, top_n: int = 3) -> list:
    """질의에서 키워드를 추출해 가장 관련성 높은 에이전트 반환"""
    q_clean = query.lower().replace(" ", "")
    q_words = set(re.split(r"[\s,]+", query.lower()))

    expanded = set(q_words)
    # 부분 일치 매칭
    for kr_key, en_vals in _KR_MAP.items():
        if kr_key in q_clean:
            expanded.update(en_vals)

    scored = []
    for key, ag in _agent_index.items():
        # 1. 키워드 집합 교집합 점수
        score = len(ag["keywords"] & expanded) * 2
        
        # 2. 파일명에 질의 단어가 포함된 경우 가산점
        for word in expanded:
            if word in key.lower():
                score += 3
        
        if score > 0:
            scored.append((score, key, ag))
            
    scored.sort(key=lambda x: -x[0])
    return [(key, ag) for _, key, ag in scored[:top_n]]

def extract_relevant_text(agent: dict, query: str, max_chars: int = 600) -> str:
    """에이전트 섹션에서 질의와 관련된 핵심 내용 추출"""
    q_lower = query.lower()
    # 섹션 우선순위: 인풋, 핵심 원칙, 아웃풋, 한 줄 정의
    priority_keys = ["받는 인풋", "핵심 원칙", "인풋", "아웃풋", "한 줄 정의", "주요 업무", "체크리스트"]
    for pk in priority_keys:
        for sec_key, sec_val in agent["sections"].items():
            if pk in sec_key and len(sec_val) > 30:
                # 질의 키워드와 관련 있는 줄 우선
                lines = [l for l in sec_val.split("\n") if l.strip()]
                relevant = [l for l in lines if any(w in l.lower() for w in q_lower.split())]
                snippet = "\n".join((relevant or lines)[:8])
                return snippet[:max_chars]
    # fallback: prompt 앞부분
    return agent["prompt"][:max_chars]

# ── 메인 엔드포인트 ───────────────────────────────────────────────────────────
@app.post("/api/command", response_model=QueryResponse)
async def process_command(req: QueryRequest):
    """명령어 분석 → 관련 에이전트 MD 기반 응답 생성"""
    cmd    = req.command.strip()
    q      = cmd.lower()
    logs: List[LogEntry] = []
    matched_meta: List[dict] = []

    # 도움말
    if any(x in q for x in ["help", "도움", "명령어"]):
        logs = [
            LogEntry(type="success", text="[SYS] 사용 가능한 명령 패턴:"),
            LogEntry(type="", text='  "시스템 설계 시작"    — 시스템 엔지니어 지침 조회'),
            LogEntry(type="", text='  "배터리 전문가 현황"  — 배터리 에이전트 역할 조회'),
            LogEntry(type="", text='  "재무 분석 요청"      — 재무 분석가 지침 조회'),
            LogEntry(type="", text='  "호주 인허가 현황"    — 호주 인허가 에이전트 조회'),
        ]
        return QueryResponse(logs=logs, matched_agents=[])

    # 에이전트 매칭
    matched = match_agents(cmd, top_n=4)

    if not matched:
        return QueryResponse(
            logs=[
                LogEntry(type="warn", text=f'[CEO-001] "{cmd}" — 매칭 에이전트 없음'),
                LogEntry(type="", text="  키워드를 더 구체적으로 입력해 주세요. (예: 배터리, 시운전, 재무, 계통 등)"),
            ],
            matched_agents=[]
        )

    # 매칭된 에이전트들의 MD 기반 응답 및 메타데이터 생성
    logs.append(LogEntry(type="success", text=f'[CEO-001] 명령 분석 완료 → {len(matched)}개 전문가 응집:'))
    
    # 테마 색상 맵 (부서별)
    COLOR_MAP = {
        "CEO": "#3B82F6", "CTO": "#8B5CF6", "CFO": "#F59E0B", "COO": "#10B981", "SYS": "#8B5CF6"
    }

    for i, (_, ag) in enumerate(matched):
        dept_prefix = ag["dept"].split()[0] if ag["dept"] else "CTO"
        color = COLOR_MAP.get(dept_prefix, "#8B5CF6")
        
        matched_meta.append({
            "id": ag["id"],
            "name": ag["name"],
            "dept": ag["dept"],
            "color": color,
            "label": ag["name"].replace(" 전문가", "").replace(" 에이전트", "").replace(" ", "\n")
        })

        prefix = "├" if i < len(matched) - 1 else "└"
        logs.append(LogEntry(type="", text=f''))
        logs.append(LogEntry(type="warn" if i == 0 else "", text=f'  {prefix} [{ag["id"]}] {ag["name"]} ({ag["dept"]})'))
        
        relevant = extract_relevant_text(ag, cmd)
        for line in relevant.split("\n")[:4]:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                logs.append(LogEntry(type="", text=f'    {stripped[:100]}'))

    return QueryResponse(logs=logs, matched_agents=matched_meta)

@app.get("/api/agents")
async def list_agents():
    """전체 에이전트 목록 반환"""
    return [
        {"id": ag["id"], "name": ag["name"], "dept": ag["dept"], "desc": ag["desc"]}
        for ag in _agent_index.values()
    ]

@app.get("/api/agent/{agent_key}")
async def get_agent(agent_key: str):
    """특정 에이전트 상세 정보 반환"""
    ag = _agent_index.get(agent_key)
    if not ag:
        return {"error": "Agent not found"}
    return {
        "id": ag["id"], "name": ag["name"], "dept": ag["dept"],
        "desc": ag["desc"],
        "sections": list(ag["sections"].keys()),
        "prompt_preview": ag["prompt"][:500],
    }

@app.get("/health")
async def health():
    return {"status": "ok", "agents_loaded": len(_agent_index)}

# ── 정적 파일 서빙 (React 빌드 결과물) ──────────────────────────────────────
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

if STATIC_DIR.exists():
    # /assets 등 정적 리소스
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    # favicon, icons 등 루트 파일
    @app.get("/favicon.svg")
    async def favicon():
        return FileResponse(str(STATIC_DIR / "favicon.svg"))

    @app.get("/icons.svg")
    async def icons():
        return FileResponse(str(STATIC_DIR / "icons.svg"))

    # SPA fallback: 모든 비-API 경로를 index.html로
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        return FileResponse(str(STATIC_DIR / "index.html"))
