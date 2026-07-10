"""Regression: user messages sent to a RUNNING agent are seen, not ignored.

Symptom the user reported: "redwake cli görmür mesajlarımı, özü özünə davam edir"
(the TUI agent ignores my messages and keeps going autonomously).

Root cause was behavioral, not plumbing — delivery always worked (logs show
24/24 messages delivered, 0 failures). But when a message lands *while the
agent is mid-turn*, the next turn resumed the prior tool chain and the user
perceived their message as ignored. These tests pin the fix:

1. ``send()`` to a running, interrupt-enabled agent fires ``stream.cancel``
   and appends the user content wrapped in an ``[INTERRUPT`` banner so the
   LLM answers the user first instead of resuming its plan.
2. A parked (waiting) agent — the common interactive path — does NOT get the
   banner (no interrupt happened).
3. ``consume_pending`` returns the appended item so the next turn sees it.
"""

from __future__ import annotations

import asyncio

import pytest

from redwake.core.agents import AgentCoordinator


class _FakeSession:
    def __init__(self) -> None:
        self.items: list[dict[str, object]] = []

    async def add_items(self, items: list[dict[str, object]]) -> None:
        self.items.extend(items)

    async def get_items(self, limit: int | None = None) -> list[dict[str, object]]:
        return list(self.items[-limit:] if limit else self.items)


class _FakeStream:
    def __init__(self) -> None:
        self.cancel_mode: str | None = None
        self.cancelled = False

    def cancel(self, mode: str = "immediate") -> None:
        self.cancel_mode = mode
        self.cancelled = True


def _user_content(session: _FakeSession) -> str:
    assert session.items, "no item appended to session"
    item = session.items[-1]
    assert item["role"] == "user"
    return str(item["content"])


@pytest.mark.asyncio
async def test_interrupt_while_running_wraps_message_and_cancels_stream() -> None:
    """A message to a mid-turn agent is banner-wrapped and cancels the stream."""
    coordinator = AgentCoordinator()
    session = _FakeSession()
    await coordinator.register("root", "redwake", parent_id=None)
    await coordinator.attach_runtime("root", session=session, interrupt_on_message=True)

    stream = _FakeStream()
    await coordinator.attach_stream("root", stream)

    delivered = await coordinator.send(
        "root", {"from": "user", "content": "what did you find so far?", "type": "instruction"}
    )

    assert delivered is True
    assert stream.cancelled is True
    assert stream.cancel_mode == "immediate"
    content = _user_content(session)
    assert content.startswith("[INTERRUPT")
    assert "what did you find so far?" in content
    assert coordinator.pending_counts["root"] == 1


@pytest.mark.asyncio
async def test_parked_message_is_not_wrapped() -> None:
    """A message to a waiting/parked agent has no interrupt banner (none happened)."""
    coordinator = AgentCoordinator()
    session = _FakeSession()
    await coordinator.register("root", "redwake", parent_id=None)
    # No stream attached + interrupt_on_message left default (False) => parked path.
    await coordinator.attach_runtime("root", session=session)

    delivered = await coordinator.send(
        "root", {"from": "user", "content": "hello", "type": "instruction"}
    )

    assert delivered is True
    content = _user_content(session)
    assert not content.startswith("[INTERRUPT")
    assert content == "hello"


@pytest.mark.asyncio
async def test_consume_pending_returns_appended_message() -> None:
    """After send(), consume_pending surfaces the item for the next turn's input."""
    coordinator = AgentCoordinator()
    session = _FakeSession()
    await coordinator.register("root", "redwake", parent_id=None)
    await coordinator.attach_runtime("root", session=session, interrupt_on_message=True)

    await coordinator.send("root", {"from": "user", "content": "stop", "type": "instruction"})

    count, items = await coordinator.consume_pending("root", include_items=True)

    assert count == 1
    assert len(items) == 1
    assert items[0]["role"] == "user"
    assert coordinator.pending_counts["root"] == 0


@pytest.mark.asyncio
async def test_send_to_unknown_target_drops_silently() -> None:
    """A message to a non-existent agent id is dropped, not crashed."""
    coordinator = AgentCoordinator()
    delivered = await coordinator.send(
        "nope", {"from": "user", "content": "x", "type": "instruction"}
    )
    assert delivered is False


@pytest.mark.asyncio
async def test_peer_message_uses_sender_format_not_interrupt_banner() -> None:
    """Only user-originated messages get the interrupt banner; peer messages keep their format."""
    coordinator = AgentCoordinator()
    session = _FakeSession()
    await coordinator.register("child", "recon", parent_id="root")
    await coordinator.register("root", "redwake", parent_id=None)
    await coordinator.attach_runtime("child", session=session, interrupt_on_message=True)

    stream = _FakeStream()
    await coordinator.attach_stream("child", stream)

    await coordinator.send(
        "child", {"from": "root", "content": "status?", "type": "information"}
    )

    content = _user_content(session)
    assert not content.startswith("[INTERRUPT")
    assert "[Message from redwake (root)" in content
