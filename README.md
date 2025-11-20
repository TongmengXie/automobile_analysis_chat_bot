# automobile_analysis_chat_bot
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
