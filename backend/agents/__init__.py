# MyAgent - Multi-Agent System
# 
# Agents:
#   - supervisor: Multilingual router (qwen3.5-omni-plus)
#   - energia_agent: Energy tariffs, savings, contracts
#   - logistica_agent: Packages, deliveries, returns
#   - soporte_agent: Recharges, PINs, RAG support
#   - visual_agent: Image analysis (qwen3-vl-235b-a22b)
#   - analytics_agent: Performance metrics and insights
#   - society/: Multi-agent strategic debate (4 agents + moderator)
#
# Supporting modules:
#   - state: Shared LangGraph state definition
#   - graph: LangGraph orchestration
#   - memory: In-session conversational memory
#   - persistent_memory: Cross-session persistent memory engine
#   - token_utils: Token optimization helpers
#   - tool_policy: Tool validation for support agent
#   - product_resolver: Product catalog fuzzy matching
