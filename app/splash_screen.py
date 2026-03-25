"""
Splash screen CPTU SETRAF ANALYSE
Affiche le logo + animation SVG au démarrage pendant le chargement.
"""
import os
from PySide6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget, QProgressBar
from PySide6.QtCore    import Qt, QTimer, QSize, QUrl
from PySide6.QtGui     import QPixmap, QColor, QPainter, QFont, QPen, QBrush, QLinearGradient
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

# ── Couleurs ────────────────────────────────────────────────────────────────
BG_COLOR     = QColor(22,  20,  18)
ORANGE_DARK  = QColor(193, 85,  15)
ORANGE_MID   = QColor(218, 112, 28)
ORANGE_LIGHT = QColor(245, 155, 58)
CREAM        = QColor(240, 225, 195)


class SplashScreen(QWidget):
    """Splash screen avec logo + animation SVG des 4 activités CPTU."""

    def __init__(self):
        super().__init__()
        self._progress = 0
        self._setup_window()
        self._build_ui()
        self._start_progress()

    # ── Fenêtre ──────────────────────────────────────────────────────────────
    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(960, 620)
        # Centrer à l'écran
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width()  - self.width())  // 2,
            (screen.height() - self.height()) // 2,
        )

    # ── Interface ────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Container principal avec fond arrondi
        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet("""
            QWidget#container {
                background-color: #16140e;
                border: 2px solid #DA701C;
                border-radius: 16px;
            }
        """)
        root.addWidget(container)

        inner = QVBoxLayout(container)
        inner.setContentsMargins(0, 0, 0, 0)
        inner.setSpacing(0)

        # ── En-tête (logo + titre)
        header = self._make_header()
        inner.addWidget(header)

        # ── Animation SVG
        self._web = self._make_web_view()
        inner.addWidget(self._web, stretch=1)

        # ── Pied de page (barre de progression + message)
        footer = self._make_footer()
        inner.addWidget(footer)

    # ── En-tête ──────────────────────────────────────────────────────────────
    def _make_header(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(90)
        w.setStyleSheet("background: #1e1a12; border-bottom: 1px solid #3a2c18;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 8, 20, 8)
        lay.setSpacing(2)

        # Logo icône (si disponible)
        icon_row_widget = QWidget()
        icon_row = QVBoxLayout(icon_row_widget)
        icon_row.setContentsMargins(0, 0, 0, 0)

        # Cherche logo ico/png
        here = os.path.dirname(__file__)
        logo_label = QLabel()
        for fname in ["icon.ico", "logo_square.png", "LOGO VECTORISE PNG.png"]:
            path = os.path.join(here, fname)
            if os.path.exists(path):
                pix = QPixmap(path)
                if not pix.isNull():
                    logo_label.setPixmap(pix.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio,
                                                    Qt.TransformationMode.SmoothTransformation))
                    break

        # Titre
        title = QLabel("CPTU SETRAF ANALYSE")
        title.setFont(QFont("Arial Black", 24, QFont.Weight.Black))
        title.setStyleSheet("color: #F59B3A; letter-spacing: 4px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Logiciel d'Analyse Géotechnique CPTU  •  Chargement en cours…")
        subtitle.setFont(QFont("Arial", 9))
        subtitle.setStyleSheet("color: #a07840; letter-spacing: 2px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lay.addWidget(logo_label, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)
        lay.addWidget(subtitle)

        return w

    # ── Vue SVG ──────────────────────────────────────────────────────────────
    def _make_web_view(self) -> QWebEngineView:
        view = QWebEngineView()
        view.setStyleSheet("background: transparent; border: none;")
        svg_path = os.path.join(os.path.dirname(__file__), "cptu_animation.svg")
        if os.path.exists(svg_path):
            # Embed le SVG dans une page HTML avec fond noir
            svg_url = QUrl.fromLocalFile(svg_path)
            html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{ width:100%; height:100%; background:#16140e; overflow:hidden; }}
  object {{ width:100%; height:100%; }}
</style>
</head>
<body>
  <object type="image/svg+xml" data="{svg_url.toString()}"></object>
</body>
</html>"""
            view.setHtml(html, svg_url)
        else:
            # Fallback texte si SVG manquant
            view.setHtml("""<body style='background:#16140e;color:#F59B3A;
                font-family:Arial;text-align:center;padding-top:80px;font-size:18px;'>
                Animation CPTU en cours de chargement…</body>""")
        return view

    # ── Pied de page ─────────────────────────────────────────────────────────
    def _make_footer(self) -> QWidget:
        w = QWidget()
        w.setFixedHeight(52)
        w.setStyleSheet("background: #1a1710; border-top: 1px solid #3a2c18;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 6, 20, 6)
        lay.setSpacing(4)

        self._status_label = QLabel("Initialisation de l'application…")
        self._status_label.setFont(QFont("Arial", 8))
        self._status_label.setStyleSheet("color: #a07840;")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2a2018;
                border: 1px solid #3a2c18;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #C1550F, stop:0.5 #F59B3A, stop:1 #DA701C);
                border-radius: 3px;
            }
        """)

        lay.addWidget(self._status_label)
        lay.addWidget(self._progress_bar)
        return w

    # ── Progression animée ───────────────────────────────────────────────────
    _STEPS = [
        (10,  "Chargement des modules Python…"),
        (25,  "Initialisation de l'interface Qt…"),
        (42,  "Chargement des outils géotechniques…"),
        (58,  "Vérification de l'intégrité des données…"),
        (72,  "Préparation des visualisations…"),
        (85,  "Connexion au moteur d'analyse…"),
        (95,  "Finalisation…"),
        (100, "Démarrage de CPTU SETRAF ANALYSE ✓"),
    ]

    def _start_progress(self):
        self._step_idx = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick_progress)
        self._timer.start(350)

    def _tick_progress(self):
        if self._step_idx >= len(self._STEPS):
            self._timer.stop()
            return
        val, msg = self._STEPS[self._step_idx]
        self._progress_bar.setValue(val)
        self._status_label.setText(msg)
        self._step_idx += 1

    def set_status(self, message: str, value: int = -1):
        """Appelable depuis l'extérieur pour mettre à jour le message."""
        self._status_label.setText(message)
        if 0 <= value <= 100:
            self._progress_bar.setValue(value)

    def finish_and_close(self, main_window):
        """Termine la barre à 100 % puis ferme le splash après 400 ms."""
        self._timer.stop()
        self._progress_bar.setValue(100)
        self._status_label.setText("Démarrage de CPTU SETRAF ANALYSE ✓")
        QTimer.singleShot(500, lambda: (self.close(), main_window.show()))
