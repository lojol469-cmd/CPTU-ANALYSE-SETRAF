"""
SETRAF CPT Analysis Studio — Dialogue Code PIN
===============================================
Premier verrou d'accès : code à 4 chiffres requis avant toute
authentification OTP ou chargement de l'application.

Usage :
    from pin_dialog import PinDialog
    dlg = PinDialog()
    if dlg.exec() != QDialog.Accepted:
        sys.exit(0)
"""
import os
import bcrypt

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QWidget, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPixmap

# ── Palette (identique au reste de l'app) ────────────────────────────────────
_DARK_BG  = "#16140e"
_CARD_BG  = "#1e1b14"
_ORANGE   = "#C1550F"
_ORANGE_L = "#F59B3A"
_TEXT     = "#F0E1C3"
_MUTED    = "#9B8E7D"
_BORDER   = "#3a3020"
_ERR      = "#e05050"
_INPUT_BG = "#2a2418"

_STYLE = f"""
QDialog, QWidget {{
    background-color: {_DARK_BG};
    color: {_TEXT};
    font-family: 'Segoe UI', Arial, sans-serif;
}}
QLabel#title {{
    font-size: 18px;
    font-weight: bold;
    color: {_ORANGE};
}}
QLabel#sub {{
    font-size: 11px;
    color: {_MUTED};
}}
QLabel#display {{
    font-size: 34px;
    font-family: Consolas, 'Courier New', monospace;
    font-weight: bold;
    color: {_ORANGE_L};
    background-color: {_INPUT_BG};
    border: 2px solid {_BORDER};
    border-radius: 10px;
    padding: 12px 24px;
    letter-spacing: 14px;
    qproperty-alignment: AlignCenter;
}}
QLabel#display_err {{
    font-size: 34px;
    font-family: Consolas, 'Courier New', monospace;
    font-weight: bold;
    color: {_ERR};
    background-color: #2a1414;
    border: 2px solid {_ERR};
    border-radius: 10px;
    padding: 12px 24px;
    letter-spacing: 14px;
    qproperty-alignment: AlignCenter;
}}
QLabel#display_ok {{
    font-size: 34px;
    font-family: Consolas, 'Courier New', monospace;
    font-weight: bold;
    color: #4caf50;
    background-color: #0e2010;
    border: 2px solid #4caf50;
    border-radius: 10px;
    padding: 12px 24px;
    letter-spacing: 14px;
    qproperty-alignment: AlignCenter;
}}
QPushButton#num {{
    background-color: {_CARD_BG};
    color: {_TEXT};
    border: 1.5px solid {_BORDER};
    border-radius: 10px;
    font-size: 20px;
    font-weight: bold;
    min-width: 72px;
    min-height: 62px;
    max-width: 72px;
    max-height: 62px;
}}
QPushButton#num:hover  {{ background-color: #2e2a1c; border-color: {_ORANGE}; color: {_ORANGE_L}; }}
QPushButton#num:pressed {{ background-color: {_ORANGE}; color: white; }}
QPushButton#del {{
    background-color: #261a10;
    color: {_MUTED};
    border: 1.5px solid {_BORDER};
    border-radius: 10px;
    font-size: 18px;
    min-width: 72px;
    min-height: 62px;
    max-width: 72px;
    max-height: 62px;
}}
QPushButton#del:hover  {{ color: {_ERR}; border-color: {_ERR}; }}
QPushButton#del:pressed {{ background-color: #3a0a0a; }}
QPushButton#ok {{
    background-color: {_ORANGE};
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 15px;
    font-weight: bold;
    min-width: 72px;
    min-height: 62px;
    max-width: 72px;
    max-height: 62px;
}}
QPushButton#ok:hover  {{ background-color: {_ORANGE_L}; }}
QPushButton#ok:pressed {{ background-color: #9d4409; }}
QFrame#sep {{ background-color: {_BORDER}; max-height: 1px; }}
QFrame#card {{
    background-color: {_CARD_BG};
    border: 1px solid {_BORDER};
    border-radius: 16px;
}}
"""

_PIN_MAX = 4


class PinDialog(QDialog):
    """
    Dialogue modal de code PIN (clavier numérique à l'écran).
    Appelle accept() si le PIN saisi correspond au hash stocké dans .env
    (CPT_ACCESS_PIN), reject() sinon (ou si annulé).

    Si CPT_ACCESS_PIN est absent de .env, aucun code n'est demandé
    et le dialogue accepte immédiatement. (mode dev non sécurisé)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pin_hash  = os.environ.get("CPT_ACCESS_PIN", "").encode()
        self._current   = ""
        self._attempts  = 0
        self._max_att   = 5
        self._locked    = False

        # Si aucun hash configuré, pas de vérification
        if not self._pin_hash:
            QTimer.singleShot(0, self.accept)
            return

        self.setWindowTitle("SETRAF CPT Analysis Studio — Accès sécurisé")
        self.setFixedSize(340, 560)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setModal(True)
        self.setStyleSheet(_STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)

        card = QFrame()
        card.setObjectName("card")
        v = QVBoxLayout(card)
        v.setContentsMargins(24, 24, 24, 24)
        v.setSpacing(12)

        # ── Logo ──────────────────────────────────────────────────────────────
        logo_lbl = QLabel()
        logo_path = os.path.join(
            os.path.dirname(__file__), "..", "app", "setraf_logo.png"
        )
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaledToHeight(52, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
        else:
            logo_lbl.setText("SETRAF")
            logo_lbl.setStyleSheet(
                f"font-size:20px; font-weight:bold; color:{_ORANGE};"
            )
        logo_lbl.setAlignment(Qt.AlignCenter)
        v.addWidget(logo_lbl)

        # ── Titre ─────────────────────────────────────────────────────────────
        title = QLabel("Code d'accès requis")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        v.addWidget(title)

        sub = QLabel("Entrez le code pour accéder à l'application.")
        sub.setObjectName("sub")
        sub.setAlignment(Qt.AlignCenter)
        sub.setWordWrap(True)
        v.addWidget(sub)

        # ── Séparateur ────────────────────────────────────────────────────────
        sep = QFrame(); sep.setObjectName("sep"); sep.setFixedHeight(1)
        v.addWidget(sep)

        # ── Afficheur PIN ─────────────────────────────────────────────────────
        self._display = QLabel("_ _ _ _")
        self._display.setObjectName("display")
        self._display.setAlignment(Qt.AlignCenter)
        v.addWidget(self._display)

        # ── Message d'erreur ─────────────────────────────────────────────────
        self._err_lbl = QLabel("")
        self._err_lbl.setObjectName("sub")
        self._err_lbl.setAlignment(Qt.AlignCenter)
        self._err_lbl.setStyleSheet(f"color: {_ERR}; font-size:11px;")
        self._err_lbl.hide()
        v.addWidget(self._err_lbl)

        # ── Clavier numérique ─────────────────────────────────────────────────
        keys = [
            ["1", "2", "3"],
            ["4", "5", "6"],
            ["7", "8", "9"],
        ]
        for row_keys in keys:
            row = QHBoxLayout()
            row.setSpacing(10)
            row.addStretch()
            for k in row_keys:
                btn = QPushButton(k)
                btn.setObjectName("num")
                btn.clicked.connect(lambda _, d=k: self._press(d))
                row.addWidget(btn)
            row.addStretch()
            v.addLayout(row)

        # Dernière ligne : ← | 0 | ✓
        last = QHBoxLayout()
        last.setSpacing(10)
        last.addStretch()

        btn_del = QPushButton("⌫")
        btn_del.setObjectName("del")
        btn_del.clicked.connect(self._backspace)
        last.addWidget(btn_del)

        btn_0 = QPushButton("0")
        btn_0.setObjectName("num")
        btn_0.clicked.connect(lambda: self._press("0"))
        last.addWidget(btn_0)

        btn_ok = QPushButton("✓")
        btn_ok.setObjectName("ok")
        btn_ok.clicked.connect(self._validate)
        last.addWidget(btn_ok)

        last.addStretch()
        v.addLayout(last)

        v.addStretch()

        # ── Fermer ────────────────────────────────────────────────────────────
        btn_quit = QPushButton("Annuler / Fermer")
        btn_quit.setStyleSheet(
            f"background:transparent; color:{_MUTED}; border:none; "
            f"font-size:11px; text-decoration:underline;"
        )
        btn_quit.clicked.connect(self.reject)
        v.addWidget(btn_quit)

        root.addWidget(card)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _update_display(self):
        n    = len(self._current)
        dots = "●" * n + "○" * (_PIN_MAX - n)
        self._display.setText(dots)
        self._display.setObjectName("display")
        self._display.setStyleSheet("")
        self._display.style().unpolish(self._display)
        self._display.style().polish(self._display)

    def _press(self, digit: str):
        if self._locked:
            return
        if len(self._current) < _PIN_MAX:
            self._current += digit
            self._update_display()
            self._err_lbl.hide()
        if len(self._current) == _PIN_MAX:
            # Auto-valider après la saisie du 4e chiffre
            QTimer.singleShot(120, self._validate)

    def _backspace(self):
        if self._locked:
            return
        self._current = self._current[:-1]
        self._update_display()
        self._err_lbl.hide()

    def _validate(self):
        if self._locked:
            return

        entered = self._current.encode()
        self._current = ""

        try:
            ok = bcrypt.checkpw(entered, self._pin_hash)
        except Exception:
            ok = False

        if ok:
            # Affiche un flash vert avant de fermer
            self._display.setText("✓ ✓ ✓ ✓")
            self._display.setObjectName("display_ok")
            self._display.setStyleSheet("")
            self._err_lbl.hide()
            QTimer.singleShot(400, self.accept)
        else:
            self._attempts += 1
            remaining = self._max_att - self._attempts

            self._display.setText("✗ ✗ ✗ ✗")
            self._display.setObjectName("display_err")
            self._display.setStyleSheet("")

            if remaining <= 0:
                self._locked = True
                self._err_lbl.setText(
                    "Trop de tentatives.\nFermeture dans 5 secondes…"
                )
                self._err_lbl.show()
                QTimer.singleShot(5000, self.reject)
            else:
                self._err_lbl.setText(
                    f"Code incorrect — {remaining} tentative{'s' if remaining > 1 else ''} restante{'s' if remaining > 1 else ''}."
                )
                self._err_lbl.show()
                QTimer.singleShot(600, self._update_display)
