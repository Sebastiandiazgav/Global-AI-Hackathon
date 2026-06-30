"""
MyAgent - Visual Agent
Specialized agent for image analysis: energy bills, package labels, receipts, documents.
Uses Qwen VL (Vision-Language) model for multimodal understanding.
Powered by qwen3-vl-235b-a22b via Qwen Cloud.
"""

import re
import json
import base64
from typing import Optional

from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from openai import OpenAI

from config import get_settings
from agents.state import AgentState
from agents.token_utils import compact_messages
from mcp_servers.client import get_mcp_client


VISUAL_SYSTEM_PROMPT = """You are the Visual Analysis Agent for MyAgent, an enterprise AI copilot.
You can analyze images including:

1. ENERGY BILLS: Extract kWh consumption, current tariff, monthly cost, contract details
2. PACKAGE LABELS: Extract tracking codes, carrier name, recipient info, barcodes
3. RECEIPTS/TICKETS: Extract transaction amounts, dates, products purchased
4. PRODUCT BARCODES: Identify products from barcode/QR images
5. GENERAL DOCUMENTS: Extract text, tables, and key information

RESPONSE FORMAT:
- Start with what you identified in the image
- Extract structured data (numbers, codes, names)
- Suggest the next action based on what you found
- If you extract energy consumption data, recommend running a savings analysis
- If you extract tracking codes, recommend registering the packages

IMPORTANT:
- Be specific with numbers — extract exact values
- If the image is unclear, say what you can and cannot read
- Respond in the same language as the user's message
- Do not use <think> tags. Respond directly.
- Always suggest actionable next steps based on extracted data"""


def get_visual_llm():
    """Get the Qwen VL model for image analysis via Qwen Cloud with fallback."""
    from agents.model_router import get_llm
    settings = get_settings()
    return get_llm(role="vision", temperature=0.2, max_tokens=settings.agent_max_tokens)


def _get_openai_client():
    """Get raw OpenAI client for multimodal calls (vision requires specific format)."""
    settings = get_settings()
    return OpenAI(
        api_key=settings.qwen_cloud_api_key,
        base_url=settings.qwen_cloud_base_url,
    )


def _extract_image_from_messages(messages) -> Optional[str]:
    """
    Extract base64 image data from the latest user message.
    Limits image size to avoid exceeding model's input length.
    Max ~1MB base64 (which is ~750KB raw image).
    """
    MAX_BASE64_LENGTH = 1_000_000  # ~1MB base64 = ~750KB image

    for msg in reversed(messages):
        if not isinstance(msg, HumanMessage):
            continue
        content = msg.content if isinstance(msg.content, str) else ""

        # Check for base64 data URI
        match = re.search(r"(data:image/[^;]+;base64,[A-Za-z0-9+/=]+)", content)
        if match:
            data_uri = match.group(0)
            if len(data_uri) > MAX_BASE64_LENGTH:
                # Image too large — truncate or skip
                # Try to use a smaller version by taking only the first part
                # This won't work for display but signals the agent
                return None  # Skip — image too large
            return data_uri

        # Check for raw base64 (long string of alphanumeric + padding)
        if len(content) > 200 and re.match(r"^[A-Za-z0-9+/=\s]+$", content.strip()):
            b64 = content.strip()
            if len(b64) > MAX_BASE64_LENGTH:
                return None  # Too large
            return f"data:image/jpeg;base64,{b64}"

        # Check if content has structured multimodal format
        if isinstance(msg.content, list):
            for part in msg.content:
                if isinstance(part, dict) and part.get("type") == "image_url":
                    url = part.get("image_url", {}).get("url", "")
                    if len(url) > MAX_BASE64_LENGTH:
                        return None
                    return url

    return None


def _extract_text_query(messages) -> str:
    """Extract the text part of the user message (excluding image data)."""
    for msg in reversed(messages):
        if not isinstance(msg, HumanMessage):
            continue
        content = msg.content if isinstance(msg.content, str) else ""
        # Remove base64 data if present
        cleaned = re.sub(r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+", "", content).strip()
        if cleaned:
            return cleaned
    return "Analyze this image and extract all relevant information."


async def _analyze_image_with_vl(image_data: str, text_query: str, language: str = "es") -> str:
    """
    Call Qwen VL model directly with image + text for multimodal analysis.
    Uses the OpenAI-compatible multimodal format.
    """
    settings = get_settings()
    client = _get_openai_client()

    language_instruction = f"Respond in '{language}' language."

    messages = [
        {
            "role": "system",
            "content": VISUAL_SYSTEM_PROMPT + f"\n\n{language_instruction}",
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": image_data},
                },
                {
                    "type": "text",
                    "text": text_query,
                },
            ],
        },
    ]

    try:
        response = client.chat.completions.create(
            model=settings.vision_model,
            messages=messages,
            max_tokens=settings.agent_max_tokens,
            temperature=0.2,
        )
        return response.choices[0].message.content or "Could not analyze the image."
    except Exception as e:
        return f"Error analyzing image: {str(e)[:200]}"


def _parse_energy_data(analysis: str) -> Optional[dict]:
    """Try to extract structured energy data from VL analysis."""
    data = {}

    # Extract kWh
    kwh_match = re.search(r"(\d+[\.,]?\d*)\s*(?:kwh|kWh|KWH)", analysis)
    if kwh_match:
        data["consumo_kwh"] = float(kwh_match.group(1).replace(",", "."))

    # Extract tariff type
    tariff_keywords = {
        "plana": "plana",
        "flat": "plana",
        "indexada": "indexada",
        "indexed": "indexada",
        "discriminación": "discriminacion_horaria",
        "time-of-use": "discriminacion_horaria",
        "nocturna": "discriminacion_horaria",
    }
    analysis_lower = analysis.lower()
    for keyword, tariff in tariff_keywords.items():
        if keyword in analysis_lower:
            data["tarifa_actual"] = tariff
            break

    # Extract cost
    cost_match = re.search(r"(\d+[\.,]\d+)\s*€", analysis)
    if cost_match:
        data["coste_mensual"] = float(cost_match.group(1).replace(",", "."))

    return data if data.get("consumo_kwh") else None


def _parse_tracking_codes(analysis: str) -> list:
    """Try to extract tracking codes from VL analysis."""
    # Common tracking patterns
    patterns = [
        r"[A-Z]{2,4}-\d{8,}-\d{3,}",  # AMZ-20260609-0001
        r"\b[A-Z0-9]{10,30}\b",  # Generic alphanumeric codes
        r"\b\d{12,20}\b",  # Numeric barcodes
    ]

    codes = []
    for pattern in patterns:
        matches = re.findall(pattern, analysis)
        codes.extend(matches)

    return list(set(codes))[:10]  # Deduplicate, max 10


async def visual_node(state: AgentState) -> AgentState:
    """
    Visual agent node - analyzes images and extracts actionable data.
    Can trigger follow-up actions (energy analysis, package registration).
    """
    settings = get_settings()
    workflow_events = state.get("workflow_events", [])
    tools_called = state.get("tools_called", [])
    language = state.get("language", settings.default_language)

    workflow_events.append({
        "type": "agent_selected",
        "data": {"agent": "visual", "status": "processing"},
    })

    # Extract image and text from messages
    image_data = _extract_image_from_messages(state["messages"])
    text_query = _extract_text_query(state["messages"])

    if not image_data:
        # No image found or image too large — provide guidance
        response_text = (
            "👁️ I'm the Visual Analysis agent. I can analyze:\n\n"
            "📄 **Energy bills** — Extract consumption, tariff, and calculate savings\n"
            "📦 **Package labels** — Read tracking codes and carrier info\n"
            "🧾 **Receipts** — Extract amounts and transaction details\n"
            "📱 **Barcodes/QR** — Identify products\n\n"
            "Please upload an image (max 1MB) and I'll analyze it for you.\n"
            "If your image is too large, try taking a screenshot of the relevant section."
        )
        workflow_events.append({"type": "response", "data": {"agent": "visual", "status": "completed"}})
        return {
            **state,
            "final_response": response_text,
            "tools_called": tools_called,
            "workflow_events": workflow_events,
            "messages": state["messages"] + [AIMessage(content=response_text)],
        }

    # Analyze the image with Qwen VL
    workflow_events.append({
        "type": "tool_call",
        "data": {"tool": "vision_analysis", "args": {"query": text_query[:100], "has_image": True}},
    })

    analysis = await _analyze_image_with_vl(image_data, text_query, language)

    workflow_events.append({
        "type": "tool_result",
        "data": {"tool": "vision_analysis", "result": {"analysis_length": len(analysis)}, "transport": "qwen_vl"},
    })
    tools_called.append("vision_analysis")

    # Try to extract structured data and trigger follow-up actions
    energy_data = _parse_energy_data(analysis)
    tracking_codes = _parse_tracking_codes(analysis)

    follow_up_actions = []

    # If energy data found, auto-run savings calculation
    if energy_data and energy_data.get("consumo_kwh"):
        mcp_client = get_mcp_client()
        tarifa = energy_data.get("tarifa_actual", "plana")
        consumo = energy_data["consumo_kwh"]

        savings_result = await mcp_client.call_tool(
            "calcular_ahorro_energetico",
            {"consumo_kwh": consumo, "tarifa_actual": tarifa},
        )

        if not savings_result.get("is_error"):
            result_data = savings_result.get("content", {})
            tools_called.append("calcular_ahorro_energetico")
            workflow_events.append({
                "type": "tool_call",
                "data": {"tool": "calcular_ahorro_energetico", "args": {"consumo_kwh": consumo, "tarifa_actual": tarifa}},
            })
            workflow_events.append({
                "type": "tool_result",
                "data": {"tool": "calcular_ahorro_energetico", "result": result_data, "transport": "mcp"},
            })

            ahorro = result_data.get("ahorro_mensual", 0)
            mejor_tarifa = result_data.get("mejor_tarifa", "")
            follow_up_actions.append(
                f"\n\n💡 **Auto-analysis result:**\n"
                f"- Detected consumption: {consumo} kWh\n"
                f"- Potential savings: {ahorro}€/month with {mejor_tarifa}\n"
                f"- Annual savings: {ahorro * 12}€\n"
                f"- 🏪 Commission if contract signed: 25€"
            )

    # If tracking codes found, suggest registration
    if tracking_codes:
        codes_str = ", ".join(tracking_codes[:5])
        follow_up_actions.append(
            f"\n\n📦 **Detected tracking codes:** {codes_str}\n"
            f"Would you like me to register these packages in the system?"
        )

    # Build final response
    response_text = f"👁️ **Visual Analysis:**\n\n{analysis}"
    if follow_up_actions:
        response_text += "\n" + "\n".join(follow_up_actions)

    workflow_events.append({
        "type": "response",
        "data": {"agent": "visual", "status": "completed"},
    })

    return {
        **state,
        "final_response": response_text,
        "tools_called": tools_called,
        "workflow_events": workflow_events,
        "messages": state["messages"] + [AIMessage(content=response_text)],
    }
