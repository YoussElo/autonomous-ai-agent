"""CLI : `python main.py "tâche à accomplir"`."""
import sys

from agent import run


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python main.py "tâche à accomplir"')
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    result = run(task)

    print(f"\n--- statut: {result.status} ({result.turns_used} tour(s)) ---")
    for step in result.trace:
        print(f"  [{step['tool']}] {step['input']} -> {step['output']}")
    if result.verification:
        print(f"--- vérification: {result.verification} ---")


if __name__ == "__main__":
    main()
