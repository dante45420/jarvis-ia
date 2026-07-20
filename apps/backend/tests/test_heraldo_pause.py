"""Tests de la política de pausa por tema: cero IA, independiente entre temas."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from jarvis.modules.actions import ModuleAction
from jarvis.modules.heraldo.delivery import Delivery, DeliveryKind
from jarvis.modules.heraldo.domain import PodcastStyle, Topic, TopicProfile, TopicState
from jarvis.modules.heraldo.pause import (
    GenerationDecision,
    PauseController,
    decide_generation,
    decide_news_generation,
    pause,
    resume,
)

NOW = datetime(2026, 7, 20, tzinfo=UTC)
_PROFILE = TopicProfile((), (), (), reach_threshold=1, recency_hours=48)


def _topic(state: TopicState = TopicState.ACTIVE) -> Topic:
    return Topic(
        id="t1",
        owner_id="u1",
        name="IA en medicina",
        profile=_PROFILE,
        podcast_style=PodcastStyle.NARRATOR,
        state=state,
    )


def _delivery(*, consumed: bool) -> Delivery:
    return Delivery(
        id="d1",
        topic_id="t1",
        kind=DeliveryKind.PODCAST,
        created_at=NOW,
        consumed_at=NOW if consumed else None,
    )


class _FakeInbox:
    def __init__(self) -> None:
        self.actions: list[ModuleAction] = []

    async def emit(self, action: ModuleAction) -> None:
        self.actions.append(action)


def test_generates_when_nothing_pending() -> None:
    assert decide_generation(TopicState.ACTIVE, None) is GenerationDecision.GENERATE


def test_pauses_when_pending_not_consumed() -> None:
    decision = decide_generation(TopicState.ACTIVE, _delivery(consumed=False))
    assert decision is GenerationDecision.PAUSE


def test_generates_when_pending_already_consumed() -> None:
    decision = decide_generation(TopicState.ACTIVE, _delivery(consumed=True))
    assert decision is GenerationDecision.GENERATE


def test_holds_when_already_paused() -> None:
    assert decide_generation(TopicState.PAUSED, None) is GenerationDecision.HOLD


def test_news_generates_when_nothing_accumulated() -> None:
    assert decide_news_generation(TopicState.ACTIVE, None, NOW) is GenerationDecision.GENERATE


def test_news_keeps_generating_within_window() -> None:
    recent = NOW - timedelta(days=2)
    assert decide_news_generation(TopicState.ACTIVE, recent, NOW) is GenerationDecision.GENERATE


def test_news_pauses_after_three_days_without_response() -> None:
    stale = NOW - timedelta(days=4)
    assert decide_news_generation(TopicState.ACTIVE, stale, NOW) is GenerationDecision.PAUSE


def test_news_holds_when_already_paused() -> None:
    stale = NOW - timedelta(days=10)
    assert decide_news_generation(TopicState.PAUSED, stale, NOW) is GenerationDecision.HOLD


def test_pause_and_resume_flip_state() -> None:
    assert pause(_topic()).state is TopicState.PAUSED
    assert resume(_topic(TopicState.PAUSED)).state is TopicState.ACTIVE


async def test_controller_notifies_when_pausing() -> None:
    inbox = _FakeInbox()
    decision = await PauseController(inbox).evaluate(_topic(), _delivery(consumed=False), NOW)
    assert decision is GenerationDecision.PAUSE
    assert len(inbox.actions) == 1
    action = inbox.actions[0]
    assert action.kind == "topic_paused"
    assert action.subject == "IA en medicina"
    assert action.owner_id == "u1"


async def test_controller_stays_silent_when_generating() -> None:
    inbox = _FakeInbox()
    decision = await PauseController(inbox).evaluate(_topic(), _delivery(consumed=True), NOW)
    assert decision is GenerationDecision.GENERATE
    assert inbox.actions == []
