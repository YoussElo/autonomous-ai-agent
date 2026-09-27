# Autonomous AI Agent

Un agent qui planifie, utilise des outils, et n'a le droit de se déclarer "terminé" qu'après
qu'un vérificateur indépendant ait confirmé, sur preuve, que la tâche est faite.

## Pourquoi ce projet

Deux objectifs à la fois :

1. **Portfolio.** Deuxième des 5 projets recommandés pour candidater en IA/data en 2026
   (RAG chatbot, agent autonome, ML model as API, recommendation engine, dashboard). Celui-ci
   démontre tool use, boucle agentique, et guardrails, sans dépendre d'un framework opaque.
2. **Banc d'essai pour un système plus autonome.** Ce dépôt sert à tester en public des
   patterns qu'on veut ensuite réutiliser dans un système d'agents privé plus large : la
   preuve-avant-terminé, le confinement des outils, le journal append-only. Rien ici ne
   contient de données personnelles ou professionnelles.

## Ce qui le distingue d'une boucle "tool use" basique

- **Vérification séparée.** L'agent qui a fait le travail ne juge jamais lui-même s'il a
  terminé. Un second appel LLM, qui ne voit que la tâche et la trace des tool calls (pas le
  raisonnement de l'agent), tranche uniquement sur preuve (`verify.py`).
- **Outils confinés.** Aucun outil ne touche le disque hors de `workspace/` (`tools.py`).
- **Journal append-only.** Chaque appel LLM et chaque tool call est horodaté dans
  `logs/YYYY-MM-DD.jsonl`, pour pouvoir reconstituer après coup ce que l'agent a réellement
  fait (`logger.py`).
- **Mode demo sans clé.** `LLM_PROVIDER=demo` fait tourner toute la boucle et les tests sans
  appel réseau, pour vérifier la mécanique indépendamment du modèle.

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

## Utilisation

```bash
export ANTHROPIC_API_KEY=sk-...   # ou ANTHROPIC_BASE_URL pour un proxy compatible
python main.py "Calcule 12*7 et écris le résultat dans resultat.txt"
```

Sans clé configurée, l'agent tourne en mode demo (aucun tool call, réponse simulée) :

```bash
python main.py "n'importe quelle tâche"
```

## Tests

```bash
pytest
```

Tous les tests tournent en mode demo ou avec des outils monkeypatchés : aucun réseau requis.

## Structure

```
agent.py     boucle centrale (appel LLM -> tool calls -> vérification)
llm.py       couche d'appel LLM, fournisseur interchangeable (anthropic | demo)
tools.py     outils exposés à l'agent, confinés à workspace/
verify.py    vérification indépendante avant de déclarer une tâche terminée
logger.py    journal append-only horodaté
main.py      CLI
```
