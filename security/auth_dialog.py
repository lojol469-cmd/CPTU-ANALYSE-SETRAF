"""
SETRAF CPT Analysis Studio — Auth Dialog (PySide6)
====================================================
Dialogue d'authentification complet :
  PAGE 0 — LOGIN         : username + password + OTP 6 chiffres
  PAGE 1 — SETUP         : création de compte (1re fois)
  PAGE 2 — QR_CODE       : affichage QR Google Authenticator
  PAGE 3 — OTP_CONFIRM   : confirmation après scan QR

+ SessionLockScreen : écran de verrouillage (session expirée)
"""
import io
import os

import pyotp
import qrcode

from PySide6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QWidget, QFrame,
    QStackedWidget, QSizePolicy, QMessageBox,
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QFont, QColor

# ── Palette ───────────────────────────────────────────────────────────────────
_DARK_BG  = "#16140e"
_CARD_BG  = "#1e1b14"
_ORANGE   = "#C1550F"
_ORANGE_L = "#F59B3A"
_TEXT     = "#F0E1C3"
_MUTED    = "#9B8E7D"
_BORDER   = "#3a3020"
_ERR      = "#e05050"
_OK       = "#4caf50"
_INPUT_BG = "#2a2418"

_STYLE = f"""
QWidget {{
    background-color: {_DARK_BG};
    color: {_TEXT};
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}}
QLineEdit {{
    background-color: {_INPUT_BG};
    color: {_TEXT};
    border: 1.5px solid {_BORDER};
    border-radius: 6px;
    padding: 9px 12px;
    min-height: 18px;
}}
QLineEdit:focus {{
    border-color: {_ORANGE};
    background-color: #2e2a1c;
}}
QPushButton#primary {{
    background-color: {_ORANGE};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-size: 13px;
    font-weight: bold;
    min-height: 40px;
}}
QPushButton#primary:hover   {{ background-color: {_ORANGE_L}; }}
QPushButton#primary:pressed {{ background-color: #9d4409; }}
QPushButton#primary:disabled{{
    background-color: #5a3a1a;
    color: #888;
}}
QPushButton#ghost {{
    background-color: transparent;
    color: {_ORANGE_L};
    border: none;
    padding: 6px;
    font-size: 12px;
    text-decoration: underline;
}}
QPushButton#ghost:hover {{ color: {_TEXT}; }}
QPushButton#back {{
    background-color: transparent;
    color: {_MUTED};
    border: 1px solid {_BORDER};
    border-radius: 5px;
    padding: 7px 14px;
    font-size: 11px;
}}
QPushButton#back:hover {{ color: {_TEXT}; border-color: {_MUTED}; }}
QLabel#title {{
    font-size: 17px;
    font-weight: bold;
    color: {_ORANGE};
}}
QLabel#sub {{
    font-size: 11px;
    color: {_MUTED};
    line-height: 1.4;
}}
QLabel#errL  {{ color: {_ERR}; font-size: 11px; padding: 3px 0; }}
QLabel#okL   {{ color: {_OK};  font-size: 11px; padding: 3px 0; }}
QLabel#timer {{ font-size: 11px; color: {_MUTED}; }}
QFrame#sep   {{ background-color: {_BORDER}; max-height: 1px; }}
QFrame#card  {{
    background-color: {_CARD_BG};
    border: 1px solid {_BORDER};
    border-radius: 12px;
}}
"""

# ── Pages ─────────────────────────────────────────────────────────────────────
PAGE_LOGIN       = 0
PAGE_SETUP       = 1
PAGE_QR          = 2
PAGE_OTP_CONFIRM = 3


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_qr_pixmap(uri: str, size: int = 220) -> QPixmap:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=7,
        border=3,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    img  = qr.make_image(fill_color="#111111", back_color="#ffffff")
    buf  = io.BytesIO()
    img.save(buf, format="PNG")
    pix  = QPixmap()
    pix.loadFromData(buf.getvalue())
    return pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


def _sep() -> QFrame:
    f = QFrame()
    f.setObjectName("sep")
    f.setFixedHeight(1)
    return f


def _err_lbl() -> QLabel:
    lbl = QLabel()
    lbl.setObjectName("errL")
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setWordWrap(True)
    lbl.hide()
    return lbl


class _PwField(QWidget):
    """QLineEdit mot de passe avec bouton œil."""

    def __init__(self, placeholder="🔒  Mot de passe", parent=None):
        super().__init__(parent)
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        self.field = QLineEdit()
        self.field.setPlaceholderText(placeholder)
        self.field.setEchoMode(QLineEdit.Password)
        self.field.setStyleSheet(
            f"QLineEdit {{ border-radius: 6px 0 0 6px; }}"
        )
        self.btn = QPushButton("👁")
        self.btn.setFixedSize(38, 38)
        self.btn.setStyleSheet(
            f"QPushButton {{"
            f"  background:{_INPUT_BG}; border:1.5px solid {_BORDER};"
            f"  border-left:none; border-radius:0 6px 6px 0;"
            f"  color:{_MUTED}; font-size:14px;"
            f"}}"
            f"QPushButton:hover {{ color:{_TEXT}; }}"
        )
        self.btn.clicked.connect(self._toggle)
        h.addWidget(self.field, 1)
        h.addWidget(self.btn)

    def _toggle(self):
        if self.field.echoMode() == QLineEdit.Password:
            self.field.setEchoMode(QLineEdit.Normal)
            self.btn.setText("🙈")
        else:
            self.field.setEchoMode(QLineEdit.Password)
            self.btn.setText("👁")

    def text(self):         return self.field.text()
    def clear(self):        self.field.clear()


# ══════════════════════════════════════════════════════════════════════════════
#  DIALOGUE PRINCIPAL D'AUTHENTIFICATION
# ══════════════════════════════════════════════════════════════════════════════

class AuthDialog(QDialog):
    """
    Dialogue complet d'authentification avec :
     - Connexion (login + OTP)
     - Premier setup (création compte + QR code)
     - Confirmation OTP post-inscription
    """

    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self._am              = auth_manager
        self.session_token    = None       # rempli après succès
        self._reg_secret      = None       # secret TOTP en cours d'inscription
        self._reg_username    = None

        self.setWindowTitle("SETRAF CPT Analysis Studio — Authentification")
        self.setFixedWidth(430)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setStyleSheet(_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("card")
        card_v = QVBoxLayout(card)
        card_v.setContentsMargins(32, 26, 32, 26)
        card_v.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._page_login())        # 0
        self.stack.addWidget(self._page_setup())        # 1
        self.stack.addWidget(self._page_qr())           # 2
        self.stack.addWidget(self._page_otp_confirm())  # 3

        card_v.addWidget(self.stack)
        root.addWidget(card)

        # Démarre sur la bonne page
        if not self._am.has_any_user():
            self.stack.setCurrentIndex(PAGE_SETUP)
        else:
            self.stack.setCurrentIndex(PAGE_LOGIN)

        self.adjustSize()

    # ── Logo ─────────────────────────────────────────────────────────────────

    def _logo(self) -> QLabel:
        lbl = QLabel()
        logo_path = os.path.join(
            os.path.dirname(__file__), "..", "app", "setraf_logo.png"
        )
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaledToHeight(56, Qt.SmoothTransformation)
            lbl.setPixmap(pix)
        else:
            lbl.setText("SETRAF")
            lbl.setStyleSheet(f"font-size:22px;font-weight:bold;color:{_ORANGE};")
        lbl.setAlignment(Qt.AlignCenter)
        return lbl

    # ── PAGE 0 : LOGIN ────────────────────────────────────────────────────────

    def _page_login(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(9)

        v.addWidget(self._logo())
        v.addSpacing(4)

        t = QLabel("Connexion Sécurisée")
        t.setObjectName("title")
        t.setAlignment(Qt.AlignCenter)
        v.addWidget(t)

        s = QLabel("SETRAF · CPT Analysis Studio")
        s.setObjectName("sub")
        s.setAlignment(Qt.AlignCenter)
        v.addWidget(s)

        v.addSpacing(6)
        v.addWidget(_sep())
        v.addSpacing(8)

        self._li_user = QLineEdit()
        self._li_user.setPlaceholderText("👤  Nom d'utilisateur")
        v.addWidget(self._li_user)

        self._li_pw = _PwField("🔒  Mot de passe")
        v.addWidget(self._li_pw)

        self._li_otp = QLineEdit()
        self._li_otp.setPlaceholderText("🔑  Code Google Authenticator (6 chiffres)")
        self._li_otp.setMaxLength(6)
        self._li_otp.returnPressed.connect(self._do_login)
        v.addWidget(self._li_otp)

        self._li_err = _err_lbl()
        v.addWidget(self._li_err)

        self._btn_login = QPushButton("  Se connecter")
        self._btn_login.setObjectName("primary")
        self._btn_login.clicked.connect(self._do_login)
        v.addWidget(self._btn_login)

        v.addSpacing(4)
        v.addWidget(_sep())
        v.addSpacing(4)

        btn_setup = QPushButton("Première connexion / Créer un compte administrateur")
        btn_setup.setObjectName("ghost")
        btn_setup.clicked.connect(lambda: self.stack.setCurrentIndex(PAGE_SETUP))
        v.addWidget(btn_setup)

        v.addSpacing(10)
        lbl_sec = QLabel("🔒  Chiffrement JWT · TOTP RFC6238 · bcrypt · MongoDB Atlas")
        lbl_sec.setObjectName("sub")
        lbl_sec.setAlignment(Qt.AlignCenter)
        v.addWidget(lbl_sec)

        return w

    # ── PAGE 1 : SETUP ────────────────────────────────────────────────────────

    def _page_setup(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(9)

        v.addWidget(self._logo())
        v.addSpacing(4)

        t = QLabel("Créer un compte Administrateur")
        t.setObjectName("title")
        t.setAlignment(Qt.AlignCenter)
        v.addWidget(t)

        s = QLabel(
            "Configurez votre accès sécurisé.\n"
            "Vous aurez besoin de l'application Google Authenticator."
        )
        s.setObjectName("sub")
        s.setAlignment(Qt.AlignCenter)
        s.setWordWrap(True)
        v.addWidget(s)

        v.addSpacing(6)
        v.addWidget(_sep())
        v.addSpacing(8)

        self._su_user = QLineEdit()
        self._su_user.setPlaceholderText("👤  Nom d'utilisateur (3+ car.)")
        v.addWidget(self._su_user)

        self._su_pw = _PwField("🔒  Mot de passe (8+ car., 1 maj., 1 chiffre)")
        v.addWidget(self._su_pw)

        self._su_pw2 = _PwField("🔒  Confirmer le mot de passe")
        v.addWidget(self._su_pw2)

        self._su_err = _err_lbl()
        v.addWidget(self._su_err)

        btn = QPushButton("  Créer le compte →")
        btn.setObjectName("primary")
        btn.clicked.connect(self._do_register)
        v.addWidget(btn)

        v.addStretch()

        btn_back = QPushButton("← Déjà un compte ? Se connecter")
        btn_back.setObjectName("back")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(PAGE_LOGIN))
        v.addWidget(btn_back)

        return w

    # ── PAGE 2 : QR CODE ─────────────────────────────────────────────────────

    def _page_qr(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(8)

        t = QLabel("Scanner avec Google Authenticator")
        t.setObjectName("title")
        t.setAlignment(Qt.AlignCenter)
        v.addWidget(t)

        instr = QLabel(
            "1. Ouvrez Google Authenticator sur votre téléphone\n"
            "2. Appuyez sur  +  →  Scanner un code QR\n"
            "3. Pointez l'appareil photo vers le QR code ci-dessous"
        )
        instr.setObjectName("sub")
        instr.setAlignment(Qt.AlignCenter)
        instr.setWordWrap(True)
        v.addWidget(instr)

        v.addWidget(_sep())

        # QR code
        self._lbl_qr = QLabel()
        self._lbl_qr.setAlignment(Qt.AlignCenter)
        self._lbl_qr.setStyleSheet(
            "background:white; border-radius:10px; padding:10px;"
        )
        self._lbl_qr.setFixedSize(250, 250)
        row = QWidget()
        rh  = QHBoxLayout(row)
        rh.setContentsMargins(0, 0, 0, 0)
        rh.addStretch()
        rh.addWidget(self._lbl_qr)
        rh.addStretch()
        v.addWidget(row)

        # Code manuel
        self._lbl_manual = QLabel()
        self._lbl_manual.setAlignment(Qt.AlignCenter)
        self._lbl_manual.setStyleSheet(
            f"color:{_ORANGE_L}; font-family:Consolas,monospace; font-size:12px;"
            f"background:{_INPUT_BG}; border-radius:6px; padding:8px 14px;"
        )
        self._lbl_manual.setWordWrap(True)
        v.addWidget(self._lbl_manual)

        btn = QPushButton("  J'ai scanné le QR code →  Confirmer le code OTP")
        btn.setObjectName("primary")
        btn.clicked.connect(lambda: self.stack.setCurrentIndex(PAGE_OTP_CONFIRM))
        v.addWidget(btn)

        return w

    # ── PAGE 3 : OTP CONFIRM ─────────────────────────────────────────────────

    def _page_otp_confirm(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setSpacing(10)

        t = QLabel("Confirmer l'OTP")
        t.setObjectName("title")
        t.setAlignment(Qt.AlignCenter)
        v.addWidget(t)

        s = QLabel(
            "Entrez le code à 6 chiffres affiché\n"
            "dans Google Authenticator pour finaliser."
        )
        s.setObjectName("sub")
        s.setAlignment(Qt.AlignCenter)
        s.setWordWrap(True)
        v.addWidget(s)

        v.addWidget(_sep())

        self._conf_otp = QLineEdit()
        self._conf_otp.setPlaceholderText("  🔑  0  0  0  0  0  0")
        self._conf_otp.setMaxLength(6)
        self._conf_otp.setAlignment(Qt.AlignCenter)
        self._conf_otp.setStyleSheet(
            f"font-size: 26px; letter-spacing: 8px; "
            f"background:{_INPUT_BG}; color:{_ORANGE_L}; "
            f"border: 1.5px solid {_ORANGE}; border-radius: 8px; "
            f"padding: 12px;"
        )
        self._conf_otp.returnPressed.connect(self._do_confirm_otp)
        v.addWidget(self._conf_otp)

        self._conf_err = _err_lbl()
        v.addWidget(self._conf_err)

        btn = QPushButton("  Valider et accéder à l'application  ✓")
        btn.setObjectName("primary")
        btn.clicked.connect(self._do_confirm_otp)
        v.addWidget(btn)

        v.addStretch()

        btn_back = QPushButton("← Retour au QR code")
        btn_back.setObjectName("back")
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(PAGE_QR))
        v.addWidget(btn_back)

        return w

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _do_login(self):
        username = self._li_user.text().strip()
        password = self._li_pw.text()
        otp      = self._li_otp.text().strip()

        if not username or not password or not otp:
            self._li_err.setText("Tous les champs sont obligatoires.")
            self._li_err.show()
            return

        self._btn_login.setEnabled(False)
        self._btn_login.setText("Vérification en cours…")
        QApplication.processEvents()

        token, err = self._am.authenticate(username, password, otp)

        self._btn_login.setEnabled(True)
        self._btn_login.setText("  Se connecter")

        if err:
            self._li_err.setText(err)
            self._li_err.show()
            return

        self.session_token = token
        self.accept()

    def _do_register(self):
        username = self._su_user.text().strip()
        password = self._su_pw.text()
        confirm  = self._su_pw2.text()

        if not username or not password or not confirm:
            self._su_err.setText("Tous les champs sont obligatoires.")
            self._su_err.show()
            return

        if password != confirm:
            self._su_err.setText("Les mots de passe ne correspondent pas.")
            self._su_err.show()
            return

        totp_secret, err = self._am.register_user(username, password)
        if err:
            self._su_err.setText(err)
            self._su_err.show()
            return

        self._reg_secret   = totp_secret
        self._reg_username = username

        # Génère et affiche le QR code
        uri = self._am.get_totp_uri(username, totp_secret)
        pix = _make_qr_pixmap(uri, size=230)
        self._lbl_qr.setPixmap(pix)
        self._lbl_manual.setText(
            f"Clé manuelle (si scan impossible) :\n{totp_secret}"
        )
        self._conf_otp.clear()
        self._conf_err.hide()
        self.stack.setCurrentIndex(PAGE_QR)

    def _do_confirm_otp(self):
        otp = self._conf_otp.text().strip()
        if len(otp) < 6:
            self._conf_err.setText("Entrez le code complet à 6 chiffres.")
            self._conf_err.show()
            return

        if not self._am.verify_totp_only(self._reg_secret, otp):
            self._conf_err.setText("Code incorrect — attendez le prochain code et réessayez.")
            self._conf_err.show()
            return

        # Succès — prérempli le login
        self._li_user.setText(self._reg_username)
        self._li_otp.clear()
        self._li_pw.clear()
        self._li_err.hide()

        QMessageBox.information(
            self,
            "Configuration terminée !",
            f"Votre compte «{self._reg_username}» est prêt.\n\n"
            "Google Authenticator est configuré.\n"
            "Connectez-vous maintenant avec votre mot de passe et votre code OTP.",
        )
        self.stack.setCurrentIndex(PAGE_LOGIN)


# ══════════════════════════════════════════════════════════════════════════════
#  ÉCRAN DE VERROUILLAGE (session expirée)
# ══════════════════════════════════════════════════════════════════════════════

class SessionLockScreen(QDialog):
    """
    Dialogue modal affiché quand la session d'une heure expire.
    Permet de se reconnecter sans fermer l'application et perdre le travail.
    """

    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self._am           = auth_manager
        self.session_token = None

        self.setWindowTitle("Session expirée — Reconnexion requise")
        self.setFixedWidth(400)
        self.setWindowFlags(
            Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setModal(True)
        self.setStyleSheet(_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet(
            f"QFrame#card {{ background:{_CARD_BG}; "
            f"border: 2px solid {_ORANGE}; border-radius: 12px; }}"
        )
        v = QVBoxLayout(card)
        v.setContentsMargins(30, 26, 30, 26)
        v.setSpacing(10)

        ico = QLabel("🔐")
        ico.setAlignment(Qt.AlignCenter)
        ico.setStyleSheet("font-size:38px; background:transparent;")
        v.addWidget(ico)

        title = QLabel("Session Expirée")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)

        sub = QLabel(
            "Votre session d'une heure a expiré.\n"
            "Veuillez vous reconnecter pour continuer."
        )
        sub.setObjectName("sub")
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        v.addWidget(sub)

        v.addWidget(_sep())

        self._lu = QLineEdit()
        self._lu.setPlaceholderText("👤  Nom d'utilisateur")
        v.addWidget(self._lu)

        self._lp = _PwField()
        v.addWidget(self._lp)

        self._lo = QLineEdit()
        self._lo.setPlaceholderText("🔑  Code Google Authenticator")
        self._lo.setMaxLength(6)
        self._lo.returnPressed.connect(self._do_unlock)
        v.addWidget(self._lo)

        self._lerr = _err_lbl()
        v.addWidget(self._lerr)

        btn_ok = QPushButton("  Reprendre la session")
        btn_ok.setObjectName("primary")
        btn_ok.clicked.connect(self._do_unlock)
        v.addWidget(btn_ok)

        v.addSpacing(4)

        btn_quit = QPushButton("Fermer l'application")
        btn_quit.setObjectName("back")
        btn_quit.clicked.connect(self.reject)
        v.addWidget(btn_quit)

        root.addWidget(card)
        self.adjustSize()

    def _do_unlock(self):
        u  = self._lu.text().strip()
        p  = self._lp.text()
        ot = self._lo.text().strip()

        if not u or not p or not ot:
            self._lerr.setText("Tous les champs sont obligatoires.")
            self._lerr.show()
            return

        token, err = self._am.authenticate(u, p, ot)
        if err:
            self._lerr.setText(err)
            self._lerr.show()
            return

        self.session_token = token
        self.accept()
