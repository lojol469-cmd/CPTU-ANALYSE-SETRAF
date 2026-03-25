"""
SETRAF CPT Analysis Studio — Script de configuration administrateur
====================================================================
Exécutez ce script UNE SEULE FOIS pour :
  1. Générer la clé secrète JWT (écrite dans .env)
  2. Créer le premier compte administrateur
  3. Afficher le QR code Google Authenticator dans une fenêtre

Usage :
    python\python.exe security\setup_admin.py
"""
import sys
import os
import io
import getpass
import secrets

# ── Chemins ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "security"))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv, set_key

ENV_FILE = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_FILE, override=False)

# ── Génère CPT_SECRET_KEY si absente ─────────────────────────────────────────
if not os.getenv("CPT_SECRET_KEY"):
    key = secrets.token_hex(32)
    set_key(ENV_FILE, "CPT_SECRET_KEY", key)
    print(f"[✓] CPT_SECRET_KEY générée et sauvegardée dans .env")

# Recharge après écriture
load_dotenv(ENV_FILE, override=True)

# ── Import du gestionnaire d'auth ─────────────────────────────────────────────
try:
    from auth_manager import AuthManager
except ImportError as e:
    print(f"[✗] Erreur d'import : {e}")
    sys.exit(1)

print("\n" + "="*55)
print("  SETRAF CPT Analysis Studio — Configuration Sécurité")
print("="*55)

# ── Connexion MongoDB ─────────────────────────────────────────────────────────
print("\n[·] Connexion à MongoDB Atlas…")
try:
    am = AuthManager()
    print("[✓] Connexion réussie.\n")
except Exception as e:
    print(f"[✗] Impossible de se connecter à MongoDB :\n    {e}")
    sys.exit(1)

# ── Vérifie si des utilisateurs existent déjà ────────────────────────────────
if am.has_any_user():
    print("[!] Des utilisateurs existent déjà dans la base.")
    print("[!] Ce script crée uniquement le premier administrateur.")
    cont = input("    Continuer quand même ? (o/n) : ").strip().lower()
    if cont != "o":
        print("[·] Annulé.")
        am.close()
        sys.exit(0)

# ── Saisie des informations ───────────────────────────────────────────────────
print("─"*55)
print("  Création du compte administrateur")
print("─"*55)

username = input("  Nom d'utilisateur : ").strip()
while not username:
    username = input("  Nom d'utilisateur (obligatoire) : ").strip()

password = getpass.getpass("  Mot de passe      : ")
confirm  = getpass.getpass("  Confirmer mdp     : ")

if password != confirm:
    print("[✗] Les mots de passe ne correspondent pas.")
    am.close()
    sys.exit(1)

# ── Enregistrement ───────────────────────────────────────────────────────────
print("\n[·] Création du compte…")
totp_secret, err = am.register_user(username, password)
if err:
    print(f"[✗] Erreur : {err}")
    am.close()
    sys.exit(1)

print(f"[✓] Compte «{username}» créé avec succès.")
print(f"\n  Clé TOTP (pour saisie manuelle si nécessaire) :")
print(f"  ┌─────────────────────────────────────────────┐")
print(f"  │  {totp_secret:<43s} │")
print(f"  └─────────────────────────────────────────────┘")

# ── Affichage du QR code ─────────────────────────────────────────────────────
uri = am.get_totp_uri(username, totp_secret)
print(f"\n  URI Google Authenticator :\n  {uri}\n")

# Affichage PySide6 (avec QR image)
try:
    import qrcode
    from PySide6.QtWidgets import (
        QApplication, QDialog, QVBoxLayout, QLabel, QPushButton
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QPixmap

    app = QApplication.instance() or QApplication(sys.argv)

    qr_obj = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=8,
        border=4,
    )
    qr_obj.add_data(uri)
    qr_obj.make(fit=True)
    qr_img = qr_obj.make_image(fill_color="#111", back_color="white")

    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")

    pix = QPixmap()
    pix.loadFromData(buf.getvalue())
    pix = pix.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    dlg = QDialog()
    dlg.setWindowTitle("Scannez avec Google Authenticator")
    dlg.setFixedSize(380, 460)
    dlg.setStyleSheet("background:#16140e; color:#F0E1C3;")
    v = QVBoxLayout(dlg)
    v.setSpacing(12)
    v.setContentsMargins(20, 20, 20, 20)

    lbl_title = QLabel("Scanner ce QR code avec Google Authenticator")
    lbl_title.setAlignment(Qt.AlignCenter)
    lbl_title.setStyleSheet(
        "font-size:14px; font-weight:bold; color:#C1550F;"
    )
    lbl_title.setWordWrap(True)
    v.addWidget(lbl_title)

    lbl_qr = QLabel()
    lbl_qr.setPixmap(pix)
    lbl_qr.setAlignment(Qt.AlignCenter)
    lbl_qr.setStyleSheet(
        "background:white; border-radius:10px; padding:8px;"
    )
    v.addWidget(lbl_qr)

    lbl_key = QLabel(
        f"Clé manuelle :\n{totp_secret}"
    )
    lbl_key.setAlignment(Qt.AlignCenter)
    lbl_key.setStyleSheet(
        "font-family:Consolas,monospace; font-size:12px; "
        "color:#F59B3A; background:#2a2418; border-radius:6px; padding:8px;"
    )
    v.addWidget(lbl_key)

    lbl_instr = QLabel(
        "1. Ouvrez Google Authenticator\n"
        "2. Appuyez sur  +  →  Scanner un QR code\n"
        "3. Scannez le code ci-dessus\n"
        "4. Lancez le logiciel avec launch.bat"
    )
    lbl_instr.setAlignment(Qt.AlignCenter)
    lbl_instr.setStyleSheet("font-size:11px; color:#9B8E7D;")
    lbl_instr.setWordWrap(True)
    v.addWidget(lbl_instr)

    btn = QPushButton("  J'ai scanné — Fermer")
    btn.setStyleSheet(
        "background:#C1550F; color:white; border:none; border-radius:6px; "
        "padding:10px 20px; font-weight:bold; font-size:13px;"
    )
    btn.clicked.connect(dlg.accept)
    v.addWidget(btn)

    dlg.exec()
    print("[✓] QR code fermé.")

except Exception as e:
    print(f"[!] Impossible d'afficher le QR graphique : {e}")
    print("[!] Utilisez la clé manuelle ci-dessus pour configurer Google Authenticator.")

# ── Résumé ────────────────────────────────────────────────────────────────────
print("\n" + "="*55)
print("  Configuration terminée avec succès !")
print("="*55)
print(f"\n  Utilisateur : {username}")
print("  Lancez l'application : launch.bat")
print("  Authentification    : password + code Google Authenticator\n")

am.close()
