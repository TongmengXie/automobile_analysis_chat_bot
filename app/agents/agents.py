from typing import List, Optional, Tuple

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.agents.tooling import AgenticToolchain


class FinancialReportAgent:
    """retrieval, judging, and search"""

    def __init__(self) -> None:
        self.retriever = AgenticToolchain.provision_local_retriever()
        self.web_search = AgenticToolchain.provision_web_search()

        self.judge_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.answer_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        self.conversation_history: List[Tuple[str, str]] = []
        self.max_history = 5

        self.judge_system = (
            "You decide if report context answers the user's question. Respond with USE_LOCAL"
            " or NEED_WEB on the first line followed by \"RATIONALE: ...\" in <= 40 words."
        )
        self.answer_system = (
            "You are a retrieval-grounded automobile analyst. Answer only with supplied snippets,"
            " cite reports as [company year — source], cite web snippets as [web:title — url],"
            " and mention when web data was used."
        )

    def run(self, message: str) -> str:
        status: List[str] = []
        history_text = self._format_history()
        if history_text:
            status.append("Using earlier Q&A context for this follow-up.")
        augmented_question = self._augment_question(message, history_text)

        docs = self._retrieve(augmented_question)
        status.append("Searching local reports...")
        status.append(
            f"Found {len(docs)} local snippet(s)." if docs else "No relevant local snippets found."
        )
        report_context = self._format_reports(docs)

        decision, rationale = self._run_judge(augmented_question, report_context)
        status.append(f"Judge decision: {decision} — {rationale}")

        web_context = ""
        if decision == "NEED_WEB":
            web_context, web_status = self._maybe_search_web(augmented_question)
            status.extend(web_status)
        else:
            status.append("Local context sufficient; skipping web search.")

        answer_text = self._call_llm(
            self.answer_llm,
            self.answer_system,
            "\n".join(
                [
                    f"QUESTION: {message}",
                    "CONVERSATION CONTEXT:",
                    history_text or "No earlier conversation context available.",
                    "",
                    f"JUDGE_DECISION: {decision}",
                    f"JUDGE_RATIONALE: {rationale}",
                    "",
                    "REPORT CONTEXT:",
                    report_context or "NO REPORT CONTEXT",
                    "",
                    "WEB SEARCH CONTEXT:",
                    web_context or "NO WEB CONTEXT",
                ]
            ),
        )
        self._remember(message, answer_text)

        verbose_header = "\n".join(status).strip()
        return f"{verbose_header}\n\n{answer_text}".strip() if verbose_header else answer_text

    def _run_judge(self, question: str, report_context: str) -> Tuple[str, str]:
        raw = self._call_llm(
            self.judge_llm,
            self.judge_system,
            f"Question: {question}\n\nReport context:\n{report_context or 'NO REPORT CONTEXT'}",
        )
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        decision = (lines[0] if lines else "NEED_WEB").upper()
        if decision not in {"USE_LOCAL", "NEED_WEB"}:
            decision = "NEED_WEB"
        rationale = "No rationale provided"
        for line in lines[1:]:
            if line.upper().startswith("RATIONALE"):
                rationale = line.split(":", 1)[-1].strip() or rationale
                break
        return decision, rationale

    def _maybe_search_web(self, question: str) -> Tuple[str, List[str]]:
        status = ["Need web context; searching online..."]
        try:
            results = self.web_search.search(question)
        except RuntimeError as exc:
            status.append(f"Web search failed: {exc}")
            return "", status
        if not results:
            status.append("Web search returned no supplemental snippets.")
            return "", status
        status.append("Web search completed with supplemental context.")
        return self._format_web_results(results), status

    def _retrieve(self, question: str):
        if hasattr(self.retriever, "get_relevant_documents"):
            return self.retriever.get_relevant_documents(question)
        return self.retriever.invoke(question)

    @staticmethod
    def _format_reports(docs) -> str:
        snippets = []
        for doc in docs or []:
            metadata = doc.metadata or {}
            citation = (
                f"[{metadata.get('company', 'unknown')} {metadata.get('year', 'n/a')} — "
                f"{metadata.get('source', 'report')}]"
            )
            snippets.append(f"SOURCE: {citation}\nCONTENT:\n{doc.page_content.strip()}")
        return "\n\n---\n\n".join(snippets)

    @staticmethod
    def _format_web_results(results: List[dict]) -> str:
        snippets = []
        for result in results:
            title = result.get("title") or "web result"
            url = result.get("href") or result.get("url") or "unknown"
            body = result.get("body") or result.get("snippet") or ""
            snippets.append(f"SOURCE: [web:{title} — {url}]\nCONTENT:\n{body.strip()}")
        return "\n\n---\n\n".join(snippets)

    def _augment_question(self, question: str, history: Optional[str] = None) -> str:
        history = history or self._format_history()
        if not history:
            return question
        return f"Conversation history:\n{history}\n\nFollow-up question: {question}"

    def _format_history(self) -> str:
        if not self.conversation_history:
            return ""
        return "\n\n".join(
            f"Q: {prior_q.strip()}\nA: {prior_a.strip()}" for prior_q, prior_a in self.conversation_history
        )

    def _remember(self, question: str, answer: str) -> None:
        self.conversation_history.append((question, answer))
        if len(self.conversation_history) > self.max_history:
            self.conversation_history.pop(0)

    @staticmethod
    def _call_llm(llm, system_prompt: str, user_prompt: str) -> str:
        response = llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        return (response.content or "").strip()
