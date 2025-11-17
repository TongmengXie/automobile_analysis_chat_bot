# app/agents/financial_rag_agent.py

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from app.retrieval.vectorstore import get_retriever
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from app.config import OPENAI_API_KEY

class FinancialReportAgent:
    def __init__(self):
        retriever = get_retriever()
        self.SYSTEM_PROMPT = """
            You are a strictly retrieval-grounded financial assistant.

            RULES:
            1. You MUST answer ONLY using the retrieved documents.
            2. If retrieval returns NO relevant documents, you MUST answer:
            "The answer is not available in the provided documents."

            3. You MUST NOT use outside knowledge.
            4. You MUST NOT guess, estimate, or hallucinate missing numbers.
            5. You MUST ALWAYS cite the source of retrieved information as:
            [company year — filename].
            6. If multiple sources are retrieved, summarize only what they say.

            You must follow these rules exactly.
        """

        # Wrap retriever as a LangChain tool
        # ===== TOOL WRAPPER =====
        @tool
        def retrieve_reports(query: str):
            """Retrieve financial report chunks from the vector database."""

            # ONLY the query — not the system prompt
            docs = retriever.invoke(query)

            if not docs:
                return {"error": "NO_DOCUMENTS"}

            formatted = []
            for d in docs:
                citation = (
                    f"[{d.metadata.get('company')} "
                    f"{d.metadata.get('year')} — "
                    f"{d.metadata.get('source')}]"
                )

                formatted.append(
                    f"SOURCE: {citation}\nCONTENT:\n{d.page_content}"
                )

            return "\n\n---\n\n".join(formatted)
        
        # LLM you used in the notebook
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # Build the ReAct agent exactly as you did in the notebook
        self.agent = create_react_agent(
            model=llm,
            tools=[retrieve_reports],
        )

    def run(self, message: str):
        result = self.agent.invoke(
            {
                "messages": [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": message}
                ]
            }
        )
        return result["messages"][-1].content

