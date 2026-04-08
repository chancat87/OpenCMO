"""Tests for shared marketing output review helpers."""

import json
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_review_marketing_output_skips_without_api_key():
    from opencmo.marketing_review import review_marketing_output

    with patch("opencmo.marketing_review.llm.get_key_async", AsyncMock(return_value=None)):
        result = await review_marketing_output(
            agent_name="CMO Agent",
            user_message="Help me write positioning",
            output_text="Original output",
        )

    assert result == "Original output"


@pytest.mark.asyncio
async def test_review_marketing_output_rewrites_for_supported_agent():
    from opencmo.marketing_review import review_marketing_output

    with patch("opencmo.marketing_review.llm.get_key_async", AsyncMock(return_value="sk-test")), \
         patch("opencmo.marketing_review.llm.chat_completion", AsyncMock(return_value="Rewritten output")):
        result = await review_marketing_output(
            agent_name="CMO Agent",
            user_message="Help me write positioning",
            output_text="Original output with a longer draft that explains the product, the audience, and the value proposition.",
        )

    assert result == "Rewritten output"


def test_marketing_review_profile_selection():
    from opencmo.marketing_review import get_marketing_review_profile

    assert get_marketing_review_profile("Reddit Expert") == "community_social"
    assert get_marketing_review_profile("LinkedIn Expert") == "professional_social"
    assert get_marketing_review_profile("SEO Audit Expert") == "seo_growth"
    assert get_marketing_review_profile("CMO Agent") == "strategic_marketing"


@pytest.mark.asyncio
async def test_review_marketing_output_with_metadata_returns_tags():
    from opencmo.marketing_review import review_marketing_output_with_metadata

    llm_payload = {
        "revised_output": "Reviewed output",
        "weak_points": ["proof", "next_move"],
    }
    with patch("opencmo.marketing_review.llm.get_key_async", AsyncMock(return_value="sk-test")), \
         patch("opencmo.marketing_review.llm.chat_completion", AsyncMock(return_value=json.dumps(llm_payload))):
        result = await review_marketing_output_with_metadata(
            agent_name="LinkedIn Expert",
            user_message="Rewrite this post",
            output_text="Original draft with enough content for review to run safely.",
        )

    assert result["final_output"] == "Reviewed output"
    assert result["review_applied"] is True
    assert result["profile"] == "professional_social"
    assert result["weak_points"] == ["proof", "next_move"]
