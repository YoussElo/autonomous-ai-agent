"""Tests de la boucle agent en mode demo (aucun réseau, aucune clé requise)."""
import os

from agent import run


def test_demo_run_completes_without_network(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "demo")

    result = run("dis bonjour")

    assert result.status in ("incomplete", "done")
    assert result.turns_used == 1
    assert result.trace == []  # le mode demo ne fait jamais de tool call
