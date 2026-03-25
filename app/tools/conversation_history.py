"""
Module de gestion de l'historique des conversations.
Stocke et recherche les messages pour le contexte conversationnel.
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Historique en mémoire (liste de dicts {role, content, score})
_history: List[Dict] = []


def add_message(role: str, content: str) -> None:
    """Ajoute un message à l'historique."""
    _history.append({"role": role, "content": content})


def search_conversation_history(query: str, limit: int = 5) -> List[Dict]:
    """
    Recherche dans l'historique les messages les plus pertinents par rapport à la query.
    Retourne une liste de dicts {role, content, score}.
    """
    if not _history:
        return []

    query_words = set(query.lower().split())
    scored = []
    for msg in _history:
        content_words = set(msg["content"].lower().split())
        score = len(query_words & content_words)
        if score > 0:
            scored.append({**msg, "score": score})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]


def clear_history() -> None:
    """Vide l'historique."""
    _history.clear()


def get_all_history() -> List[Dict]:
    """Retourne tout l'historique."""
    return list(_history)
