"""
Action & Drafting Agent for Prometheus.
Adheres strictly to the 'Propose, Don't Impose' principle.
Prepares scheduled alignment digests and action cards with require_confirmation=True.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.memory.state_store import state_store, ActionDraftRecord, BlockerRecord, DraftStatus
from app.tools.slack_tools import SlackTools


class ActionAgent:
    """
    Sub-agent 6: Action & Drafting Agent
    Drafts contextual remediation actions and scheduled leadership briefings for human sign-off.
    """

    name: str = "ActionAndDraftingAgent"
    role: str = "Human-in-the-Loop Action Drafting"

    @classmethod
    async def create_action_drafts_for_blockers(
        cls,
        blockers: List[BlockerRecord],
    ) -> List[ActionDraftRecord]:
        """
        Translates root-cause blockers into concrete human-reviewable action proposals.
        """
        drafts: List[ActionDraftRecord] = []

        for blocker in blockers:
            # 1. Stale PR / reviewer ping proposal
            if "PR-402" in blocker.source_artifacts:
                ping_content = (
                    "Hi @alex-lead, PR #402 (OAuth 2.1) has been awaiting review for over 48 hours "
                    "and is currently blocking Epic PROJ-108 (v2.1 Gateway). Could you complete the review "
                    "or delegate to @sarah-reviewer today?"
                )
                draft = await SlackTools.draft_action_card(
                    target="@alex-lead",
                    action_type="slack_dm",
                    content=ping_content,
                    context_blocker_id=blocker.blocker_id,
                    require_confirmation=True,
                )
                drafts.append(draft)

            # 2. Squad-wide delivery alert proposal
            if blocker.severity in ("CRITICAL", "HIGH"):
                channel_alert = (
                    f"⚠️ *Prometheus Blocker Alert [{blocker.blocker_id}]*:\n"
                    f"{blocker.title}\n"
                    f"Impact: Squads {', '.join(blocker.impacted_squads)}\n"
                    f"Summary: {blocker.description}"
                )
                channel_draft = await SlackTools.draft_action_card(
                    target="#platform-engineering",
                    action_type="slack_channel_alert",
                    content=channel_alert,
                    context_blocker_id=blocker.blocker_id,
                    require_confirmation=True,
                )
                drafts.append(channel_draft)

        return drafts

    @classmethod
    async def generate_alignment_digest(
        cls,
        blockers: List[BlockerRecord],
        drafts: List[ActionDraftRecord],
    ) -> Dict[str, Any]:
        """
        Generates the formatted 08:00 AM Daily Alignment Briefing.
        """
        return {
            "digest_title": "Daily Executive Workstream Alignment Digest",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "critical_blockers_count": len([b for b in blockers if b.severity == "CRITICAL"]),
            "total_active_blockers": len(blockers),
            "pending_action_proposals": len([d for d in drafts if d.status == DraftStatus.PENDING]),
            "blockers": [b.model_dump() for b in blockers],
            "action_drafts": [d.model_dump() for d in drafts],
            "summary_statement": (
                f"Prometheus identified {len(blockers)} high-priority delivery bottleneck(s). "
                f"{len(drafts)} contextual action draft(s) are ready for human approval."
            ),
        }
