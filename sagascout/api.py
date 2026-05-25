"""
SagaScout REST API using FastAPI.

Start the server with::

    uvicorn sagascout.api:app --reload

Or install the ``api`` extras and run::

    pip install sagascout[api]
    uvicorn sagascout.api:app --host 0.0.0.0 --port 8000

Endpoints
---------
POST /scout/analyze
POST /archivist/parse
POST /archivist/merge
POST /archivist/infer
POST /archivist/query
POST /oracle/research
POST /oracle/extract
POST /oracle/translate
POST /oracle/search_archives
POST /diplomat/draft
POST /diplomat/send
POST /diplomat/respond
POST /diplomat/analyze_culture
GET  /health
"""

from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from sagascout.agents.scout import Scout
from sagascout.agents.archivist import Archivist
from sagascout.agents.oracle import Oracle
from sagascout.agents.diplomat import Diplomat

app = FastAPI(
    title="SagaScout API",
    description="Autonomous Lineage Intelligence REST API",
    version="0.1.0",
)

# Module-level agent singletons (stateless per request for simplicity;
# swap for dependency-injected instances in production).
_scout = Scout()
_archivist = Archivist()
_oracle = Oracle()
_diplomat = Diplomat()


# ---------------------------------------------------------------------------
# Generic request/response models
# ---------------------------------------------------------------------------

class AgentRequest(BaseModel):
    """Generic wrapper that forwards arbitrary JSON to an agent's process()."""
    payload: Dict[str, Any]


class AgentResponse(BaseModel):
    result: Dict[str, Any]


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health", tags=["system"])
def health() -> Dict[str, str]:
    """Return API liveness status."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Scout endpoints
# ---------------------------------------------------------------------------

@app.post("/scout/analyze", tags=["scout"], response_model=AgentResponse)
def scout_analyze(request: AgentRequest) -> AgentResponse:
    """
    Analyze DNA matches.

    Pass the same payload you would give ``Scout.process()``:

    ```json
    {
      "payload": {
        "matches": [{"id": "m1", "name": "John", "shared_cm": 850, "segments": 15}],
        "threshold_cm": 20
      }
    }
    ```
    """
    try:
        result = _scout.process(request.payload)
        return AgentResponse(result=result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Archivist endpoints
# ---------------------------------------------------------------------------

def _archivist_action(action: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return _archivist.process({"action": action, "data": data})


@app.post("/archivist/parse", tags=["archivist"], response_model=AgentResponse)
def archivist_parse(request: AgentRequest) -> AgentResponse:
    """Parse family tree data (individuals + relationships)."""
    try:
        return AgentResponse(result=_archivist_action("parse", request.payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/archivist/merge", tags=["archivist"], response_model=AgentResponse)
def archivist_merge(request: AgentRequest) -> AgentResponse:
    """Merge another tree into the current tree."""
    try:
        return AgentResponse(result=_archivist_action("merge", request.payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/archivist/infer", tags=["archivist"], response_model=AgentResponse)
def archivist_infer(request: AgentRequest) -> AgentResponse:
    """Infer relationship between two individuals."""
    try:
        return AgentResponse(result=_archivist_action("infer", request.payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/archivist/query", tags=["archivist"], response_model=AgentResponse)
def archivist_query(request: AgentRequest) -> AgentResponse:
    """Query the family tree (ancestors, descendants, siblings, statistics)."""
    try:
        return AgentResponse(result=_archivist_action("query", request.payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Oracle endpoints
# ---------------------------------------------------------------------------

@app.post("/oracle/research", tags=["oracle"], response_model=AgentResponse)
def oracle_research(request: AgentRequest) -> AgentResponse:
    """Conduct multilingual genealogical research."""
    try:
        payload = {"action": "research", **request.payload}
        return AgentResponse(result=_oracle.process(payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/oracle/extract", tags=["oracle"], response_model=AgentResponse)
def oracle_extract(request: AgentRequest) -> AgentResponse:
    """Extract data from a genealogical document."""
    try:
        payload = {"action": "extract", **request.payload}
        return AgentResponse(result=_oracle.process(payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/oracle/translate", tags=["oracle"], response_model=AgentResponse)
def oracle_translate(request: AgentRequest) -> AgentResponse:
    """Translate a query into multiple languages."""
    try:
        payload = {"action": "translate", **request.payload}
        return AgentResponse(result=_oracle.process(payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/oracle/search_archives", tags=["oracle"], response_model=AgentResponse)
def oracle_search_archives(request: AgentRequest) -> AgentResponse:
    """Search genealogical archives across countries."""
    try:
        payload = {"action": "search_archives", **request.payload}
        return AgentResponse(result=_oracle.process(payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Diplomat endpoints
# ---------------------------------------------------------------------------

@app.post("/diplomat/draft", tags=["diplomat"], response_model=AgentResponse)
def diplomat_draft(request: AgentRequest) -> AgentResponse:
    """Draft a culturally-appropriate outreach message."""
    try:
        payload = {"action": "draft", **request.payload}
        return AgentResponse(result=_diplomat.process(payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/diplomat/send", tags=["diplomat"], response_model=AgentResponse)
def diplomat_send(request: AgentRequest) -> AgentResponse:
    """Send a message and record it in communication history."""
    try:
        payload = {"action": "send", **request.payload}
        return AgentResponse(result=_diplomat.process(payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/diplomat/respond", tags=["diplomat"], response_model=AgentResponse)
def diplomat_respond(request: AgentRequest) -> AgentResponse:
    """Generate a response to a received message."""
    try:
        payload = {"action": "respond", **request.payload}
        return AgentResponse(result=_diplomat.process(payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/diplomat/analyze_culture", tags=["diplomat"], response_model=AgentResponse)
def diplomat_analyze_culture(request: AgentRequest) -> AgentResponse:
    """Analyze cultural communication context for a country."""
    try:
        payload = {"action": "analyze_culture", **request.payload}
        return AgentResponse(result=_diplomat.process(payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
