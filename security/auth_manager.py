"""
SETRAF CPT Analysis Studio — Authentication Manager
=====================================================
MongoDB Atlas + bcrypt (12 rounds) + pyOTP (TOTP) + JWT (HS256)

Sécurité :
 - Mots de passe hachés bcrypt (12 rounds)
 - TOTP compatible Google Authenticator (RFC 6238)
 - JWT HS256 signé avec clé secrète 256 bits
 - Verrouillage compte après 5 tentatives (15 min)
 - Session configurable (défaut 3 600 s = 1 h)
 - Clé secrète auto-générée et persistée dans .env si absente
"""
import os
import datetime
import secrets
import re

import pyotp
import bcrypt
import jwt
from pymongo import MongoClient, errors as mongo_errors
from dotenv import load_dotenv, set_key

# ── Charge .env (cherche dans le dossier parent = racine du projet) ────────────
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV_FILE = os.path.join(_BASE_DIR, ".env")
load_dotenv(_ENV_FILE, override=False)

# ── Clé secrète JWT : auto-générée et sauvegardée si absente ──────────────────
_SECRET_KEY = os.getenv("CPT_SECRET_KEY")
if not _SECRET_KEY:
    _SECRET_KEY = secrets.token_hex(32)          # 256 bits = 64 hex chars
    try:
        set_key(_ENV_FILE, "CPT_SECRET_KEY", _SECRET_KEY)
    except Exception:
        pass  # .env peut être en lecture seule → la clé sera regénérée au prochain lancement

_SESSION_DURATION  = int(os.getenv("CPT_SESSION_DURATION", "3600"))
_AUTH_COLLECTION   = os.getenv("CPT_AUTH_COLLECTION", "cpt_studio_users")
_MAX_ATTEMPTS      = 5
_LOCKOUT_MINUTES   = 15


class AuthManager:
    """Gestionnaire d'authentification principal."""

    def __init__(self):
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise RuntimeError(
                "MONGO_URI manquant dans .env\n"
                "Vérifiez le fichier C:\\...\\CPT_Analysis_Studio_PORTABLE\\.env"
            )
        self.client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=10_000,
            connectTimeoutMS=10_000,
        )
        # Ping pour vérifier la connexion au démarrage
        self.client.admin.command("ping")

        db_name      = os.getenv("MONGO_DB_NAME", "cptu_studio")
        self.db      = self.client[db_name]
        self.users   = self.db[_AUTH_COLLECTION]
        self.sessions = self.db["cpt_sessions"]

        # Index unique sur username
        self.users.create_index("username", unique=True)

    # ─────────────────────────────────────────────────────────────────────────
    # Gestion des utilisateurs
    # ─────────────────────────────────────────────────────────────────────────

    def has_any_user(self) -> bool:
        """Vérifie si au moins un utilisateur existe."""
        return self.users.count_documents({}, limit=1) > 0

    def register_user(self, username: str, password: str) -> tuple:
        """
        Enregistre un nouvel utilisateur.
        Retourne (totp_secret, error_message).
        error_message est None en cas de succès.
        """
        username = username.strip()

        # Validations
        if len(username) < 3:
            return None, "Le nom d'utilisateur doit contenir au moins 3 caractères."
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', username):
            return None, "Caractères autorisés : lettres, chiffres, _, -, ."
        if len(password) < 8:
            return None, "Le mot de passe doit contenir au moins 8 caractères."
        if not re.search(r'[A-Z]', password):
            return None, "Le mot de passe doit contenir au moins une majuscule."
        if not re.search(r'[0-9]', password):
            return None, "Le mot de passe doit contenir au moins un chiffre."

        if self.users.find_one({"username": username}):
            return None, "Ce nom d'utilisateur est déjà pris."

        hashed_pw   = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
        totp_secret = pyotp.random_base32()

        role = "admin" if not self.has_any_user() else "user"

        self.users.insert_one({
            "username":       username,
            "password":       hashed_pw,
            "totp_secret":    totp_secret,
            "role":           role,
            "active":         True,
            "created_at":     datetime.datetime.utcnow(),
            "last_login":     None,
            "login_attempts": 0,
            "locked_until":   None,
        })
        return totp_secret, None

    def get_totp_uri(self, username: str, totp_secret: str) -> str:
        """Retourne l'URI otpauth:// pour Google Authenticator."""
        totp = pyotp.TOTP(totp_secret)
        return totp.provisioning_uri(
            name=username.strip(),
            issuer_name="SETRAF · CPT Analysis Studio"
        )

    def verify_totp_only(self, totp_secret: str, otp_code: str) -> bool:
        """Vérifie un code OTP sans passer par l'authentification complète."""
        return pyotp.TOTP(totp_secret).verify(otp_code.strip(), valid_window=1)

    # ─────────────────────────────────────────────────────────────────────────
    # Authentification
    # ─────────────────────────────────────────────────────────────────────────

    def authenticate(self, username: str, password: str, otp_code: str) -> tuple:
        """
        Authentifie un utilisateur (password + OTP).
        Retourne (jwt_token, error_message).
        error_message est None en cas de succès.
        """
        username = username.strip()
        user = self.users.find_one({"username": username, "active": True})
        if not user:
            return None, "Identifiant ou mot de passe incorrect."

        # Vérifie verrouillage
        locked_until = user.get("locked_until")
        if locked_until and datetime.datetime.utcnow() < locked_until:
            remaining = int((locked_until - datetime.datetime.utcnow()).total_seconds())
            return None, f"Compte verrouillé — réessayez dans {remaining}s."

        # Vérifie mot de passe
        if not bcrypt.checkpw(password.encode("utf-8"), user["password"]):
            attempts = user.get("login_attempts", 0) + 1
            upd = {"login_attempts": attempts}
            if attempts >= _MAX_ATTEMPTS:
                upd["locked_until"] = (
                    datetime.datetime.utcnow() + datetime.timedelta(minutes=_LOCKOUT_MINUTES)
                )
                upd["login_attempts"] = 0
                err_msg = (
                    f"Trop de tentatives — compte verrouillé {_LOCKOUT_MINUTES} minutes."
                )
            else:
                remaining_att = _MAX_ATTEMPTS - attempts
                err_msg = (
                    f"Identifiant ou mot de passe incorrect. "
                    f"({remaining_att} tentative{'s' if remaining_att > 1 else ''} restante{'s' if remaining_att > 1 else ''})"
                )
            self.users.update_one({"username": username}, {"$set": upd})
            return None, err_msg

        # Vérifie OTP
        if not self.verify_totp_only(user["totp_secret"], otp_code):
            return None, "Code OTP invalide — vérifiez Google Authenticator."

        # Génère JWT
        now = datetime.datetime.utcnow()
        exp = now + datetime.timedelta(seconds=_SESSION_DURATION)
        jti = secrets.token_hex(16)   # identifiant unique de la session
        payload = {
            "sub":  username,
            "iat":  now,
            "exp":  exp,
            "role": user.get("role", "user"),
            "jti":  jti,
        }
        token = jwt.encode(payload, _SECRET_KEY, algorithm="HS256")

        # Persiste en base
        self.users.update_one(
            {"username": username},
            {"$set": {"last_login": now, "login_attempts": 0, "locked_until": None}},
        )
        self.sessions.update_one(
            {"username": username},
            {"$set": {
                "token":      token,
                "expires_at": exp,
                "created_at": now,
                "jti":        jti,
            }},
            upsert=True,
        )
        return token, None

    # ─────────────────────────────────────────────────────────────────────────
    # Token / Session
    # ─────────────────────────────────────────────────────────────────────────

    def verify_token(self, token: str) -> tuple:
        """
        Vérifie la validité d'un JWT.
        Retourne (username, error_message).
        """
        if not token:
            return None, "Aucun token de session."
        try:
            payload = jwt.decode(token, _SECRET_KEY, algorithms=["HS256"])
            return payload["sub"], None
        except jwt.ExpiredSignatureError:
            return None, "Session expirée."
        except jwt.InvalidTokenError:
            return None, "Token de session invalide."

    def get_expiry(self, token: str):
        """Retourne la datetime d'expiration UTC, ou None."""
        try:
            payload = jwt.decode(token, _SECRET_KEY, algorithms=["HS256"])
            return datetime.datetime.utcfromtimestamp(payload["exp"])
        except Exception:
            return None

    def remaining_seconds(self, token: str) -> int:
        """Retourne les secondes restantes (0 si expiré / invalide)."""
        exp = self.get_expiry(token)
        if not exp:
            return 0
        return max(0, int((exp - datetime.datetime.utcnow()).total_seconds()))

    def revoke_token(self, token: str):
        """Révoque la session (supprime de la base)."""
        try:
            payload = jwt.decode(token, _SECRET_KEY, algorithms=["HS256"])
            self.sessions.delete_one({"username": payload["sub"]})
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # Nettoyage
    # ─────────────────────────────────────────────────────────────────────────

    def close(self):
        try:
            self.client.close()
        except Exception:
            pass
