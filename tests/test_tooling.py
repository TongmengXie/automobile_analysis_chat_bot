mport json

import pytest

from app.agents.tooling import GPTWebSearchHelper


@pytest.fixture
def search_helper(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    return GPTWebSearchHelper()


def test_parse_payload_prefers_structured_json(monkeypatch, search_helper):
    raw_payload = json.dumps(
        [
            {"title": "Item 1", "url": "https://example.com/a", "snippet": "alpha"},
            {"title": "Item 2", "url": "https://example.com/b", "snippet": "beta"},
        ]
    )

    results = search_helper._parse_payload(raw_payload, limit=1)

    assert len(results) == 1
    assert results[0]["href"] == "https://example.com/a"
    assert results[0]["body"] == "alpha"


def test_parse_payload_falls_back_to_markdown_blocks(monkeypatch, search_helper):
    raw_payload = (
        "Latest sales report\nhttps://example.com/report\nHighlights...\n\n"
        "Follow-up insight without URL"
    )

    results = search_helper._parse_payload(raw_payload, limit=2)

    assert len(results) == 2
    assert results[0]["href"] == "https://example.com/report"
    assert "Follow-up insight" in results[1]["body"]


def test_extract_text_block_requires_content(monkeypatch, search_helper):
    with pytest.raises(RuntimeError):
        search_helper._extract_text_block({"output": []})