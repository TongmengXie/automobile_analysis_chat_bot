# Automobile Analysis Chat Bot

## Overview
This FastAPI application answers automobile domain questions through multi-round conversations, keeping a short dialogue history so follow-up prompts stay grounded.
The web client renders this experience in a simple UI, and Docker support lets you run the full stack locally with minimal setup.
The `FinancialReportAgent` orchestrates retrieval, judging, and answer generation so responses cite either report snippets or supplemental web findings as needed.
Local document chunks come from a Chroma vector store populated with PDF text split into fragments that include company, year, and source metadata for grounding.

## Retrieval and fallback behavior
1. **Local lookup first.** Each user question (optionally augmented with the last three Q&A turns) queries the Chroma retriever to pull relevant report snippets, preserving metadata for downstream citations. (app/agents/agents.py; app/retrieval/vectorstore.py).
2. **Judge-directed escalation.** A dedicated judge prompt classifies whether the local snippets are sufficient (`USE_LOCAL`) or if extra context is required (`NEED_WEB`). (app/agents/agents.py)
3. **Fallback to online search.** When the judge signals `NEED_WEB`, the agent calls the GPT-powered web search helper, which returns structured snippets (with title, URL, and body) or gracefully notes failures; otherwise, it skips web search entirely. The final answer cites which sources—local or web—were used. (app/agents/agents.py; app/agents/tooling.py).

## Highlights
- **Resilient context pipeline.** Users benefit from a two-stage grounding flow: metadata-rich local report retrieval followed by a judge-gated online search when local evidence is insufficient, ensuring coverage even when the vector store lacks relevant matches.
- **Citation-aware outputs.** Report snippets retain company/year/source tags from ingestion, and web snippets are normalized with titles and URLs so the answer generator can cite them explicitly.
- **Deployable everywhere.** Run the FastAPI backend and web front end together via Docker, or launch the web client directly during development for quick iteration.

## Future improvements
- **Refine judge prompt toward local-first answers.** The current judge instruction is neutral between local and web sources. Adjusting it to prefer local evidence—only declaring failure after more relaxed thresholds (e.g., allowing partial matches or encouraging re-querying metadata facets)—would reduce unnecessary web calls while keeping accuracy.

## Architecture
- FastAPI backend exposes endpoints for chat, retrieval, and search orchestration.
- Front-end web client communicates with the backend to provide a conversational interface and display citations.
- Chroma vector store holds ingested PDF fragments with metadata, feeding the retrieval step before any web escalation.
- GPT judge and generation steps decide when to fall back to web search and compose the final cited response.

                 ┌────────────────────────────────────┐
                 │            User Query               │
                 └────────────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │  Augment With History    │
                    │ (last 3 Q/A turns)       │
                    └──────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │   Local Vector Search     │
                    │ (Chroma Retriever)        │
                    └──────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │        Judge LLM         │
                    │ USE_LOCAL / NEED_WEB     │
                    └──────────────────────────┘
                         │              │
               USE_LOCAL │              │ NEED_WEB
                         │              ▼
                         │      ┌────────────────────┐
                         │      │   Web Search Tool  │
                         │      │ (A different GPT model) │
                         │      └────────────────────┘
                         │              │
                         └──────────────┘
                                   │
                                   ▼
                      ┌────────────────────────────┐
                      │ LLM Final Answer Generator │
                      │  (uses: reports + web +    │
                      │   judge rationale + history)│
                      └────────────────────────────┘
                                   │
                                   ▼
                     ┌───────────────────────────────┐
                     │      Telemetry + Final Answer  │
                     │  (search steps, citations, etc)│
                     └───────────────────────────────┘
