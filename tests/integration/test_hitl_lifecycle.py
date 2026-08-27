"""
Tier 3 Integration Tests: Human-In-The-Loop (HITL) Lifecycle, Idempotency & State Store
Validates draft creation, approval/rejection state machines, concurrent idempotency, and session checkpoints.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from prometheus.memory.state_store import (
    state_store,
    DraftStatus,
    BlockerRecord,
    ActionDraftRecord,
)
from prometheus.agents.action_agent import ActionAgent
from prometheus.tools.slack_tools import SlackTools
from prometheus.engine_app import PrometheusAgentEngineApp


@pytest.mark.integration
class TestHITLLifecycle:
    @pytest.mark.asyncio
    async def test_draft_creation_from_blockers(self):
        """Validates that ActionAgent creates PENDING action drafts with Slack Block Kit UI metadata."""
        await state_store.init_db()

        blocker = BlockerRecord(
            blocker_id="BLK-AUTH-001",
            title="OAuth 2.1 Stale Review",
            description="PR-402 is pending review for >48h, blocking PROJ-108",
            severity="CRITICAL",
            source_artifacts=["PR-402", "PROJ-108"],
            impacted_squads=["engineering", "platform"],
        )

        drafts = await ActionAgent.create_action_drafts_for_blockers([blocker])
        assert len(drafts) >= 1

        draft = drafts[0]
        assert draft.status == DraftStatus.PENDING
        assert draft.context_blocker_id == "BLK-AUTH-001"
        assert "slack_blocks" in draft.metadata
        assert draft.metadata.get("require_confirmation") is True

    @pytest.mark.asyncio
    async def test_approval_state_transition_and_audit_fields(self):
        """Validates transition from PENDING to EXECUTED with audit logs."""
        await state_store.init_db()

        draft = await SlackTools.draft_action_card(
            target="#platform-engineering",
            action_type="slack_channel_alert",
            content="Alert squad of critical build failure.",
        )
        assert draft.status == DraftStatus.PENDING

        app_res = await SlackTools.dispatch_approved_action(
            draft_id=draft.draft_id,
            approver_username="lead-sarah",
        )
        assert app_res["status"] == "success"

        updated = await state_store.get_draft(draft.draft_id)
        assert updated.status == DraftStatus.EXECUTED
        assert updated.approved_by == "lead-sarah"
        assert updated.approved_at is not None
        assert updated.execution_result is not None

    @pytest.mark.asyncio
    async def test_rejection_state_transition(self):
        """Validates transition from PENDING to REJECTED via Reasoning Engine app."""
        await state_store.init_db()

        draft = await SlackTools.draft_action_card(
            target="#billing-squad",
            action_type="slack_channel_alert",
            content="Spam alert to be discarded",
        )
        assert draft.status == DraftStatus.PENDING

        app = PrometheusAgentEngineApp()
        rej_res = app.reject_action(draft_id=draft.draft_id, approver_username="alex-lead")
        assert rej_res["status"] == "rejected"
        assert rej_res["draft_id"] == draft.draft_id

        updated = await state_store.get_draft(draft.draft_id)
        assert updated.status == DraftStatus.REJECTED

    @pytest.mark.asyncio
    async def test_sequential_approval_idempotency(self):
        """Validates that re-approving an already executed action returns already_executed idempotently."""
        await state_store.init_db()

        draft = await SlackTools.draft_action_card(
            target="#platform-engineering",
            action_type="slack_channel_alert",
            content="Idempotency test card",
        )

        res1 = await SlackTools.dispatch_approved_action(draft.draft_id, "alex-lead")
        assert res1["status"] == "success"

        res2 = await SlackTools.dispatch_approved_action(draft.draft_id, "alex-lead")
        assert res2["status"] == "already_executed"
        assert res2["draft_id"] == draft.draft_id

    @pytest.mark.asyncio
    async def test_concurrent_approval_race_condition(self):
        """Fires 10 concurrent approval coroutines for the same draft; exactly 1 succeeds, 9 return already_executed."""
        await state_store.init_db()

        draft = await SlackTools.draft_action_card(
            target="#platform-engineering",
            action_type="slack_channel_alert",
            content="High concurrency race condition draft",
        )

        async def _approve():
            return await SlackTools.dispatch_approved_action(draft.draft_id, "concurrent-lead")

        # Execute 10 concurrent approvals
        results = await asyncio.gather(*[_approve() for _ in range(10)])

        success_count = sum(1 for r in results if r["status"] == "success")
        already_count = sum(1 for r in results if r["status"] == "already_executed")

        assert success_count == 1
        assert already_count == 9

    @pytest.mark.asyncio
    async def test_reject_already_executed_action(self):
        """Validates that attempting to reject an already executed draft returns already_executed."""
        await state_store.init_db()

        draft = await SlackTools.draft_action_card(
            target="#platform-engineering",
            action_type="slack_channel_alert",
            content="Already executed draft rejection test",
        )

        await SlackTools.dispatch_approved_action(draft.draft_id, "alex-lead")

        app = PrometheusAgentEngineApp()
        res = app.reject_action(draft.draft_id, "alex-lead")
        assert res["status"] == "already_executed"

    @pytest.mark.asyncio
    async def test_session_state_persistence_across_turns(self):
        """Validates SQLite session checkpoint storage and multi-turn state preservation."""
        await state_store.init_db()

        session_id = "sess_multi_turn_test_123"
        session_data = {
            "turn": 1,
            "query": "Review blocked PRs",
            "blockers_found": ["BLK-101", "BLK-102"],
            "pending_drafts": ["DRAFT-001"],
        }

        await state_store.save_checkpoint(session_id, session_data)

        # Retrieve checkpoint in subsequent turn
        saved_checkpoint = await state_store.get_checkpoint(session_id)
        assert saved_checkpoint is not None
        assert saved_checkpoint["session_id"] == session_id
        assert saved_checkpoint["data"]["turn"] == 1
        assert "BLK-101" in saved_checkpoint["data"]["blockers_found"]
