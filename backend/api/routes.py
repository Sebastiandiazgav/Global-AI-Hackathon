"""
MyAgent - API Routes
Main REST endpoints for the copilot system.
"""

import structlog
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from agents.graph import run_agent_graph
from rag.retriever import query_knowledge_base
from guardrails.input_validator import get_input_validator, get_transaction_validator
from guardrails.output_sanitizer import get_output_sanitizer
from guardrails.content_filter import classify_content
from config import get_settings
from database.db import save_guardrail_event, save_agent_call
from api.transaction_persistence import save_tool_transaction_event

logger = structlog.get_logger()

router = APIRouter()


def _persist_transactions_from_workflow(workflow_steps: List[dict], session_id: str) -> None:
    for step in workflow_steps:
        if not isinstance(step, dict):
            continue
        if step.get("type") != "tool_result":
            continue
        data = step.get("data", {})
        if isinstance(data, dict):
            save_tool_transaction_event(data, session_id)


# ============================================
# Request/Response Models
# ============================================

class ChatRequest(BaseModel):
    """Incoming chat message from the Smart POS."""
    message: str = Field(..., description="User message from the operator")
    session_id: str = Field(default="default", description="Session identifier")
    context: Optional[dict] = Field(default=None, description="Additional context")
    image: Optional[str] = Field(default=None, description="Base64 encoded image data (data:image/...;base64,...)")


class ChatResponse(BaseModel):
    """Response from the agent system."""
    response: str = Field(..., description="Agent response text")
    agent_used: str = Field(..., description="Which agent handled the request")
    tools_called: List[str] = Field(default=[], description="Tools invoked during execution")
    workflow_steps: List[dict] = Field(default=[], description="Execution steps for visualization")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = Field(default=0.95, description="Agent confidence score")
    trace_id: Optional[str] = Field(default=None, description="Trace correlation ID")
    guardrails_applied: List[str] = Field(default=[], description="Guardrails that were applied")


class RAGQueryRequest(BaseModel):
    """Direct RAG query for knowledge base search."""
    query: str = Field(..., description="Search query")
    top_k: int = Field(default=5, description="Number of results")


class RAGQueryResponse(BaseModel):
    """RAG search results."""
    results: List[dict] = Field(default=[], description="Retrieved documents")
    query: str


# ============================================
# Endpoints
# ============================================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint - processes tendero messages through the multi-agent system.
    
    Pipeline:
    1. INPUT GUARDRAILS: Validate and sanitize user input
    2. AGENT EXECUTION: Route through LangGraph multi-agent system
    3. OUTPUT GUARDRAILS: Sanitize response before delivery
    """
    settings = get_settings()
    guardrails_applied = []

    # ─────────────────────────────────────────────
    # STEP 1: INPUT GUARDRAILS
    # ─────────────────────────────────────────────
    if settings.guardrails_enabled:
        input_validator = get_input_validator()

        # Validate input
        is_valid, error_msg = input_validator.validate(request.message)
        if not is_valid:
            logger.warning(
                "input_validation_failed",
                message=request.message[:50],
                error=error_msg,
                session_id=request.session_id,
            )
            save_guardrail_event(
                event_type="input_validation",
                stage="input",
                action="blocked",
                message_preview=request.message,
                session_id=request.session_id,
            )
            guardrails_applied.append("input_blocked")
            return ChatResponse(
                response=f"⚠️ {error_msg}",
                agent_used="guardrails",
                tools_called=[],
                workflow_steps=[{
                    "type": "guardrail_block",
                    "data": {"reason": error_msg, "stage": "input"},
                }],
                confidence=0.0,
                guardrails_applied=guardrails_applied,
            )

        # Sanitize input
        sanitized_message = input_validator.sanitize(request.message)
        guardrails_applied.append("input_sanitized")

        # ML-based content classification
        content_result = await classify_content(sanitized_message)
        if content_result.get("action") == "BLOCKED":
            logger.warning(
                "content_filter_blocked",
                message=sanitized_message[:50],
                session_id=request.session_id,
                category=content_result.get("category"),
            )
            save_guardrail_event(
                event_type="content_filter",
                stage="input",
                action="blocked",
                message_preview=sanitized_message,
                session_id=request.session_id,
            )
            guardrails_applied.append("content_blocked")
            replacement = content_result.get("replacement_text", "Message not allowed.")
            return ChatResponse(
                response=f"🛡️ {replacement}",
                agent_used="guardrails",
                tools_called=[],
                workflow_steps=[{
                    "type": "guardrail_block",
                    "data": {"reason": content_result.get("category", ""), "stage": "input", "layer": "content_filter"},
                }],
                confidence=0.0,
                guardrails_applied=guardrails_applied,
            )
        guardrails_applied.append("content_passed")
    else:
        sanitized_message = request.message

    # ─────────────────────────────────────────────
    # STEP 2: AGENT EXECUTION
    # ─────────────────────────────────────────────
    try:
        # If image is provided, append it to the message for the visual agent
        agent_message = sanitized_message
        if request.image:
            agent_message = f"{sanitized_message}\n{request.image}"

        result = await run_agent_graph(
            message=agent_message,
            session_id=request.session_id,
            context=request.context,
        )
    except Exception as e:
        logger.error("agent_execution_error", error=str(e), session_id=request.session_id)
        raise HTTPException(status_code=500, detail=f"Agent execution error: {str(e)}")

    # ─────────────────────────────────────────────
    # STEP 3: OUTPUT GUARDRAILS
    # ─────────────────────────────────────────────
    if settings.guardrails_enabled:
        output_sanitizer = get_output_sanitizer()

        # Validate output
        is_valid, reason = output_sanitizer.validate(result.get("response", ""))
        if not is_valid:
            logger.warning(
                "output_validation_failed",
                reason=reason,
                agent=result.get("agent_used"),
                session_id=request.session_id,
            )
            save_guardrail_event(
                event_type="output_validation",
                stage="output",
                action="regenerated",
                message_preview=result.get("response", ""),
                session_id=request.session_id,
            )
            guardrails_applied.append("output_regenerated")
            result["response"] = (
                "Lo siento, hubo un problema generando la respuesta. "
                "¿Podrías reformular tu pregunta?"
            )

        # Sanitize output (mask DNI, phone numbers, sensitive data)
        result["response"] = output_sanitizer.sanitize(result.get("response", ""))
        guardrails_applied.append("output_sanitized")

    # Add guardrails info to workflow
    result["workflow_steps"] = result.get("workflow_steps", [])
    if guardrails_applied:
        result["workflow_steps"].insert(0, {
            "type": "guardrails",
            "data": {"applied": guardrails_applied, "stage": "pipeline"},
        })

    save_agent_call(
        session_id=request.session_id,
        trace_id=result.get("trace_id", ""),
        agent=result.get("agent_used", ""),
        intent=result.get("intent", ""),
        tools_used=result.get("tools_called", []),
        confidence=result.get("confidence", 0),
    )

    _persist_transactions_from_workflow(result.get("workflow_steps", []), request.session_id)

    return ChatResponse(
        **result,
        guardrails_applied=guardrails_applied,
    )


@router.post("/rag/query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest):
    """Direct query to the knowledge base."""
    try:
        results = await query_knowledge_base(
            query=request.query,
            top_k=request.top_k,
        )
        return RAGQueryResponse(results=results, query=request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query error: {str(e)}")


@router.get("/agents/status")
async def agents_status():
    """Get status of all agents in the system."""
    return {
        "agents": [
            {
                "name": "Supervisor",
                "role": "Router/Orchestrator",
                "status": "active",
                "description": "Routes messages to specialized agents based on intent",
            },
            {
                "name": "Energía",
                "role": "Energy Specialist",
                "status": "active",
                "description": "Handles energy comparisons, tariff analysis, contract management",
            },
            {
                "name": "Logística",
                "role": "Logistics Specialist",
                "status": "active",
                "description": "Manages packages, Amazon Hub, GLS operations",
            },
            {
                "name": "Soporte",
                "role": "Support & Catalog Specialist",
                "status": "active",
                "description": "RAG-powered support, recharges, product catalog queries",
            },
        ],
        "orchestrator": "LangGraph",
        "protocol": "MCP",
    }


# ============================================
# MCP Protocol Endpoints
# ============================================

@router.get("/mcp/servers")
async def mcp_list_servers():
    """
    MCP Discovery: List all registered MCP servers.
    Implements the server discovery aspect of the Model Context Protocol.
    """
    from mcp_servers.registry import get_mcp_registry
    registry = get_mcp_registry()
    return {
        "protocol": "MCP",
        "protocol_version": "2024-11-05",
        "servers": registry.list_servers(),
    }


@router.get("/mcp/tools")
async def mcp_list_tools(server: str = None):
    """
    MCP Protocol: tools/list
    List all available tools across MCP servers.
    Optionally filter by server name.
    """
    from mcp_servers.registry import get_mcp_registry
    registry = get_mcp_registry()
    return {
        "tools": registry.list_tools(server_name=server),
        "total": len(registry.list_tools(server_name=server)),
    }


@router.post("/mcp/tools/call")
async def mcp_call_tool(
    request: dict,
    x_mcp_client_id: str | None = Header(default=None),
    x_mcp_api_key: str | None = Header(default=None),
):
    """
    MCP Protocol: tools/call
    Invoke a tool on the appropriate MCP server.
    
    Body: {"tool_name": "...", "arguments": {...}}
    """
    from mcp_servers.client import get_mcp_client
    from database.mcp_ops import (
        check_mcp_rate_limit,
        get_tool_policy,
        is_tool_allowed_for_client,
        save_mcp_tool_audit,
        validate_mcp_client,
    )
    from time import perf_counter

    tool_name = request.get("tool_name")
    arguments = request.get("arguments", {})

    if not tool_name:
        raise HTTPException(status_code=400, detail="tool_name is required")

    client_id = request.get("client_id") or x_mcp_client_id or "internal-system"
    trace_id = request.get("trace_id", "")

    # External clients must be validated. Internal calls keep backward compatibility.
    if client_id != "internal-system":
        valid, reason, client_data = validate_mcp_client(client_id, x_mcp_api_key or "")
        if not valid:
            save_mcp_tool_audit(
                client_id=client_id,
                tool_name=tool_name,
                status="denied",
                latency_ms=0,
                transport="api",
                server="",
                trace_id=trace_id,
                error=reason,
            )
            raise HTTPException(status_code=401, detail={"error": "mcp_client_not_authorized", "reason": reason})

        if not is_tool_allowed_for_client(client_data or {}, tool_name):
            save_mcp_tool_audit(
                client_id=client_id,
                tool_name=tool_name,
                status="denied",
                latency_ms=0,
                transport="api",
                server="",
                trace_id=trace_id,
                error="tool_not_allowed",
            )
            raise HTTPException(status_code=403, detail={"error": "tool_not_allowed", "tool": tool_name})

        rate_limit = int((client_data or {}).get("rate_limit_per_minute", get_settings().rate_limit_per_minute))
        allowed, retry_after, current = check_mcp_rate_limit(client_id, rate_limit)
        if not allowed:
            save_mcp_tool_audit(
                client_id=client_id,
                tool_name=tool_name,
                status="throttled",
                latency_ms=0,
                transport="api",
                server="",
                trace_id=trace_id,
                error=f"rate_limit_exceeded:{current}/{rate_limit}",
            )
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "client_id": client_id,
                    "limit_per_minute": rate_limit,
                    "retry_after_seconds": retry_after,
                },
            )

    policy = get_tool_policy(tool_name) or {}
    timeout_ms = int(policy.get("timeout_ms", 8000))

    client = get_mcp_client()
    started = perf_counter()
    result = await client.call_tool(
        tool_name,
        arguments,
        client_id=client_id,
        trace_id=trace_id,
    )
    latency_ms = int((perf_counter() - started) * 1000)

    if latency_ms > timeout_ms:
        logger.warning(
            "mcp_tool_latency_above_policy",
            tool_name=tool_name,
            client_id=client_id,
            latency_ms=latency_ms,
            timeout_ms=timeout_ms,
        )

    if result.get("is_error"):
        detail = result.get("content") or {"error": result.get("error", "MCP tool execution failed")}
        raise HTTPException(status_code=500, detail=detail)

    return result


# ============================================
# Observability Endpoints
# ============================================

@router.get("/observability/status")
async def observability_status():
    """Get observability configuration status (LangSmith, logging)."""
    from observability.langsmith_config import get_langsmith_status
    return {
        "langsmith": get_langsmith_status(),
        "structured_logging": True,
        "guardrails_monitoring": True,
    }


# ============================================
# Memory/Session Endpoints
# ============================================

@router.get("/sessions")
async def list_sessions():
    """List all active conversation sessions."""
    from agents.memory import get_memory_store
    store = get_memory_store()
    return {"sessions": store.list_active_sessions()}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get info about a specific session."""
    from agents.memory import get_memory_store
    store = get_memory_store()
    return store.get_session_info(session_id)


@router.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation history and agent tracking for a session."""
    from agents.memory import get_memory_store
    from agents.graph import _session_last_agent
    store = get_memory_store()
    store.clear_session(session_id)
    _session_last_agent.pop(session_id, None)
    return {"status": "cleared", "session_id": session_id}


# ============================================
# Persistent Memory Endpoints
# ============================================

@router.get("/memories/{session_id}")
async def get_memories(session_id: str, memory_type: str = None, limit: int = 20):
    """Get persistent memories for a session."""
    from agents.persistent_memory import get_persistent_memory
    store = get_persistent_memory()
    store.load_from_db(session_id)
    memories = store.recall(
        session_id=session_id,
        memory_type=memory_type,
        limit=limit,
        min_relevance=0.1,
    )
    return {
        "session_id": session_id,
        "count": len(memories),
        "memories": memories,
    }


@router.get("/memories/{session_id}/summary")
async def get_memory_summary(session_id: str):
    """Get memory summary for a session."""
    from agents.persistent_memory import get_persistent_memory
    store = get_persistent_memory()
    store.load_from_db(session_id)
    return store.get_session_summary(session_id)


@router.post("/memories/{session_id}")
async def store_memory(session_id: str, request: dict):
    """Manually store a memory for a session."""
    from agents.persistent_memory import get_persistent_memory
    store = get_persistent_memory()
    memory_id = store.store(
        session_id=session_id,
        memory_type=request.get("memory_type", "preference"),
        content=request.get("content", ""),
        relevance=request.get("relevance", 0.7),
        metadata=request.get("metadata"),
    )
    return {"stored": True, "memory_id": memory_id}


@router.delete("/memories/{session_id}/{memory_id}")
async def forget_memory(session_id: str, memory_id: str):
    """Explicitly forget a specific memory."""
    from agents.persistent_memory import get_persistent_memory
    store = get_persistent_memory()
    success = store.forget(session_id=session_id, memory_id=memory_id)
    return {"forgotten": success, "memory_id": memory_id}
