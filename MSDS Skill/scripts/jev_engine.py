# -*- coding: utf-8 -*-
"""Jev System One Core Engine & Decision Ledger for MSDS and TDS Standardization.

Provides a robust, typesafe System One decision client with on-demand invocation,
deterministic fallback protection, caching, and an auditable Decision Ledger.
"""

from __future__ import annotations

import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
import uuid
from typing import Any, Dict, List, Optional, Tuple

# Default API key and endpoint
# API key must be provided via environment variable (ZEN_API_KEY / JEV_API_KEY) or ~/.jev/zen.key
DEFAULT_ENDPOINT = "https://opencode.ai/zen/v1/systemone"
DEFAULT_MODEL = "jev-1.13-free"
RETRYABLE_CODES = {429, 500, 502, 503, 529}


class DecisionLedger:
    """Auditable ledger recording all Jev queries, decisions, confidence scores, and fallbacks."""

    def __init__(self) -> None:
        self.entries: List[Dict[str, Any]] = []

    def record(
        self,
        scenario: str,
        state_summary: str,
        question_type: str,
        instructions: str,
        result: Any,
        confidence: float,
        duration_ms: float,
        used_fallback: bool = False,
        error: Optional[str] = None,
    ) -> None:
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "scenario": scenario,
            "state_summary": state_summary,
            "question_type": question_type,
            "instructions": instructions,
            "result": result,
            "confidence": round(confidence, 4),
            "duration_ms": round(duration_ms, 2),
            "used_fallback": used_fallback,
            "error": error,
        }
        self.entries.append(entry)

    def export(self, filepath: str) -> None:
        """Export the decision ledger to a JSON file."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({"total_decisions": len(self.entries), "ledger": self.entries}, f, ensure_ascii=False, indent=2)

    def clear(self) -> None:
        self.entries.clear()


# Global ledger singleton
GLOBAL_LEDGER = DecisionLedger()


class JevEngine:
    """TypeSafe System One Jev Client with connection resiliency and fallback safety."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 8.0,
        max_retries: int = 2,
    ) -> None:
        self.api_key = api_key or os.environ.get("ZEN_API_KEY") or os.environ.get("JEV_API_KEY") or self._read_local_key() or ""
        self.endpoint = endpoint or os.environ.get("JEV_ENDPOINT") or DEFAULT_ENDPOINT
        self.model = model or os.environ.get("JEV_MODEL") or DEFAULT_MODEL
        self.timeout = timeout
        self.max_retries = max_retries

    @staticmethod
    def _read_local_key() -> Optional[str]:
        candidates = [
            os.path.expanduser("~/.jev/zen.key"),
            r"C:\Users\Administrator\.jev\zen.key",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "zen.key"),
        ]
        for path in candidates:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            return content
                except Exception:
                    pass
        return None

    def call_raw(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute raw HTTP request to Jev System One endpoint."""
        if not self.api_key:
            raise ValueError(
                "Jev API Key is missing. Please configure ZEN_API_KEY or JEV_API_KEY in environment variables, "
                "or place the key in ~/.jev/zen.key"
            )
        payload.setdefault("model", self.model)
        data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "opencode/1.18.31",
            "x-opencode-client": "cli",
            "x-opencode-session": f"ses_{uuid.uuid4().hex[:16]}",
            "x-opencode-request": f"msg_{uuid.uuid4().hex[:16]}",
        }

        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                req = urllib.request.Request(self.endpoint, data=data_bytes, headers=headers, method="POST")
                with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                last_exc = e
                if e.code in RETRYABLE_CODES and attempt < self.max_retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                err_body = e.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"HTTP {e.code}: {err_body}") from e
            except Exception as e:
                last_exc = e
                if attempt < self.max_retries:
                    time.sleep(0.5)
                    continue
                raise last_exc
        if last_exc:
            raise last_exc
        return {}

    def decide_choice(
        self,
        state: str,
        instructions: str,
        criteria: Dict[str, str],
        fallback_choice: str,
        scenario: str = "general_choice",
    ) -> Tuple[str, float]:
        """Execute a categorical choice decision with confidence score and fallback."""
        start_t = time.time()
        try:
            payload = {
                "state": state,
                "questions": {"q": {"type": "choice", "instructions": instructions, "criteria": criteria}},
            }
            res = self.call_raw(payload)
            ans = res.get("answers", {}).get("q", {})
            choice = ans.get("choice", "")
            confidence = float(ans.get("confidence", 0.0))
            if choice not in criteria:
                choice = fallback_choice
                confidence = 0.0
            dur = (time.time() - start_t) * 1000.0
            GLOBAL_LEDGER.record(
                scenario=scenario,
                state_summary=state[:120],
                question_type="choice",
                instructions=instructions,
                result=choice,
                confidence=confidence,
                duration_ms=dur,
                used_fallback=False,
            )
            return choice, confidence
        except Exception as err:
            dur = (time.time() - start_t) * 1000.0
            GLOBAL_LEDGER.record(
                scenario=scenario,
                state_summary=state[:120],
                question_type="choice",
                instructions=instructions,
                result=fallback_choice,
                confidence=0.0,
                duration_ms=dur,
                used_fallback=True,
                error=str(err),
            )
            return fallback_choice, 0.0

    def decide_noul(
        self,
        state: str,
        instructions: str,
        fallback_noul: float = 0.0,
        scenario: str = "general_noul",
    ) -> float:
        """Execute a noul probability (0.0 to 1.0) decision with fallback."""
        start_t = time.time()
        try:
            payload = {
                "state": state,
                "questions": {"q": {"type": "noul", "instructions": instructions}},
            }
            res = self.call_raw(payload)
            ans = res.get("answers", {}).get("q", {})
            val = float(ans.get("noul", fallback_noul))
            dur = (time.time() - start_t) * 1000.0
            GLOBAL_LEDGER.record(
                scenario=scenario,
                state_summary=state[:120],
                question_type="noul",
                instructions=instructions,
                result=val,
                confidence=1.0,
                duration_ms=dur,
                used_fallback=False,
            )
            return val
        except Exception as err:
            dur = (time.time() - start_t) * 1000.0
            GLOBAL_LEDGER.record(
                scenario=scenario,
                state_summary=state[:120],
                question_type="noul",
                instructions=instructions,
                result=fallback_noul,
                confidence=0.0,
                duration_ms=dur,
                used_fallback=True,
                error=str(err),
            )
            return fallback_noul

    def decide_score(
        self,
        state: str,
        instructions: str,
        criteria: List[str],
        fallback_score: int = 0,
        scenario: str = "general_score",
    ) -> Tuple[int, float]:
        """Execute an ordinal score decision with confidence and fallback."""
        start_t = time.time()
        try:
            payload = {
                "state": state,
                "questions": {"q": {"type": "score", "instructions": instructions, "criteria": criteria}},
            }
            res = self.call_raw(payload)
            ans = res.get("answers", {}).get("q", {})
            score = int(ans.get("score", fallback_score))
            confidence = float(ans.get("confidence", 0.0))
            dur = (time.time() - start_t) * 1000.0
            GLOBAL_LEDGER.record(
                scenario=scenario,
                state_summary=state[:120],
                question_type="score",
                instructions=instructions,
                result=score,
                confidence=confidence,
                duration_ms=dur,
                used_fallback=False,
            )
            return score, confidence
        except Exception as err:
            dur = (time.time() - start_t) * 1000.0
            GLOBAL_LEDGER.record(
                scenario=scenario,
                state_summary=state[:120],
                question_type="score",
                instructions=instructions,
                result=fallback_score,
                confidence=0.0,
                duration_ms=dur,
                used_fallback=True,
                error=str(err),
            )
            return fallback_score, 0.0


# Shared default engine instance
DEFAULT_ENGINE = JevEngine()
