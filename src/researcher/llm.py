from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Tuple

import litellm

from .config import get_settings


async def _ensure_embedding_response(model: str, text: str) -> List[float]:
    """
    Call litellm.embedding and normalize the possible sync/async return types.
    """
    resp = litellm.embedding(model=model, input=[text])
    if asyncio.iscoroutine(resp):
        resp = await resp
    embeddings = getattr(resp, "data", None) or resp["data"]
    vector = embeddings[0]["embedding"]
    return [float(x) for x in vector]


async def embed_text(text: str) -> List[float]:
    settings = get_settings()
    return await _ensure_embedding_response(settings.embedding_model, text)


async def summarize_paper(
    *, title: str, abstract: str, url: str
) -> Tuple[str, List[str], List[str], float, float]:
    """
    Ask the LLM to generate:
    - summary paragraph
    - tags
    - key findings
    - real world relevancy score
    - interestingness score
    """
    settings = get_settings()
    prompt = f"""
You are helping maintain a research catalog of AI-related papers.

Paper title: {title}
URL: {url}
Abstract:
{abstract}

1) Provide a concise summary (3-5 sentences).
2) Provide 5-10 short, comma-separated tags.
3) Provide a bullet-style list of 3-8 key findings (short phrases).
4) Rate the real-world relevancy of this paper from 1-10.
5) Rate how interesting/innovative this paper is from 1-10.

Respond in JSON with keys:
summary, tags, key_findings, real_world_relevancy, interestingness.
"""
    result = await litellm.acompletion(
        model=settings.default_model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    content = result.choices[0].message.content  # type: ignore[attr-defined]
    import json

    data: Dict[str, Any] = json.loads(content)
    summary = str(data.get("summary", "")).strip()
    raw_tags = str(data.get("tags", "")).replace("\n", " ")
    tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
    key_findings_value = data.get("key_findings", [])
    if isinstance(key_findings_value, str):
        key_findings = [line.strip("- ").strip() for line in key_findings_value.split("\n") if line.strip()]
    else:
        key_findings = [str(x).strip() for x in key_findings_value]

    real_world_relevancy = float(data.get("real_world_relevancy", 5.0))
    interestingness = float(data.get("interestingness", 5.0))

    return summary, tags, key_findings, real_world_relevancy, interestingness


async def summarize_repository(
    *, name: str, description: str, url: str, readme_text: str | None
) -> Tuple[str, List[str], List[str], float, float]:
    settings = get_settings()
    prompt = f"""
You are helping maintain a research catalog of AI-related code repositories.

Repository name: {name}
URL: {url}
Description: {description}

README (may be partial):
{readme_text or 'N/A'}

1) Provide a concise summary (3-5 sentences) of the repository.
2) Provide 5-10 short, comma-separated tags.
3) Provide a bullet-style list of 3-8 key findings or capabilities.
4) Rate the real-world relevancy of this repo from 1-10.
5) Rate how interesting/innovative this repo is from 1-10.

Respond in JSON with keys:
summary, tags, key_findings, real_world_relevancy, interestingness.
"""
    result = await litellm.acompletion(
        model=settings.default_model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    content = result.choices[0].message.content  # type: ignore[attr-defined]
    import json

    data: Dict[str, Any] = json.loads(content)
    summary = str(data.get("summary", "")).strip()
    raw_tags = str(data.get("tags", "")).replace("\n", " ")
    tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
    key_findings_value = data.get("key_findings", [])
    if isinstance(key_findings_value, str):
        key_findings = [line.strip("- ").strip() for line in key_findings_value.split("\n") if line.strip()]
    else:
        key_findings = [str(x).strip() for x in key_findings_value]

    real_world_relevancy = float(data.get("real_world_relevancy", 5.0))
    interestingness = float(data.get("interestingness", 5.0))

    return summary, tags, key_findings, real_world_relevancy, interestingness


async def classify_theory_against_items(
    theory: str, items: List[Dict[str, Any]]
) -> Dict[str, str]:
    """
    Given a theory/question and a list of catalog items (with id, kind, title, summary),
    ask the LLM whether each item agrees, disagrees, or is neutral/uncertain.
    Returns mapping item_id -> label ('agree'|'disagree'|'uncertain').
    """
    settings = get_settings()
    import json

    formatted_items = [
        {
            "id": item["id"],
            "kind": item["kind"],
            "title": item["title"],
            "summary": item["summary"],
        }
        for item in items
    ]

    prompt = f"""
You are helping analyze research findings with respect to a theory or question.

Theory / question:
\"\"\"{theory}\"\"\"

Below is a JSON list of catalog items (papers or repositories), each with
an id, kind, title, and summary:

{json.dumps(formatted_items, indent=2)}

For each item, decide whether the item:
- clearly supports the theory ('agree'),
- clearly contradicts it ('disagree'), or
- is related but not clearly one or the other ('uncertain').

Respond strictly as JSON mapping item id -> one of: "agree", "disagree", "uncertain".
"""
    result = await litellm.acompletion(
        model=settings.default_model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    content = result.choices[0].message.content  # type: ignore[attr-defined]
    labels: Dict[str, str] = json.loads(content)
    normalized: Dict[str, str] = {}
    for item_id, label in labels.items():
        value = str(label).strip().lower()
        if value not in {"agree", "disagree", "uncertain"}:
            value = "uncertain"
        normalized[item_id] = value
    return normalized

