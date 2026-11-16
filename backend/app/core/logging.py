from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field

logger = logging.getLogger("agent_audit")


class AgentAuditLog(BaseModel):
    model_config = {"protected_namespaces": ()}
    request_id: str
    session_id: str
    user_id: str
    tenant_id: str
    role: str
    intent: str
    selected_agents: list[str] = Field(default_factory=list)
    selected_tools: list[str] = Field(default_factory=list)
    api_calls: list[str] = Field(default_factory=list)
    model_provider: str
    latency_ms: float
    token_usage: dict[str, int] = Field(default_factory=dict)
    success: bool
    error: str | None = None
    final_response_status: str = "completed"
    requires_confirmation: bool = False
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class StructuredAuditLogger:
    def __init__(self, log_dir: Path | None = None) -> None:
        if log_dir is None:
            log_dir = Path(__file__).resolve().parents[2] / "logs"
        self.log_dir = log_dir
        self.log_file = self.log_dir / "agent_audit.jsonl"
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create log directory {self.log_dir}: {e}")

    def log(self, entry: AgentAuditLog) -> None:
        # 1. Console structured summary
        logger.info(
            f"[AUDIT] req={entry.request_id} role={entry.role} intent={entry.intent} "
            f"agents={entry.selected_agents} tools={entry.selected_tools} "
            f"provider={entry.model_provider} latency={entry.latency_ms:.1f}ms success={entry.success}"
        )
        # 2. Append to JSONL file asynchronously / safely
        try:
            line = entry.model_dump_json()
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as exc:
            logger.error(f"Failed to write audit log to {self.log_file}: {exc}")


_AUDIT_LOGGER = StructuredAuditLogger()


def get_audit_logger() -> StructuredAuditLogger:
    return _AUDIT_LOGGER
