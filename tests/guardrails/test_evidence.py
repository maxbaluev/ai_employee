"""Specification tests for the evidence guardrail."""

from __future__ import annotations

from types import SimpleNamespace

import pytest


@pytest.fixture
def callback_context() -> SimpleNamespace:
    return SimpleNamespace(shared_state={})


def _check(ctx: SimpleNamespace, proposal):
    from agent.guardrails import evidence

    return evidence.check(ctx, proposal)


def test_blocks_when_proposal_missing(callback_context):
    result = _check(callback_context, None)
    assert result.allowed is False


def test_blocks_when_evidence_empty_string(callback_context):
    result = _check(callback_context, {"evidence": "   "})
    assert result.allowed is False


def test_blocks_when_evidence_empty_list(callback_context):
    result = _check(callback_context, {"evidence": [" ", ""]})
    assert result.allowed is False


def test_allows_with_citation_list(callback_context):
    result = _check(callback_context, {"evidence": ["doc://123"]})
    assert result.allowed is True


def test_allows_with_text_evidence(callback_context):
    result = _check(callback_context, {"evidence": "User confirmed via email"})
    assert result.allowed is True
