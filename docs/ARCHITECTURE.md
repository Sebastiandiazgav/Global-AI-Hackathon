# MyAgent - Architecture Diagram

## System Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 14)                        │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌───────────────┐   │
│  │   Chat   │ │  Voice   │ │   Image    │ │   Language    │   │
│  │  Panel   │ │  Input   │ │   Upload   │ │   Selector    │   │
│  └────┬─────┘ └────┬─────┘ └─────┬──────┘ └───────────────┘   │
│       │             │             │                             │
│  ┌────▼─────────────▼─────────────▼──────┐  ┌──────────────┐  │
│  │          SSE Stream Client            │  │  Workflow     │  │
│  │    (Real-time event visualization)    │  │  Panel        │  │
│  └───────────────────┬───────────────────┘  │  (Society     │  │
│                      │                      │   Debate)     │  │
│                      │                      └──────────────┘  │
└──────────────────────┼─────────────────────────────────────────┘
                       │ HTTPS + SSE
┌──────────────────────▼─────────────────────────────────────────┐
│                 BACKEND (FastAPI + Python 3.11)                 │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              GUARDRAILS (Dual Layer)                     │   │
│  │  [Custom Regex] → [ML Content Filter via Qwen]          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         SUPERVISOR (qwen3.5-omni-plus)                  │   │
│  │         Multilingual Router • 7 Languages               │   │
│  └──────┬────────┬────────┬────────┬────────┬────────┬─────┘   │
│         │        │        │        │        │        │         │
│    ┌────▼──┐ ┌──▼───┐ ┌──▼───┐ ┌──▼───┐ ┌──▼────┐ ┌▼──────┐  │
│    │Energy │ │Logis.│ │Supp. │ │Visual│ │Analyt.│ │Society│  │
│    │Agent  │ │Agent │ │Agent │ │Agent │ │Agent  │ │Agent  │  │
│    │(flash)│ │(flash)│ │(flash)│ │(VL)  │ │(flash)│ │(plus) │  │
│    └───┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬────┘ └──┬────┘  │
│        │        │        │        │        │         │        │
│  ┌─────▼────────▼────────▼────────▼────────▼─────────▼─────┐  │
│  │           MCP PROTOCOL (5 Servers • 20 Tools)            │  │
│  │  [energia] [logistica] [catalogo] [memory] [analytics]   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │      AGENT SOCIETY (Strategic Consulting Engine)         │   │
│  │  ┌──────┐ ┌────────┐ ┌──────┐ ┌───────┐ ┌──────────┐  │   │
│  │  │Sales │ │Market. │ │ Ops  │ │Finance│ │Moderator │  │   │
│  │  └──┬───┘ └───┬────┘ └──┬───┘ └───┬───┘ └────┬─────┘  │   │
│  │     └──────────┴─────────┴─────────┘          │        │   │
│  │            Round 1 → Conflict Detection → Round 2       │   │
│  │                        → Consensus                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                │
│  ┌───────────────────┐  ┌──────────────────────────────────┐   │
│  │ Persistent Memory │  │       Observability              │   │
│  │ (Cross-session)   │  │  [LangSmith Tracing]             │   │
│  │ TTL + Relevance   │  │  [Structured Logging]            │   │
│  └─────────┬─────────┘  └──────────────────────────────────┘   │
│            │                                                   │
└────────────┼───────────────────────────────────────────────────┘
             │
    ┌────────┼────────────────────────────────┐
    │        │        ALIBABA CLOUD           │
    │  ┌─────▼──────┐  ┌────────────────┐    │
    │  │ ApsaraDB   │  │  Qwen Cloud    │    │
    │  │ RDS Postgres│  │  (LLM APIs)    │    │
    │  │ + pgvector  │  │  - omni-plus   │    │
    │  │ (RAG)       │  │  - omni-flash  │    │
    │  └─────────────┘  │  - VL-235B     │    │
    │                   │  - embedding-v4│    │
    │  ┌─────────────┐  └────────────────┘    │
    │  │    ECS      │                        │
    │  │ (Containers)│  ┌────────────────┐    │
    │  └─────────────┘  │  Container     │    │
    │                   │  Registry      │    │
    │  ┌─────────────┐  └────────────────┘    │
    │  │    OSS      │                        │
    │  │ (Storage)   │                        │
    │  └─────────────┘                        │
    └─────────────────────────────────────────┘
```

## Hackathon Tracks Coverage

| Track | Coverage | Evidence |
|-------|----------|----------|
| **Track 4: Autopilot Agent** | ✅ Primary | End-to-end automation of energy, logistics, support workflows with human-in-the-loop |
| **Track 1: MemoryAgent** | ✅ Strong | Cross-session persistent memory with TTL, relevance scoring, intelligent forgetting |
| **Track 3: Agent Society** | ✅ Feature | Multi-agent debate (Sales, Marketing, Ops, Finance) with conflict resolution |

## Key Differentiators

1. **7 Specialized Agents** — Not a monolithic chatbot, but a true multi-agent system
2. **Agent Society** — Agents debate and negotiate strategies with real business data
3. **MCP Protocol** — 20 tools across 5 servers, fully standardized
4. **Vision Analysis** — Upload bills/labels for automatic data extraction + action
5. **Persistent Memory** — Cross-session learning with intelligent forgetting
6. **Multilingual** — 7 languages auto-detected and responded
7. **Dual-Layer Security** — Regex guardrails + ML content classification
8. **Production-Ready** — Docker, PostgreSQL, health checks, rate limiting, audit trail
