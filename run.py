"""
SETRAF CPT Analysis Studio — Point d'entrée sécurisé
=====================================================
Authentification obligatoire avant accès au code source (app/).
Workflow :
  1. Connexion à MongoDB Atlas
  2. Dialogue de connexion (username + password + OTP Google Authenticator)
  3. Génération d'un JWT valide 1 heure
  4. Chargement de l'application principale
  5. Watchdog de session : verrouillage automatique à l'expiration
"""
import sys
import os

# ── Encoding UTF-8 (Windows) ──────────────────────────────────────────────────
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ── Chemins ───────────────────────────────────────────────────────────────────
base_dir   = os.path.dirname(os.path.abspath(__file__))
app_dir    = os.path.join(base_dir, "app")
sec_dir    = os.path.join(base_dir, "security")
models_dir = os.path.join(base_dir, "models")

sys.path.insert(0, sec_dir)
sys.path.insert(0, app_dir)
sys.path.insert(0, base_dir)
if os.path.isdir(models_dir):
    sys.path.insert(0, models_dir)

os.chdir(app_dir)

# ── Charge .env ───────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(base_dir, ".env"))
except Exception:
    pass

# ── QApplication (doit exister avant tout widget) ────────────────────────────
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog
from PySide6.QtCore import QTimer

app = QApplication(sys.argv)
app.setApplicationName("SETRAF CPT Analysis Studio")

# ── Étape 1 : Code PIN d'accès (avant toute connexion réseau) ────────────────
try:
    from pin_dialog import PinDialog
    _pin_dlg = PinDialog()
    if _pin_dlg.exec() != QDialog.Accepted:
        sys.exit(0)
except ImportError:
    pass   # module absent → pas de blocage PIN

# ── Étape 2 : Authentification OTP + MongoDB ──────────────────────────
try:
    from auth_manager import AuthManager
    from auth_dialog  import AuthDialog, SessionLockScreen
    from folder_lock  import lock as _lock_app, unlock as _unlock_app, is_locked as _app_is_locked
except ImportError as e:
    QMessageBox.critical(
        None, "Module sécurité manquant",
        f"Impossible de charger le module de sécurité :\n{e}\n\n"
        "Vérifiez que le dossier security/ est présent."
    )
    sys.exit(1)

try:
    auth_manager = AuthManager()
except Exception as e:
    QMessageBox.critical(
        None, "Erreur de connexion",
        f"Impossible de se connecter à MongoDB :\n\n{e}\n\n"
        "• Vérifiez votre connexion internet\n"
        "• Vérifiez le fichier .env (MONGO_URI)\n"
        "• Vérifiez que votre IP est autorisée dans Atlas"
    )
    sys.exit(1)

# ── Dialogue de connexion ─────────────────────────────────────────────────────
auth_dlg = AuthDialog(auth_manager)
if auth_dlg.exec() != QDialog.Accepted or not auth_dlg.session_token:
    auth_manager.close()
    sys.exit(0)

# ── Déverrouille le dossier app/ (NTFS) → accès autorisé ────────────────────
_unlock_app()

# Enregistre le verrou à la fermeture de l'app
app.aboutToQuit.connect(_lock_app)

# Jeton deposé dans l'environnement → verrou d'accès à app/
_token = auth_dlg.session_token
os.environ["CPT_SESSION_TOKEN"]  = _token
os.environ["CPT_APP_AUTHORIZED"] = "1"
del auth_dlg

# ── Splash screen (facultatif) ────────────────────────────────────────────────
_splash = None
try:
    from splash_screen import SplashScreen
    _splash = SplashScreen()
    _splash.show()
    app.processEvents()
except Exception:
    pass

# ── Chargement de main.py (sans déclencher __main__) ─────────────────────────
import importlib.util as _ilu

_spec = _ilu.spec_from_file_location("cpt_main", os.path.join(app_dir, "main.py"))
if not (_spec and _spec.loader):
    QMessageBox.critical(None, "Erreur", "Impossible de charger app/main.py")
    sys.exit(1)

_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_mod)     # type: ignore
# __name__ == "cpt_main" → le bloc if __name__=='__main__' ne s'exécute PAS

MainWindow = _mod.MainWindow

# ── Fenêtre principale ────────────────────────────────────────────────────────
_window = None

def _show_main():
    global _window
    try:
        _window = MainWindow()
        if _splash:
            _splash.finish_and_close(_window)
        else:
            _window.show()
    except Exception:
        if _splash:
            _splash.close()
        import traceback
        QMessageBox.critical(
            None, "Erreur de démarrage",
            traceback.format_exc()
        )
        sys.exit(1)

if _splash:
    QTimer.singleShot(2800, _show_main)
else:
    _show_main()

# ── Watchdog de session (vérifie toutes les 30 s) ────────────────────────────
def _session_check():
    remaining = auth_manager.remaining_seconds(
        os.environ.get("CPT_SESSION_TOKEN", "")
    )

    # Avertissement 5 minutes avant expiration
    if 0 < remaining <= 300:
        mins = remaining // 60
        secs = remaining % 60
        if _window:
            try:
                _window.statusBar().showMessage(
                    f"⚠️  Session expire dans {mins}m {secs:02d}s — "
                    "Sauvegardez votre travail.",
                    10_000,
                )
            except Exception:
                pass

    # Session expirée → verrouillage
    if remaining <= 0:
        os.environ.pop("CPT_SESSION_TOKEN",  None)
        os.environ.pop("CPT_APP_AUTHORIZED", None)

        lock = SessionLockScreen(auth_manager, _window)
        if lock.exec() == QDialog.Accepted and lock.session_token:
            new_token = lock.session_token
            os.environ["CPT_SESSION_TOKEN"]  = new_token
            os.environ["CPT_APP_AUTHORIZED"] = "1"
            # Redémarre le watchdog
            _watchdog.start(30_000)
        else:
            auth_manager.revoke_token(os.environ.get("CPT_SESSION_TOKEN", ""))
            auth_manager.close()
            app.quit()

_watchdog = QTimer()
_watchdog.setSingleShot(False)
_watchdog.timeout.connect(_session_check)
_watchdog.start(30_000)   # vérifie toutes les 30 secondes

sys.exit(app.exec())
