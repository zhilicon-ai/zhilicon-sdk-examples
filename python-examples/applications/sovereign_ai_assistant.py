"""
Zhilicon Example - Sovereign AI Assistant
==========================================
Complete AI assistant with sovereignty: conversation management, RAG for
knowledge base, tool calling (calculator, database query), session memory,
sovereignty enforcement on all interactions.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolType(Enum):
    CALCULATOR = "calculator"
    DATABASE = "database"
    KNOWLEDGE = "knowledge"
    SEARCH = "search"


class SessionStatus(Enum):
    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class SovereigntyLevel(Enum):
    STRICT = "strict"
    MODERATE = "moderate"
    RELAXED = "relaxed"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Message:
    role: MessageRole
    content: str
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: float = field(default_factory=time.time)
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[str] = None
    zone_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Conversation:
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    messages: List[Message] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    zone_id: str = ""
    user_id: str = ""
    title: str = ""
    summary: str = ""

    def add_message(self, msg: Message) -> None:
        msg.zone_id = self.zone_id
        self.messages.append(msg)
        self.updated_at = time.time()

    @property
    def length(self) -> int:
        return len(self.messages)

    def get_context_window(self, max_messages: int = 20) -> List[Message]:
        return self.messages[-max_messages:]


@dataclass
class KnowledgeDocument:
    doc_id: str = field(default_factory=lambda: str(uuid.uuid4())[:10])
    title: str = ""
    content: str = ""
    source: str = ""
    zone_id: str = ""
    embedding: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDefinition:
    name: str
    description: str
    tool_type: ToolType
    parameters: Dict[str, Any] = field(default_factory=dict)
    zone_restricted: bool = True


@dataclass
class SessionMemory:
    session_id: str
    user_id: str
    facts: List[str] = field(default_factory=list)
    preferences: Dict[str, str] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def add_fact(self, fact: str) -> None:
        if fact not in self.facts:
            self.facts.append(fact)
            if len(self.facts) > 100:
                self.facts = self.facts[-50:]

    def set_preference(self, key: str, value: str) -> None:
        self.preferences[key] = value


@dataclass
class AssistantConfig:
    zone_id: str = "eu-sovereign"
    model_name: str = "zhilicon-assistant-7b"
    max_context_messages: int = 20
    max_response_tokens: int = 2048
    temperature: float = 0.7
    sovereignty_level: SovereigntyLevel = SovereigntyLevel.STRICT
    enable_tools: bool = True
    enable_rag: bool = True
    session_timeout_s: float = 3600.0
    system_prompt: str = "You are a helpful sovereign AI assistant."


# ---------------------------------------------------------------------------
# Simple embedding (demo)
# ---------------------------------------------------------------------------

def _embed(text: str, dim: int = 64) -> List[float]:
    h = hashlib.sha256(text.lower().encode()).digest()
    vec = [(h[i % len(h)] + i) / 255.0 - 0.5 for i in range(dim)]
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: List[float], b: List[float]) -> float:
    d = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return d / (na * nb)


# ---------------------------------------------------------------------------
# RAG knowledge base
# ---------------------------------------------------------------------------

class RAGKnowledgeBase:
    """Vector-based knowledge retrieval within sovereign boundary."""

    def __init__(self, zone_id: str = "", embedding_dim: int = 64):
        self.zone_id = zone_id
        self._dim = embedding_dim
        self._docs: Dict[str, KnowledgeDocument] = {}

    def add_document(self, doc: KnowledgeDocument) -> str:
        doc.zone_id = self.zone_id
        doc.embedding = _embed(f"{doc.title} {doc.content}", self._dim)
        self._docs[doc.doc_id] = doc
        return doc.doc_id

    def add_documents(self, docs: List[KnowledgeDocument]) -> List[str]:
        return [self.add_document(d) for d in docs]

    def search(self, query: str, top_k: int = 3) -> List[Tuple[KnowledgeDocument, float]]:
        qvec = _embed(query, self._dim)
        scored = [(doc, _cosine(qvec, doc.embedding)) for doc in self._docs.values()]
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]

    def get_context(self, query: str, top_k: int = 3, max_chars: int = 2000) -> str:
        results = self.search(query, top_k)
        parts = []
        total = 0
        for doc, score in results:
            chunk = f"[{doc.title}] {doc.content}"
            if total + len(chunk) > max_chars:
                chunk = chunk[:max_chars - total]
            parts.append(chunk)
            total += len(chunk)
            if total >= max_chars:
                break
        return "\n\n".join(parts)

    @property
    def size(self) -> int:
        return len(self._docs)


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

class CalculatorTool:
    """Safe math expression evaluator."""

    NAME = "calculator"
    DESCRIPTION = "Evaluate mathematical expressions"

    def evaluate(self, expression: str) -> str:
        try:
            safe_dict = {"__builtins__": {}}
            safe_dict.update({
                "abs": abs, "round": round, "min": min, "max": max,
                "sqrt": math.sqrt, "log": math.log, "log10": math.log10,
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "pi": math.pi, "e": math.e, "pow": pow,
            })
            result = eval(expression, safe_dict)  # noqa: S307
            return str(result)
        except Exception as exc:
            return f"Error: {exc}"


class DatabaseQueryTool:
    """Simulated sovereign database query tool."""

    NAME = "database"
    DESCRIPTION = "Query the sovereign database"

    def __init__(self, zone_id: str = ""):
        self.zone_id = zone_id
        self._tables: Dict[str, List[Dict[str, Any]]] = {
            "users": [
                {"id": 1, "name": "Alice", "department": "Engineering", "role": "Senior"},
                {"id": 2, "name": "Bob", "department": "Marketing", "role": "Manager"},
                {"id": 3, "name": "Carol", "department": "Engineering", "role": "Lead"},
                {"id": 4, "name": "Dave", "department": "Sales", "role": "Associate"},
                {"id": 5, "name": "Eve", "department": "Engineering", "role": "Junior"},
            ],
            "metrics": [
                {"date": "2024-01-15", "revenue": 150000, "users": 1200},
                {"date": "2024-02-15", "revenue": 175000, "users": 1350},
                {"date": "2024-03-15", "revenue": 190000, "users": 1500},
            ],
        }

    def query(self, sql: str) -> str:
        sql_lower = sql.lower().strip()
        if "select" not in sql_lower:
            return "Only SELECT queries are permitted"
        for table_name, rows in self._tables.items():
            if table_name in sql_lower:
                if "where" in sql_lower:
                    parts = sql_lower.split("where")
                    if len(parts) > 1:
                        cond = parts[1].strip().rstrip(";")
                        filtered = self._filter_rows(rows, cond)
                        return json.dumps(filtered, indent=2)
                if "count" in sql_lower:
                    return json.dumps({"count": len(rows)})
                return json.dumps(rows, indent=2)
        return "Table not found"

    def _filter_rows(self, rows: List[Dict], cond: str) -> List[Dict]:
        parts = re.split(r"\s*=\s*", cond)
        if len(parts) != 2:
            return rows
        col = parts[0].strip().strip("'\"")
        val = parts[1].strip().strip("'\"")
        return [r for r in rows if str(r.get(col, "")).lower() == val.lower()]


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

class ToolRegistry:
    """Manages available tools with sovereignty enforcement."""

    def __init__(self, zone_id: str = ""):
        self.zone_id = zone_id
        self._tools: Dict[str, Any] = {}
        self._definitions: Dict[str, ToolDefinition] = {}

    def register(self, defn: ToolDefinition, impl: Any) -> None:
        self._definitions[defn.name] = defn
        self._tools[defn.name] = impl

    def call(self, tool_name: str, args: Dict[str, Any]) -> str:
        if tool_name not in self._tools:
            return f"Unknown tool: {tool_name}"
        defn = self._definitions[tool_name]
        if defn.zone_restricted:
            logger.info("Tool %s running in zone %s", tool_name, self.zone_id)
        impl = self._tools[tool_name]
        if tool_name == "calculator":
            return impl.evaluate(args.get("expression", ""))
        if tool_name == "database":
            return impl.query(args.get("query", ""))
        return "Tool executed"

    def list_tools(self) -> List[Dict[str, str]]:
        return [{"name": d.name, "description": d.description,
                 "type": d.tool_type.value}
                for d in self._definitions.values()]


# ---------------------------------------------------------------------------
# Session manager
# ---------------------------------------------------------------------------

class SessionManager:
    """Manages user sessions with memory and sovereignty."""

    def __init__(self, zone_id: str = "", timeout_s: float = 3600.0):
        self.zone_id = zone_id
        self._timeout = timeout_s
        self._sessions: Dict[str, SessionMemory] = {}
        self._conversations: Dict[str, Conversation] = {}

    def get_or_create_session(self, user_id: str) -> SessionMemory:
        sid = f"{user_id}:{self.zone_id}"
        if sid not in self._sessions:
            self._sessions[sid] = SessionMemory(session_id=sid, user_id=user_id)
        return self._sessions[sid]

    def get_or_create_conversation(self, user_id: str,
                                    conv_id: Optional[str] = None) -> Conversation:
        if conv_id and conv_id in self._conversations:
            return self._conversations[conv_id]
        conv = Conversation(user_id=user_id, zone_id=self.zone_id)
        if conv_id:
            conv.conversation_id = conv_id
        self._conversations[conv.conversation_id] = conv
        return conv

    def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        return [
            {"id": c.conversation_id, "title": c.title,
             "length": c.length, "updated": c.updated_at}
            for c in self._conversations.values()
            if c.user_id == user_id
        ]

    def cleanup_expired(self) -> int:
        now = time.time()
        expired = [sid for sid, s in self._sessions.items()
                   if (now - s.created_at) > self._timeout]
        for sid in expired:
            self._sessions.pop(sid, None)
        return len(expired)


# ---------------------------------------------------------------------------
# Sovereignty enforcer
# ---------------------------------------------------------------------------

class SovereigntyEnforcer:
    """Ensures all operations stay within sovereign boundaries."""

    def __init__(self, zone_id: str, level: SovereigntyLevel = SovereigntyLevel.STRICT):
        self.zone_id = zone_id
        self.level = level
        self._blocked_domains = ["external-api.com", "non-sovereign.net"]
        self._audit: List[Dict[str, Any]] = []

    def check_request(self, user_id: str, content: str) -> Tuple[bool, str]:
        for domain in self._blocked_domains:
            if domain in content.lower():
                self._log("blocked_domain", user_id, domain)
                if self.level == SovereigntyLevel.STRICT:
                    return False, f"Blocked: reference to external domain {domain}"
        self._log("request_allowed", user_id, "")
        return True, ""

    def check_response(self, response: str) -> Tuple[bool, str]:
        if len(response) > 50000:
            return False, "Response exceeds maximum size"
        return True, ""

    def check_tool_call(self, tool_name: str, args: Dict[str, Any]) -> Tuple[bool, str]:
        self._log("tool_call", "", f"{tool_name}")
        return True, ""

    def _log(self, action: str, user: str, detail: str) -> None:
        self._audit.append({
            "timestamp": time.time(), "zone": self.zone_id,
            "action": action, "user": user, "detail": detail,
        })

    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._audit[-limit:]


# ---------------------------------------------------------------------------
# Response generator (simulated LLM)
# ---------------------------------------------------------------------------

class SimulatedLLM:
    """Simulates LLM response generation for demo purposes."""

    def __init__(self, model_name: str = "zhilicon-7b"):
        self.model_name = model_name

    def generate(self, messages: List[Message],
                 context: str = "", temperature: float = 0.7) -> str:
        last = messages[-1] if messages else None
        if not last:
            return "I'm ready to help. What would you like to know?"
        query = last.content.lower()
        if "hello" in query or "hi" in query:
            return "Hello! I'm your sovereign AI assistant. How can I help?"
        if "what can you do" in query or "capabilities" in query:
            return ("I can help with calculations, database queries, and "
                    "knowledge retrieval -- all within your sovereign zone.")
        if context:
            return f"Based on the knowledge base: {context[:300]}..."
        if "calculate" in query or "math" in query:
            return "I can help with calculations. Please provide the expression."
        return (f"I understand your question about '{last.content[:50]}'. "
                "Let me help you with that within our sovereign boundary.")


# ---------------------------------------------------------------------------
# Sovereign AI Assistant
# ---------------------------------------------------------------------------

class SovereignAIAssistant:
    """Full sovereign AI assistant with tools, RAG, and session management."""

    def __init__(self, config: Optional[AssistantConfig] = None):
        self.config = config or AssistantConfig()
        self.zone_id = self.config.zone_id
        self._llm = SimulatedLLM(self.config.model_name)
        self._kb = RAGKnowledgeBase(self.zone_id)
        self._tools = ToolRegistry(self.zone_id)
        self._sessions = SessionManager(self.zone_id, self.config.session_timeout_s)
        self._enforcer = SovereigntyEnforcer(self.zone_id, self.config.sovereignty_level)
        self._setup_tools()

    def _setup_tools(self) -> None:
        self._tools.register(
            ToolDefinition("calculator", "Evaluate math", ToolType.CALCULATOR),
            CalculatorTool())
        self._tools.register(
            ToolDefinition("database", "Query database", ToolType.DATABASE),
            DatabaseQueryTool(self.zone_id))

    def add_knowledge(self, docs: List[KnowledgeDocument]) -> int:
        return len(self._kb.add_documents(docs))

    def chat(self, user_id: str, message: str,
             conversation_id: Optional[str] = None) -> Dict[str, Any]:
        ok, reason = self._enforcer.check_request(user_id, message)
        if not ok:
            return {"error": reason, "zone_id": self.zone_id}
        session = self._sessions.get_or_create_session(user_id)
        conv = self._sessions.get_or_create_conversation(user_id, conversation_id)
        user_msg = Message(role=MessageRole.USER, content=message)
        conv.add_message(user_msg)
        tool_result = self._check_tool_call(message) if self.config.enable_tools else None
        if tool_result:
            tool_msg = Message(role=MessageRole.TOOL, content=tool_result["result"],
                               tool_name=tool_result["tool"])
            conv.add_message(tool_msg)
        rag_context = ""
        if self.config.enable_rag and self._kb.size > 0:
            rag_context = self._kb.get_context(message)
        context_msgs = conv.get_context_window(self.config.max_context_messages)
        response_text = self._llm.generate(
            context_msgs, context=rag_context, temperature=self.config.temperature)
        if tool_result:
            response_text = f"{response_text}\n\nTool result: {tool_result['result']}"
        ok, reason = self._enforcer.check_response(response_text)
        if not ok:
            response_text = f"[Filtered: {reason}]"
        asst_msg = Message(role=MessageRole.ASSISTANT, content=response_text)
        conv.add_message(asst_msg)
        session.add_fact(f"User asked about: {message[:80]}")
        return {
            "response": response_text,
            "conversation_id": conv.conversation_id,
            "message_id": asst_msg.message_id,
            "zone_id": self.zone_id,
            "tool_used": tool_result["tool"] if tool_result else None,
            "rag_used": bool(rag_context),
        }

    def _check_tool_call(self, message: str) -> Optional[Dict[str, Any]]:
        lower = message.lower()
        if any(kw in lower for kw in ["calculate", "compute", "what is", "solve"]):
            expr = re.sub(r"^.*?([\d\.\+\-\*/\(\)\s\^]+).*$", r"\1", message).strip()
            if expr and any(c.isdigit() for c in expr):
                ok, _ = self._enforcer.check_tool_call("calculator", {"expression": expr})
                if ok:
                    result = self._tools.call("calculator", {"expression": expr})
                    return {"tool": "calculator", "result": result}
        if "select" in lower:
            ok, _ = self._enforcer.check_tool_call("database", {"query": message})
            if ok:
                result = self._tools.call("database", {"query": message})
                return {"tool": "database", "result": result}
        return None

    def get_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        return self._sessions.list_conversations(user_id)

    def get_audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._enforcer.get_audit_log(limit)

    def get_status(self) -> Dict[str, Any]:
        return {
            "zone_id": self.zone_id,
            "model": self.config.model_name,
            "sovereignty": self.config.sovereignty_level.value,
            "knowledge_docs": self._kb.size,
            "tools": self._tools.list_tools(),
        }


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def run_demo() -> None:
    assistant = SovereignAIAssistant(AssistantConfig(zone_id="eu-sovereign"))
    assistant.add_knowledge([
        KnowledgeDocument(title="Sovereignty Policy",
                          content="All data must remain within the EU sovereign zone. "
                                  "No data transfers to non-EU jurisdictions."),
        KnowledgeDocument(title="Model Catalog",
                          content="Zhilicon offers 7B, 13B, and 70B parameter models "
                                  "optimized for sovereign inference on Zhipu chips."),
    ])
    queries = [
        "Hello! What can you do?",
        "Calculate 42 * 17 + 3.14",
        "Tell me about sovereignty policy",
        "SELECT * FROM users WHERE department = 'Engineering'",
    ]
    for q in queries:
        resp = assistant.chat("user_01", q)
        logger.info("Q: %s\nA: %s\n", q, resp["response"][:200])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_demo()
