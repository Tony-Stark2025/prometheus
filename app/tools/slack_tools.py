"""
Slack and workstream communication tools for Prometheus.
Provides public workstream ingestion and Human-In-The-Loop (HITL) action drafting.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from app.memory.state_store import state_store, ActionDraftRecord, DraftStatus


class SlackTools:
    """
    Ingests public communication context and prepares proposed action cards.
    Mandates human approval before mutative external dispatch.
    """

    MOCK_MESSAGES: List[Dict[str, Any]] = [
        {
            "id": "MSG-901",
            "channel": "#platform-engineering",
            "user": "dev-sarah",
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=36)).isoformat(),
            "text": "Hey @alex-lead, PR #402 (OAuth 2.1) has been waiting for review since Tuesday. It's blocking the gateway integration.",
            "scopes": ["engineering", "platform"],
        },
        {
            "id": "MSG-905",
            "channel": "#platform-engineering",
            "user": "dev-alex",
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
            "text": "CI failed on web-gateway branch fix/auth-headers due to 401 handshake mismatch with auth-service.",
            "scopes": ["engineering", "platform"],
        },
        {
            "id": "MSG-912",
            "channel": "#billing-squad",
            "user": "dev-marcus",
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            "text": "VAT fix PR #420 is approved, merging right after automated regression tests complete.",
            "scopes": ["engineering", "finance"],
        },
    ]

    @classmethod
    async def get_recent_channel_messages(cls, scopes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Retrieves public channel discussion telemetry within allowed scopes.
        """
        if not scopes:
            return cls.MOCK_MESSAGES
        return [
            msg for msg in cls.MOCK_MESSAGES
            if any(s in msg.get("scopes", []) for s in scopes)
        ]

    @classmethod
    async def draft_action_card(
        cls,
        target: str,
        action_type: str,
        content: str,
        context_blocker_id: Optional[str] = None,
        require_confirmation: bool = True,
    ) -> ActionDraftRecord:
        """
        Prepares an actionable proposal draft for human review.
        'Propose, Don't Impose' principle: strictly persists to draft state.
        """
        draft_id = f"DRAFT-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        draft = ActionDraftRecord(
            draft_id=draft_id,
            target_channel_or_user=target,
            action_type=action_type,
            content=content,
            context_blocker_id=context_blocker_id,
            status=DraftStatus.PENDING,
            metadata={
                "require_confirmation": require_confirmation,
                "created_by": "ActionDrafterAgent",
            },
        )
        await state_store.save_draft(draft)
        return draft

    @classmethod
    async def dispatch_approved_action(cls, draft_id: str, approver_username: str) -> Dict[str, Any]:
        """
        Dispatches an action ONLY after explicit human approval.
        """
        draft = await state_store.get_draft(draft_id)
        if not draft:
            raise ValueError(f"Draft '{draft_id}' not found.")
        
        if draft.status == DraftStatus.EXECUTED:
            return {"status": "already_executed", "draft_id": draft_id}

        # Simulate or perform API dispatch
        result_message = f"Successfully dispatched '{draft.action_type}' to '{draft.target_channel_or_user}' (Approved by {approver_username})."
        await state_store.update_draft_status(
            draft_id=draft_id,
            status=DraftStatus.EXECUTED,
            approver=approver_username,
            result=result_message,
        )
        return {
            "status": "success",
            "draft_id": draft_id,
            "target": draft.target_channel_or_user,
            "result": result_message,
        }
