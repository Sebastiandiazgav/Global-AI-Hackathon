<p align="center">
  <img src="https://img.shields.io/badge/MyAgent-Enterprise%20AI%20Copilot-1e40af?style=for-the-badge&logo=robot&logoColor=white" alt="MyAgent"/>
</p>

<h1 align="center">🤖 MyAgent — Enterprise AI Copilot</h1>

<p align="center">
  <strong>Multi-agent AI system for enterprise operations powered by Qwen Cloud</strong><br/>
  <em>7 Agents · 20 MCP Tools · 5 Servers · 7 Languages · Agent Society Debate</em>
</p>

<p align="center">
  <a href="#-architecture"><img src="https://img.shields.io/badge/Architecture-Multi--Agent-blue?style=flat-square"/></a>
  <a href="#-tech-stack"><img src="https://img.shields.io/badge/LLM-Qwen%20Cloud-orange?style=flat-square"/></a>
  <a href="#-mcp-protocol"><img src="https://img.shields.io/badge/Protocol-MCP-purple?style=flat-square"/></a>
  <a href="#-infrastructure"><img src="https://img.shields.io/badge/Cloud-Alibaba-red?style=flat-square"/></a>
  <a href="#-agent-society"><img src="https://img.shields.io/badge/Society-4%20Agents%20Debate-pink?style=flat-square"/></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/Docs-Español-green?style=flat-square"/></a>
</p>

<p align="center">
  <a href="README.es.md">📖 Documentación en Español</a> ·
  <a href="docs/architecture-diagram.md">📐 Architecture Diagram</a> ·
  <a href="http://43.98.164.203:3000">🌐 Live Demo</a>
</p>

---

## 🎯 The Problem

Enterprise operations managing **32,000+ points of sale** with **500+ digital products** face:

- 📚 Steep learning curve for new operators
- 🔀 Multiple interfaces for different verticals (energy, logistics, recharges)
- ⏱️ Manual processes consuming time while customers wait
- 💸 Difficulty maximizing commissions due to catalog unfamiliarity
- 📊 No strategic insights on growth and performance optimization

## 💡 The Solution

**MyAgent** is an agentic AI copilot that:

| Capability | Description |
|-----------|-------------|
| 🧠 **Understands** | Natural language in 7 languages (text + voice + images) |
| 🎯 **Routes** | Intelligent supervisor routes to the correct specialized agent |
| ⚡ **Executes** | Autonomous transactional actions via MCP Protocol (20 tools) |
| 🧠 **Remembers** | Persistent cross-session memory with intelligent forgetting |
| 🛡️ **Protects** | Dual-layer guardrails (regex + ML content filter) |
| 🏛️ **Advises** | Agent Society — 5 agents debate strategies with real data |
| 👁️ **Sees** | Visual analysis of bills, labels, and documents |

---

## 🏗️ Architecture

<p align="center">
  <img src="docs/architecture.png" alt="MyAgent Architecture Diagram" width="100%"/>
</p>

<details>
<summary>📐 View Interactive Architecture Diagram (Mermaid Code)</summary>

See [docs/architecture-diagram.md](docs/architecture-diagram.md) for the complete Mermaid code you can paste into [mermaid.live](https://mermaid.live).

</details>

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 14 · Tailwind CSS · React | Enterprise UI with i18n |
| Backend | FastAPI · Python 3.11 | API + Orchestration |
| Orchestration | LangGraph | Multi-agent state machine |
| Supervisor | Qwen Cloud — `qwen3.5-omni-plus` | Multilingual routing |
| Agents | Qwen Cloud — `qwen3.5-omni-flash` | Function calling |
| Vision | Qwen Cloud — `qwen-vl-max` | Image analysis |
| Society | Qwen Cloud — `qwen3.5-omni-plus` | Strategic debate |
| Embeddings | Qwen Cloud — `text-embedding-v4` | RAG vectorization |
| Database | PostgreSQL 16 + pgvector | Persistence + Vector RAG |
| Protocol | MCP (Model Context Protocol) | 5 servers · 20 tools |
| Security | Custom + ML Content Filter | Dual-layer protection |
| Observability | LangSmith | Full execution traces |
| Infrastructure | Alibaba Cloud (ECS + VPC) | Production hosting |
| Containers | Docker + Docker Compose | Deployment |

---

## 🤖 Agents

| Agent | Model | Capabilities |
|-------|-------|-------------|
| 🧭 **Supervisor** | qwen3.5-omni-plus | Multilingual intent classification + routing (7 languages) |
| ⚡ **Energy** | qwen3.5-omni-flash | Tariff comparison · Savings analysis · Contract management |
| 📦 **Logistics** | qwen3.5-omni-flash | Package registration · Delivery verification · Returns |
| 💬 **Support** | qwen3.5-omni-flash | Phone recharges (13 countries) · Digital PINs (19 platforms) · RAG |
| 👁️ **Visual** | qwen-vl-max | Bill OCR · Label reading · Document analysis |
| 📊 **Analytics** | qwen3.5-omni-flash | Commission tracking · Trends · Product performance |
| 🏛️ **Society** | qwen3.5-omni-plus | Multi-agent strategic debate (Sales · Marketing · Ops · Finance · Moderator) |

---

## 📡 MCP Protocol

5 servers exposing 20 tools via standard Model Context Protocol:

| Server | Tools | Description |
|--------|-------|-------------|
| `myagent-energia` | `calcular_ahorro_energetico` · `preparar_contrato_energia` · `consultar_tarifas_disponibles` | Energy tariffs and contracts |
| `myagent-logistica` | `registrar_paquetes` · `confirmar_entrega_paquete` · `consultar_estado_paquete` · `gestionar_devolucion` · `listar_paquetes_pendientes` | Package management |
| `myagent-catalogo` | `procesar_recarga` · `activar_pin_digital` · `buscar_en_manuales` · `consultar_catalogo_productos` | Recharges, PINs, RAG, Catalog |
| `myagent-memory` | `store_memory` · `recall_memories` · `forget_memory` · `get_memory_summary` | Persistent memory management |
| `myagent-analytics` | `get_daily_summary` · `get_top_products` · `get_commission_trend` · `compare_periods` | Business intelligence |

---

## 🏛️ Agent Society

When users ask strategic questions, MyAgent activates a **multi-agent debate**:

1. 💼 **Sales Strategist** — Revenue patterns, conversion, cross-sell
2. 📢 **Marketing Advisor** — Visibility, positioning, local tactics
3. ⚙️ **Operations Optimizer** — Efficiency, bottlenecks, time savings
4. 📊 **Finance Analyst** — ROI, projections, cost-benefit
5. 🎯 **Moderator** — Identifies conflicts → challenges positions → synthesizes consensus

The debate runs **2 rounds** with real business data, producing a prioritized action plan visible in real-time via SSE streaming.

---

## 🌍 Multilingual

Automatic language detection and response in:

🇪🇸 Spanish · 🇬🇧 English · 🇫🇷 French · 🇵🇹 Portuguese · 🇩🇪 German · 🇮🇹 Italian · 🇨🇳 Chinese

The UI also translates dynamically based on selected language.

---

## 🛡️ Security

| Layer | Protection |
|-------|-----------|
| **Input Validator** | Regex-based prompt injection detection, length limits |
| **ML Content Filter** | Qwen Cloud as classifier (SAFE/OFF_TOPIC/HARMFUL/ATTACK) |
| **Output Sanitizer** | DNI/phone masking, sensitive data redaction, hallucination detection |
| **Transaction Validator** | Amount limits, phone format verification |
| **MCP Rate Limiting** | Per-client rate limiting with audit trail |

---

## ☁️ Infrastructure

Deployed on **Alibaba Cloud**:

| Service | Usage |
|---------|-------|
| **ECS** (Elastic Compute Service) | Docker containers (backend + frontend + PostgreSQL) |
| **VPC** (Virtual Private Cloud) | Isolated network (172.16.0.0/16) |
| **Security Group** | Firewall rules (ports 22, 80, 443, 3000, 8000) |
| **Qwen Cloud** (Model Studio) | 4 LLM models (70M+ tokens free tier) |

---

## 🚀 Quick Start

```bash
# Clone
git clone <repo-url>
cd hackaton-enterprise

# Configure
cp .env.example .env
# Edit .env with your Qwen Cloud API key

# Run with Docker Compose
docker compose up --build

# Access
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# Health:   http://localhost:8000/health
```

---

## 📊 Test Results

```
78 production tests | 77 passed | 98.7% pass rate
Tested against: http://43.98.164.203 (Alibaba Cloud ECS)
```

---

## 🏆 Hackathon Tracks

| Track | Coverage |
|-------|----------|
| **Track 4: Autopilot Agent** | ✅ Primary — End-to-end workflow automation with human-in-the-loop |
| **Track 1: MemoryAgent** | ✅ Strong — Cross-session persistent memory with intelligent forgetting |
| **Track 3: Agent Society** | ✅ Feature — Multi-agent debate with conflict resolution |

---

## 👤 Author

**Sebastián Díaz G.**
AI Software Engineer · Full-Stack Developer

---

## 📄 License

[MIT License](LICENSE) — Open Source for Global AI Hackathon with Qwen Cloud 2026.
