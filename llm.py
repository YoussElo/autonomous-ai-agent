"""Couche d'appel LLM avec tool use : fournisseur interchangeable, statut toujours explicite.

Deux fournisseurs, choisis par LLM_PROVIDER ou, à défaut, détectés :

  anthropic  API Anthropic directe (Claude), tool use natif. ANTHROPIC_API_KEY requise,
             sinon ANTHROPIC_BASE_URL pour un proxy compatible (ex: passerelle locale).
  demo       Aucun appel, aucune génération. Simule un agent qui répond immédiatement
             "done" sans tool call, pour tester la boucle et les tests sans clé.

Détection quand LLM_PROVIDER n'est pas défini : anthropic si ANTHROPIC_API_KEY ou
ANTHROPIC_BASE_URL est présent, sinon demo.

Aucune fonction ne lève d'exception réseau non gérée : chaque appel renvoie un LLMResult
dont le statut dit ce qui s'est réellement passé : "ok", "unavailable" ou "demo".
"""
import json
import os
from dataclasses import dataclass, field
from typing import Any

import requests

PROVIDERS = ("anthropic", "demo")
DEFAULT_MODEL = "claude-sonnet-5"
DEFAULT_TIMEOUT = 60


@dataclass
class LLMResult:
    status: str  # "ok" | "unavailable" | "demo"
    stop_reason: str | None = None
    text_blocks: list[str] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] | None = None
    error: str | None = None


def _detect_provider() -> str:
    provider = os.environ.get("LLM_PROVIDER")
    if provider in PROVIDERS:
        return provider
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_BASE_URL"):
        return "anthropic"
    return "demo"


def call_with_tools(messages: list[dict], tools: list[dict], system: str) -> LLMResult:
    """Un tour d'appel LLM avec tool use. `messages` suit le format Anthropic Messages API."""
    provider = _detect_provider()

    if provider == "demo":
        return LLMResult(
            status="demo",
            stop_reason="end_turn",
            text_blocks=["[demo] Aucune clé configurée : réponse simulée, aucun outil appelé."],
        )

    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    model = os.environ.get("LLM_MODEL", DEFAULT_MODEL)

    headers = {
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
    }
    if api_key:
        headers["x-api-key"] = api_key

    payload = {
        "model": model,
        "max_tokens": 4096,
        "system": system,
        "messages": messages,
        "tools": tools,
    }

    try:
        resp = requests.post(
            f"{base_url}/v1/messages",
            headers=headers,
            data=json.dumps(payload),
            timeout=DEFAULT_TIMEOUT,
        )
    except requests.RequestException as exc:
        return LLMResult(status="unavailable", error=str(exc))

    if resp.status_code != 200:
        return LLMResult(status="unavailable", error=f"HTTP {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    text_blocks: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    for block in data.get("content", []):
        if block.get("type") == "text":
            text_blocks.append(block["text"])
        elif block.get("type") == "tool_use":
            tool_calls.append(block)

    if not text_blocks and not tool_calls:
        return LLMResult(status="unavailable", error="Réponse vide malgré HTTP 200.")

    return LLMResult(
        status="ok",
        stop_reason=data.get("stop_reason"),
        text_blocks=text_blocks,
        tool_calls=tool_calls,
        raw=data,
    )
