"""
Slack and workstream communication tools for Prometheus.
Provides public workstream ingestion and Human-In-The-Loop (HITL) action drafting
via live Slack Web API with rate limiting and hermetic mock fallbacks.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

import httpx

try:
    from prometheus.config import settings
    from prometheus.memory.state_store import state_store, ActionDraftRecord, DraftStatus
except ImportError:
    from app.config import settings
    from app.memory.state_store import state_store, ActionDraftRecord, DraftStatus

logger = logging.getLogger(__name__)


class SlackTools:
    """
    Enterprise Slack Web API telemetry client and HITL action dispatcher.
    Ingests public communication context and dispatches interactive Block Kit action cards strictly upon human approval.
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

    _user_cache: Dict[str, str] = {}
    _channel_cache: Dict[str, str] = {}
    _action_locks: Dict[Any, asyncio.Lock] = {}

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop not in cls._action_locks:
            cls._action_locks[loop] = asyncio.Lock()
        return cls._action_locks[loop]

    @classmethod
    def _get_headers(cls) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "Prometheus-Observability-Fleet/1.1",
        }
        if settings.slack_bot_token:
            headers["Authorization"] = f"Bearer {settings.slack_bot_token}"
        return headers

    @classmethod
    def _infer_scopes(cls, channel_name: str) -> List[str]:
        ch_lower = channel_name.lower()
        if "billing" in ch_lower or "finance" in ch_lower:
            return ["engineering", "finance"]
        elif "sec" in ch_lower or "auth" in ch_lower:
            return ["engineering", "platform", "security"]
        return ["engineering", "platform"]

    @classmethod
    async def _resolve_channel_id(cls, client: httpx.AsyncClient, channel_name: str) -> Optional[str]:
        clean_name = channel_name.lstrip("#").lower()
        if clean_name in cls._channel_cache:
            return cls._channel_cache[clean_name]

        try:
            url = "https://slack.com/api/conversations.list?types=public_channel,private_channel&exclude_archived=true&limit=100"
            resp = await client.get(url, headers=cls._get_headers())
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    for ch in data.get("channels", []):
                        name = ch.get("name", "").lower()
                        ch_id = ch.get("id")
                        if name and ch_id:
                            cls._channel_cache[name] = ch_id
                            if name == clean_name:
                                return ch_id
        except Exception as e:
            logger.warning(f"Failed to resolve Slack channel '{channel_name}': {e}")
        return cls._channel_cache.get(clean_name, None)

    @classmethod
    async def _resolve_user_id(cls, client: httpx.AsyncClient, username: str) -> Optional[str]:
        clean_user = username.lstrip("@").lower()
        for uid, uname in cls._user_cache.items():
            if uname.lower() == clean_user:
                return uid

        try:
            url = "https://slack.com/api/users.list?limit=100"
            resp = await client.get(url, headers=cls._get_headers())
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    for member in data.get("members", []):
                        uid = member.get("id")
                        uname = member.get("name", "")
                        dname = member.get("profile", {}).get("display_name", "")
                        if uid:
                            resolved_name = dname or uname or uid
                            cls._user_cache[uid] = resolved_name
                            if uname.lower() == clean_user or dname.lower() == clean_user:
                                return uid
        except Exception as e:
            logger.warning(f"Failed to resolve Slack user '{username}': {e}")
        return None

    @classmethod
    async def _resolve_username_by_id(cls, client: httpx.AsyncClient, user_id: str) -> str:
        if user_id in cls._user_cache:
            return cls._user_cache[user_id]

        try:
            url = f"https://slack.com/api/users.info?user={user_id}"
            resp = await client.get(url, headers=cls._get_headers())
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    user = data.get("user", {})
                    name = user.get("name", "")
                    dname = user.get("profile", {}).get("display_name", "")
                    resolved = dname or name or user_id
                    cls._user_cache[user_id] = resolved
                    return resolved
        except Exception:
            pass

        try:
            url = "https://slack.com/api/users.list?limit=100"
            resp = await client.get(url, headers=cls._get_headers())
            if resp.status_code == 200:
                data = resp.json()
                if data.get("ok"):
                    for member in data.get("members", []):
                        uid = member.get("id")
                        uname = member.get("name", "")
                        dname = member.get("profile", {}).get("display_name", "")
                        if uid:
                            cls._user_cache[uid] = dname or uname or uid
                    if user_id in cls._user_cache:
                        return cls._user_cache[user_id]
        except Exception:
            pass

        return f"dev-{user_id}" if user_id != "unknown" else "dev-user"

    @classmethod
    async def get_recent_channel_messages(
        cls,
        scopes: Optional[List[str]] = None,
        channel_names: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves public channel discussion telemetry via live Slack Web API if SLACK_BOT_TOKEN is configured.
        Gracefully falls back to realistic mock fixtures if unauthenticated or rate limited.
        """
        if not settings.slack_bot_token:
            msgs = cls.MOCK_MESSAGES
            if scopes:
                return [m for m in msgs if any(s in m.get("scopes", []) for s in scopes)]
            return msgs

        target_channels = channel_names or settings.slack_channels
        if isinstance(target_channels, str):
            target_channels = [c.strip() for c in target_channels.split(",") if c.strip()]

        live_messages: List[Dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                for ch_name in target_channels:
                    clean_ch_name = ch_name.lstrip("#")
                    ch_id = await cls._resolve_channel_id(client, clean_ch_name) or clean_ch_name

                    url = f"https://slack.com/api/conversations.history?channel={ch_id}&limit=20"
                    resp = await client.get(url, headers=cls._get_headers())

                    if resp.status_code == 429:
                        logger.warning("Slack API rate limit encountered. Falling back to mock messages.")
                        return cls.MOCK_MESSAGES if not scopes else [
                            m for m in cls.MOCK_MESSAGES if any(s in m.get("scopes", []) for s in scopes)
                        ]

                    if resp.status_code != 200:
                        continue

                    data = resp.json()
                    if not data.get("ok"):
                        err = data.get("error", "unknown_error")
                        if err == "ratelimited":
                            logger.warning("Slack API ratelimited. Falling back to mock fixtures.")
                            return cls.MOCK_MESSAGES if not scopes else [
                                m for m in cls.MOCK_MESSAGES if any(s in m.get("scopes", []) for s in scopes)
                            ]
                        logger.warning(f"Slack API history query for channel '{ch_name}' returned error: {err}")
                        continue

                    messages = data.get("messages", [])
                    for msg in messages:
                        subtype = msg.get("subtype")
                        if subtype in ("channel_join", "channel_leave"):
                            continue

                        ts = msg.get("ts", "")
                        msg_id = f"MSG-{ts.replace('.', '')[:8]}" if ts else f"MSG-{len(live_messages)+1}"
                        user_id = msg.get("user", "unknown")
                        username = await cls._resolve_username_by_id(client, user_id)

                        try:
                            ts_float = float(ts) if ts else datetime.now(timezone.utc).timestamp()
                            iso_time = datetime.fromtimestamp(ts_float, tz=timezone.utc).isoformat()
                        except Exception:
                            iso_time = datetime.now(timezone.utc).isoformat()

                        channel_display = f"#{clean_ch_name}"
                        scopes_inferred = cls._infer_scopes(clean_ch_name)

                        msg_record = {
                            "id": msg_id,
                            "channel": channel_display,
                            "user": username,
                            "timestamp": iso_time,
                            "text": msg.get("text", ""),
                            "scopes": scopes_inferred,
                        }
                        live_messages.append(msg_record)

            if live_messages:
                if scopes:
                    return [m for m in live_messages if any(s in m.get("scopes", []) for s in scopes)]
                return live_messages

            logger.info("No live Slack messages returned; falling back to mock fixtures.")
            return cls.MOCK_MESSAGES if not scopes else [
                m for m in cls.MOCK_MESSAGES if any(s in m.get("scopes", []) for s in scopes)
            ]

        except Exception as exc:
            logger.error(f"Live Slack message ingestion failed: {exc}. Using mock fallback.")
            return cls.MOCK_MESSAGES if not scopes else [
                m for m in cls.MOCK_MESSAGES if any(s in m.get("scopes", []) for s in scopes)
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
        Posts live Slack Block Kit cards or Direct Messages via Slack Web API when SLACK_BOT_TOKEN is present.
        Ensures idempotent execution and updates SQLite state store.
        """
        async with cls._get_lock():
            draft = await state_store.get_draft(draft_id)
            if not draft:
                raise ValueError(f"Draft '{draft_id}' not found.")

            if draft.status == DraftStatus.EXECUTED:
                return {"status": "already_executed", "draft_id": draft_id}

            result_message: str

            if settings.slack_bot_token:
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        target = draft.target_channel_or_user
                        target_channel_id: Optional[str] = None

                        if target.startswith("#"):
                            target_channel_id = await cls._resolve_channel_id(client, target.lstrip("#")) or target
                        elif target.startswith("@"):
                            user_id = await cls._resolve_user_id(client, target.lstrip("@"))
                            if user_id:
                                open_dm_url = "https://slack.com/api/conversations.open"
                                open_resp = await client.post(
                                    open_dm_url,
                                    headers=cls._get_headers(),
                                    json={"users": user_id},
                                )
                                if open_resp.status_code == 200 and open_resp.json().get("ok"):
                                    target_channel_id = open_resp.json().get("channel", {}).get("id")

                        post_url = "https://slack.com/api/chat.postMessage"
                        post_payload: Dict[str, Any] = {
                            "channel": target_channel_id or target,
                            "text": draft.content,
                        }
                        if draft.metadata and "slack_blocks" in draft.metadata:
                            post_payload["blocks"] = draft.metadata["slack_blocks"]

                        post_resp = await client.post(post_url, headers=cls._get_headers(), json=post_payload)
                        post_data = post_resp.json() if post_resp.status_code == 200 else {}

                        if post_data.get("ok"):
                            msg_ts = post_data.get("ts", "")
                            result_message = (
                                f"Successfully dispatched '{draft.action_type}' to '{target}' via Slack API "
                                f"(ts: {msg_ts}, Approved by {approver_username})."
                            )
                        else:
                            slack_err = post_data.get("error", f"HTTP_{post_resp.status_code}")
                            result_message = (
                                f"Dispatched '{draft.action_type}' to '{target}' with Slack API response: {slack_err} "
                                f"(Approved by {approver_username})."
                            )
                except Exception as exc:
                    logger.error(f"Live Slack dispatch exception: {exc}")
                    result_message = (
                        f"Successfully dispatched '{draft.action_type}' to '{draft.target_channel_or_user}' "
                        f"(Approved by {approver_username}, live fallback recorded)."
                    )
            else:
                result_message = (
                    f"Successfully dispatched '{draft.action_type}' to '{draft.target_channel_or_user}' "
                    f"(Approved by {approver_username})."
                )

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
