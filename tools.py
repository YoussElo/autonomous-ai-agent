"""Outils exposés à l'agent : chacun a un schéma JSON, une implémentation, une limite.

Toute écriture ou lecture de fichier reste confinée au dossier `workspace/` : l'agent ne
touche jamais au reste du disque. C'est la limite de sécurité minimale pour un agent qui
exécute des tool calls générés par un LLM sans supervision humaine par étape.
"""
import ast
import operator
from pathlib import Path

WORKSPACE = Path(__file__).parent / "workspace"
WORKSPACE.mkdir(exist_ok=True)

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError(f"Expression non supportée: {ast.dump(node)}")


def calculator(expression: str) -> str:
    try:
        tree = ast.parse(expression, mode="eval")
        return str(_safe_eval(tree.body))
    except Exception as exc:
        return f"erreur: {exc}"


def _resolve(path: str) -> Path:
    target = (WORKSPACE / path).resolve()
    if not target.is_relative_to(WORKSPACE.resolve()):
        raise ValueError("Chemin hors du workspace autorisé.")
    return target


def read_file(path: str) -> str:
    try:
        target = _resolve(path)
        if not target.exists():
            return f"erreur: fichier introuvable: {path}"
        return target.read_text()[:8000]
    except Exception as exc:
        return f"erreur: {exc}"


def write_file(path: str, content: str) -> str:
    try:
        target = _resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return f"ok: écrit {len(content)} caractères dans {path}"
    except Exception as exc:
        return f"erreur: {exc}"


def list_workspace() -> str:
    files = sorted(p.relative_to(WORKSPACE).as_posix() for p in WORKSPACE.rglob("*") if p.is_file())
    return "\n".join(files) if files else "(workspace vide)"


TOOL_SCHEMAS = [
    {
        "name": "calculator",
        "description": "Évalue une expression arithmétique simple (+ - * / **). Pas d'appel de fonction.",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
    },
    {
        "name": "read_file",
        "description": "Lit un fichier dans le workspace de l'agent (chemin relatif uniquement).",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Écrit un fichier dans le workspace de l'agent (chemin relatif uniquement).",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "list_workspace",
        "description": "Liste les fichiers présents dans le workspace de l'agent.",
        "input_schema": {"type": "object", "properties": {}},
    },
]

TOOL_IMPLS = {
    "calculator": lambda inp: calculator(inp["expression"]),
    "read_file": lambda inp: read_file(inp["path"]),
    "write_file": lambda inp: write_file(inp["path"], inp["content"]),
    "list_workspace": lambda inp: list_workspace(),
}
