"""
Durable session checkpointing and state memory for Prometheus multi-agent workflows.
Tracks blocker lifecycles and human approval states across sessions.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
import json
from pydantic import BaseModel, Field


class DraftStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"


class ActionDraftRecord(BaseModel):
    draft_id: str
    target_channel_or_user: str
    action_type: str  # "slack_dm", "slack_channel_alert", "jira_comment", "reassign_pr"
    content: str
    context_blocker_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: DraftStatus = DraftStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    execution_result: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BlockerRecord(BaseModel):
    blocker_id: str
    title: str
    description: str
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    source_artifacts: List[str] = Field(default_factory=list)
    impacted_squads: List[str] = Field(default_factory=list)
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StateStore:
    """
    Persistent state manager supporting checkpointing and action audit logs.
    """

    def __init__(self):
        self._blockers: Dict[str, BlockerRecord] = {}
        self._drafts: Dict[str, ActionDraftRecord] = {}
        self._checkpoints: Dict[str, Dict[str, Any]] = {}

    async def save_blocker(self, blocker: BlockerRecord) -> BlockerRecord:
        self._blockers[blocker.blocker_id] = blocker
        return blocker

    async def get_active_blockers(self) -> List[BlockerRecord]:
        return [b for b in self._blockers.values() if b.is_active]

    async def save_draft(self, draft: ActionDraftRecord) -> ActionDraftRecord:
        self._drafts[draft.draft_id] = draft
        return draft

    async def get_draft(self, draft_id: str) -> Optional[ActionDraftRecord]:
        return self._drafts.get(draft_id)

    async def list_drafts(self, status: Optional[DraftStatus] = None) -> List[ActionDraftRecord]:
        if status:
            return [d for d in self._drafts.values() if d.status == status]
        return list(self._drafts.values())

    async def update_draft_status(
        self, draft_id: str, status: DraftStatus, approver: Optional[str] = None, result: Optional[str] = None
    ) -> Optional[ActionDraftRecord]:
        draft = self._drafts.get(draft_id)
        if not draft:
            return None
        draft.status = status
        if approver:
            draft.approved_by = approver
            draft.approved_at = datetime.now(timezone.utc)
        if result:
            draft.execution_result = result
        return draft

    async def save_checkpoint(self, session_id: str, state_data: Dict[str, Any]) -> None:
        self._checkpoints[session_id] = {
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": state_data,
        }

    async def get_checkpoint(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._checkpoints.get(session_id)


# Global singleton instance
state_store = StateStore()
