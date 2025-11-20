import json
import os
import re
from dataclasses import dataclass
from typing import List, Optional

import requests

from app.retrieval.vectorstore import get_retriever


@dataclass
class GPTWebSearchHelper:
    """Wrapper around OpenAI's GPT web-search tool."""

    model: Optional[str] = None
    temperature: Optional[float] = None
    max_results: int = 5

    def __post_init__(self):
        self._api_key = os.getenv("OPENAI_API_KEY")
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY must be set for GPT web search")
        self._endpoint = os.getenv(
            "OPENAI_RESPONSES_ENDPOINT",
            "https://api.openai.com/v1/responses",
        )
        self.model = self.model or os.getenv("OPENAI_WEB_SEARCH_MODEL", "gpt-4.1-mini")
        if self.temperature is None:
            try:
                self.temperature = float(
                    os.getenv("OPENAI_WEB_SEARCH_TEMPERATURE", "0")
                )
            except ValueError as exc:  # pragma: no cover - configuration guard
                raise RuntimeError("OPENAI_WEB_SEARCH_TEMPERATURE must be numeric") from exc

    def search(self, query: str, max_results: Optional[int] = None) -> List[dict]:
        """Run GPT web search and return structured snippets."""

        limit = max_results or self.max_results
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "system",
                    "content": (
                        "Use the web_search tool to gather factual snippets."
                        " Always respond with JSON containing a list of objects"
                        " that include 'title', 'url', and 'snippet'."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Query: {query}\n"
                        f"Return at most {limit} high-quality results ordered by relevance."
                    ),
                },
            ],
            "tools": [{"type": "web_search"}],
            "temperature": self.temperature,
        }

        try:
            response = requests.post(
                self._endpoint,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60,
            )
        except Exception as exc:  # pragma: no cover - external dependency
            raise RuntimeError(f"GPT web search failed: {exc}") from exc

        if response.status_code >= 400:
            raise RuntimeError(
                f"GPT web search failed with status {response.status_code}: {response.text}"
            )

        raw_payload = self._extract_text_block(response.json())
        results = self._parse_payload(raw_payload, limit)

        if not results:
            raise RuntimeError("GPT web search returned no structured results")

        return results[:limit]

    def _extract_text_block(self, response_json) -> str:
        """Flatten the response output into a single text block."""

        chunks: List[str] = []
        for item in (response_json or {}).get("output", []) or []:
            for content in item.get("content", []) or []:
                text = content.get("text")
                if text:
                    chunks.append(text)
        if not chunks:
            raise RuntimeError("GPT web search response did not include text output")
        return "\n".join(chunks).strip()

    def _parse_payload(self, raw_payload: str, limit: int) -> List[dict]:
        """Parse JSON when available and fall back to markdown-ish snippets."""

        results: List[dict] = []
        try:
            parsed = json.loads(raw_payload)
            items = parsed if isinstance(parsed, list) else parsed.get("results", [])
            for item in items:
                if not isinstance(item, dict):
                    continue
                results.append(
                    {
                        "title": item.get("title") or item.get("heading") or "",
                        "href": item.get("url") or item.get("href") or "",
                        "body": item.get("snippet") or item.get("summary") or "",
                    }
                )
                if len(results) >= limit:
                    return results
        except (json.JSONDecodeError, AttributeError, TypeError):
            # Fall back to heuristic parsing when the model emits natural language.
            pass

        if results:
            return results

        return self._parse_markdown_payload(raw_payload, limit)

    def _parse_markdown_payload(self, raw_payload: str, limit: int) -> List[dict]:
        """Heuristically extract snippets and links from plain-text payloads."""

        blocks = [block.strip() for block in raw_payload.split("\n\n") if block.strip()]
        url_pattern = re.compile(r"https?://\S+")
        results: List[dict] = []
        for block in blocks:
            url_match = url_pattern.search(block)
            url = url_match.group(0) if url_match else ""
            title = block.splitlines()[0][:120] if block else "web result"
            results.append({"title": title, "href": url, "body": block})
            if len(results) >= limit:
                break
        return results

    def health_check(self):
        """Verify the GPT web-search tool is callable before serving traffic."""

        try:
            self.search("automobile industry latest", max_results=1)
        except Exception as exc:  # pragma: no cover - external dependency
            raise RuntimeError("Web search helper is not ready") from exc


class AgenticToolchain:
    """Provision and cache retrieval and search helpers."""

    _retriever = None
    _web_search: Optional[GPTWebSearchHelper] = None

    @classmethod
    def provision_local_retriever(cls):
        if cls._retriever is None:
            cls._retriever = get_retriever()
        return cls._retriever

    @classmethod
    def provision_web_search(cls) -> GPTWebSearchHelper:
        if cls._web_search is None:
            cls._web_search = GPTWebSearchHelper()
        return cls._web_search


def ensure_agentic_tooling_ready():
    """Provision both tools and fail fast if either cannot be used."""

    retriever = AgenticToolchain.provision_local_retriever()
    if retriever is None:
        raise RuntimeError("Vector-store retriever could not be provisioned")

    web_search = AgenticToolchain.provision_web_search()
    web_search.health_check()

    return retriever, web_search