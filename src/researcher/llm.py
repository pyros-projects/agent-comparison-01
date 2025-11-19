"""litellm helpers with pragmatic fallbacks."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Dict, List

import numpy as np
from litellm import completion, embedding

from .config import get_settings
from .models import AnalysisResult, ScoredTag

log = logging.getLogger(__name__)


def _fallback_embedding(text: str) -> List[float]:
    # Deterministic pseudo-embedding using hash to stay stable without remote calls
    h = hashlib.sha256(text.encode("utf-8")).digest()
    arr = np.frombuffer(h, dtype=np.uint8)[:32].astype(np.float32)
    arr = arr / np.linalg.norm(arr)
    return arr.tolist()


def embed_text(text: str) -> List[float]:
    settings = get_settings()
    try:
        resp = embedding(model=settings.default_embedding_model, input=text)
        return resp["data"][0]["embedding"]
    except Exception as exc:  # noqa: BLE001
        log.warning("Embedding fell back to local hash due to: %s", exc)
        return _fallback_embedding(text)


SYSTEM_PROMPT = """You summarize AI research artifacts. Respond in strict JSON with keys: summary (2 sentences), tags (list of strings), questions (list of strings), findings (list of strings), relevance (0-10 float), interesting (0-10 float). Do not add prose."""


def analyze_payload(title: str, abstract: str, kind: str) -> AnalysisResult:
    settings = get_settings()
    user_prompt = (
        f"Type: {kind}\nTitle: {title}\nAbstract or description:\n{abstract}\n"
        "Return compact fields as requested."
    )
    try:
        resp = completion(
            model=settings.default_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        content = resp["choices"][0]["message"]["content"]
        data: Dict = json.loads(content)
        tags = [ScoredTag(tag=t, weight=1.0) for t in data.get("tags", [])][:10]
        return AnalysisResult(
            summary=data.get("summary", "")[:500],
            tags=tags,
            questions_answered=data.get("questions", [])[:10],
            key_findings=data.get("findings", [])[:10],
            relevance_score=float(data.get("relevance", 5)),
            interesting_score=float(data.get("interesting", 5)),
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("LLM analysis failed, using heuristic fallback: %s", exc)
        tags = [ScoredTag(tag=word, weight=0.8) for word in title.split()[:5]]
        return AnalysisResult(
            summary=abstract[:400] if abstract else f"Preview for {title}",
            tags=tags,
            questions_answered=[f"What does {title} propose?"],
            key_findings=["Insight pending LLM analysis."],
            relevance_score=6.0,
            interesting_score=6.5,
        )


__all__ = ["embed_text", "analyze_payload"]
