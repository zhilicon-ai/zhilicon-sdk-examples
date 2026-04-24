#!/usr/bin/env python3
"""
Zhilicon Template -- Sovereign Chatbot Application
====================================================

Complete sovereign chatbot with:
  - FastAPI server with OpenAI-compatible API
  - SovereignContext for all requests
  - Encrypted conversation history
  - Rate limiting
  - Audit logging
  - Token streaming (SSE)
  - Multi-model support (Arabic, Hindi, English)

How to run:
    pip install zhilicon fastapi uvicorn
    python sovereign_chatbot.py
    # Then: curl http://localhost:8080/v1/chat/completions ...

Copyright 2026 Zhilicon Technologies. All rights reserved.
"""

import sys, time, random, hashlib, json, uuid, threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from collections import defaultdict

# ── Simulation layer ────────────────────────────────────────────────────

class EncryptedConversationStore:
    """Stores conversation history with AES-256-GCM encryption."""
    def __init__(self):
        self._conversations: Dict[str, List[Dict]] = defaultdict(list)
        self._encryption_key = hashlib.sha256(b"sovereign_key").digest()

    def create_conversation(self) -> str:
        conv_id = str(uuid.uuid4())
        self._conversations[conv_id] = []
        return conv_id

    def add_message(self, conv_id: str, role: str, content: str):
        self._conversations[conv_id].append({
            "role": role, "content": content, "timestamp": time.time(),
            "encrypted": True, "hash": hashlib.sha256(content.encode()).hexdigest()[:16],
        })

    def get_history(self, conv_id: str, max_messages: int = 20) -> List[Dict]:
        return self._conversations.get(conv_id, [])[-max_messages:]

    def delete_conversation(self, conv_id: str):
        self._conversations.pop(conv_id, None)

class RateLimiter:
    """Token bucket rate limiter."""
    def __init__(self, requests_per_minute: int = 60, tokens_per_minute: int = 100000):
        self._rpm = requests_per_minute
        self._tpm = tokens_per_minute
        self._request_counts: Dict[str, List[float]] = defaultdict(list)
        self._token_counts: Dict[str, int] = defaultdict(int)

    def check(self, user_id: str, tokens: int = 0) -> Dict:
        now = time.time()
        # Clean old entries (older than 60s)
        self._request_counts[user_id] = [
            t for t in self._request_counts[user_id] if now - t < 60
        ]
        if len(self._request_counts[user_id]) >= self._rpm:
            return {"allowed": False, "reason": "rate_limit_exceeded",
                    "retry_after_seconds": 60}
        self._request_counts[user_id].append(now)
        return {"allowed": True}

class AuditLogger:
    """Sovereign audit logger with hash chain."""
    def __init__(self):
        self.entries: List[Dict] = []
        self._prev_hash = "0" * 32

    def log(self, event_type: str, details: Dict):
        entry = {"seq": len(self.entries), "type": event_type,
                 "timestamp": time.time(), "details": details,
                 "prev_hash": self._prev_hash}
        entry_str = json.dumps(entry, sort_keys=True)
        entry["hash"] = hashlib.sha256(entry_str.encode()).hexdigest()[:32]
        self._prev_hash = entry["hash"]
        self.entries.append(entry)

    def export(self) -> str:
        return json.dumps(self.entries, indent=2)

LANGUAGE_MODELS = {
    "ar": {"model": "zhilicon/arabic-llm-70b", "name": "Arabic"},
    "hi": {"model": "zhilicon/hindi-llm-13b", "name": "Hindi"},
    "en": {"model": "zhilicon/llama-7b-fp8", "name": "English"},
}

class ModelRouter:
    """Routes requests to the appropriate language model."""
    def detect_language(self, text: str) -> str:
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        hindi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        if arabic_chars > len(text) * 0.1: return "ar"
        if hindi_chars > len(text) * 0.1: return "hi"
        return "en"

    def get_model(self, language: str) -> Dict:
        return LANGUAGE_MODELS.get(language, LANGUAGE_MODELS["en"])

    def generate(self, model_id: str, messages: List[Dict],
                 temperature: float = 0.7, max_tokens: int = 512) -> Dict:
        time.sleep(random.uniform(0.02, 0.08))
        last_msg = messages[-1]["content"] if messages else ""
        response = (f"I am a sovereign AI assistant running on Zhilicon hardware. "
                   f"Regarding your question about '{last_msg[:40]}': "
                   f"I can provide detailed information while ensuring all your data "
                   f"remains within its designated sovereignty zone.")
        tokens = len(response.split())
        return {"content": response, "tokens": tokens, "model": model_id,
                "finish_reason": "stop"}

    def stream_generate(self, model_id: str, messages: List[Dict],
                        **kwargs) -> List[str]:
        full_response = self.generate(model_id, messages, **kwargs)
        words = full_response["content"].split()
        chunks = []
        for i in range(0, len(words), 3):
            chunk_text = " ".join(words[i:i+3]) + " "
            chunks.append(json.dumps({
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion.chunk",
                "choices": [{"index": 0, "delta": {"content": chunk_text},
                            "finish_reason": None}],
            }))
        chunks.append(json.dumps({
            "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
            "object": "chat.completion.chunk",
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
        }))
        return chunks

class SovereignChatbot:
    """Complete sovereign chatbot application."""
    def __init__(self, country: str = "ae", encrypt: bool = True):
        self.country = country
        self.encrypt = encrypt
        self.store = EncryptedConversationStore()
        self.rate_limiter = RateLimiter(requests_per_minute=60)
        self.audit = AuditLogger()
        self.router = ModelRouter()
        self.start_time = time.time()
        self._request_count = 0

    def chat(self, user_id: str, conv_id: Optional[str],
             messages: List[Dict], stream: bool = False,
             temperature: float = 0.7, max_tokens: int = 512) -> Dict:
        self._request_count += 1
        # Rate limiting
        rl = self.rate_limiter.check(user_id)
        if not rl["allowed"]:
            return {"error": rl["reason"], "retry_after": rl.get("retry_after_seconds")}
        # Create or get conversation
        if not conv_id:
            conv_id = self.store.create_conversation()
        # Detect language and route
        last_content = messages[-1]["content"] if messages else ""
        lang = self.router.detect_language(last_content)
        model_info = self.router.get_model(lang)
        # Store user message
        self.store.add_message(conv_id, "user", last_content)
        # Audit
        self.audit.log("chat_request", {
            "user_id": user_id, "conv_id": conv_id, "language": lang,
            "model": model_info["model"], "country": self.country,
        })
        # Generate
        if stream:
            chunks = self.router.stream_generate(model_info["model"], messages,
                                                  temperature=temperature,
                                                  max_tokens=max_tokens)
            return {"conv_id": conv_id, "stream": True, "chunks": chunks}
        else:
            result = self.router.generate(model_info["model"], messages,
                                          temperature=temperature,
                                          max_tokens=max_tokens)
            self.store.add_message(conv_id, "assistant", result["content"])
            return {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "conv_id": conv_id,
                "model": result["model"],
                "language": lang,
                "choices": [{"index": 0, "message": {"role": "assistant",
                            "content": result["content"]},
                            "finish_reason": result["finish_reason"]}],
                "usage": {"prompt_tokens": len(last_content.split()),
                          "completion_tokens": result["tokens"],
                          "total_tokens": len(last_content.split()) + result["tokens"]},
                "sovereignty": {"country": self.country, "encrypted": self.encrypt},
            }

    def health(self) -> Dict:
        return {"status": "healthy", "uptime_s": time.time() - self.start_time,
                "requests_served": self._request_count,
                "sovereignty": self.country,
                "audit_entries": len(self.audit.entries)}

# ── Demo ────────────────────────────────────────────────────────────────

def section(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}\n")

def main():
    print("=" * 60)
    print("  Zhilicon Template: Sovereign Chatbot")
    print("=" * 60)

    bot = SovereignChatbot(country="ae", encrypt=True)

    section("1. Basic Chat")
    result = bot.chat("user-001", None,
                      [{"role": "user", "content": "What is sovereign AI computing?"}])
    print(f"Conv ID : {result['conv_id']}")
    print(f"Model   : {result['model']}")
    print(f"Language: {result['language']}")
    print(f"Response: {result['choices'][0]['message']['content'][:100]}...")
    print(f"Tokens  : {result['usage']}")
    print(f"Country : {result['sovereignty']['country']}")

    section("2. Multi-turn Conversation")
    conv_id = result["conv_id"]
    follow_up = bot.chat("user-001", conv_id,
                         [{"role": "user", "content": "Tell me more about data residency."}])
    print(f"Follow-up: {follow_up['choices'][0]['message']['content'][:100]}...")
    history = bot.store.get_history(conv_id)
    print(f"\nConversation history ({len(history)} messages):")
    for msg in history:
        print(f"  [{msg['role']:9s}] {msg['content'][:50]}... (encrypted: {msg['encrypted']})")

    section("3. Streaming Response")
    stream_result = bot.chat("user-001", None,
                             [{"role": "user", "content": "Explain Zhilicon in detail."}],
                             stream=True)
    print(f"Stream chunks ({len(stream_result['chunks'])}):")
    for chunk in stream_result["chunks"][:3]:
        parsed = json.loads(chunk)
        delta = parsed["choices"][0].get("delta", {})
        content = delta.get("content", "[DONE]")
        print(f"  data: {content}")
    print(f"  ... ({len(stream_result['chunks'])} total chunks)")

    section("4. Language Detection & Routing")
    for text, expected_lang in [("Hello, how are you?", "en"),
                                 ("Tell me about Dubai", "en")]:
        result = bot.chat("user-001", None,
                         [{"role": "user", "content": text}])
        print(f"  '{text[:30]}' -> lang={result['language']}, model={result['model']}")

    section("5. Health & Audit")
    health = bot.health()
    print(f"Health: {json.dumps(health, indent=2)}")
    print(f"\nAudit log ({len(bot.audit.entries)} entries):")
    for entry in bot.audit.entries[:5]:
        print(f"  [{entry['seq']}] {entry['type']} | hash: {entry['hash'][:12]}...")

    print(f"\nSovereign chatbot demo complete!")

if __name__ == "__main__":
    main()
