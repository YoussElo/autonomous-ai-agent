"""Boucle centrale : appelle le LLM avec les outils, exécute les tool calls, boucle jusqu'à
arrêt, puis exige une vérification indépendante avant de déclarer la tâche terminée.

Chaque tour est journalisé (logger.py). Chaque outil est confiné au workspace (tools.py).
Aucune tâche n'est déclarée "done" sans passer par verify.py.
"""
from dataclasses import dataclass, field

from llm import call_with_tools
from logger import log_event
from tools import TOOL_IMPLS, TOOL_SCHEMAS
from verify import verify_completion

SYSTEM_PROMPT = (
    "Tu es un agent autonome. Tu disposes d'outils : calculator, read_file, write_file, "
    "list_workspace. Utilise-les pour accomplir la tâche donnée, étape par étape. Quand tu "
    "penses avoir terminé, arrête d'appeler des outils et résume ce que tu as fait."
)

MAX_TURNS = 12


@dataclass
class RunResult:
    task: str
    messages: list[dict] = field(default_factory=list)
    trace: list[dict] = field(default_factory=list)
    turns_used: int = 0
    verification: dict | None = None
    status: str = "unknown"  # "done" | "incomplete" | "unavailable" | "max_turns"


def run(task: str) -> RunResult:
    messages = [{"role": "user", "content": task}]
    result = RunResult(task=task, messages=messages)
    log_event("run_start", task=task)

    for turn in range(1, MAX_TURNS + 1):
        result.turns_used = turn
        response = call_with_tools(messages, TOOL_SCHEMAS, SYSTEM_PROMPT)
        log_event("llm_call", turn=turn, status=response.status, stop_reason=response.stop_reason)

        if response.status == "unavailable":
            result.status = "unavailable"
            log_event("run_end", status="unavailable", error=response.error)
            return result

        assistant_content = []
        for text in response.text_blocks:
            assistant_content.append({"type": "text", "text": text})
        for call in response.tool_calls:
            assistant_content.append(call)
        messages.append({"role": "assistant", "content": assistant_content})

        if not response.tool_calls:
            # Pas de tool call : l'agent pense avoir fini. On vérifie avant de le croire.
            break

        tool_results = []
        for call in response.tool_calls:
            name = call.get("name")
            tool_input = call.get("input", {})
            impl = TOOL_IMPLS.get(name)
            output = impl(tool_input) if impl else f"erreur: outil inconnu '{name}'"
            log_event("tool_call", turn=turn, tool=name, input=tool_input, output=output)
            result.trace.append({"tool": name, "input": tool_input, "output": output})
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": call.get("id"),
                    "content": str(output),
                }
            )
        messages.append({"role": "user", "content": tool_results})

        if response.stop_reason == "end_turn":
            break
    else:
        result.status = "max_turns"
        log_event("run_end", status="max_turns")
        return result

    verification = verify_completion(task, result.trace)
    result.verification = verification
    result.status = "done" if verification.get("done") else "incomplete"
    log_event("run_end", status=result.status, verification=verification)
    return result
