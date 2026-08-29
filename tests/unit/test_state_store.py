"""
Tier 1 Unit Tests: SQLite StateStore Persistence & Session Checkpointing
Validates CRUD operations, status queries, draft transitions, and checkpointing.
"""

import pytest
import uuid
from datetime import datetime, timezone
from prometheus.memory.state_store import (
    StateStore,
    BlockerRecord,
    ActionDraftRecord,
    DraftStatus,
)


@pytest.fixture
async def local_store(tmp_path):
    """Provides an isolated SQLite StateStore instance using a temporary file."""
    db_file = str(tmp_path / f"test_state_{uuid.uuid4().hex[:8]}.db")
    store = StateStore()
    store._db_path = db_file
    await store.init_db()
    return store


@pytest.mark.unit
class TestStateStore:
    @pytest.mark.asyncio
    async def test_init_db_idempotency(self, local_store):
        """init_db can be safely called multiple times without error."""
        await local_store.init_db()
        await local_store.init_db()
        assert local_store._initialized is True

    @pytest.mark.asyncio
    async def test_save_and_get_blocker(self, local_store):
        """Saves a BlockerRecord to SQLite and retrieves all attributes accurately."""
        blocker = BlockerRecord(
            blocker_id="BLK-TEST-001",
            title="Database Connection Pool Exhaustion",
            description="High latency on auth service causing connection pool saturation",
            severity="CRITICAL",
            source_artifacts=["PR-402", "CI-8902"],
            impacted_squads=["auth", "gateway"],
            is_active=True,
            metadata={"priority_score": 9.5},
        )
        saved = await local_store.save_blocker(blocker)
        assert saved.blocker_id == "BLK-TEST-001"

        active_blockers = await local_store.get_active_blockers()
        matched = next((b for b in active_blockers if b.blocker_id == "BLK-TEST-001"), None)
        assert matched is not None
        assert matched.title == "Database Connection Pool Exhaustion"
        assert matched.severity == "CRITICAL"
        assert matched.source_artifacts == ["PR-402", "CI-8902"]
        assert matched.impacted_squads == ["auth", "gateway"]
        assert matched.is_active is True
        assert matched.metadata.get("priority_score") == 9.5

    @pytest.mark.asyncio
    async def test_active_blockers_filtering(self, local_store):
        """get_active_blockers only returns blockers where is_active is True."""
        active = BlockerRecord(
            blocker_id="BLK-ACTIVE",
            title="Active Blocker",
            description="Currently blocking",
            severity="HIGH",
            is_active=True,
        )
        resolved = BlockerRecord(
            blocker_id="BLK-RESOLVED",
            title="Resolved Blocker",
            description="Was resolved",
            severity="LOW",
            is_active=False,
            resolved_at=datetime.now(timezone.utc),
        )
        await local_store.save_blocker(active)
        await local_store.save_blocker(resolved)

        active_list = await local_store.get_active_blockers()
        active_ids = [b.blocker_id for b in active_list]
        assert "BLK-ACTIVE" in active_ids
        assert "BLK-RESOLVED" not in active_ids

    @pytest.mark.asyncio
    async def test_save_and_get_draft(self, local_store):
        """Saves an ActionDraftRecord and retrieves it by draft_id."""
        draft = ActionDraftRecord(
            draft_id="DRAFT-001",
            target_channel_or_user="#platform-engineering",
            action_type="slack_channel_alert",
            content="Notify squad of stale PR review",
            context_blocker_id="BLK-TEST-001",
            status=DraftStatus.PENDING,
            metadata={"created_by": "ActionAgent"},
        )
        await local_store.save_draft(draft)

        fetched = await local_store.get_draft("DRAFT-001")
        assert fetched is not None
        assert fetched.draft_id == "DRAFT-001"
        assert fetched.target_channel_or_user == "#platform-engineering"
        assert fetched.action_type == "slack_channel_alert"
        assert fetched.status == DraftStatus.PENDING
        assert fetched.metadata.get("created_by") == "ActionAgent"

    @pytest.mark.asyncio
    async def test_list_drafts_by_status(self, local_store):
        """list_drafts correctly filters by DraftStatus."""
        d1 = ActionDraftRecord(draft_id="D-PENDING", target_channel_or_user="@lead", action_type="slack_dm", content="c1", status=DraftStatus.PENDING)
        d2 = ActionDraftRecord(draft_id="D-APPROVED", target_channel_or_user="@lead", action_type="slack_dm", content="c2", status=DraftStatus.APPROVED)
        d3 = ActionDraftRecord(draft_id="D-EXECUTED", target_channel_or_user="@lead", action_type="slack_dm", content="c3", status=DraftStatus.EXECUTED)
        
        await local_store.save_draft(d1)
        await local_store.save_draft(d2)
        await local_store.save_draft(d3)

        pending_list = await local_store.list_drafts(status=DraftStatus.PENDING)
        assert any(d.draft_id == "D-PENDING" for d in pending_list)
        assert not any(d.draft_id == "D-APPROVED" for d in pending_list)

        all_list = await local_store.list_drafts()
        assert len(all_list) >= 3

    @pytest.mark.asyncio
    async def test_update_draft_status_lifecycle(self, local_store):
        """update_draft_status updates state, approver, and result fields."""
        draft = ActionDraftRecord(
            draft_id="DRAFT-LIFECYCLE",
            target_channel_or_user="#alerts",
            action_type="slack_channel_alert",
            content="Lifecycle content",
            status=DraftStatus.PENDING,
        )
        await local_store.save_draft(draft)

        # Transition: PENDING -> APPROVED
        updated = await local_store.update_draft_status(
            draft_id="DRAFT-LIFECYCLE",
            status=DraftStatus.APPROVED,
            approver="alex-lead",
            result="Approved by lead",
        )
        assert updated is not None
        assert updated.status == DraftStatus.APPROVED
        assert updated.approved_by == "alex-lead"
        assert updated.approved_at is not None
        assert updated.execution_result == "Approved by lead"

        # Verify DB persistence of update
        reloaded = await local_store.get_draft("DRAFT-LIFECYCLE")
        assert reloaded.status == DraftStatus.APPROVED
        assert reloaded.approved_by == "alex-lead"

    @pytest.mark.asyncio
    async def test_update_nonexistent_draft_returns_none(self, local_store):
        """Updating status of a nonexistent draft safely returns None."""
        res = await local_store.update_draft_status(
            draft_id="NONEXISTENT-DRAFT-XYZ",
            status=DraftStatus.APPROVED,
        )
        assert res is None

    @pytest.mark.asyncio
    async def test_session_checkpoints(self, local_store):
        """save_checkpoint and get_checkpoint preserve session state dictionaries."""
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        state_data = {
            "query": "Review platform blockers",
            "blocker_count": 3,
            "sub_agents": ["router", "git", "jira", "workstream", "synthesis", "action"],
        }
        await local_store.save_checkpoint(session_id, state_data)

        checkpoint = await local_store.get_checkpoint(session_id)
        assert checkpoint is not None
        assert checkpoint["session_id"] == session_id
        assert checkpoint["data"]["query"] == "Review platform blockers"
        assert checkpoint["data"]["blocker_count"] == 3
        assert len(checkpoint["data"]["sub_agents"]) == 6

    @pytest.mark.asyncio
    async def test_update_draft_content(self, local_store):
        """update_draft_content updates text content and target."""
        draft = ActionDraftRecord(
            draft_id="DRAFT-EDIT-001",
            target_channel_or_user="@alex",
            action_type="slack_dm",
            content="Original content",
            status=DraftStatus.PENDING,
            metadata={"slack_blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": "Original content"}}]}
        )
        await local_store.save_draft(draft)

        updated = await local_store.update_draft_content(
            draft_id="DRAFT-EDIT-001",
            content="Updated edited content",
            target="@sarah",
        )
        assert updated is not None
        assert updated.content == "Updated edited content"
        assert updated.target_channel_or_user == "@sarah"
        assert updated.metadata["slack_blocks"][0]["text"]["text"] == "Updated edited content"

        reloaded = await local_store.get_draft("DRAFT-EDIT-001")
        assert reloaded.content == "Updated edited content"
        assert reloaded.target_channel_or_user == "@sarah"

    @pytest.mark.asyncio
    async def test_get_nonexistent_checkpoint_returns_none(self, local_store):
        """Querying nonexistent session checkpoint returns None."""
        res = await local_store.get_checkpoint("sess_nonexistent_123")
        assert res is None
