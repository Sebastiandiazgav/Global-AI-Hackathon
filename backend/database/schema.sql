-- ============================================
-- MyAgent - Database Schema
-- PostgreSQL + pgvector
-- ============================================

-- Enable pgvector extension for RAG
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TRANSACTIONS (Core business data)
-- ============================================
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    type VARCHAR(50) NOT NULL DEFAULT '',
    tool_name VARCHAR(100) NOT NULL DEFAULT '',
    description TEXT DEFAULT '',
    commission NUMERIC(10,2) DEFAULT 0,
    amount NUMERIC(10,2) DEFAULT 0,
    agent VARCHAR(50) DEFAULT '',
    session_id VARCHAR(100) DEFAULT '',
    transport VARCHAR(50) DEFAULT '',
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);
CREATE INDEX idx_transactions_session_id ON transactions(session_id);
CREATE INDEX idx_transactions_type ON transactions(type);

-- ============================================
-- AGENT CALLS (Observability / Analytics)
-- ============================================
CREATE TABLE IF NOT EXISTS agent_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id VARCHAR(100) DEFAULT '',
    trace_id VARCHAR(100) DEFAULT '',
    agent VARCHAR(50) DEFAULT '',
    intent TEXT DEFAULT '',
    tools_used JSONB DEFAULT '[]'::jsonb,
    confidence NUMERIC(4,3) DEFAULT 0,
    response_time_ms INTEGER DEFAULT 0,
    language VARCHAR(10) DEFAULT 'es'
);

CREATE INDEX idx_agent_calls_created_at ON agent_calls(created_at DESC);
CREATE INDEX idx_agent_calls_agent ON agent_calls(agent);
CREATE INDEX idx_agent_calls_session_id ON agent_calls(session_id);

-- ============================================
-- GUARDRAIL EVENTS (Security monitoring)
-- ============================================
CREATE TABLE IF NOT EXISTS guardrail_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    event_type VARCHAR(50) DEFAULT '',
    stage VARCHAR(20) DEFAULT '',
    action VARCHAR(20) DEFAULT '',
    message_preview VARCHAR(200) DEFAULT '',
    session_id VARCHAR(100) DEFAULT '',
    category VARCHAR(50) DEFAULT ''
);

CREATE INDEX idx_guardrail_events_created_at ON guardrail_events(created_at DESC);
CREATE INDEX idx_guardrail_events_action ON guardrail_events(action);

-- ============================================
-- MCP CLIENTS (External client auth)
-- ============================================
CREATE TABLE IF NOT EXISTS mcp_clients (
    client_id VARCHAR(100) PRIMARY KEY,
    api_key VARCHAR(200) NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    allowed_tools JSONB DEFAULT '["*"]'::jsonb,
    rate_limit_per_minute INTEGER DEFAULT 60,
    description TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- MCP TOOL POLICIES (Per-tool configuration)
-- ============================================
CREATE TABLE IF NOT EXISTS mcp_tool_policies (
    tool_name VARCHAR(100) PRIMARY KEY,
    timeout_ms INTEGER DEFAULT 8000,
    max_retries INTEGER DEFAULT 2,
    requires_auth BOOLEAN DEFAULT FALSE,
    description TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- MCP TOOL AUDIT (Invocation log)
-- ============================================
CREATE TABLE IF NOT EXISTS mcp_tool_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    client_id VARCHAR(100) DEFAULT 'internal-system',
    tool_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT '',
    latency_ms INTEGER DEFAULT 0,
    transport VARCHAR(50) DEFAULT '',
    server VARCHAR(100) DEFAULT '',
    trace_id VARCHAR(100) DEFAULT '',
    error TEXT DEFAULT ''
);

CREATE INDEX idx_mcp_tool_audit_created_at ON mcp_tool_audit(created_at DESC);
CREATE INDEX idx_mcp_tool_audit_client_id ON mcp_tool_audit(client_id);
CREATE INDEX idx_mcp_tool_audit_tool_name ON mcp_tool_audit(tool_name);

-- ============================================
-- PERSISTENT MEMORIES (Cross-session memory)
-- ============================================
CREATE TABLE IF NOT EXISTS persistent_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id VARCHAR(100) NOT NULL,
    memory_type VARCHAR(50) NOT NULL,
    -- Types: preference, pattern, client_info, service_history, insight
    content TEXT NOT NULL,
    relevance NUMERIC(4,3) DEFAULT 0.5,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '90 days'),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_persistent_memories_session_id ON persistent_memories(session_id);
CREATE INDEX idx_persistent_memories_type ON persistent_memories(memory_type);
CREATE INDEX idx_persistent_memories_relevance ON persistent_memories(relevance DESC);
CREATE INDEX idx_persistent_memories_expires ON persistent_memories(expires_at);

-- ============================================
-- DOCUMENT EMBEDDINGS (RAG with pgvector)
-- ============================================
CREATE TABLE IF NOT EXISTS document_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    content TEXT NOT NULL,
    source VARCHAR(200) DEFAULT '',
    chunk_index INTEGER DEFAULT 0,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_document_embeddings_source ON document_embeddings(source);
-- HNSW index for fast similarity search
CREATE INDEX idx_document_embeddings_vector ON document_embeddings 
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- ============================================
-- SOCIETY DEBATES (Agent Society history)
-- ============================================
CREATE TABLE IF NOT EXISTS society_debates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id VARCHAR(100) DEFAULT '',
    query TEXT NOT NULL,
    participants JSONB DEFAULT '[]'::jsonb,
    rounds JSONB DEFAULT '[]'::jsonb,
    consensus TEXT DEFAULT '',
    action_plan JSONB DEFAULT '[]'::jsonb,
    metrics JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_society_debates_session_id ON society_debates(session_id);
CREATE INDEX idx_society_debates_created_at ON society_debates(created_at DESC);
