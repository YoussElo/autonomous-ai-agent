"""Vérification obligatoire avant de déclarer une tâche terminée.

Un agent qui s'auto-évalue avec le même appel qui a produit le travail tend à se croire.
Ici la vérification est un second appel LLM, séparé, à qui on ne montre que la tâche
d'origine et la trace des tool calls (pas le raisonnement de l'agent), et à qui on demande
de juger uniquement sur les preuves : c'est le rôle du "cold reader" dans claude-workforce.
"""
import json

from llm import call_with_tools

VERIFY_SYSTEM = (
    "Tu es un vérificateur indépendant. On te donne une tâche et la trace des actions "
    "réellement exécutées (tool calls + résultats). Réponds uniquement par un JSON "
    '{"done": true|false, "reason": "..."}. "done" est true seulement si la trace contient '
    "une preuve concrète que la tâche est accomplie. Une simple affirmation textuelle sans "
    "tool call correspondant ne compte pas comme preuve."
)


def verify_completion(task: str, trace: list[dict]) -> dict:
    trace_summary = json.dumps(trace, ensure_ascii=False)[:6000]
    messages = [
        {
            "role": "user",
            "content": f"Tâche: {task}\n\nTrace des actions:\n{trace_summary}",
        }
    ]
    result = call_with_tools(messages, tools=[], system=VERIFY_SYSTEM)

    if result.status == "demo":
        return {"done": bool(trace), "reason": "[demo] validé s'il y a au moins une action tracée."}
    if result.status != "ok" or not result.text_blocks:
        return {"done": False, "reason": f"vérificateur indisponible ({result.error or result.status})"}

    raw = result.text_blocks[0].strip()
    try:
        start, end = raw.index("{"), raw.rindex("}") + 1
        return json.loads(raw[start:end])
    except (ValueError, json.JSONDecodeError):
        return {"done": False, "reason": f"réponse du vérificateur non parsable: {raw[:200]}"}
