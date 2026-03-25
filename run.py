"""
CPT Analysis Studio
Script de lancement portable
"""
import sys
import os

# Forcer UTF-8 pour la console Windows (evite les crashes avec les emojis)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Chemin du dossier du launcher (RISKIA_PORTABLE/)
base_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(base_dir, "app")
python_dir = os.path.join(base_dir, "python")

# Ajouter le dossier app au path Python pour les imports relatifs
sys.path.insert(0, app_dir)
# Ajouter base_dir pour permettre "from models.rag_system import ..."
sys.path.insert(0, base_dir)

# Ajouter le dossier modeles IA si present
models_dir = os.path.join(base_dir, "models")
if os.path.isdir(models_dir):
    sys.path.insert(0, models_dir)

# Changer le repertoire courant vers app/ pour que les fichiers relatifs fonctionnent
os.chdir(app_dir)

# Lancer main.py
import importlib.util
spec = importlib.util.spec_from_file_location("__main__", os.path.join(app_dir, "main.py"))
if spec and spec.loader:
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
