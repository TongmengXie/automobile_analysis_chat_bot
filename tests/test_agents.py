from app.agents.agents import FinancialReportAgent


def build_agent(max_history: int = 3) -> FinancialReportAgent:
    """Create an agent instance without triggering external dependencies."""

    agent = FinancialReportAgent.__new__(FinancialReportAgent)
    agent.conversation_history = []
    agent.max_history = max_history
    agent.judge_system = "judge system"
    return agent


def test_run_judge_parses_decision_and_rationale():
    agent = build_agent()
    agent.judge_llm = object()
    agent._call_llm = lambda llm, system_prompt, user_prompt: "USE_LOCAL\nRATIONALE: context sufficient"

    decision, rationale = agent._run_judge("question", "context")

    assert decision == "USE_LOCAL"
    assert rationale == "context sufficient"


def test_run_judge_defaults_to_need_web_on_unknown_output():
    agent = build_agent()
    agent.judge_llm = object()
    agent._call_llm = lambda llm, system_prompt, user_prompt: "Unexpected content"

    decision, rationale = agent._run_judge("question", "context")

    assert decision == "NEED_WEB"
    assert rationale == "No rationale provided"


def test_maybe_search_web_handles_runtime_errors():
    class FailingSearch:
        def search(self, question):  # pragma: no cover - explicit behavior below
            raise RuntimeError("search unavailable")

    agent = build_agent()
    agent.web_search = FailingSearch()
    agent._format_web_results = lambda results: ""

    context, status = agent._maybe_search_web("Need web context?")

    assert context == ""
    assert status[0] == "Need web context; searching online..."
    assert any("search unavailable" in message for message in status)


def test_maybe_search_web_formats_results_when_available():
    class StubSearch:
        def __init__(self, results):
            self._results = results

        def search(self, question):
            return self._results

    agent = build_agent()
    agent.web_search = StubSearch([{"title": "t", "href": "u", "body": "b"}])
    agent._format_web_results = lambda results: "formatted"

    context, status = agent._maybe_search_web("Need web context?")

    assert context == "formatted"
    assert status[0] == "Need web context; searching online..."
    assert "Web search completed with supplemental context." in status


def test_remember_trims_history_to_maximum():
    agent = build_agent(max_history=2)

    agent._remember("q1", "a1")
    agent._remember("q2", "a2")
    agent._remember("q3", "a3")

    assert len(agent.conversation_history) == 2
    assert agent.conversation_history == [("q2", "a2"), ("q3", "a3")]