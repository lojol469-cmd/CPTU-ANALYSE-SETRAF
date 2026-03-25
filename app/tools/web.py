import os
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse

# On tente l'import propre du package officiel
try:
    from duckduckgo_search import DDGS
except ImportError:
    # Si le package n'est pas installé, on définit une classe vide pour éviter le crash au chargement
    DDGS = None

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def web_search(query: str, disabled=False):
    """Recherche web pilotée par l'orchestrateur Kibali"""
    if disabled:
        return {"results": [], "images": [], "query": query, "source": "disabled"}

    # --- 1. Tentative avec Tavily (Priorité IA) ---
    if TAVILY_API_KEY:
        try:
            from tavily import TavilyClient
            tavily = TavilyClient(api_key=TAVILY_API_KEY)
            res = tavily.search(query=query, search_depth="advanced", include_images=True)
            return {
                "results": res.get('results', []), 
                "images": res.get('images', []), 
                "query": query, 
                "source": "tavily"
            }
        except Exception:
            pass # On bascule sur le backup si Tavily échoue

    # --- 2. Backup avec DuckDuckGo (Corrigé) ---
    if DDGS is not None:
        try:
            with DDGS() as ddgs:
                # Récupération des textes et images
                results = [r for r in ddgs.text(query, max_results=5)]
                images = [i for i in ddgs.images(query, max_results=5)]
                return {
                    "results": results, 
                    "images": images, 
                    "query": query, 
                    "source": "duckduckgo"
                }
        except Exception as e:
            return {"results": [], "images": [], "query": query, "error": str(e)}
    
    return {"results": [], "images": [], "query": query, "error": "No search provider available"}

def display_images(web_results, max_images=3):
    """Formatage Markdown des images pour le chat"""
    if not web_results or not web_results.get('images'):
        return ""
    
    images = web_results['images']
    output = "\n🖼️ **Inspirations visuelles trouvées :**\n"
    for img in images[:max_images]:
        # On gère les différents noms de clés selon le moteur (Tavily vs DDG)
        url = img.get('url') or img.get('image')
        title = img.get('title', 'Lien')
        if url:
            output += f"- [{title}]({url})\n"
    return output