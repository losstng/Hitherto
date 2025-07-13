from __future__ import annotations
import uuid
import json
import logging
from pathlib import Path
import os

from fastapi import APIRouter
from pydantic import BaseModel

from ..schemas import ApiResponse

try:
    from jupyter_client import KernelManager
except Exception:  # pragma: no cover - optional dependency may be missing
    KernelManager = None  # type: ignore

router = APIRouter(tags=["Notebook"])
logger = logging.getLogger(__name__)


class ExecutePayload(BaseModel):
    cellId: str
    code: str


class NotebookPayload(BaseModel):
    notebook: dict


class Session:
    def __init__(self) -> None:
        if KernelManager is None:
            raise RuntimeError("jupyter_client not available")
        self.km = KernelManager()
        env = os.environ.copy()
        # Disable parent polling so kernels persist if the web server reloads
        env.setdefault("JPY_PARENT_PID", "1")
        self.km.start_kernel(env=env)
        self.kc = self.km.client()
        self.kc.start_channels()

    def shutdown(self) -> None:
        self.kc.stop_channels()
        self.km.shutdown_kernel(now=True)
        try:
            self.km.cleanup_resources()
        except Exception:
            pass


SESSIONS: dict[str, Session] = {}
NOTEBOOK_DIR = Path("notebooks")
NOTEBOOK_DIR.mkdir(exist_ok=True)


@router.post("/new", response_model=ApiResponse)
def new_session() -> ApiResponse:
    """Create a new Jupyter kernel session."""
    try:
        sess = Session()
    except Exception as exc:  # pragma: no cover - runtime failure
        logger.exception("Failed to start kernel")
        return ApiResponse(success=False, error=str(exc))
    sid = str(uuid.uuid4())
    SESSIONS[sid] = sess
    logger.debug("Started notebook session %s", sid)
    return ApiResponse(success=True, data={"session_id": sid})


@router.post("/{session}/execute", response_model=ApiResponse)
def execute_cell(session: str, payload: ExecutePayload) -> ApiResponse:
    """Execute one cell of code and return captured output."""
    sess = SESSIONS.get(session)
    if not sess:
        return ApiResponse(success=False, error="Invalid session")

    kc = sess.kc
    msg_id = kc.execute(payload.code)
    stdout = ""
    stderr = ""
    html = ""
    images: list[str] = []

    while True:
        msg = kc.get_iopub_msg(timeout=10)
        mtype = msg["header"]["msg_type"]
        content = msg["content"]
        if mtype == "stream":
            if content.get("name") == "stdout":
                stdout += content.get("text", "")
            else:
                stderr += content.get("text", "")
        elif mtype == "error":
            stderr += "\n".join(content.get("traceback", []))
        elif mtype == "display_data":
            data = content.get("data", {})
            if "text/html" in data:
                html += data["text/html"]
            if "image/png" in data:
                images.append(f"data:image/png;base64,{data['image/png']}")
        elif mtype == "status" and content.get("execution_state") == "idle":
            break
    return ApiResponse(
        success=True,
        data={
            "cellId": payload.cellId,
            "stdout": stdout,
            "stderr": stderr,
            "html": html,
            "images": images,
        },
    )


@router.post("/{session}/save", response_model=ApiResponse)
def save_notebook(session: str, payload: NotebookPayload) -> ApiResponse:
    """Persist notebook JSON to disk."""
    path = NOTEBOOK_DIR / f"{session}.ipynb"
    try:
        path.write_text(json.dumps(payload.notebook))
        logger.debug("Saved notebook %s", path)
        return ApiResponse(success=True, data={"path": str(path)})
    except Exception as exc:  # pragma: no cover - file write error
        logger.exception("Failed saving notebook")
        return ApiResponse(success=False, error=str(exc))


@router.get("/{session}/load", response_model=ApiResponse)
def load_notebook(session: str) -> ApiResponse:
    """Load notebook JSON from disk, if present."""
    path = NOTEBOOK_DIR / f"{session}.ipynb"
    if not path.exists():
        return ApiResponse(success=True, data=None)
    try:
        data = json.loads(path.read_text())
        return ApiResponse(success=True, data=data)
    except Exception as exc:  # pragma: no cover - file read error
        logger.exception("Failed loading notebook")
        return ApiResponse(success=False, error=str(exc))


@router.post("/{session}/shutdown", response_model=ApiResponse)
def shutdown_session(session: str) -> ApiResponse:
    """Terminate a kernel session."""
    sess = SESSIONS.pop(session, None)
    if not sess:
        return ApiResponse(success=False, error="Invalid session")
    try:
        sess.shutdown()
        logger.debug("Shutdown session %s", session)
        return ApiResponse(success=True, data=True)
    except Exception as exc:  # pragma: no cover - kernel shutdown error
        logger.exception("Failed to shutdown kernel")
        return ApiResponse(success=False, error=str(exc))
