import os
import pytest
from openai import OpenAI

from pdf_summariser import summarize_url


TEST_URL = "https://www.berkshirehathaway.com/letters/2024ltr.pdf"


@pytest.mark.integration
def test_summarize_url_calls_openai_integration():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping live OpenAI integration test")

    model = os.getenv("TEST_OPENAI_MODEL", "gpt-4o-mini")
    client = OpenAI(api_key=api_key)

    result = summarize_url(client, TEST_URL, model=model)

    assert isinstance(result, str)
    assert result.strip() != ""
    assert not result.startswith("Error summarizing ")
