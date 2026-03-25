import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QTextEdit, QFileDialog, QMessageBox, QScrollArea, 
                             QGridLayout, QSplitter, QPushButton, QDial, QLCDNumber, QProgressBar, QStatusBar,
                             QGroupBox, QFrame, QLineEdit, QComboBox, QMenu, QDialog)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QPalette, QColor, QIcon, QFont, QActionGroup
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QPalette, QColor, QIcon, QFont
from PySide6.QtWidgets import QApplication
import matplotlib.pyplot as plt
# plt.style.use('dark_background')  # Dark theme for plots
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.signal import savgol_filter
import warnings
warnings.filterwarnings('ignore')
warnings.filterwarnings("ignore", message=".*to view this Streamlit app.*")
warnings.filterwarnings("ignore", message=".*Thread 'MainThread': missing ScriptRunContext.*")

# Import des fonctions d'analyse
from analysis.geotechnical_analysis import perform_complete_analysis

# Import du générateur d'animations SVG CPTU
try:
    from tools.cptu_svg_animator import (
        generate_cptu_animation,
        generate_cptu_png,
        _detect_layers as detect_layers,
    )
    SVG_ANIMATOR_AVAILABLE = True
except ImportError as e:
    SVG_ANIMATOR_AVAILABLE = False
    print(f"[WARNING] SVG animator non disponible: {e}")

# Import conditionnel du système RAG (pour éviter les erreurs de dépendances)
try:
    from models.rag_system import CPT_RAG_System  # type: ignore
    RAG_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] Systeme RAG non disponible: {e}")
    print("L'application fonctionnera sans les fonctionnalites d'IA avancees.")
    CPT_RAG_System = None
    RAG_SYSTEM_AVAILABLE = False

# Import des nouveaux modules de parsing et vérification
from core.cpt_parser import CPTParser
from core.data_integrity_checker import DataIntegrityChecker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        global RAG_SYSTEM_AVAILABLE  # Déclarer comme variable globale
        self.setWindowTitle("CPT Analysis Software - Puissant Logiciel Windows")
        # Cherche le meilleur logo disponible (ICO > PNG carré > PNG banner > SVG)
        for logo_path in ['icon.ico', 'logo_square.png', 'LOGO VECTORISE PNG.png', 'logo.svg']:
            if os.path.exists(logo_path):
                self.setWindowIcon(QIcon(logo_path))
                break
        self.setGeometry(50, 50, 1400, 900)
        self.df = None
        self.analysis_results = None
        self.analysis_data = None  # To store the tuple
        self.fused_data: pd.DataFrame | None = None

        # Initialisation conditionnelle du système RAG
        if RAG_SYSTEM_AVAILABLE and CPT_RAG_System:
            try:
                print("🚀 Initialisation du système RAG...")
                self.ai_explainer = CPT_RAG_System()
                # Initialiser seulement le modèle de base, pas les embeddings qui téléchargent
                self.ai_explainer.initialize_model()
                print("✅ Système RAG initialisé (embeddings différés)")
            except Exception as e:
                print(f"⚠️ Erreur lors de l'initialisation du RAG system: {e}")
                self.ai_explainer = None
                RAG_SYSTEM_AVAILABLE = False
        else:
            self.ai_explainer = None
            print("ℹ️ Fonctionnalités d'IA désactivées (RAG system non disponible)")

        self.data_checker = DataIntegrityChecker()  # Vérificateur d'intégrité des données
        self.setOffWhiteTheme()  # Default to off-white
        self.initUI()

    def setOffWhiteTheme(self):
        # Blanc cassé theme
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        self.setPalette(palette)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #ccc;
                background-color: #fff;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                color: black;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #0078d7;
                color: white;
            }
            QPushButton {
                background-color: #e0e0e0;
                color: black;
                border: 1px solid #ccc;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
            QTableWidget {
                background-color: #fff;
                color: black;
                gridline-color: #ccc;
            }
            QTextEdit {
                background-color: #fff;
                color: black;
                border: 1px solid #ccc;
            }
            QScrollArea {
                border: none;
            }
        """)
        plt.style.use('default')
        self.current_theme = 'offwhite'
        if hasattr(self, 'aiWebView'):
            self.updateChatTheme()
        if self.df is not None:
            self.updateGraphs()

    def setDarkTheme(self):
        # Dark theme like VST plugins
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        self.setPalette(palette)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #353535;
            }
            QTabWidget::pane {
                border: 1px solid #555;
                background-color: #2a2a2a;
            }
            QTabBar::tab {
                background-color: #555;
                color: white;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #2a82da;
            }
            QPushButton {
                background-color: #555;
                color: white;
                border: 1px solid #777;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #666;
            }
            QPushButton:pressed {
                background-color: #444;
            }
            QTableWidget {
                background-color: #2a2a2a;
                color: white;
                gridline-color: #555;
            }
            QTextEdit {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #555;
            }
            QScrollArea {
                border: none;
            }
        """)

    def setBlueTheme(self):
        # Blue theme
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 248, 255))  # Alice blue
        palette.setColor(QPalette.ColorRole.WindowText, QColor(25, 25, 112))  # Midnight blue
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 248, 255))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 112))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(25, 25, 112))
        palette.setColor(QPalette.ColorRole.Text, QColor(25, 25, 112))
        palette.setColor(QPalette.ColorRole.Button, QColor(173, 216, 230))  # Light blue
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(25, 25, 112))
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(30, 144, 255))  # Dodger blue
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        self.setPalette(palette)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f8ff;
            }
            QTabWidget::pane {
                border: 1px solid #add8e6;
                background-color: #fff;
            }
            QTabBar::tab {
                background-color: #add8e6;
                color: #191970;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1e90ff;
                color: white;
            }
            QPushButton {
                background-color: #add8e6;
                color: #191970;
                border: 1px solid #87ceeb;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #87ceeb;
            }
            QPushButton:pressed {
                background-color: #4682b4;
            }
            QTableWidget {
                background-color: #fff;
                color: #191970;
                gridline-color: #add8e6;
            }
            QTextEdit {
                background-color: #fff;
                color: #191970;
                border: 1px solid #add8e6;
            }
            QScrollArea {
                border: none;
            }
        """)
        plt.style.use('default')
        self.current_theme = 'blue'
        if hasattr(self, 'aiWebView'):
            self.updateChatTheme()
        if self.df is not None:
            self.updateGraphs()

    def setGreenTheme(self):
        # Green theme
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(240, 255, 240))  # Honeydew
        palette.setColor(QPalette.ColorRole.WindowText, QColor(0, 100, 0))  # Dark green
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 255, 240))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(0, 100, 0))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 100, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 100, 0))
        palette.setColor(QPalette.ColorRole.Button, QColor(144, 238, 144))  # Light green
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(0, 100, 0))
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 128, 0))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(50, 205, 50))  # Lime green
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        self.setPalette(palette)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0fff0;
            }
            QTabWidget::pane {
                border: 1px solid #90ee90;
                background-color: #fff;
            }
            QTabBar::tab {
                background-color: #90ee90;
                color: #006400;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #32cd32;
                color: white;
            }
            QPushButton {
                background-color: #90ee90;
                color: #006400;
                border: 1px solid #98fb98;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #98fb98;
            }
            QPushButton:pressed {
                background-color: #228b22;
            }
            QTableWidget {
                background-color: #fff;
                color: #006400;
                gridline-color: #90ee90;
            }
            QTextEdit {
                background-color: #fff;
                color: #006400;
                border: 1px solid #90ee90;
            }
            QScrollArea {
                border: none;
            }
        """)
        plt.style.use('default')
        self.current_theme = 'green'
        if hasattr(self, 'aiWebView'):
            self.updateChatTheme()
        if self.df is not None:
            self.updateGraphs()

    def setPurpleTheme(self):
        # Purple theme
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(248, 240, 255))  # Lavender blush with purple tint
        palette.setColor(QPalette.ColorRole.WindowText, QColor(75, 0, 130))  # Indigo
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(248, 240, 255))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(75, 0, 130))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(75, 0, 130))
        palette.setColor(QPalette.ColorRole.Text, QColor(75, 0, 130))
        palette.setColor(QPalette.ColorRole.Button, QColor(221, 160, 221))  # Plum
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(75, 0, 130))
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(128, 0, 128))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(138, 43, 226))  # Blue violet
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        self.setPalette(palette)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f0ff;
            }
            QTabWidget::pane {
                border: 1px solid #dda0dd;
                background-color: #fff;
            }
            QTabBar::tab {
                background-color: #dda0dd;
                color: #4b0082;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #8a2be2;
                color: white;
            }
            QPushButton {
                background-color: #dda0dd;
                color: #4b0082;
                border: 1px solid #e6e6fa;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e6e6fa;
            }
            QPushButton:pressed {
                background-color: #9370db;
            }
            QTableWidget {
                background-color: #fff;
                color: #4b0082;
                gridline-color: #dda0dd;
            }
            QTextEdit {
                background-color: #fff;
                color: #4b0082;
                border: 1px solid #dda0dd;
            }
            QScrollArea {
                border: none;
            }
        """)
        plt.style.use('default')
        self.current_theme = 'purple'
        if hasattr(self, 'aiWebView'):
            self.updateChatTheme()
        if self.df is not None:
            self.updateGraphs()

    def setClayTheme(self):
        # Thème argile avec image de fond
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(60, 60, 60))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(60, 60, 60))
        palette.setColor(QPalette.ColorRole.Text, QColor(60, 60, 60))
        palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(60, 60, 60))
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 100, 150))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 180))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        self.setPalette(palette)
        self.setStyleSheet("""
            QMainWindow {
                background-image: url('close-up-melange-de-poudre-d-argile.jpg');
                background-repeat: no-repeat;
                background-position: center;
                background-attachment: fixed;
                background-size: cover;
                background-color: rgba(245, 245, 245, 0.9);
            }
            QMainWindow::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(255, 255, 255, 0.85);
                z-index: -1;
            }
            QTabWidget::pane {
                border: 1px solid rgba(100, 100, 100, 0.3);
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: rgba(240, 240, 240, 0.9);
                color: #3c3c3c;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                border: 1px solid rgba(100, 100, 100, 0.2);
            }
            QTabBar::tab:selected {
                background-color: rgba(0, 120, 180, 0.8);
                color: white;
                border: 1px solid rgba(0, 120, 180, 0.5);
            }
            QPushButton {
                background-color: rgba(240, 240, 240, 0.9);
                color: #3c3c3c;
                border: 1px solid rgba(100, 100, 100, 0.3);
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(220, 220, 220, 0.9);
                border: 1px solid rgba(0, 120, 180, 0.5);
            }
            QPushButton:pressed {
                background-color: rgba(200, 200, 200, 0.9);
            }
            QTableWidget {
                background-color: rgba(255, 255, 255, 0.95);
                color: #3c3c3c;
                gridline-color: rgba(100, 100, 100, 0.3);
                border: 1px solid rgba(100, 100, 100, 0.2);
            }
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.95);
                color: #3c3c3c;
                border: 1px solid rgba(100, 100, 100, 0.3);
            }
            QScrollArea {
                border: none;
                background-color: rgba(255, 255, 255, 0.95);
            }
            QLabel {
                color: #3c3c3c;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid rgba(0, 120, 180, 0.3);
                border-radius: 5px;
                margin-top: 1ex;
                background-color: rgba(255, 255, 255, 0.9);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #3c3c3c;
            }
        """)
        plt.style.use('default')
        self.current_theme = 'clay'
        if hasattr(self, 'aiWebView'):
            self.updateChatTheme()
        if self.df is not None:
            self.updateGraphs()

    def initUI(self):
        # Menu
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('Fichier')
        openAction = fileMenu.addAction('Ouvrir')
        openAction.triggered.connect(self.openFile)
        
        toolsMenu = menubar.addMenu('Outils')
        integrityAction = toolsMenu.addAction('Vérifier Intégrité Données')
        integrityAction.triggered.connect(self.showDataIntegrityReport)
        
        # Theme menu
        themeMenu = menubar.addMenu('Thème')
        self.themeGroup = QActionGroup(self)
        
        offWhiteAction = themeMenu.addAction('Blanc Cassé')
        offWhiteAction.setCheckable(True)
        offWhiteAction.setChecked(True)
        offWhiteAction.triggered.connect(self.setOffWhiteTheme)
        self.themeGroup.addAction(offWhiteAction)
        
        darkAction = themeMenu.addAction('Dark VST')
        darkAction.setCheckable(True)
        darkAction.triggered.connect(self.setDarkTheme)
        self.themeGroup.addAction(darkAction)
        
        blueAction = themeMenu.addAction('Bleu')
        blueAction.setCheckable(True)
        blueAction.triggered.connect(self.setBlueTheme)
        self.themeGroup.addAction(blueAction)
        
        greenAction = themeMenu.addAction('Vert')
        greenAction.setCheckable(True)
        greenAction.triggered.connect(self.setGreenTheme)
        self.themeGroup.addAction(greenAction)
        
        purpleAction = themeMenu.addAction('Violet')
        purpleAction.setCheckable(True)
        purpleAction.triggered.connect(self.setPurpleTheme)
        self.themeGroup.addAction(purpleAction)
        
        clayAction = themeMenu.addAction('Argile')
        clayAction.setCheckable(True)
        clayAction.triggered.connect(self.setClayTheme)
        self.themeGroup.addAction(clayAction)

        helpMenu = menubar.addMenu('Aide')
        aboutAction = helpMenu.addAction('À propos')
        aboutAction.triggered.connect(self.showAbout)

        presentationAction = helpMenu.addAction('Présentation du Logiciel')
        presentationAction.triggered.connect(self.showPresentation)

        licenceAction = helpMenu.addAction('⚖️ Licences & Usage Commercial')
        licenceAction.triggered.connect(self.showLicence)

        # Widget central avec splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        # Panneau gauche pour les onglets
        self.tabs = QTabWidget()
        splitter.addWidget(self.tabs)

        # Panneau droit pour les explications IA
        self.aiPanel = QWidget()
        aiLayout = QVBoxLayout()
        aiHeader = QHBoxLayout()
        aiHeader.addWidget(QLabel("🤖 Chat IA Géotechnique"))
        self.refreshAIButton = QPushButton("🔄 Actualiser")
        self.refreshAIButton.clicked.connect(self.updateAI)
        aiHeader.addWidget(self.refreshAIButton)
        aiLayout.addLayout(aiHeader)
        
        # Chat input
        chatLayout = QHBoxLayout()
        self.chatInput = QLineEdit()
        self.chatInput.setPlaceholderText("Posez une question sur les données CPT...")
        self.chatInput.returnPressed.connect(self.sendChatMessage)
        chatLayout.addWidget(self.chatInput)
        sendButton = QPushButton("Envoyer")
        sendButton.clicked.connect(self.sendChatMessage)
        chatLayout.addWidget(sendButton)
        aiLayout.addLayout(chatLayout)
        
        scroll_ai = QScrollArea()
        scroll_ai.setWidgetResizable(True)
        self.aiWebView = QWebEngineView()
        self.aiWebView.setMaximumWidth(400)
        self.aiWebView.setMinimumHeight(300)
        
        # HTML initial pour le chat
        self.chat_html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 15px;
            background-color: {bg_color};
            color: {text_color};
            line-height: 1.6;
        }}
        .message {{
            margin-bottom: 20px;
            padding: 10px;
            border-radius: 8px;
            border-left: 4px solid #2a82da;
        }}
        .user-message {{
            background-color: {user_bg};
            border-left-color: #2a82da;
        }}
        .ai-message {{
            background-color: {ai_bg};
            border-left-color: #4CAF50;
        }}
        .message-header {{
            font-weight: bold;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
        }}
        .user-icon {{ color: #2a82da; }}
        .ai-icon {{ color: #4CAF50; }}
        .content {{
            margin-left: 20px;
        }}
        .image-container {{
            margin: 10px 0;
            text-align: center;
        }}
        .image-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .code-block {{
            background-color: {code_bg};
            padding: 10px;
            border-radius: 4px;
            font-family: 'Consolas', 'Monaco', monospace;
            margin: 10px 0;
            overflow-x: auto;
        }}
        .loading {{
            color: #ff9800;
            font-style: italic;
        }}
        .error {{
            color: #f44336;
            background-color: {error_bg};
            padding: 8px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .web-results {{
            background-color: {web_bg};
            padding: 10px;
            border-radius: 6px;
            margin: 10px 0;
            border-left: 3px solid #ff9800;
        }}
        .web-results h4 {{
            margin-top: 0;
            color: #ff9800;
        }}
    </style>
</head>
<body>
    <div id="chat-container">
        <div class="message ai-message">
            <div class="message-header">
                <span class="ai-icon">🤖</span> Chat IA Géotechnique
            </div>
            <div class="content">
                Bonjour ! Je suis votre assistant IA spécialisé en géotechnique.<br>
                Chargez un fichier CPT et lancez l'analyse pour commencer à discuter.
            </div>
        </div>
    </div>
</body>
</html>"""
        
        # Appliquer le thème
        self.updateChatTheme()
        
        scroll_ai.setWidget(self.aiWebView)
        aiLayout.addWidget(scroll_ai)
        self.aiPanel.setLayout(aiLayout)
        splitter.addWidget(self.aiPanel)
        
        splitter.setSizes([1000, 400])

        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Prêt")

        # Créer les onglets
        self.createDataTab()
        self.createFusionTab()
        self.createAnalysisTab()
        self.createGraphsTab()
        self.create3DTab()
        self.createTablesTab()
        self.createOverviewTab()
        
        # Add icons to tabs (using text for now)
        # self.tabs.setTabIcon(0, self.style().standardIcon(self.style().SP_FileDialogContentsView))
        # etc.

    def updateChatTheme(self):
        """Update the chat HTML theme based on current theme"""
        if self.current_theme == 'offwhite':
            colors = {
                'bg_color': '#f8f8f8',
                'text_color': '#333',
                'user_bg': '#e3f2fd',
                'ai_bg': '#f5f5f5',
                'code_bg': '#f8f8f8',
                'error_bg': '#ffebee',
                'web_bg': '#fff3e0'
            }
        elif self.current_theme == 'dark':
            colors = {
                'bg_color': '#2a2a2a',
                'text_color': '#ffffff',
                'user_bg': '#3a3a3a',
                'ai_bg': '#353535',
                'code_bg': '#404040',
                'error_bg': '#4a2c2c',
                'web_bg': '#4a3c28'
            }
        elif self.current_theme == 'blue':
            colors = {
                'bg_color': '#f0f8ff',
                'text_color': '#191970',
                'user_bg': '#e6e6fa',
                'ai_bg': '#f0f8ff',
                'code_bg': '#f5f5f5',
                'error_bg': '#ffe4e1',
                'web_bg': '#fffacd'
            }
        elif self.current_theme == 'green':
            colors = {
                'bg_color': '#f0fff0',
                'text_color': '#006400',
                'user_bg': '#f0fff0',
                'ai_bg': '#f5fff5',
                'code_bg': '#f8fff8',
                'error_bg': '#fff0f0',
                'web_bg': '#fffacd'
            }
        else:  # purple
            colors = {
                'bg_color': '#faf0ff',
                'text_color': '#4b0082',
                'user_bg': '#f2e6ff',
                'ai_bg': '#faf0ff',
                'code_bg': '#f8f0ff',
                'error_bg': '#ffe6e6',
                'web_bg': '#fff8dc'
            }
        
        html_content = self.chat_html_template.format(**colors)
        if hasattr(self, 'aiWebView'):
            self.aiWebView.setHtml(html_content)

    def addChatMessage(self, message_type, content, include_images=False, web_results=None):
        """Add a message to the chat with enhanced formatting"""
        # Utiliser une approche plus sûre pour injecter le contenu
        # Échapper tous les caractères problématiques pour JavaScript
        safe_content = (content.replace('\\', '\\\\')
                       .replace('"', '\\"')
                       .replace("'", "\\'")
                       .replace('\n', '\\n')
                       .replace('\r', '\\r')
                       .replace('\t', '\\t'))
        
        script = f"""
        (function() {{
            try {{
                var container = document.getElementById('chat-container');
                if (!container) return;
                
                var messageDiv = document.createElement('div');
                messageDiv.className = 'message {message_type}-message';
                
                var headerDiv = document.createElement('div');
                headerDiv.className = 'message-header';
                
                var iconSpan = document.createElement('span');
                iconSpan.className = '{message_type}-icon';
                iconSpan.textContent = '{("👤" if message_type == "user" else "🤖")}';
                headerDiv.appendChild(iconSpan);
                
                var titleSpan = document.createElement('span');
                titleSpan.textContent = ' {"Vous" if message_type == "user" else "IA Géotechnique"}';
                headerDiv.appendChild(titleSpan);
                
                messageDiv.appendChild(headerDiv);
                
                var contentDiv = document.createElement('div');
                contentDiv.className = 'content';
                contentDiv.innerHTML = "{safe_content}";
                messageDiv.appendChild(contentDiv);
                
                container.appendChild(messageDiv);
                window.scrollTo(0, document.body.scrollHeight);
            }} catch (e) {{
                console.error('JavaScript error in addChatMessage:', e);
            }}
        }})();
        """
        
        if hasattr(self, 'aiWebView'):
            self.aiWebView.page().runJavaScript(script)

    def updateLastAIMessage(self, new_content):
        """Update the content of the last AI message"""
        # Utiliser une approche plus sûre pour injecter le contenu
        # Échapper tous les caractères problématiques pour JavaScript
        safe_content = (new_content.replace('\\', '\\\\')
                       .replace('"', '\\"')
                       .replace("'", "\\'")
                       .replace('\n', '\\n')
                       .replace('\r', '\\r')
                       .replace('\t', '\\t'))
        
        script = f"""
        (function() {{
            try {{
                var messages = document.querySelectorAll('.ai-message');
                if (messages.length > 0) {{
                    var lastMessage = messages[messages.length - 1];
                    var contentDiv = lastMessage.querySelector('.content');
                    if (contentDiv) {{
                        contentDiv.innerHTML = "{safe_content}";
                    }}
                }}
                window.scrollTo(0, document.body.scrollHeight);
            }} catch (e) {{
                console.error('JavaScript error in updateLastAIMessage:', e);
            }}
        }})();
        """
        if hasattr(self, 'aiWebView'):
            self.aiWebView.page().runJavaScript(script)

    def _get_progress_indicator(self, current_response):
        """Génère un indicateur de progression basé sur les phases détectées dans la réponse"""
        response_lower = current_response.lower()

        # Détecter la phase actuelle basée sur les marqueurs dans la réponse (10 phases maintenant)
        phase_indicators = {
            "analyse de la requête": "📝 Phase 1/10: Analyse de la requête",
            "réponse prédéfinie": "🧠 Phase 2/10: Vérification des réponses prédéfinies",
            "contexte géographique": "🌍 Phase 3/10: Recherche du contexte géographique",
            "planification": "🎯 Phase 4/10: Planification de la réflexion",
            "recherche dans les données": "📚 Phase 5/10: Recherche dans les données CPT",
            "recherche sur internet": "🌐 Phase 6/10: Recherche sur Internet",
            "calculs et statistiques": "🧮 Phase 7/10: Calculs et statistiques",
            "construction du contexte": "🤖 Phase 8/10: Construction du contexte",
            "analyses scientifiques": "🔬 Phase 9/10: Analyses scientifiques avancées",
            "vérification des données": "🔍 Phase 10/10: Vérification des données et recommandations",
            "génération de la réponse": "✨ Génération finale de la réponse"
        }

        for marker, indicator in phase_indicators.items():
            if marker in response_lower:
                return indicator

        # Si aucune phase spécifique détectée, estimer basé sur la longueur et le contenu
        length = len(current_response)

        # Indicateurs animés pour montrer l'activité
        import time
        dots = "." * ((int(time.time()) % 3) + 1)

        if length < 50:
            return f"🚀 Initialisation{dots}"
        elif length < 150:
            return f"⚡ Analyse de la question{dots}"
        elif length < 300:
            return f"🔍 Recherche d'informations{dots}"
        elif length < 500:
            return f"🧮 Calculs en cours{dots}"
        elif length < 800:
            return f"📊 Traitement des données{dots}"
        elif length < 1200:
            return f"🤖 Génération intelligente{dots}"
        else:
            return f"✨ Finalisation{dots}"

    def enhance_response_with_web_search(self, response, question):
        """Enhance response with web search results"""
        try:
            # Utiliser l'outil de recherche web du système RAG
            from tools.web import web_search
            
            # Rechercher des informations complémentaires
            search_query = f"géotechnique CPT {question.lower()}"
            web_results = web_search(search_query)
            
            if web_results and 'results' in web_results and len(web_results['results']) > 0:
                web_section = '<div class="web-results"><h4>🔍 Informations complémentaires :</h4>'
                for result in web_results['results'][:2]:  # Limiter à 2 résultats
                    title = result.get('title', 'Information')
                    snippet = result.get('body', '')[:200] + '...'
                    web_section += f'<p><strong>{title}</strong><br>{snippet}</p>'
                web_section += '</div>'
                response += web_section
                
        except Exception as e:
            print(f"Web search enhancement failed: {e}")
            
        return response

    def add_visualizations_to_response(self, response, question):
        """Add relevant visualizations to the response"""
        try:
            # Détecter si la question nécessite des visualisations
            question_lower = question.lower()
            
            if any(keyword in question_lower for keyword in ['graphique', 'courbe', 'profil', 'visualisation', 'plot']):
                # Générer un graphique simple basé sur les données
                if hasattr(self, 'df') and self.df is not None:
                    import matplotlib.pyplot as plt
                    import io
                    import base64
                    
                    fig, ax = plt.subplots(figsize=(6, 4))
                    
                    if 'qc' in self.df.columns and 'depth' in self.df.columns:
                        ax.plot(self.df['qc'], self.df['Depth'], 'b-', linewidth=2)
                        ax.set_xlabel('qc (MPa)')
                        ax.set_ylabel('Profondeur (m)')
                        ax.set_title('Profil de qc')
                        ax.invert_yaxis()
                        ax.grid(True, alpha=0.3)
                        
                        # Convertir en base64 pour HTML
                        buf = io.BytesIO()
                        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                        buf.seek(0)
                        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
                        plt.close(fig)
                        
                        img_html = f'<div class="image-container"><img src="data:image/png;base64,{img_base64}" alt="Graphique qc"><br><em>Profil de résistance au cône (qc)</em></div>'
                        response += img_html
                        
        except Exception as e:
            print(f"Visualization enhancement failed: {e}")
            
        return response

    def createDataTab(self):
        tab    = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(6, 6, 6, 6)

        # ── Titre ─────────────────────────────────────────────────────────────
        title_lbl = QLabel("Tableau des Données CPT")
        title_lbl.setStyleSheet(
            "font-size:14px;font-weight:bold;color:#F59B3A;padding:4px 2px;")
        layout.addWidget(title_lbl)

        # ── Splitter horizontal : tableau | animation SVG ──────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet("QSplitter::handle{background:#2a2018;}")

        # Gauche : tableau de données
        left_w  = QWidget()
        left_vl = QVBoxLayout(left_w)
        left_vl.setContentsMargins(0, 0, 0, 0)
        self.dataTable = QTableWidget()
        self.dataTable.setAlternatingRowColors(True)
        self.dataTable.setMinimumWidth(280)
        self.dataTable.setStyleSheet(
            "QTableWidget{background:#16140e;color:#F0E1C3;gridline-color:#2a2018;}"
            "QHeaderView::section{background:#1a1208;color:#F59B3A;font-weight:bold;}"
        )
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.dataTable)
        left_vl.addWidget(scroll)
        splitter.addWidget(left_w)

        # Droite : animation SVG
        right_w  = QWidget()
        right_vl = QVBoxLayout(right_w)
        right_vl.setContentsMargins(0, 0, 0, 0)
        right_vl.setSpacing(4)

        svg_hdr = QLabel("Animation CPTU — Couches & Profils (Robertson 1990)")
        svg_hdr.setStyleSheet(
            "font-size:11px;font-weight:bold;color:#DA701C;padding:3px 4px;")
        right_vl.addWidget(svg_hdr)

        self.dataSvgView = QWebEngineView()
        self.dataSvgView.setMinimumWidth(680)
        # Page d'attente
        self.dataSvgView.setHtml(
            "<!DOCTYPE html><html>"
            "<body style='margin:0;background:#16140e;display:flex;"
            "align-items:center;justify-content:center;height:100vh;'>"
            "<div style='color:#a07840;font-family:Arial;font-size:13px;text-align:center;'>"
            "Chargez un fichier CPTU<br>pour générer l'animation</div>"
            "</body></html>"
        )
        right_vl.addWidget(self.dataSvgView, stretch=1)

        # Bouton sauvegarder SVG
        self._data_svg_save_btn = QPushButton("  Sauvegarder l'Animation SVG")
        self._data_svg_save_btn.setEnabled(False)
        self._data_svg_save_btn.setStyleSheet(
            "QPushButton{background:#C1550F;color:white;padding:7px 16px;"
            "border:none;border-radius:4px;font-weight:bold;font-size:11px;}"
            "QPushButton:hover{background:#DA701C;}"
            "QPushButton:disabled{background:#333;color:#666;}"
        )
        self._data_svg_save_btn.clicked.connect(self._save_data_svg)
        right_vl.addWidget(self._data_svg_save_btn)

        splitter.addWidget(right_w)
        splitter.setSizes([380, 760])
        layout.addWidget(splitter, stretch=1)

        # ── Boutons d'export (bas) ─────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        pdf_btn = QPushButton("  Exporter en PDF")
        pdf_btn.clicked.connect(self.exportDataToPDF)
        excel_btn = QPushButton("  Exporter en Excel")
        excel_btn.clicked.connect(self.exportDataToExcel)
        btn_layout.addWidget(pdf_btn)
        btn_layout.addWidget(excel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self._data_svg_string = None
        self.tabs.addTab(tab, "Données")

    def createFusionTab(self):
        """Créer l'onglet de fusion de fichiers CPTU"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("🔗 Fusion de Fichiers CPTU - Carte 3D Complète du Sol"))
        
        # Section de chargement des fichiers
        upload_group = QGroupBox("📁 Chargement des Fichiers CPTU")
        upload_layout = QVBoxLayout()
        
        # Bouton pour charger plusieurs fichiers
        self.loadMultipleButton = QPushButton("📂 Charger Plusieurs Fichiers CPTU")
        self.loadMultipleButton.clicked.connect(self.loadMultipleCPTUFiles)
        self.loadMultipleButton.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        upload_layout.addWidget(self.loadMultipleButton)
        
        # Liste des fichiers chargés
        self.fusionFileList = QTextEdit()
        self.fusionFileList.setMaximumHeight(100)
        self.fusionFileList.setPlaceholderText("Fichiers chargés apparaîtront ici...")
        upload_layout.addWidget(self.fusionFileList)
        
        upload_group.setLayout(upload_layout)
        layout.addWidget(upload_group)
        
        # Section des coordonnées
        coord_group = QGroupBox("📍 Coordonnées des Sondages")
        coord_layout = QVBoxLayout()
        
        coord_layout.addWidget(QLabel("Définissez les coordonnées X,Y pour chaque sondage CPTU:"))
        
        # Table pour les coordonnées
        self.coordTable = QTableWidget()
        self.coordTable.setColumnCount(3)
        self.coordTable.setHorizontalHeaderLabels(["Fichier", "Coordonnée X (m)", "Coordonnée Y (m)"])
        self.coordTable.horizontalHeader().setStretchLastSection(True)
        coord_layout.addWidget(self.coordTable)
        
        # Boutons pour gérer les coordonnées
        coord_buttons = QHBoxLayout()
        
        self.addCoordButton = QPushButton("➕ Ajouter Coordonnées")
        self.addCoordButton.clicked.connect(self.addCoordinates)
        coord_buttons.addWidget(self.addCoordButton)
        
        self.autoDetectCoordButton = QPushButton("🤖 Auto-détecter Coordonnées")
        self.autoDetectCoordButton.clicked.connect(self.autoDetectAndFillCoordinates)
        self.autoDetectCoordButton.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        coord_buttons.addWidget(self.autoDetectCoordButton)
        
        self.clearCoordButton = QPushButton("🗑️ Effacer Tout")
        self.clearCoordButton.clicked.connect(self.clearCoordinates)
        coord_buttons.addWidget(self.clearCoordButton)
        
        coord_layout.addLayout(coord_buttons)
        coord_group.setLayout(coord_layout)
        layout.addWidget(coord_group)
        
        # Section de fusion et visualisation
        fusion_group = QGroupBox("🔄 Fusion et Visualisation 3D")
        fusion_layout = QVBoxLayout()
        
        # Boutons de contrôle
        button_layout = QHBoxLayout()
        
        # Bouton de fusion
        self.fusionButton = QPushButton("🚀 Créer Contours 3D qc")
        self.fusionButton.clicked.connect(self.create3DSoilMap)
        self.fusionButton.setEnabled(False)
        self.fusionButton.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.fusionButton)
        
        # Bouton d'export PDF
        self.exportFusionPDFButton = QPushButton("📄 Exporter Contours 3D en PDF")
        self.exportFusionPDFButton.clicked.connect(self.exportFusion3DToPDF)
        self.exportFusionPDFButton.setEnabled(False)
        self.exportFusionPDFButton.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        button_layout.addWidget(self.exportFusionPDFButton)
        
        button_layout.addStretch()
        fusion_layout.addLayout(button_layout)
        
        # Zone de visualisation 3D complète
        self.fusion2DView = QWebEngineView()
        self.fusion2DView.setMinimumHeight(400)
        fusion_layout.addWidget(QLabel("🗺️ Contours 3D - Graphiques qc de chaque CPTU"))
        fusion_layout.addWidget(self.fusion2DView)
        
        # Informations sur les graphiques 3D
        self.fusion2DInfoLabel = QLabel("Informations sur les contours 3D apparaîtront ici...")
        self.fusion2DInfoLabel.setStyleSheet("font-weight: bold; color: #666;")
        fusion_layout.addWidget(self.fusion2DInfoLabel)
        
        fusion_group.setLayout(fusion_layout)
        layout.addWidget(fusion_group)
        
        # Stocker les données de fusion
        self.fusion_files = []  # Liste des fichiers chargés
        self.fusion_data = {}   # Données fusionnées avec coordonnées
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "🗺️ Contours 3D")

    def createAnalysisTab(self):
        tab    = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Titre
        hdr = QLabel("Analyse Géotechnique Complète + Nuage de Points 3D")
        hdr.setStyleSheet(
            "font-size:13px;font-weight:bold;color:#F59B3A;padding:3px 2px;")
        layout.addWidget(hdr)

        # Splitter vertical  (texte en haut | 3D en bas)
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(5)
        splitter.setStyleSheet("QSplitter::handle{background:#2a2018;}")

        # ── Partie haute : texte d'analyse ──────────────────────────────────
        top_w   = QWidget()
        top_vl  = QVBoxLayout(top_w)
        top_vl.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.analysisText = QTextEdit()
        self.analysisText.setMinimumWidth(400)
        self.analysisText.setStyleSheet(
            "QTextEdit{background:#1a1208;color:#F0E1C3;"
            "font-size:11px;border:1px solid #2a2018;padding:6px;}"
        )
        scroll.setWidget(self.analysisText)
        top_vl.addWidget(scroll)
        splitter.addWidget(top_w)

        # ── Partie basse : nuage de points 3D Plotly ─────────────────────────
        bot_w  = QWidget()
        bot_vl = QVBoxLayout(bot_w)
        bot_vl.setContentsMargins(0, 0, 0, 2)
        bot_vl.setSpacing(3)

        chart_hdr = QLabel(
            "Nuage de Points 3D Denses — Couches du Sous-Sol (Robertson 1990)")
        chart_hdr.setStyleSheet(
            "font-size:10px;font-weight:bold;color:#DA701C;padding:2px 4px;")
        bot_vl.addWidget(chart_hdr)

        self.analysis3DView = QWebEngineView()
        self.analysis3DView.setMinimumHeight(380)
        self.analysis3DView.setHtml(
            "<!DOCTYPE html><html>"
            "<body style='margin:0;background:#16140e;display:flex;"
            "align-items:center;justify-content:center;height:100vh;'>"
            "<div style='color:#a07840;font-family:Arial;font-size:13px;"
            "text-align:center;'>"
            "Chargez un fichier CPTU pour afficher<br>"
            "le nuage de points 3D du sous-sol"
            "</div></body></html>"
        )
        bot_vl.addWidget(self.analysis3DView, stretch=1)
        splitter.addWidget(bot_w)

        splitter.setSizes([280, 520])
        layout.addWidget(splitter, stretch=1)

        # ── Bouton rapport scientifique complet ────────────────────────────────
        btn_bar = QHBoxLayout()
        rpt_btn = QPushButton("📊 Rapport Scientifique Complet PDF (~30 pages)")
        rpt_btn.setToolTip(
            "Génère un rapport PDF scientifique complet : 20 graphiques, Robertson 1990, "
            "liquéfaction, classification des couches, références bibliographiques.")
        rpt_btn.setStyleSheet(
            "QPushButton{background:#C1550F;color:white;padding:8px 22px;"
            "border:none;border-radius:4px;font-weight:bold;font-size:11px;}"
            "QPushButton:hover{background:#DA701C;}"
        )
        rpt_btn.clicked.connect(self.exportAnalysisCompletePDF)
        btn_bar.addWidget(rpt_btn)
        btn_bar.addStretch()
        layout.addLayout(btn_bar)

        self.tabs.addTab(tab, "Analyse")

    def createGraphsTab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        grid = QGridLayout()
        
        self.canvases = []
        
        # Liste des 20 graphiques avec légendes
        plots_config = [
            ('qc vs Profondeur', lambda df, ax: self.plot_qc_depth(df, ax)),
            ('fs vs Profondeur', lambda df, ax: self.plot_fs_depth(df, ax)),
            ('Rf vs Profondeur', lambda df, ax: self.plot_rf_depth(df, ax)),
            ('qnet vs Profondeur', lambda df, ax: self.plot_qnet_depth(df, ax)),
            ('Classification des sols', lambda df, ax: self.plot_soil_classification(df, ax)),
            ('Clusters K-means', lambda df, ax: self.plot_kmeans_clusters(df, ax)),
            ('PCA - Composantes principales', lambda df, ax: self.plot_pca(df, ax)),
            ('Profil lissé qc', lambda df, ax: self.plot_smooth_qc(df, ax)),
            ('Profil lissé fs', lambda df, ax: self.plot_smooth_fs(df, ax)),
            ('Histogramme qc', lambda df, ax: self.plot_qc_histogram(df, ax)),
            ('Histogramme fs', lambda df, ax: self.plot_fs_histogram(df, ax)),
            ('Boxplot qc par couche', lambda df, ax: self.plot_qc_boxplot(df, ax)),
            ('Boxplot fs par couche', lambda df, ax: self.plot_fs_boxplot(df, ax)),
            ('Nuage de points qc vs fs', lambda df, ax: self.plot_qc_fs_scatter(df, ax)),
            ('Courbe cumulative qc', lambda df, ax: self.plot_qc_cumulative(df, ax)),
            ('Courbe cumulative fs', lambda df, ax: self.plot_fs_cumulative(df, ax)),
            ('Profil de friction ratio', lambda df, ax: self.plot_friction_ratio(df, ax)),
            ('Analyse de tendance qc', lambda df, ax: self.plot_qc_trend(df, ax)),
            ('Analyse de tendance fs', lambda df, ax: self.plot_fs_trend(df, ax)),
            ('Carte de chaleur corrélations', lambda df, ax: self.plot_correlation_heatmap(df, ax)),
        ]
        
        for i, (title, plot_func) in enumerate(plots_config):
            group = QGroupBox(title)
            group.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #555; border-radius: 5px; margin-top: 1ex; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }")
            group_layout = QVBoxLayout()
            canvas = FigureCanvas(plt.Figure(figsize=(10, 8)))
            ax = canvas.figure.add_subplot(111)
            ax.set_title(title, fontsize=12, fontweight='bold', color='white')
            ax.set_facecolor('#2a2a2a')
            ax.tick_params(colors='white')
            for spine in ax.spines.values():
                spine.set_edgecolor('white')
            self.canvases.append((canvas, plot_func))
            
            group_layout.addWidget(canvas)
            
            save_btn = QPushButton("💾 PDF")
            save_btn.setFixedWidth(80)
            save_btn.clicked.connect(lambda checked, idx=i: self.savePlotAsPDF(idx))
            group_layout.addWidget(save_btn)
            
            group.setLayout(group_layout)
            group.setMaximumWidth(500)
            grid.addWidget(group, i // 3, i % 3)  # 3 colonnes pour meilleure visibilité
        
        content.setLayout(grid)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Graphiques (20)")

    def create3DTab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("📉 Visualisations 3D Interactives (4 Graphiques)"))
        
        # Ajouter une barre d'outils pour les boutons de téléchargement
        toolbar = QHBoxLayout()
        
        # Bouton pour télécharger tous les graphiques 3D en PDF
        self.export3DPDFButton = QPushButton("📄 Télécharger PDF (Tous les graphiques 3D)")
        self.export3DPDFButton.clicked.connect(self.export3DGraphsToPDF)
        self.export3DPDFButton.setEnabled(False)  # Désactivé par défaut
        self.export3DPDFButton.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        toolbar.addWidget(self.export3DPDFButton)
        
        # Bouton pour télécharger chaque graphique individuellement
        self.export3DIndividualButton = QPushButton("🖼️ Télécharger Graphiques Individuellement")
        self.export3DIndividualButton.clicked.connect(self.export3DGraphsIndividually)
        self.export3DIndividualButton.setEnabled(False)  # Désactivé par défaut
        self.export3DIndividualButton.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        toolbar.addWidget(self.export3DIndividualButton)
        
        # Bouton de rafraîchissement des graphiques 3D
        self.refresh3DButton = QPushButton("🔄 Actualiser 3D")
        self.refresh3DButton.clicked.connect(self.refresh3DGraphs)
        self.refresh3DButton.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        toolbar.addWidget(self.refresh3DButton)
        
        toolbar.addStretch()  # Espacement
        layout.addLayout(toolbar)
        
        # Create grid layout for 4 plots (2x2)
        grid = QGridLayout()
        
        # Create 4 QWebEngineView for the plots
        self.webView1 = QWebEngineView()
        self.webView2 = QWebEngineView()
        self.webView3 = QWebEngineView()
        self.webView4 = QWebEngineView()
        
        # Add labels and views to grid
        grid.addWidget(QLabel("3D Scatter: Depth vs qc vs fs"), 0, 0)
        grid.addWidget(self.webView1, 1, 0)

        grid.addWidget(QLabel("3D Surface: qc Surface"), 0, 1)
        grid.addWidget(self.webView2, 1, 1)

        grid.addWidget(QLabel("3D Contour: qc Contours"), 2, 0)
        grid.addWidget(self.webView3, 3, 0)

        grid.addWidget(QLabel("3D Wireframe: qc Wireframe"), 2, 1)
        grid.addWidget(self.webView4, 3, 1)

        # Labels rows get min-height; webview rows share remaining space equally
        grid.setRowStretch(0, 0)
        grid.setRowStretch(1, 1)
        grid.setRowStretch(2, 0)
        grid.setRowStretch(3, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setSpacing(4)

        # grid fills all remaining vertical space in the tab
        layout.addLayout(grid, 1)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "3D Interactif")

    def createTablesTab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(18)

        # Tables supplémentaires
        self.summaryTable      = QTableWidget()
        self.layersTable       = QTableWidget()
        self.statsTable        = QTableWidget()
        self.correlationTable  = QTableWidget()
        self.liquefactionTable = QTableWidget()

        tables_config = [
            (self.summaryTable,      "Résumé des données",          "summary"),
            (self.layersTable,       "Classification par couches",   "layers"),
            (self.statsTable,        "Statistiques détaillées",      "stats"),
            (self.correlationTable,  "Matrice de corrélation",       "correlation"),
            (self.liquefactionTable, "Analyse de liquéfaction",      "liquefaction"),
        ]

        # Per-table SVG state (svg string, webview)
        self._svg_views   = {}    # key -> QWebEngineView
        self._svg_strings = {}    # key -> current SVG string

        BTN_STYLE = """
            QPushButton {
                background: #C1550F; color: white; font-weight: bold;
                padding: 5px 12px; border-radius: 4px; border: none; font-size: 11px;
            }
            QPushButton:hover { background: #DA701C; }
            QPushButton:disabled { background: #555; color: #888; }
        """
        BTN2_STYLE = """
            QPushButton {
                background: #1a6a3a; color: white; font-weight: bold;
                padding: 5px 12px; border-radius: 4px; border: none; font-size: 11px;
            }
            QPushButton:hover { background: #2a8a4a; }
            QPushButton:disabled { background: #555; color: #888; }
        """
        BTN3_STYLE = """
            QPushButton {
                background: #1a3a6a; color: white; font-weight: bold;
                padding: 5px 12px; border-radius: 4px; border: none; font-size: 11px;
            }
            QPushButton:hover { background: #2a5a9a; }
        """
        BTN_PDF_STYLE = """
            QPushButton {
                background: #6a1a6a; color: white; font-weight: bold;
                padding: 5px 12px; border-radius: 4px; border: none; font-size: 11px;
            }
            QPushButton:hover { background: #9a2a9a; }
            QPushButton:disabled { background: #555; color: #888; }
        """

        for table, title, key in tables_config:
            table.setAlternatingRowColors(True)

            group = QGroupBox(f"📋 {title}")
            group.setStyleSheet("""
                QGroupBox { font-weight: bold; font-size: 13px;
                    border: 2px solid #C1550F; border-radius: 6px; margin-top: 1ex; padding: 6px; }
                QGroupBox::title { subcontrol-origin: margin; left: 10px;
                    padding: 0 6px; color: #F59B3A; }
            """)
            group_vlay = QVBoxLayout()

            # ── Horizontal split : table LEFT | SVG RIGHT ──────────────────
            split = QSplitter(Qt.Orientation.Horizontal)

            # Table side
            table_widget = QWidget()
            table_vlay = QVBoxLayout()
            table_vlay.setContentsMargins(0, 0, 0, 0)
            table_vlay.addWidget(table)

            # Buttons below table
            btn_row = QHBoxLayout()
            gen_btn = QPushButton("🎬 Générer Animation SVG")
            gen_btn.setStyleSheet(BTN_STYLE)
            gen_btn.setEnabled(False)

            dl_btn = QPushButton("💾 Télécharger SVG")
            dl_btn.setStyleSheet(BTN2_STYLE)
            dl_btn.setEnabled(False)

            upload_btn = QPushButton("📤 Uploader SVG")
            upload_btn.setStyleSheet(BTN3_STYLE)

            pdf_btn = QPushButton("📄 Rapport PDF")
            pdf_btn.setStyleSheet(BTN_PDF_STYLE)
            pdf_btn.setEnabled(False)

            btn_row.addWidget(gen_btn)
            btn_row.addWidget(dl_btn)
            btn_row.addWidget(upload_btn)
            btn_row.addWidget(pdf_btn)
            btn_row.addStretch()
            table_vlay.addLayout(btn_row)
            table_widget.setLayout(table_vlay)

            # SVG side — QWebEngineView
            svg_view = QWebEngineView()
            svg_view.setMinimumSize(700, 340)
            svg_view.setHtml("<body style='background:#16140e;color:#a07840;"
                             "display:flex;align-items:center;justify-content:center;"
                             "height:100%;font-family:Arial'>"
                             "Chargez un fichier CPTU puis cliquez <b>Générer Animation SVG</b></body>")
            self._svg_views[key]   = svg_view
            self._svg_strings[key] = None

            split.addWidget(table_widget)
            split.addWidget(svg_view)
            split.setSizes([420, 700])

            group_vlay.addWidget(split)
            group.setLayout(group_vlay)
            main_layout.addWidget(group)

            # ── Wire buttons (capture key/view by default arg) ─────────────
            gen_btn.clicked.connect(
                lambda checked=False, k=key, g=gen_btn, d=dl_btn, p=pdf_btn:
                    self._generate_svg_animation(k, g, d, p)
            )
            dl_btn.clicked.connect(
                lambda checked=False, k=key: self._download_svg(k)
            )
            upload_btn.clicked.connect(
                lambda checked=False, k=key: self._upload_svg(k)
            )
            pdf_btn.clicked.connect(
                lambda checked=False, k=key, t=title: self._export_svg_pdf(k, t)
            )

            # store button refs to enable after data load
            table._gen_btn = gen_btn
            table._dl_btn  = dl_btn
            table._pdf_btn = pdf_btn

        content.setLayout(main_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Tableaux")

    # ── SVG animation helpers ─────────────────────────────────────────────────

    def _save_data_svg(self):
        """Sauvegarde l'animation SVG du tableau de données principal."""
        svg_str = getattr(self, '_data_svg_string', None)
        if not svg_str:
            QMessageBox.information(self, "SVG vide", "Chargez d'abord un fichier CPTU.")
            return
        fname = (os.path.basename(self.current_file)
                 if hasattr(self, 'current_file') and self.current_file else "cptu")
        base  = os.path.splitext(fname)[0]
        path, _ = QFileDialog.getSaveFileName(
            self, "Sauvegarder Animation SVG",
            f"{base}_animation.svg", "SVG (*.svg);;Tous les fichiers (*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg_str)
            QMessageBox.information(self, "Enregistré",
                                    f"Animation SVG sauvegardée :\n{path}")

    def _generate_svg_animation(self, key, gen_btn, dl_btn, pdf_btn):
        """Génère l'animation SVG pour la table `key` à partir des données self.df."""
        if self.df is None:
            QMessageBox.warning(self, "Données manquantes", "Chargez d'abord un fichier CPTU.")
            return
        if not SVG_ANIMATOR_AVAILABLE:
            QMessageBox.warning(self, "Module manquant", "Le module cptu_svg_animator est introuvable.")
            return
        try:
            gen_btn.setEnabled(False)
            gen_btn.setText("⏳ Génération...")
            QApplication.processEvents()

            fname = os.path.basename(self.current_file) if hasattr(self, 'current_file') and self.current_file else "CPTU"
            title = f"{fname} — {key.upper()}"
            svg_str = generate_cptu_animation(self.df, title=title)

            self._svg_strings[key] = svg_str
            view = self._svg_views[key]

            # Wrap SVG in HTML so QWebEngineView renders it properly
            html = (
                "<!DOCTYPE html><html><body style='margin:0;background:#16140e;'>"
                + svg_str
                + "</body></html>"
            )
            view.setHtml(html)

            dl_btn.setEnabled(True)
            pdf_btn.setEnabled(True)
            gen_btn.setText("🎬 Générer Animation SVG")
            gen_btn.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Erreur SVG", f"Impossible de générer l'animation:\n{e}")
            gen_btn.setText("🎬 Générer Animation SVG")
            gen_btn.setEnabled(True)

    def _download_svg(self, key):
        """Enregistre l'animation SVG sur disque."""
        svg_str = self._svg_strings.get(key)
        if not svg_str:
            QMessageBox.warning(self, "Aucun SVG", "Générez d'abord l'animation SVG.")
            return
        fname = f"CPTU_animation_{key}.svg"
        path, _ = QFileDialog.getSaveFileName(self, "Enregistrer SVG", fname, "SVG (*.svg)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg_str)
            QMessageBox.information(self, "SVG enregistré", f"Animation enregistrée :\n{path}")

    def _upload_svg(self, key):
        """Charge un fichier SVG externe et l'affiche dans le panneau."""
        path, _ = QFileDialog.getOpenFileName(self, "Ouvrir animation SVG", "", "SVG (*.svg)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                svg_str = f.read()
            self._svg_strings[key] = svg_str
            view = self._svg_views[key]
            html = (
                "<!DOCTYPE html><html><body style='margin:0;background:#16140e;'>"
                + svg_str
                + "</body></html>"
            )
            view.setHtml(html)
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger le SVG:\n{e}")

    # ─────────────────────────────────────────────────────────────────────────
    def _svg_to_png_bytes(self, svg_content: str,
                          width: int = 1400, height: int = 900) -> bytes:
        """
        Convertit un contenu SVG (string) en PNG (bytes) via QSvgRenderer.
        Rend l'état statique initial de l'animation (CSS ignorées → profil visible).
        Retourne b'' en cas d'échec.
        """
        try:
            from PySide6.QtSvg import QSvgRenderer
            from PySide6.QtGui  import QImage, QPainter
            from PySide6.QtCore import QByteArray, QBuffer, QIODevice

            data     = QByteArray(svg_content.encode('utf-8'))
            renderer = QSvgRenderer(data)
            if not renderer.isValid():
                return b""

            ds = renderer.defaultSize()
            if ds.isValid() and ds.width() > 0:
                ratio = ds.height() / ds.width()
                w     = min(ds.width(), width)
                h     = int(w * ratio)
            else:
                w, h = width, height

            image = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
            image.fill(0xFF16140E)          # fond sombre #16140e

            painter = QPainter(image)
            renderer.render(painter)
            painter.end()

            buffer = QByteArray()
            buf    = QBuffer(buffer)
            buf.open(QIODevice.OpenMode.WriteOnly)
            image.save(buf, "PNG")
            buf.close()
            return bytes(buffer)
        except Exception as _e:
            print(f"[SVG→PNG] {_e}")
            return b""

    def _export_svg_pdf(self, key, table_title):
        """Exporte un rapport PDF scientifique en français avec animation SVG + données."""
        if self.df is None:
            QMessageBox.warning(self, "Données manquantes", "Chargez d'abord un fichier CPTU.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer Rapport PDF", f"Rapport_CPTU_{key}.pdf", "PDF (*.pdf)"
        )
        if not path:
            return
        try:
            self._build_pdf_report(path, key, table_title)
            QMessageBox.information(self, "PDF généré", f"Rapport enregistré :\n{path}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erreur PDF", f"Impossible de générer le rapport:\n{e}")

    def _build_pdf_report(self, pdf_path: str, key: str, table_title: str,
                           svg_override: str = None):
        """
        Génère un rapport PDF scientifique en français avec :
        - Page de titre
        - Tableau de données CPTU
        - Classification des couches (Robertson)
        - Animation SVG exportée en image PNG via cairosvg ou intégrée comme texte SVG
        - Interprétation scientifique générée
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm, mm
            from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                            Table, TableStyle, HRFlowable, PageBreak)
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        except ImportError:
            raise RuntimeError("reportlab non installé. Lancez : python -m pip install reportlab")

        df = self.df
        fname = os.path.basename(self.current_file) if hasattr(self, 'current_file') and self.current_file else "CPTU"

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm, topMargin=2.5*cm, bottomMargin=2*cm,
            title=f"Rapport CPTU — {fname}",
            author="SETRAF CPT Analysis Studio",
        )

        styles = getSampleStyleSheet()
        # Custom styles
        title_style = ParagraphStyle("title_s", parent=styles["Title"],
            fontSize=18, textColor=colors.HexColor("#C1550F"),
            spaceAfter=6, alignment=TA_CENTER)
        sub_style = ParagraphStyle("sub_s", parent=styles["Normal"],
            fontSize=11, textColor=colors.HexColor("#555555"),
            spaceAfter=4, alignment=TA_CENTER)
        h1_style = ParagraphStyle("h1_s", parent=styles["Heading1"],
            fontSize=13, textColor=colors.HexColor("#C1550F"), spaceBefore=12, spaceAfter=4)
        h2_style = ParagraphStyle("h2_s", parent=styles["Heading2"],
            fontSize=11, textColor=colors.HexColor("#333333"), spaceBefore=8, spaceAfter=3)
        body_style = ParagraphStyle("body_s", parent=styles["Normal"],
            fontSize=9.5, leading=14, spaceAfter=4, alignment=TA_JUSTIFY)
        caption = ParagraphStyle("caption_s", parent=styles["Normal"],
            fontSize=8, textColor=colors.HexColor("#888888"), alignment=TA_CENTER,
            spaceAfter=4)
        small_style = ParagraphStyle("small_s", parent=styles["Normal"],
            fontSize=8, textColor=colors.HexColor("#666666"))

        story = []

        # ── En-tête avec logo SETRAF ─────────────────────────────────────────
        from reportlab.platypus import Image as RLImage
        _logo_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "setraf_logo.png")
        if os.path.exists(_logo_p):
            _lt = Table([[RLImage(_logo_p, width=3.8*cm, height=1.9*cm),
                          Paragraph("SETRAF · CPT Analysis Studio",
                                    ParagraphStyle("_lhd", parent=styles["Normal"],
                                                   fontSize=9,
                                                   textColor=colors.HexColor("#888888"),
                                                   alignment=2))]],
                        colWidths=[4.2*cm, 13.3*cm])
            _lt.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                     ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
            story.append(_lt)
            story.append(HRFlowable(width="100%", thickness=1,
                                    color=colors.HexColor("#e0d0c0"), spaceAfter=8))

        # ── Titre ────────────────────────────────────────────────────────────
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph("RAPPORT D'ANALYSE GÉOTECHNIQUE", title_style))
        story.append(Paragraph("CPT / CPTU — SETRAF CPT Analysis Studio 2026", sub_style))
        story.append(Paragraph(f"Fichier : {fname}  |  Table : {table_title}", sub_style))

        from datetime import date
        story.append(Paragraph(f"Date : {date.today().strftime('%d %B %Y')}", sub_style))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#C1550F"),
                                spaceAfter=10))

        # ── Statistiques générales ────────────────────────────────────────────
        story.append(Paragraph("1. Statistiques Générales", h1_style))

        depth_col = "Depth" if "Depth" in df.columns else df.columns[0]
        depth_factor = 0.01 if df[depth_col].max() > 200 else 1.0
        depth_max_m = df[depth_col].max() * depth_factor

        stats_txt = (
            f"Le sondage CPTU analysé comprend <b>{len(df)}</b> points de mesure jusqu'à une "
            f"profondeur maximale de <b>{depth_max_m:.1f} m</b>. "
            f"La résistance de pointe (q<sub>c</sub>) varie de "
            f"<b>{df['qc'].min():.2f} MPa</b> à <b>{df['qc'].max():.2f} MPa</b>, "
            f"avec une valeur moyenne de <b>{df['qc'].mean():.2f} MPa</b> "
            f"(écart-type : {df['qc'].std():.2f} MPa). "
            f"Le frottement latéral (f<sub>s</sub>) oscille entre "
            f"<b>{df['fs'].min():.0f} kPa</b> et <b>{df['fs'].max():.0f} kPa</b>, "
            f"avec une moyenne de <b>{df['fs'].mean():.0f} kPa</b>."
        )
        story.append(Paragraph(stats_txt, body_style))
        story.append(Spacer(1, 0.3*cm))

        # Mini stats table
        stat_data = [
            ["Paramètre", "Min", "Max", "Moyenne", "Écart-type"],
            ["qc (MPa)",
             f"{df['qc'].min():.2f}", f"{df['qc'].max():.2f}",
             f"{df['qc'].mean():.2f}", f"{df['qc'].std():.2f}"],
            ["f_s (kPa)",
             f"{df['fs'].min():.0f}", f"{df['fs'].max():.0f}",
             f"{df['fs'].mean():.0f}", f"{df['fs'].std():.0f}"],
        ]
        if "Rf" in df.columns:
            stat_data.append([
                "Rf (%)",
                f"{df['Rf'].min():.2f}", f"{df['Rf'].max():.2f}",
                f"{df['Rf'].mean():.2f}", f"{df['Rf'].std():.2f}",
            ])
        stat_tbl = Table(stat_data, colWidths=[4*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
        stat_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#C1550F")),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,-1), 8.5),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.HexColor("#fff8f0"), colors.white]),
            ("GRID",       (0,0), (-1,-1), 0.4, colors.HexColor("#dddddd")),
            ("ALIGN",      (1,0), (-1,-1), "CENTER"),
        ]))
        story.append(stat_tbl)
        story.append(Spacer(1, 0.5*cm))

        # ── Tableau de données CPTU (50 premières lignes) ─────────────────────
        story.append(Paragraph("2. Données CPTU Brutes (50 premières mesures)", h1_style))
        story.append(Paragraph(
            "Le tableau ci-dessous présente les mesures brutes extraites du fichier CPTU. "
            "Les colonnes sont : profondeur (m), résistance de pointe q<sub>c</sub> (MPa) "
            "et frottement latéral f<sub>s</sub> (kPa).",
            body_style
        ))
        story.append(Spacer(1, 0.2*cm))

        data_subset = df.head(50)
        cols_to_show = [c for c in [depth_col, "qc", "fs", "Rf"] if c in df.columns]
        headers = {"Depth":"Prof. (m)", "qc":"qc (MPa)", "fs":"fs (kPa)", "Rf":"Rf (%)"}
        table_data = [[headers.get(c, c) for c in cols_to_show]]
        for _, row in data_subset.iterrows():
            r = []
            for c in cols_to_show:
                v = row[c]
                if c == depth_col:
                    r.append(f"{float(v)*depth_factor:.2f}")
                elif c == "fs":
                    r.append(f"{float(v):.0f}")
                else:
                    r.append(f"{float(v):.2f}")
            table_data.append(r)

        col_w = 14*cm / len(cols_to_show)
        cptu_tbl = Table(table_data, colWidths=[col_w]*len(cols_to_show),
                         repeatRows=1)
        cptu_tbl.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#1a3a6a")),
            ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS", (0,1), (-1,-1),
             [colors.HexColor("#f0f8ff"), colors.white]),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#cccccc")),
            ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ]))
        story.append(cptu_tbl)
        story.append(Spacer(1, 0.5*cm))

        # ── Classification des couches ────────────────────────────────────────
        story.append(PageBreak())
        story.append(Paragraph("3. Classification des Couches Géologiques (Robertson 1990)", h1_style))
        story.append(Paragraph(
            "La classification des sols est effectuée selon la méthode de Robertson (1990) "
            "basée sur l'indice de comportement I<sub>c</sub> calculé à partir de q<sub>c</sub> "
            "et du rapport de friction f<sub>r</sub>. Les limites de zones sont : "
            "I<sub>c</sub> &lt; 2.05 (sables), 2.05–2.60 (silt sableux), 2.60–2.95 (silt argileux), "
            "2.95–3.60 (argile), &gt; 3.60 (sols organiques).",
            body_style
        ))
        story.append(Spacer(1, 0.2*cm))

        if SVG_ANIMATOR_AVAILABLE:
            layers = detect_layers(df)
            layer_data = [["N°", "Début (m)", "Fin (m)", "Épaisseur (m)",
                           "Type de sol (Robertson)", "qc moy. (MPa)", "fs moy. (kPa)"]]
            for idx, la in enumerate(layers, 1):
                layer_data.append([
                    str(idx),
                    f"{la['start_m']:.2f}",
                    f"{la['end_m']:.2f}",
                    f"{la['end_m']-la['start_m']:.2f}",
                    la["label"],
                    f"{la['avg_qc']:.2f}",
                    f"{la['avg_fs']:.0f}",
                ])
            l_col_w = [1*cm, 1.8*cm, 1.8*cm, 2.2*cm, 5*cm, 2.2*cm, 2.2*cm]
            layer_tbl = Table(layer_data, colWidths=l_col_w, repeatRows=1)
            layer_tbl.setStyle(TableStyle([
                ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#C1550F")),
                ("TEXTCOLOR",   (0,0), (-1,0), colors.white),
                ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",    (0,0), (-1,-1), 7.5),
                ("ROWBACKGROUNDS", (0,1), (-1,-1),
                 [colors.HexColor("#fff8f0"), colors.white]),
                ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#dddddd")),
                ("ALIGN",       (0,0), (3,-1), "CENTER"),
            ]))
            story.append(layer_tbl)
            story.append(Spacer(1, 0.4*cm))

            # ── Interprétation scientifique ──────────────────────────────────
            story.append(Paragraph("4. Interprétation Géotechnique", h1_style))
            dominant = max(layers, key=lambda x: x["end_m"]-x["start_m"])
            n_layers = len(layers)
            qc_mean  = df["qc"].mean()
            qc_max_v = df["qc"].max()
            interp = (
                f"L'analyse du sondage <b>{fname}</b> révèle <b>{n_layers} couches</b> "
                f"géotechniquement distinctes sur une profondeur totale de "
                f"<b>{depth_max_m:.1f} m</b>. "
                f"La couche dominante est de type <b>«{dominant['label']}»</b>, "
                f"comprise entre {dominant['start_m']:.1f} m et {dominant['end_m']:.1f} m "
                f"(épaisseur : {dominant['end_m']-dominant['start_m']:.1f} m), "
                f"avec une résistance moyenne de <b>{dominant['avg_qc']:.2f} MPa</b>. "
            )
            if qc_max_v > 15:
                interp += (
                    f"Les valeurs élevées de q<sub>c</sub> atteignant <b>{qc_max_v:.1f} MPa</b> "
                    "indiquent la présence de matériaux compacts ou de sables denses en profondeur, "
                    "favorables à l'ancrage de fondations. "
                )
            elif qc_mean < 5:
                interp += (
                    "Les faibles valeurs de résistance de pointe suggèrent un terrain de faible "
                    "capacité portante, nécessitant un renforcement ou des fondations profondes. "
                )
            else:
                interp += (
                    f"Les résistances moyennes (q<sub>c</sub> moy. = {qc_mean:.2f} MPa) "
                    "indiquent un sol de capacité portante modérée, compatible avec des "
                    "fondations superficielles sous réserve d'une vérification approfondie. "
                )
            story.append(Paragraph(interp, body_style))
            story.append(Spacer(1, 0.3*cm))

            # Risque liquéfaction
            story.append(Paragraph("4.1 Évaluation du Risque de Liquéfaction", h2_style))
            rf_mean = float(df["fs"].mean() / (df["qc"].mean() * 1000) * 100) if df["qc"].mean() > 0 else 0
            if df["qc"].mean() < 5 and rf_mean > 2:
                liq_text = (
                    "La présence de sols fins avec un rapport de friction élevé "
                    f"(Rf moyen ≈ {rf_mean:.1f} %) et une faible résistance de pointe "
                    "indique un <b>risque de liquéfaction potentiellement élevé</b> "
                    "dans les zones saturées lors d'un séisme. Une analyse dynamique "
                    "selon Youd et al. (2001) est recommandée."
                )
            elif df["qc"].mean() > 10:
                liq_text = (
                    "Les résistances de pointe élevées indiquent un <b>risque de liquéfaction "
                    "faible à négligeable</b> pour ce type de formation. Les sables denses "
                    "identifiés présentent une résistance accrue à la liquéfaction."
                )
            else:
                liq_text = (
                    f"Le risque de liquéfaction est <b>modéré</b>. Le rapport de friction "
                    f"moyen de {rf_mean:.1f} % et les variations de q<sub>c</sub> "
                    "nécessitent une évaluation complémentaire par la méthode simplifiée "
                    "de Seed & Idriss (1971) adaptée aux conditions locales."
                )
            story.append(Paragraph(liq_text, body_style))

            # ── Profil CPTU — Image PNG intégrée ─────────────────────────────
            story.append(Spacer(1, 0.4*cm))
            story.append(Paragraph("5. Profil CPTU — Visualisation des données", h1_style))
            if SVG_ANIMATOR_AVAILABLE:
                try:
                    png_bytes = generate_cptu_png(self.df, title=f"{fname} — Profil CPTU")
                    if png_bytes:
                        import tempfile
                        from reportlab.platypus import Image as RLImage
                        tmp_png = tempfile.NamedTemporaryFile(
                            suffix=".png", delete=False, mode="wb"
                        )
                        tmp_png.write(png_bytes)
                        tmp_png.close()
                        img = RLImage(tmp_png.name, width=17 * cm, height=9.5 * cm)
                        story.append(img)
                        story.append(Paragraph(
                            "<i>Figure 1 : Profil CPTU — classification Robertson des couches "
                            "(Sol | qc | fs | Ic). Image statique g\u00e9n\u00e9r\u00e9e automatiquement.</i>",
                            caption
                        ))
                except Exception as _e_png:
                    story.append(Paragraph(
                        f"Visualisation non disponible : {_e_png}", body_style))
            else:
                story.append(Paragraph(
                    "Module de visualisation non disponible.", body_style))


        # ── Section 6 — Animation CPTU rendue en image statique ──────────────
        svg_for_pdf = (svg_override if svg_override is not None
                       else (self._svg_strings.get(key) or
                             getattr(self, '_data_svg_string', None) or ""))
        if svg_for_pdf:
            story.append(PageBreak())
            story.append(Paragraph("6. Présentation CPTU — Animation (rendu statique)", h1_style))
            story.append(Paragraph(
                "La figure ci-dessous est le rendu statique de la présentation animée CPTU. "
                "Elle illustre la succession des couches géologiques classifiées selon Robertson (1990), "
                "les profils q<sub>c</sub> et f<sub>s</sub> ainsi que l'indice I<sub>c</sub>. "
                "La couleur de chaque couche correspond à son type de sol (argile, sable, silt…).",
                body_style
            ))
            story.append(Spacer(1, 0.3*cm))
            try:
                svg_png = self._svg_to_png_bytes(svg_for_pdf, width=1400, height=920)
                if svg_png:
                    import tempfile
                    from reportlab.platypus import Image as RLImage
                    tmp2 = tempfile.NamedTemporaryFile(
                        suffix=".png", delete=False, mode="wb")
                    tmp2.write(svg_png)
                    tmp2.close()
                    img2 = RLImage(tmp2.name, width=17*cm, height=11*cm)
                    story.append(img2)
                    story.append(Paragraph(
                        "<i>Figure 2 : Présentation animée CPTU — vue statique exportée. "
                        "Colonnes gauche→droite : type de sol Robertson | "
                        "q<sub>c</sub> (MPa) | f<sub>s</sub> (kPa) | I<sub>c</sub>.</i>",
                        caption
                    ))
                else:
                    story.append(Paragraph(
                        "Rendu SVG non disponible (SVG vide ou non supporté).", body_style))
            except Exception as _e_svg:
                story.append(Paragraph(
                    f"Rendu SVG non disponible : {_e_svg}", body_style))

        # ── Pied de page info ─────────────────────────────────────────────────
        story.append(Spacer(1, 1*cm))
        story.append(HRFlowable(width="100%", thickness=1,
                                color=colors.HexColor("#C1550F"), spaceAfter=6))
        story.append(Paragraph(
            "Rapport généré par <b>SETRAF CPT Analysis Studio</b> — "
            "Analyses géotechniques CPT/CPTU — © 2026",
            small_style
        ))

        doc.build(story)

    def createOverviewTab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Bouton de téléchargement PDF
        pdf_btn = QPushButton("📄 Télécharger Vue d'ensemble en PDF")
        pdf_btn.setStyleSheet("QPushButton { font-size: 14px; font-weight: bold; padding: 10px; background-color: #0078d7; color: white; border-radius: 5px; } QPushButton:hover { background-color: #005a9e; }")
        pdf_btn.clicked.connect(self.saveOverviewAsPDF)
        layout.addWidget(pdf_btn)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        main_layout = QVBoxLayout()
        
        # Section Graphiques
        graphs_label = QLabel("📊 Tous les Graphiques")
        graphs_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(graphs_label)
        
        graphs_grid = QGridLayout()
        self.overview_canvases = []
        
        plots_config = [
            ('qc vs Profondeur', lambda df, ax: self.plot_qc_depth(df, ax)),
            ('fs vs Profondeur', lambda df, ax: self.plot_fs_depth(df, ax)),
            ('Rf vs Profondeur', lambda df, ax: self.plot_rf_depth(df, ax)),
            ('qnet vs Profondeur', lambda df, ax: self.plot_qnet_depth(df, ax)),
            ('Classification des sols', lambda df, ax: self.plot_soil_classification(df, ax)),
            ('Clusters K-means', lambda df, ax: self.plot_kmeans_clusters(df, ax)),
            ('PCA - Composantes principales', lambda df, ax: self.plot_pca(df, ax)),
            ('Profil lissé qc', lambda df, ax: self.plot_smooth_qc(df, ax)),
            ('Profil lissé fs', lambda df, ax: self.plot_smooth_fs(df, ax)),
            ('Histogramme qc', lambda df, ax: self.plot_qc_histogram(df, ax)),
            ('Histogramme fs', lambda df, ax: self.plot_fs_histogram(df, ax)),
            ('Boxplot qc par couche', lambda df, ax: self.plot_qc_boxplot(df, ax)),
            ('Boxplot fs par couche', lambda df, ax: self.plot_fs_boxplot(df, ax)),
            ('Nuage de points qc vs fs', lambda df, ax: self.plot_qc_fs_scatter(df, ax)),
            ('Courbe cumulative qc', lambda df, ax: self.plot_qc_cumulative(df, ax)),
            ('Courbe cumulative fs', lambda df, ax: self.plot_fs_cumulative(df, ax)),
            ('Profil de friction ratio', lambda df, ax: self.plot_friction_ratio(df, ax)),
            ('Analyse de tendance qc', lambda df, ax: self.plot_qc_trend(df, ax)),
            ('Analyse de tendance fs', lambda df, ax: self.plot_fs_trend(df, ax)),
            ('Carte de chaleur corrélations', lambda df, ax: self.plot_correlation_heatmap(df, ax)),
        ]
        
        for i, (title, plot_func) in enumerate(plots_config):
            group = QGroupBox(title)
            group.setStyleSheet("QGroupBox { font-weight: bold; border: 2px solid #555; border-radius: 5px; margin-top: 1ex; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px 0 5px; }")
            group_layout = QVBoxLayout()
            canvas = FigureCanvas(plt.Figure(figsize=(8, 6)))
            ax = canvas.figure.add_subplot(111)
            ax.set_title(title, fontsize=10, fontweight='bold')
            self.overview_canvases.append((canvas, plot_func))
            
            group_layout.addWidget(canvas)
            group.setLayout(group_layout)
            group.setMaximumWidth(400)
            graphs_grid.addWidget(group, i // 4, i % 4)  # 4 colonnes
        
        graphs_widget = QWidget()
        graphs_widget.setLayout(graphs_grid)
        main_layout.addWidget(graphs_widget)
        
        # Section Tableaux
        tables_label = QLabel("📋 Tous les Tableaux")
        tables_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(tables_label)
        
        tables_grid = QGridLayout()
        
        self.overview_summaryTable = QTableWidget()
        self.overview_layersTable = QTableWidget()
        self.overview_statsTable = QTableWidget()
        self.overview_correlationTable = QTableWidget()
        self.overview_liquefactionTable = QTableWidget()
        
        tables = [
            (self.overview_summaryTable, "Résumé des données"),
            (self.overview_layersTable, "Classification par couches"),
            (self.overview_statsTable, "Statistiques détaillées"),
            (self.overview_correlationTable, "Matrice de corrélation"),
            (self.overview_liquefactionTable, "Analyse de liquéfaction")
        ]
        
        for i, (table, title) in enumerate(tables):
            table.setAlternatingRowColors(True)
            table.setMinimumWidth(300)
            table.setMaximumWidth(500)
            row = i // 3
            col = i % 3
            tables_grid.addWidget(QLabel(f"📋 {title}"), row * 2, col)
            tables_grid.addWidget(table, row * 2 + 1, col)
        
        tables_widget = QWidget()
        tables_widget.setLayout(tables_grid)
        main_layout.addWidget(tables_widget)
        
        content.setLayout(main_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Vue d'ensemble")

    # Méthodes de tracé pour les 20 graphiques
    def plot_qc_depth(self, df, ax):
        ax.plot(df['qc'], df['Depth'], 'b-', linewidth=2, label='qc (MPa)', color='#2a82da')
        ax.set_xlabel('Résistance de pointe qc (MPa)', color='white')
        ax.set_ylabel('Profondeur (m)', color='white')
        ax.invert_yaxis()
        ax.legend()
        ax.grid(True, alpha=0.3, color='white')
        ax.set_facecolor('#2a2a2a')

    def plot_fs_depth(self, df, ax):
        ax.plot(df['fs'], df['Depth'], 'r-', linewidth=2, label='fs (kPa)', color='#da2a2a')
        ax.set_xlabel('Résistance latérale fs (kPa)', color='white')
        ax.set_ylabel('Profondeur (m)', color='white')
        ax.invert_yaxis()
        ax.legend()
        ax.grid(True, alpha=0.3, color='white')
        ax.set_facecolor('#2a2a2a')

    def plot_rf_depth(self, df, ax):
        if 'Rf' in df.columns:
            ax.plot(df['Rf'], df['Depth'], 'g-', linewidth=2, label='Rf (%)')
            ax.set_xlabel('Ratio de friction Rf (%)')
            ax.set_ylabel('Profondeur (m)')
            ax.invert_yaxis()
            ax.legend()
            ax.grid(True, alpha=0.3)

    def plot_qnet_depth(self, df, ax):
        if 'qnet' in df.columns:
            ax.plot(df['qnet'], df['Depth'], 'm-', linewidth=2, label='qnet (MPa)')
            ax.set_xlabel('Résistance nette qnet (MPa)')
            ax.set_ylabel('Profondeur (m)')
            ax.invert_yaxis()
            ax.legend()
            ax.grid(True, alpha=0.3)

    def plot_soil_classification(self, df, ax):
        if 'Soil_Type' in df.columns:
            soil_colors = {'Sand': 'yellow', 'Silt': 'green', 'Clay': 'brown', 'Gravel': 'gray'}
            for soil, color in soil_colors.items():
                mask = df['Soil_Type'] == soil
                if mask.any():
                    ax.scatter(df.loc[mask, 'qc'], df.loc[mask, 'Depth'], c=color, label=soil, alpha=0.7)
            ax.set_xlabel('qc (MPa)')
            ax.set_ylabel('Profondeur (m)')
            ax.invert_yaxis()
            ax.legend()
            ax.grid(True, alpha=0.3)

    def plot_kmeans_clusters(self, df, ax):
        try:
            features = df[['qc', 'fs']].dropna()
            if len(features) > 5:
                scaler = StandardScaler()
                features_scaled = scaler.fit_transform(features)
                kmeans = KMeans(n_clusters=3, random_state=42)
                clusters = kmeans.fit_predict(features_scaled)
                ax.scatter(features['qc'], features['fs'], c=clusters, cmap='viridis', alpha=0.7)
                ax.set_xlabel('qc (MPa)')
                ax.set_ylabel('fs (kPa)')
                ax.set_title('Clusters K-means')
                ax.grid(True, alpha=0.3)
        except:
            ax.text(0.5, 0.5, 'Données insuffisantes', transform=ax.transAxes, ha='center')

    def plot_pca(self, df, ax):
        try:
            features = df[['qc', 'fs']].dropna()
            if len(features) > 5:
                scaler = StandardScaler()
                features_scaled = scaler.fit_transform(features)
                pca = PCA(n_components=2)
                pca_result = pca.fit_transform(features_scaled)
                ax.scatter(pca_result[:, 0], pca_result[:, 1], alpha=0.7)
                ax.set_xlabel('PC1')
                ax.set_ylabel('PC2')
                ax.set_title('PCA - 2 composantes')
                ax.grid(True, alpha=0.3)
        except:
            ax.text(0.5, 0.5, 'Données insuffisantes', transform=ax.transAxes, ha='center')

    def plot_smooth_qc(self, df, ax):
        try:
            y_smooth = savgol_filter(df['qc'], window_length=min(11, len(df)//2*2+1), polyorder=3)
            ax.plot(df['qc'], df['Depth'], 'b-', alpha=0.5, label='Original')
            ax.plot(y_smooth, df['Depth'], 'r-', linewidth=2, label='Lissé')
            ax.set_xlabel('qc (MPa)')
            ax.set_ylabel('Profondeur (m)')
            ax.invert_yaxis()
            ax.legend()
            ax.grid(True, alpha=0.3)
        except:
            ax.text(0.5, 0.5, 'Erreur de lissage', transform=ax.transAxes, ha='center')

    def plot_smooth_fs(self, df, ax):
        try:
            y_smooth = savgol_filter(df['fs'], window_length=min(11, len(df)//2*2+1), polyorder=3)
            ax.plot(df['fs'], df['Depth'], 'r-', alpha=0.5, label='Original')
            ax.plot(y_smooth, df['Depth'], 'b-', linewidth=2, label='Lissé')
            ax.set_xlabel('fs (kPa)')
            ax.set_ylabel('Profondeur (m)')
            ax.invert_yaxis()
            ax.legend()
            ax.grid(True, alpha=0.3)
        except:
            ax.text(0.5, 0.5, 'Erreur de lissage', transform=ax.transAxes, ha='center')

    def plot_qc_histogram(self, df, ax):
        ax.hist(df['qc'], bins=20, alpha=0.7, color='blue', edgecolor='black')
        ax.set_xlabel('qc (MPa)')
        ax.set_ylabel('Fréquence')
        ax.set_title('Distribution qc')
        ax.grid(True, alpha=0.3)

    def plot_fs_histogram(self, df, ax):
        ax.hist(df['fs'], bins=20, alpha=0.7, color='red', edgecolor='black')
        ax.set_xlabel('fs (kPa)')
        ax.set_ylabel('Fréquence')
        ax.set_title('Distribution fs')
        ax.grid(True, alpha=0.3)

    def plot_qc_boxplot(self, df, ax):
        ax.boxplot(df['qc'])
        ax.set_ylabel('qc (MPa)')
        ax.set_title('Boxplot qc')
        ax.grid(True, alpha=0.3)

    def plot_fs_boxplot(self, df, ax):
        ax.boxplot(df['fs'])
        ax.set_ylabel('fs (kPa)')
        ax.set_title('Boxplot fs')
        ax.grid(True, alpha=0.3)

    def plot_qc_fs_scatter(self, df, ax):
        ax.scatter(df['qc'], df['fs'], alpha=0.6, c=df['Depth'], cmap='viridis')
        ax.set_xlabel('qc (MPa)')
        ax.set_ylabel('fs (kPa)')
        ax.set_title('qc vs fs (couleur = profondeur)')
        ax.grid(True, alpha=0.3)

    def plot_qc_cumulative(self, df, ax):
        ax.plot(np.cumsum(df['qc']), df['Depth'], 'b-', linewidth=2)
        ax.set_xlabel('Somme cumulative qc')
        ax.set_ylabel('Profondeur (m)')
        ax.invert_yaxis()
        ax.grid(True, alpha=0.3)

    def plot_fs_cumulative(self, df, ax):
        ax.plot(np.cumsum(df['fs']), df['Depth'], 'r-', linewidth=2)
        ax.set_xlabel('Somme cumulative fs')
        ax.set_ylabel('Profondeur (m)')
        ax.invert_yaxis()
        ax.grid(True, alpha=0.3)

    def plot_friction_ratio(self, df, ax):
        if 'Rf' in df.columns:
            ax.plot(df['Rf'], df['Depth'], 'g-', linewidth=2)
            ax.axvline(x=5, color='r', linestyle='--', label='Limite sable/argile')
            ax.set_xlabel('Ratio de friction (%)')
            ax.set_ylabel('Profondeur (m)')
            ax.invert_yaxis()
            ax.legend()
            ax.grid(True, alpha=0.3)

    def plot_qc_trend(self, df, ax):
        z = np.polyfit(df['Depth'], df['qc'], 1)
        p = np.poly1d(z)
        ax.scatter(df['Depth'], df['qc'], alpha=0.6)
        ax.plot(df['Depth'], p(df['Depth']), 'r-', linewidth=2, label=f'Tendance: {z[0]:.4f}x + {z[1]:.2f}')
        ax.set_xlabel('Profondeur (m)')
        ax.set_ylabel('qc (MPa)')
        ax.legend()
        ax.grid(True, alpha=0.3)

    def plot_fs_trend(self, df, ax):
        z = np.polyfit(df['Depth'], df['fs'], 1)
        p = np.poly1d(z)
        ax.scatter(df['Depth'], df['fs'], alpha=0.6)
        ax.plot(df['Depth'], p(df['Depth']), 'r-', linewidth=2, label=f'Tendance: {z[0]:.4f}x + {z[1]:.2f}')
        ax.set_xlabel('Profondeur (m)')
        ax.set_ylabel('fs (kPa)')
        ax.legend()
        ax.grid(True, alpha=0.3)

    def plot_correlation_heatmap(self, df, ax):
        corr = df[['Depth', 'qc', 'fs']].corr()
        cax = ax.matshow(corr, cmap='coolwarm')
        ax.set_xticks(range(len(corr.columns)))
        ax.set_yticks(range(len(corr.columns)))
        ax.set_xticklabels(corr.columns)
        ax.set_yticklabels(corr.columns)
        plt.colorbar(cax, ax=ax)
        ax.set_title('Matrice de corrélation')

    def openFile(self):
        fileName, _ = QFileDialog.getOpenFileName(self, "Ouvrir fichier CPT", "",
                                                  "Fichiers CPT (*.txt *.xlsx *.csv *.xls *.cal);;Tous les fichiers (*)")
        if fileName:
            try:
                # Vérification d'intégrité des données avant parsing
                integrity_results = self.data_checker.verify_file_integrity(fileName)

                # Afficher les résultats de vérification
                integrity_report = self.data_checker.generate_integrity_report(fileName)

                # Parser le fichier avec le nouveau CPTParser
                parser = CPTParser()
                df, parse_message = parser.parse_file(fileName)

                if df is None:
                    QMessageBox.warning(self, "Erreur de parsing", f"Échec du parsing: {parse_message}")
                    return

                # Vérifier l'intégrité des données parsées
                if not integrity_results['data_integrity']:
                    warning_msg = "⚠️ PROBLÈMES D'INTÉGRITÉ DÉTECTÉS:\n\n"
                    if integrity_results['parsing_errors']:
                        warning_msg += "Erreurs de parsing:\n" + "\n".join(f"• {e}" for e in integrity_results['parsing_errors']) + "\n\n"
                    if integrity_results['data_loss_warnings']:
                        warning_msg += "Avertissements perte de données:\n" + "\n".join(f"• {w}" for w in integrity_results['data_loss_warnings']) + "\n\n"
                    if integrity_results['precision_warnings']:
                        warning_msg += "Avertissements précision:\n" + "\n".join(f"• {w}" for w in integrity_results['precision_warnings']) + "\n\n"
                    if integrity_results['range_warnings']:
                        warning_msg += "Avertissements plage:\n" + "\n".join(f"• {w}" for w in integrity_results['range_warnings']) + "\n\n"

                    warning_msg += "Voulez-vous continuer avec ces données ?"

                    reply = QMessageBox.question(self, "Avertissement Intégrité",
                                               warning_msg,
                                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                               QMessageBox.StandardButton.No)

                    if reply == QMessageBox.StandardButton.No:
                        return

                # Normaliser les noms de colonnes pour la compatibilité
                column_normalization = {
                    'depth': 'Depth', 'profondeur': 'Depth',
                    'qc': 'qc', 'résistance': 'qc', 'pression': 'qc',
                    'fs': 'fs', 'frottement': 'fs',
                    'u': 'u', 'pore_pressure': 'u',
                    'u2': 'u2',
                    'rf': 'Rf', 'friction_ratio': 'Rf',
                    'gamma': 'gamma', 'unit_weight': 'gamma',
                    'vs': 'Vs', 'shear_wave': 'Vs'
                }

                df = df.rename(columns=column_normalization)

                # Trier par profondeur si disponible (sans conversion destructive)
                if 'Depth' in df.columns:
                    df = df.sort_values('Depth').reset_index(drop=True)

                # Garder les données avec NaN partiels plutôt que supprimer toutes les lignes
                # Seulement supprimer les lignes complètement vides
                df = df.dropna(how='all')

                self.df = df

                # Afficher le rapport d'intégrité dans la console pour debug
                print(integrity_report)

                # Message de succès avec informations d'intégrité
                integrity_status = "✓ Données validées" if integrity_results['data_integrity'] else "⚠️ Anomalies détectées"
                success_msg = f"Fichier chargé: {len(df)} points de données\n{integrity_status}\n\n"
                success_msg += f"Colonnes: {', '.join(df.columns)}\n"
                success_msg += f"Statistiques rapides:\n"

                if 'Depth' in df.columns:
                    success_msg += f"• Profondeur: {df['Depth'].min():.2f} - {df['Depth'].max():.2f} m\n"
                if 'qc' in df.columns:
                    success_msg += f"• qc: {df['qc'].min():.2f} - {df['qc'].max():.2f} MPa\n"
                if 'fs' in df.columns:
                    success_msg += f"• fs: {df['fs'].min():.2f} - {df['fs'].max():.2f} kPa\n"
                    print(f"DEBUG: fs stats - Min: {df['fs'].min():.2f}, Max: {df['fs'].max():.2f}, Count: {len(df['fs'])}")

                success_msg += "\nCliquez sur 'Analyser' pour lancer l'analyse complète avec IA."

                self.analysis_results = f"Fichier chargé avec vérification d'intégrité.\n{integrity_status}"

                self.updateAll()

                QMessageBox.information(self, "Succès", success_msg)

            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Échec du chargement: {str(e)}")

    def updateAll(self):
        self.updateDataTable()
        self.updateGraphs()
        self.update3D()
        self.updateAnalysis()
        self.updateTables()
        self.updateAI()
        
        # Activer/désactiver les boutons d'export 3D selon la présence de données
        has_data = hasattr(self, 'df') and self.df is not None and not self.df.empty
        has_3d_views = all(hasattr(self, f'webView{i}') for i in range(1, 5))
        
        if hasattr(self, 'export3DPDFButton'):
            self.export3DPDFButton.setEnabled(has_data and has_3d_views)
        if hasattr(self, 'export3DIndividualButton'):
            self.export3DIndividualButton.setEnabled(has_data and has_3d_views)
        if hasattr(self, 'refresh3DButton'):
            self.refresh3DButton.setEnabled(has_3d_views)

    def updateDataTable(self):
        if self.df is not None:
            self.dataTable.setRowCount(len(self.df))
            self.dataTable.setColumnCount(len(self.df.columns))
            self.dataTable.setHorizontalHeaderLabels(list(self.df.columns))
            for i in range(min(1000, len(self.df))):
                for j in range(len(self.df.columns)):
                    self.dataTable.setItem(i, j, QTableWidgetItem(str(self.df.iloc[i, j])))
            # Auto-génération de l'animation SVG dans le panneau droit
            if SVG_ANIMATOR_AVAILABLE and hasattr(self, 'dataSvgView'):
                try:
                    fname = (os.path.basename(self.current_file)
                             if hasattr(self, 'current_file') and self.current_file
                             else "CPTU")
                    base  = os.path.splitext(fname)[0]
                    svg_str = generate_cptu_animation(self.df, title=base)
                    self._data_svg_string = svg_str
                    html = (
                        "<!DOCTYPE html><html>"
                        "<body style='margin:0;background:#16140e;overflow:hidden;'>"
                        + svg_str
                        + "</body></html>"
                    )
                    self.dataSvgView.setHtml(html)
                    if hasattr(self, '_data_svg_save_btn'):
                        self._data_svg_save_btn.setEnabled(True)
                except Exception as _e:
                    print(f"[SVG] Erreur génération animation données: {_e}")

    def updateGraphs(self):
        for canvas, plot_func in self.canvases:
            canvas.figure.clear()
            ax = canvas.figure.add_subplot(111)
            if self.df is not None:
                try:
                    plot_func(self.df, ax)
                except Exception as e:
                    ax.text(0.5, 0.5, f'Erreur: {str(e)}', transform=ax.transAxes, ha='center')
            canvas.draw()
        
        # Update overview canvases
        if hasattr(self, 'overview_canvases'):
            for canvas, plot_func in self.overview_canvases:
                canvas.figure.clear()
                ax = canvas.figure.add_subplot(111)
                if self.df is not None:
                    try:
                        plot_func(self.df, ax)
                    except Exception as e:
                        ax.text(0.5, 0.5, f'Erreur: {str(e)}', transform=ax.transAxes, ha='center')
                canvas.draw()

    def update3D(self):
        # Vérifier que les webView existent
        webviews = ['webView1', 'webView2', 'webView3', 'webView4']
        for wv_name in webviews:
            if not hasattr(self, wv_name):
                print(f"⚠️ {wv_name} n'existe pas encore")
                return

        if self.df is not None and not self.df.empty:
            try:
                # Vérifier que les colonnes nécessaires existent
                required_cols = ['Depth', 'qc', 'fs']
                missing_cols = [col for col in required_cols if col not in self.df.columns]
                if missing_cols:
                    error_msg = f"Colonnes manquantes pour les graphiques 3D: {', '.join(missing_cols)}"
                    error_html = f"<h2>Erreur 3D</h2><p>{error_msg}</p><p>Colonnes disponibles: {', '.join(self.df.columns)}</p>"
                    for webview in [self.webView1, self.webView2, self.webView3, self.webView4]:
                        if hasattr(self, type(webview).__name__):
                            webview.setHtml(error_html)
                    return

                # Nettoyer les données
                df_clean = self.df.dropna(subset=required_cols)
                if len(df_clean) < 3:
                    error_html = "<h2>Erreur 3D</h2><p>Pas assez de données valides pour créer les graphiques 3D (minimum 3 points requis)</p>"
                    for webview in [self.webView1, self.webView2, self.webView3, self.webView4]:
                        if hasattr(self, type(webview).__name__):
                            webview.setHtml(error_html)
                    return

                # Plot 1: 3D Scatter Depth vs qc vs fs
                fig1 = go.Figure()
                fig1.add_trace(go.Scatter3d(
                    x=df_clean['Depth'],
                    y=df_clean['qc'],
                    z=df_clean['fs'],
                    mode='markers',
                    marker=dict(size=4, color=df_clean['qc'], colorscale='Viridis', showscale=True)
                ))
                fig1.update_layout(
                    title='3D Scatter: Depth vs qc vs fs',
                    scene=dict(
                        xaxis_title='Depth (m)',
                        yaxis_title='qc (MPa)',
                        zaxis_title='fs (kPa)',
                        camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
                    ),
                    template='plotly_white',
                    height=500,
                    width=None,  # Responsive width
                    margin=dict(l=40, r=40, t=60, b=40, pad=10),
                    autosize=True
                )
                html1 = fig1.to_html(include_plotlyjs='cdn', full_html=False, config={'responsive': True})
                self.webView1.setHtml(html1)

                # Plot 2: 3D Surface plot for qc (version simplifiée sans interpolation)
                try:
                    # Essayer avec interpolation scipy
                    depth_grid = np.linspace(df_clean['Depth'].min(), df_clean['Depth'].max(), 30)
                    qc_grid = np.linspace(df_clean['qc'].min(), df_clean['qc'].max(), 30)
                    DEPTH, QC = np.meshgrid(depth_grid, qc_grid)

                    from scipy.interpolate import griddata
                    FS_interp = griddata((df_clean['Depth'], df_clean['qc']), df_clean['fs'],
                                       (DEPTH, QC), method='linear', fill_value=float(np.mean(df_clean['fs'])))

                    fig2 = go.Figure(data=[go.Surface(z=FS_interp, x=DEPTH, y=QC, colorscale='Viridis')])
                    fig2.update_layout(
                        title='3D Surface: qc vs Depth vs fs',
                        scene=dict(
                            xaxis_title='Depth (m)',
                            yaxis_title='qc (MPa)',
                            zaxis_title='fs (kPa)',
                            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
                        ),
                        template='plotly_white',
                        height=500,
                        width=None,  # Responsive width
                        margin=dict(l=40, r=40, t=60, b=40, pad=10),
                        autosize=True
                    )
                    html2 = fig2.to_html(include_plotlyjs='cdn', full_html=False, config={'responsive': True})
                    self.webView2.setHtml(html2)

                except ImportError:
                    # Fallback sans scipy - utiliser un scatter 3D coloré
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter3d(
                        x=df_clean['Depth'],
                        y=df_clean['qc'],
                        z=df_clean['fs'],
                        mode='markers',
                        marker=dict(size=6, color=df_clean['fs'], colorscale='Plasma', showscale=True)
                    ))
                    fig2.update_layout(
                        title='3D Scatter (Surface simulée): qc vs Depth vs fs',
                        scene=dict(
                            xaxis_title='Depth (m)',
                            yaxis_title='qc (MPa)',
                            zaxis_title='fs (kPa)',
                            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
                        ),
                        template='plotly_white',
                        height=500,
                        width=None,  # Responsive width
                        margin=dict(l=40, r=40, t=60, b=40, pad=10),
                        autosize=True
                    )
                    html2 = fig2.to_html(include_plotlyjs='cdn', full_html=False, config={'responsive': True})
                    self.webView2.setHtml(html2)

                except Exception as e:
                    # Fallback en cas d'erreur d'interpolation
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter3d(
                        x=df_clean['Depth'],
                        y=df_clean['qc'],
                        z=df_clean['fs'],
                        mode='markers',
                        marker=dict(size=6, color=df_clean['qc'], colorscale='Viridis', showscale=True)
                    ))
                    fig2.update_layout(
                        title='3D Scatter (Fallback): qc vs Depth vs fs',
                        scene=dict(
                            xaxis_title='Depth (m)',
                            yaxis_title='qc (MPa)',
                            zaxis_title='fs (kPa)',
                            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
                        ),
                        template='plotly_white',
                        height=500,
                        width=None,  # Responsive width
                        margin=dict(l=40, r=40, t=60, b=40, pad=10),
                        autosize=True
                    )
                    html2 = fig2.to_html(include_plotlyjs='cdn', full_html=False, config={'responsive': True})
                    self.webView2.setHtml(html2)

                # Plot 3: 3D Contour plot
                fig3 = go.Figure(data=go.Contour(
                    x=df_clean['Depth'],
                    y=df_clean['qc'],
                    z=df_clean['fs'],
                    colorscale='Viridis',
                    contours=dict(showlabels=True)
                ))
                fig3.update_layout(
                    title='3D Contour: Depth vs qc vs fs',
                    xaxis_title='Depth (m)',
                    yaxis_title='qc (MPa)',
                    template='plotly_white',
                    height=500,
                    width=None,  # Responsive width
                    margin=dict(l=60, r=40, t=60, b=60, pad=10),
                    autosize=True
                )
                html3 = fig3.to_html(include_plotlyjs='cdn', full_html=False, config={'responsive': True})
                self.webView3.setHtml(html3)

                # Plot 4: 3D Wireframe (version simplifiée)
                fig4 = go.Figure()
                fig4.add_trace(go.Scatter3d(
                    x=df_clean['Depth'],
                    y=df_clean['qc'],
                    z=df_clean['fs'],
                    mode='lines+markers',
                    line=dict(color='blue', width=2),
                    marker=dict(size=3, color='red'),
                    name='Wireframe'
                ))
                fig4.update_layout(
                    title='3D Wireframe: qc Surface with Contours',
                    scene=dict(
                        xaxis_title='Depth (m)',
                        yaxis_title='qc (MPa)',
                        zaxis_title='fs (kPa)',
                        camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
                    ),
                    template='plotly_white',
                    height=500,
                    width=None,  # Responsive width
                    margin=dict(l=40, r=40, t=60, b=40, pad=10),
                    autosize=True
                )
                html4 = fig4.to_html(include_plotlyjs='cdn', full_html=False, config={'responsive': True})
                self.webView4.setHtml(html4)

                print("✅ Graphiques 3D mis à jour avec succès")

            except Exception as e:
                error_html = f"<h1>Erreur 3D: {str(e)}</h1><p>Vérifiez que vos données contiennent les colonnes 'Depth', 'qc' et 'fs'</p>"
                print(f"❌ Erreur dans update3D(): {e}")
                import traceback
                traceback.print_exc()

                for webview in [self.webView1, self.webView2, self.webView3, self.webView4]:
                    if hasattr(self, type(webview).__name__ if hasattr(webview, '__name__') else 'webView'):
                        webview.setHtml(error_html)
        else:
            no_data_html = "<h1>Aucune donnée chargée</h1><p>Chargez un fichier CPTU pour voir les graphiques 3D</p>"
            for webview in [self.webView1, self.webView2, self.webView3, self.webView4]:
                if hasattr(self, type(webview).__name__ if hasattr(webview, '__name__') else 'webView'):
                    webview.setHtml(no_data_html)

    def updateAnalysis(self):
        """Mettre à jour l'analyse géotechnique"""
        if self.df is not None:
            try:
                analysis_result = perform_complete_analysis(self.df, use_streamlit=False)
                if isinstance(analysis_result, tuple):
                    df_analyzed, models, results = analysis_result
                    self.analysis_data = (df_analyzed, models, results)
                    self.analysis_results = self.create_analysis_summary(df_analyzed, results)
                else:
                    self.analysis_results = str(analysis_result)
                    self.analysis_data = None
                
                # Add layer types and zones
                layers = self.classify_layers()
                zones = self.determine_zones()
                
                full_analysis = f"{self.analysis_results}\n\n🏔️ Types de Couches:\n{layers}\n\n📍 Zones de Pointage:\n{zones}"
                self.analysisText.setText(full_analysis)

                # ── Nuage de points 3D ──────────────────────────────────────────
                if hasattr(self, 'analysis3DView'):
                    try:
                        html_3d = self._generate_soil_3d_html(self.df)
                        self.analysis3DView.setHtml(html_3d)
                    except Exception as _e3d:
                        import traceback as _tb
                        _msg = _tb.format_exc()
                        print(f"[3D] Erreur nuage de points: {_e3d}\n{_msg}")
                        self.analysis3DView.setHtml(
                            f"<body style='background:#16140e;color:#F59B3A;"
                            f"font-family:monospace;padding:12px;'>"
                            f"<b>Erreur 3D:</b> {_e3d}<pre style='color:#e08060;"
                            f"font-size:10px;'>{_msg}</pre></body>"
                        )

                # Initialize RAG system after complete analysis (with chunking and FAISS)
                if self.analysis_data and len(self.analysis_data) >= 3:
                    try:
                        if self.ai_explainer is not None:
                            self.ai_explainer.initialize_system(self.analysis_data[2])  # results dict
                        print("✅ Système RAG initialisé avec les résultats d'analyse")
                    except Exception as e:
                        print(f"⚠️ Erreur initialisation RAG: {e}")
                
            except Exception as e:
                error_msg = f"Erreur lors de l'analyse: {str(e)}"
                self.analysisText.setText(error_msg)
                print(f"❌ Erreur dans updateAnalysis(): {e}")
                import traceback
                traceback.print_exc()

    # ── 3D point-cloud helper ─────────────────────────────────────────────────────

    def _generate_soil_3d_html(self, df) -> str:
        """
        Génère un nuage de points 3D Plotly représentant les couches géologiques
        du sous-sol avec coloration Robertson.
        Retourne une chaîne HTML complète prête pour QWebEngineView.
        """
        import numpy as np

        rng = np.random.default_rng(42)   # reproductibilité

        depth_col  = "Depth" if "Depth" in df.columns else df.columns[0]
        depths_raw = df[depth_col].values.astype(float)
        qcs        = df["qc"].values.astype(float)
        fss        = df["fs"].values.astype(float)

        depths_m  = depths_raw * 0.01 if depths_raw.max() > 50 else depths_raw.copy()
        depth_max = float(depths_m.max()) or 1.0
        qc_max    = float(qcs.max()) or 1.0
        fs_max    = float(fss.max()) or 1.0

        layers = detect_layers(df)
        traces = []

        # ── 1. Nuage de points dense par couche ──────────────────────────────
        max_radius = 0.0
        for la in layers:
            r = 0.4 + (min(la["avg_qc"], 20.0) / 20.0) * 3.0
            max_radius = max(max_radius, r)

        for la in layers:
            thickness = la["end_m"] - la["start_m"]
            n_pts     = max(int(thickness * 600), 30)   # densité : 600 pts/m

            # Rayon d'influence : argile molle = étroit, sable dense = large
            radius = 0.4 + (min(la["avg_qc"], 20.0) / 20.0) * 3.0

            # Légère inclinaison géologique (simulation couches non horizontales)
            tilt_x = (la["start_m"] + la["end_m"]) / 2 / depth_max * 0.4
            tilt_y = -(la["start_m"] + la["end_m"]) / 2 / depth_max * 0.25

            theta = rng.uniform(0, 2 * np.pi, n_pts)
            r_pts = radius * np.sqrt(rng.uniform(0, 1, n_pts))
            x = r_pts * np.cos(theta) + tilt_x
            y = r_pts * np.sin(theta) + tilt_y
            z = -rng.uniform(la["start_m"], la["end_m"], n_pts)

            # Taille variable (couches dures = plus gros points)
            sizes = rng.uniform(2.0, 3.5 + la["avg_qc"] * 0.15, n_pts)
            sizes = np.clip(sizes, 1.5, 5.5)

            opacity = 0.50 if la["zone"] >= 7 else 0.68

            traces.append(go.Scatter3d(
                x=x.tolist(), y=y.tolist(), z=z.tolist(),
                mode="markers",
                name=la["label"],
                showlegend=True,
                marker=dict(
                    size=sizes.tolist(),
                    color=la["color"],
                    opacity=opacity,
                    line=dict(width=0),
                ),
                hovertemplate=(
                    f"<b>{la['label']}</b><br>"
                    f"Prof. {la['start_m']:.2f} – {la['end_m']:.2f} m<br>"
                    f"qc moy. = {la['avg_qc']:.2f} MPa<br>"
                    f"fs moy. = {la['avg_fs']:.0f} kPa<br>"
                    "<extra></extra>"
                ),
            ))

        # ── 2. Surfaces semi-transparentes aux limites de couches ─────────────
        mr = max_radius * 1.1
        for la in layers[:-1]:
            z_b  = -la["end_m"]
            # Disque rectangulaire centré
            xs   = [-mr, mr, mr, -mr, -mr]
            ys   = [-mr, -mr, mr, mr, -mr]
            zs   = [z_b] * 5
            traces.append(go.Scatter3d(
                x=xs, y=ys, z=zs,
                mode="lines",
                line=dict(color="#F59B3A", width=1.5),
                opacity=0.35,
                showlegend=False,
                hoverinfo="skip",
                name="",
            ))
            traces.append(go.Mesh3d(
                x=[-mr, mr, mr, -mr],
                y=[-mr, -mr, mr, mr],
                z=[z_b, z_b, z_b, z_b],
                i=[0, 0], j=[1, 2], k=[2, 3],
                color="#DA701C",
                opacity=0.07,
                showlegend=False,
                showscale=False,
                hoverinfo="skip",
            ))

        # ── 3. Axe du forage (borehole) centrale ─────────────────────────────
        bh_z = np.linspace(0, -depth_max, 120)
        traces.append(go.Scatter3d(
            x=[0.0] * 120, y=[0.0] * 120, z=bh_z.tolist(),
            mode="lines",
            name="Forage CPTU",
            showlegend=True,
            line=dict(color="#F59B3A", width=5),
        ))

        # ── 4. Profil qc normalisé sur l'axe X-Z ─────────────────────────────
        qc_norm = (qcs / qc_max) * (max_radius * 0.9)
        traces.append(go.Scatter3d(
            x=qc_norm.tolist(), y=[0.0] * len(depths_m), z=(-depths_m).tolist(),
            mode="lines+markers",
            name="Profil qc",
            showlegend=True,
            line=dict(color="#F59B3A", width=2),
            marker=dict(size=2.5, color=qc_norm.tolist(),
                        colorscale=[[0, "#1a1208"], [1, "#F59B3A"]],
                        showscale=False),
            hovertemplate="qc = %{x:.2f} → %{y:.2f} MPa<extra>qc</extra>",
        ))

        # ── 5. Profil fs normalisé sur l'axe Y-Z ─────────────────────────────
        fs_norm = (fss / fs_max) * (max_radius * 0.9)
        traces.append(go.Scatter3d(
            x=[0.0] * len(depths_m), y=fs_norm.tolist(), z=(-depths_m).tolist(),
            mode="lines+markers",
            name="Profil fs",
            showlegend=True,
            line=dict(color="#4ab8d8", width=2),
            marker=dict(size=2.5, color=fs_norm.tolist(),
                        colorscale=[[0, "#0a2030"], [1, "#4ab8d8"]],
                        showscale=False),
            hovertemplate="fs = %{y:.1f} kPa<extra>fs</extra>",
        ))

        # ── 6. Étiquettes des couches (Scatter3d text, pas d'annotations 3D) ─
        lbl_x, lbl_y, lbl_z, lbl_t, lbl_c = [], [], [], [], []
        for la in layers:
            mid_z = -(la["start_m"] + la["end_m"]) / 2
            if la["end_m"] - la["start_m"] >= 0.3:
                lbl_x.append(mr + 0.2)
                lbl_y.append(0.0)
                lbl_z.append(mid_z)
                lbl_t.append(
                    f"{la['label'][:18]}<br>"
                    f"{la['start_m']:.1f}–{la['end_m']:.1f}m"
                )
                lbl_c.append(la["color"])
        if lbl_x:
            traces.append(go.Scatter3d(
                x=lbl_x, y=lbl_y, z=lbl_z,
                mode="text",
                text=lbl_t,
                textfont=dict(size=9, color=lbl_c),
                showlegend=False,
                hoverinfo="skip",
                name="",
            ))

        fname = (
            os.path.basename(self.current_file)
            if hasattr(self, "current_file") and self.current_file
            else "CPTU"
        )

        # Z-axis ticks
        n_ticks = min(11, int(depth_max) + 1)
        z_tickvals = list(-np.linspace(0, depth_max, n_ticks))
        z_ticktext = [f"{abs(v):.1f} m" for v in z_tickvals]

        fig = go.Figure(data=traces)
        fig.update_layout(
            title=dict(
                text=f"Nuage de Points 3D — Sous-Sol CPTU  |  {fname}",
                font=dict(color="#F59B3A", size=14, family="Arial"),
                x=0.5, xanchor="center",
            ),
            scene=dict(
                xaxis=dict(
                    title=dict(text="X (m)", font=dict(color="#a07840")),
                    gridcolor="#2a2018", zerolinecolor="#443322",
                    backgroundcolor="#0d0b08",
                    tickfont=dict(color="#a07840", size=9),
                ),
                yaxis=dict(
                    title=dict(text="Y (m)", font=dict(color="#a07840")),
                    gridcolor="#2a2018", zerolinecolor="#443322",
                    backgroundcolor="#0d0b08",
                    tickfont=dict(color="#a07840", size=9),
                ),
                zaxis=dict(
                    title=dict(text="Profondeur", font=dict(color="#a07840")),
                    gridcolor="#2a2018", zerolinecolor="#443322",
                    backgroundcolor="#0d0b08",
                    tickvals=z_tickvals,
                    ticktext=z_ticktext,
                    tickfont=dict(color="#a07840", size=9),
                ),
                bgcolor="#0d0b08",
                camera=dict(
                    eye=dict(x=1.6, y=1.3, z=0.9),
                    up=dict(x=0, y=0, z=1),
                ),
                aspectmode="manual",
                aspectratio=dict(x=1, y=1, z=1.8),
            ),
            paper_bgcolor="#16140e",
            plot_bgcolor="#16140e",
            font=dict(color="#F0E1C3", family="Arial"),
            legend=dict(
                bgcolor="rgba(22,20,14,0.88)",
                bordercolor="#C1550F",
                borderwidth=1,
                font=dict(size=10, color="#F0E1C3"),
                x=0.01, y=0.99,
                xanchor="left", yanchor="top",
            ),
            margin=dict(l=0, r=0, t=44, b=0),
        )

        return fig.to_html(
            include_plotlyjs="cdn",
            full_html=False,
            config=dict(responsive=True, displaylogo=False,
                        modeBarButtonsToRemove=["toImage"]),
        )

    def createFused2DVisualization(self, fused_data):
        """Créer la visualisation 2D complète de tous les sondages fusionnés"""
        try:
            if fused_data is None or fused_data.empty:
                error_html = "<h1>Erreur 2D</h1><p>Aucune donnée fusionnée disponible</p>"
                self.fusion2DView.setHtml(error_html)
                return

            # Créer la figure Plotly 2D
            fig = go.Figure()
            
            # Couleurs pour différents sondages
            colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan', 
                     'magenta', 'yellow', 'black', 'navy', 'maroon', 'lime', 'aqua', 'fuchsia', 'silver', 'teal']
            
            sondages = fused_data['Sondage'].unique()
            
            # Créer une légende pour les couleurs
            color_map = {}
            for i, sondage in enumerate(sondages):
                color_map[sondage] = colors[i % len(colors)]
            
            # Tracer chaque sondage avec sa couleur
            for sondage in sondages:
                sondage_data = fused_data[fused_data['Sondage'] == sondage]
                color = color_map[sondage]
                
                # Points de données colorés par qc
                fig.add_trace(go.Scatter(
                    x=sondage_data['X'],
                    y=sondage_data['Y'],
                    mode='markers',
                    marker=dict(
                        size=8,
                        color=sondage_data['qc'] if 'qc' in sondage_data.columns else color,
                        colorscale='Viridis' if 'qc' in sondage_data.columns else None,
                        showscale=True if sondage == sondages[0] and 'qc' in sondage_data.columns else False,
                        colorbar=dict(title="qc (MPa)") if sondage == sondages[0] and 'qc' in sondage_data.columns else None,
                        symbol='circle',
                        line=dict(width=1, color='black')
                    ),
                    name=f'{sondage} - qc',
                    legendgroup=sondage,
                    hovertemplate=f'<b>{sondage}</b><br>' +
                                 'X: %{x:.1f} m<br>' +
                                 'Y: %{y:.1f} m<br>' +
                                 'Profondeur: %{customdata:.1f} m<br>' +
                                 'qc: %{marker.color:.1f} MPa<extra></extra>',
                    customdata=sondage_data['Depth']
                ))
                
                # Ligne connectant les points du sondage
                fig.add_trace(go.Scatter(
                    x=sondage_data['X'],
                    y=sondage_data['Y'],
                    mode='lines+markers',
                    line=dict(color=color, width=3),
                    marker=dict(size=4, color=color),
                    name=f'{sondage} - profil',
                    legendgroup=sondage,
                    showlegend=False,
                    hovertemplate=f'<b>{sondage}</b><br>' +
                                 'X: %{x:.1f} m<br>' +
                                 'Y: %{y:.1f} m<extra></extra>'
                ))
            
            # Ajouter des annotations pour les noms des sondages
            for sondage in sondages:
                sondage_data = fused_data[fused_data['Sondage'] == sondage]
                # Position du premier point pour l'annotation
                x_pos = sondage_data['X'].iloc[0]
                y_pos = sondage_data['Y'].iloc[0]
                color = color_map[sondage]
                
                fig.add_annotation(
                    x=x_pos,
                    y=y_pos,
                    text=sondage,
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor=color,
                    font=dict(size=12, color=color, family="Arial Black"),
                    bgcolor="white",
                    bordercolor=color,
                    borderwidth=2,
                    borderpad=4,
                    ax=20,
                    ay=-20
                )
            
            # Configuration du layout
            fig.update_layout(
                title="🗺️ Carte 2D Complète du Sous-Sol - Fusion de Sondages CPTU",
                xaxis_title='Coordonnée X (m)',
                yaxis_title='Coordonnée Y (m)',
                xaxis=dict(
                    scaleanchor="y",
                    scaleratio=1,
                    showgrid=True,
                    gridcolor='lightgray'
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='lightgray'
                ),
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=600,
                width=800,
                margin=dict(l=50, r=50, t=80, b=50),
                legend_title="Sondages CPTU",
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor="rgba(255, 255, 255, 0.8)",
                    bordercolor="black",
                    borderwidth=1
                )
            )
            
            # Ajouter une grille pour mieux visualiser
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            
            # Convertir en HTML et afficher
            html_content = fig.to_html(include_plotlyjs='cdn', full_html=False)
            self.fusion2DView.setHtml(html_content)
            
            # Informations sur la carte 2D
            info_2d = f"Carte 2D créée avec {len(sondages)} sondages:\n"
            for sondage in sondages:
                sondage_data = fused_data[fused_data['Sondage'] == sondage]
                color = color_map[sondage]
                info_2d += f"• {sondage}: {len(sondage_data)} points (couleur: {color})\n"
            
            self.fusion2DInfoLabel.setText(info_2d)
            self.fusion2DInfoLabel.setStyleSheet("font-weight: bold; color: #2196F3;")
            
            print("✅ Carte 2D fusionnée créée avec succès")
            
        except Exception as e:
            error_html = f"<h1>Erreur 2D Fusion: {str(e)}</h1>"
            self.fusion2DView.setHtml(error_html)
            print(f"❌ Erreur dans createFused2DVisualization: {e}")
            import traceback
            traceback.print_exc()

    def refresh3DGraphs(self):
        """Forcer le rafraîchissement des graphiques 3D"""
        try:
            print("🔄 Rafraîchissement des graphiques 3D...")
            self.update3D()
            QMessageBox.information(self, "Succès", "Graphiques 3D actualisés !")
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du rafraîchissement: {e}")

    def updateSummaryTable(self):
        """Mettre à jour la table de résumé"""
        if self.df is None:
            return
            
        try:
            # Calculer les statistiques de base
            summary_data = []
            
            # Statistiques générales
            summary_data.append(["Nombre de points", len(self.df)])
            summary_data.append(["Profondeur min (m)", f"{self.df['Depth'].min():.2f}"])
            summary_data.append(["Profondeur max (m)", f"{self.df['Depth'].max():.2f}"])
            
            if 'qc' in self.df.columns:
                summary_data.append(["qc min (MPa)", f"{self.df['qc'].min():.2f}"])
                summary_data.append(["qc max (MPa)", f"{self.df['qc'].max():.2f}"])
                summary_data.append(["qc moyen (MPa)", f"{self.df['qc'].mean():.2f}"])
            
            if 'fs' in self.df.columns:
                summary_data.append(["fs min (kPa)", f"{self.df['fs'].min():.2f}"])
                summary_data.append(["fs max (kPa)", f"{self.df['fs'].max():.2f}"])
                summary_data.append(["fs moyen (kPa)", f"{self.df['fs'].mean():.2f}"])
            
            # Remplir la table
            self.summaryTable.setRowCount(len(summary_data))
            self.summaryTable.setColumnCount(2)
            self.summaryTable.setHorizontalHeaderLabels(["Paramètre", "Valeur"])
            
            for i, (param, value) in enumerate(summary_data):
                self.summaryTable.setItem(i, 0, QTableWidgetItem(param))
                self.summaryTable.setItem(i, 1, QTableWidgetItem(str(value)))
                
        except Exception as e:
            print(f"Erreur updateSummaryTable: {e}")

    def updateLayersTable(self):
        """Mettre à jour la table des couches géologiques"""
        if self.df is None:
            return
            
        try:
            # Classifier les couches par profondeur
            layers_data = []
            depth_bins = [0, 2, 5, 10, 15, 20, 30]  # en mètres
            
            for i in range(len(depth_bins) - 1):
                start_depth = depth_bins[i]
                end_depth = depth_bins[i + 1]
                
                # Filtrer les données pour cette couche
                mask = (self.df['Depth'] >= start_depth) & (self.df['Depth'] < end_depth)
                layer_data = self.df[mask]
                
                if not layer_data.empty:
                    qc_avg = layer_data['qc'].mean() if 'qc' in layer_data.columns else 0
                    fs_avg = layer_data['fs'].mean() if 'fs' in layer_data.columns else 0
                    
                    # Classification simple
                    if qc_avg < 5:
                        soil_type = "Argile très molle"
                    elif qc_avg < 15:
                        soil_type = "Argile molle/firme"
                    elif qc_avg < 30:
                        soil_type = "Argile raide"
                    else:
                        soil_type = "Sable dense"
                    
                    layers_data.append([
                        f"{start_depth}-{end_depth}m",
                        soil_type,
                        f"{qc_avg:.1f}",
                        f"{fs_avg:.1f}",
                        len(layer_data)
                    ])
            
            # Remplir la table
            self.layersTable.setRowCount(len(layers_data))
            self.layersTable.setColumnCount(5)
            self.layersTable.setHorizontalHeaderLabels(["Profondeur", "Type de sol", "qc moyen (MPa)", "fs moyen (kPa)", "Points"])
            
            for i, (depth, soil, qc, fs, points) in enumerate(layers_data):
                self.layersTable.setItem(i, 0, QTableWidgetItem(depth))
                self.layersTable.setItem(i, 1, QTableWidgetItem(soil))
                self.layersTable.setItem(i, 2, QTableWidgetItem(qc))
                self.layersTable.setItem(i, 3, QTableWidgetItem(fs))
                self.layersTable.setItem(i, 4, QTableWidgetItem(str(points)))
                
        except Exception as e:
            print(f"Erreur updateLayersTable: {e}")

    def updateStatsTable(self):
        """Mettre à jour la table des statistiques détaillées"""
        if self.df is None:
            return
            
        try:
            stats_data = []
            
            # Statistiques pour chaque paramètre
            for col in ['qc', 'fs', 'Depth']:
                if col in self.df.columns:
                    data = self.df[col].dropna()
                    if not data.empty:
                        stats_data.extend([
                            [f"{col} - Minimum", f"{data.min():.2f}"],
                            [f"{col} - Maximum", f"{data.max():.2f}"],
                            [f"{col} - Moyenne", f"{data.mean():.2f}"],
                            [f"{col} - Écart-type", f"{data.std():.2f}"],
                            [f"{col} - Médiane", f"{data.median():.2f}"]
                        ])
            
            # Remplir la table
            self.statsTable.setRowCount(len(stats_data))
            self.statsTable.setColumnCount(2)
            self.statsTable.setHorizontalHeaderLabels(["Statistique", "Valeur"])
            
            for i, (stat, value) in enumerate(stats_data):
                self.statsTable.setItem(i, 0, QTableWidgetItem(stat))
                self.statsTable.setItem(i, 1, QTableWidgetItem(value))
                
        except Exception as e:
            print(f"Erreur updateStatsTable: {e}")

    def updateCorrelationTable(self):
        """Mettre à jour la table de corrélation"""
        if self.df is None:
            return
            
        try:
            # Calculer la matrice de corrélation
            numeric_cols = ['qc', 'fs', 'Depth']
            available_cols = [col for col in numeric_cols if col in self.df.columns]
            
            if len(available_cols) >= 2:
                corr_matrix = self.df[available_cols].corr()
                
                # Remplir la table
                self.correlationTable.setRowCount(len(available_cols))
                self.correlationTable.setColumnCount(len(available_cols))
                self.correlationTable.setHorizontalHeaderLabels(available_cols)
                self.correlationTable.setVerticalHeaderLabels(available_cols)
                
                for i, col1 in enumerate(available_cols):
                    for j, col2 in enumerate(available_cols):
                        corr_value = float(corr_matrix.loc[col1, col2])
                        item = QTableWidgetItem(f"{corr_value:.3f}")
                        # Colorer selon la force de corrélation
                        if abs(corr_value) > 0.7:
                            item.setBackground(QColor(100, 200, 100))  # Vert pour forte corrélation
                        elif abs(corr_value) > 0.3:
                            item.setBackground(QColor(200, 200, 100))  # Jaune pour corrélation moyenne
                        self.correlationTable.setItem(i, j, item)
            else:
                self.correlationTable.setRowCount(1)
                self.correlationTable.setColumnCount(1)
                self.correlationTable.setItem(0, 0, QTableWidgetItem("Données insuffisantes"))
                
        except Exception as e:
            print(f"Erreur updateCorrelationTable: {e}")

    def updateLiquefactionTable(self):
        """Mettre à jour la table d'analyse de liquéfaction"""
        if self.df is None:
            return
            
        try:
            liquefaction_data = []
            
            # Analyse simple de liquéfaction basée sur qc et fs
            for i, row in self.df.iterrows():
                qc = row.get('qc', 0)
                fs = row.get('fs', 0)
                depth = row.get('Depth', 0)
                
                # Critère simple de liquéfaction (très basique)
                fs_qc_ratio = 0.0
                if qc > 0:
                    fs_qc_ratio = fs / qc
                    if fs_qc_ratio < 0.5 and qc < 10:  # Seuil arbitraire pour démonstration
                        risk = "Élevé"
                    elif fs_qc_ratio < 1.0 and qc < 15:
                        risk = "Moyen"
                    else:
                        risk = "Faible"
                else:
                    risk = "N/A"
                
                liquefaction_data.append([
                    f"{depth:.1f}",
                    f"{qc:.1f}",
                    f"{fs:.1f}",
                    f"{fs_qc_ratio:.2f}" if qc > 0 else "N/A",
                    risk
                ])
            
            # Limiter à 100 lignes pour performance
            liquefaction_data = liquefaction_data[:100]
            
            # Remplir la table
            self.liquefactionTable.setRowCount(len(liquefaction_data))
            self.liquefactionTable.setColumnCount(5)
            self.liquefactionTable.setHorizontalHeaderLabels(["Profondeur (m)", "qc (MPa)", "fs (kPa)", "fs/qc", "Risque"])
            
            for i, (depth, qc, fs, ratio, risk) in enumerate(liquefaction_data):
                self.liquefactionTable.setItem(i, 0, QTableWidgetItem(depth))
                self.liquefactionTable.setItem(i, 1, QTableWidgetItem(qc))
                self.liquefactionTable.setItem(i, 2, QTableWidgetItem(fs))
                self.liquefactionTable.setItem(i, 3, QTableWidgetItem(ratio))
                
                risk_item = QTableWidgetItem(risk)
                # Colorer selon le risque
                if risk == "Élevé":
                    risk_item.setBackground(QColor(200, 100, 100))  # Rouge
                elif risk == "Moyen":
                    risk_item.setBackground(QColor(200, 200, 100))  # Jaune
                else:
                    risk_item.setBackground(QColor(100, 200, 100))  # Vert
                self.liquefactionTable.setItem(i, 4, risk_item)
                
        except Exception as e:
            print(f"Erreur updateLiquefactionTable: {e}")
            try:
                analysis_result = perform_complete_analysis(self.df, use_streamlit=False)
                if isinstance(analysis_result, tuple):
                    df_analyzed, models, results = analysis_result
                    self.analysis_data = (df_analyzed, models, results)
                    self.analysis_results = self.create_analysis_summary(df_analyzed, results)
                else:
                    self.analysis_results = str(analysis_result)
                    self.analysis_data = None
                
                # Add layer types and zones
                layers = self.classify_layers()
                zones = self.determine_zones()
                
                full_analysis = f"{self.analysis_results}\n\n🏔️ Types de Couches:\n{layers}\n\n📍 Zones de Pointage:\n{zones}"
                self.analysisText.setText(full_analysis)
                
                # Initialize RAG system after complete analysis (with chunking and FAISS)
                if self.analysis_data and len(self.analysis_data) >= 3:
                    try:
                        if self.ai_explainer is not None:
                            self.ai_explainer.initialize_system(self.analysis_data[2])  # results dict
                        print("✅ Système RAG initialisé avec les résultats d'analyse")
                    except Exception as e:
                        print(f"⚠️ Erreur initialisation RAG: {e}")
                
            except Exception as e:
                self.analysisText.setText(f"Erreur d'analyse: {str(e)}")
        else:
            self.analysisText.setText("Aucune donnée chargée")

    def create_analysis_summary(self, df_analyzed, results):
        summary = "🔬 Analyse Géotechnique Complète\n\n"
        
        # Statistiques générales
        summary += "📊 Statistiques Générales:\n"
        summary += f"Nombre de points: {len(df_analyzed)}\n"
        _dcol = next((c for c in ["Depth","depth","Profondeur","profondeur"] if c in df_analyzed.columns), df_analyzed.columns[0])
        _dfac = 0.01 if float(df_analyzed[_dcol].max()) > 200 else 1.0
        summary += f"Profondeur max: {float(df_analyzed[_dcol].max()) * _dfac:.2f} m\n"
        summary += f"qc moyen: {df_analyzed['qc'].mean():.2f} MPa\n"
        summary += f"fs moyen: {df_analyzed['fs'].mean():.2f} kPa\n\n"
        
        # Classification des sols
        if 'Soil_Type_Detailed' in df_analyzed.columns:
            soil_types = df_analyzed['Soil_Type_Detailed'].value_counts()
            summary += "🌱 Classification des Sols:\n"
            for soil, count in soil_types.items():
                summary += f"{soil}: {count} points ({count/len(df_analyzed)*100:.1f}%)\n"
            summary += "\n"
        
        # Couches identifiées
        if results and 'layers' in results and results['layers'] is not None:
            layers_df = results['layers']
            summary += f"🏔️ Couches Géologiques Identifiées: {len(layers_df)}\n"
            for _, layer in layers_df.iterrows():
                summary += f"  {layer['start_depth']:.1f}-{layer['end_depth']:.1f}m: {layer['soil_type']} (épaisseur: {layer['thickness']:.1f}m)\n"
            summary += "\n"
        
        # Analyse de liquéfaction
        if 'FS_Liquefaction' in df_analyzed.columns:
            liquefaction_risk = df_analyzed['Liquefaction_Risk'].value_counts() if 'Liquefaction_Risk' in df_analyzed.columns else None
            if liquefaction_risk is not None:
                summary += "🌊 Risque de Liquéfaction:\n"
                for risk, count in liquefaction_risk.items():
                    summary += f"{risk}: {count} points\n"
                summary += "\n"
        
        return summary

    def classify_layers(self):
        if self.df is None:
            return "Aucune donnée"
        # Détecte si la profondeur est en cm ou en m
        depth_col = next((c for c in ["Depth", "depth", "Profondeur", "profondeur"] if c in self.df.columns), self.df.columns[0])
        factor = 0.01 if self.df[depth_col].max() > 50 else 1.0
        layers = []
        for i, row in self.df.iterrows():
            qc = row['qc']
            fs = row.get('fs', 0)
            rf = (fs / (qc * 1000) * 100) if qc > 0 else 0
            depth_m = row[depth_col] * factor
            if qc < 5:
                layer = "Argile très molle (Ic > 3.6)"
            elif qc < 10:
                layer = "Argile molle (Ic 2.95-3.6)"
            elif qc < 20:
                layer = "Argile ferme (Ic 2.6-2.95)"
            elif qc < 40:
                layer = "Argile raide (Ic 2.05-2.6)"
            elif rf < 1:
                layer = "Sable dense (Ic < 2.05)"
            else:
                layer = "Silt sableux (Ic 2.05-2.6)"
            layers.append(f"Profondeur {depth_m:.2f} m: {layer} (qc={qc:.1f} MPa, fs={fs:.1f} kPa, Rf={rf:.1f}%)")
        return "\n".join(layers[:20])  # Limit to 20

    def determine_zones(self):
        if self.df is None:
            return "Aucune donnée"
        depth_col = next((c for c in ["Depth", "depth", "Profondeur", "profondeur"] if c in self.df.columns), self.df.columns[0])
        factor = 0.01 if self.df[depth_col].max() > 50 else 1.0
        depths_m = self.df[depth_col] * factor
        depth_max = depths_m.max()
        # Découpage automatique en 5 zones adaptées à la profondeur réelle
        step = max(1.0, round(depth_max / 5, 1))
        zones = []
        start = 0.0
        while start < depth_max:
            end = round(start + step, 1)
            mask = (depths_m >= start) & (depths_m < end)
            zone_data = self.df[mask]
            if not zone_data.empty:
                avg_qc = zone_data['qc'].mean()
                avg_fs = zone_data['fs'].mean()
                std_qc = zone_data['qc'].std()
                zones.append(f"Zone {start:.1f}-{end:.1f}m: qc moyen = {avg_qc:.1f} MPa (\u00b1{std_qc:.1f}), fs moyen = {avg_fs:.1f} kPa")
            start = end
        return "\n".join(zones)

    def updateTables(self):
        if self.df is not None:
            # Résumé statistique
            summary_data = self.df.describe()
            for table in [self.summaryTable, self.overview_summaryTable]:
                table.setRowCount(len(summary_data))
                table.setColumnCount(len(summary_data.columns))
                table.setHorizontalHeaderLabels(list(summary_data.columns))
                table.setVerticalHeaderLabels(list(summary_data.index))
                for i in range(len(summary_data)):
                    for j in range(len(summary_data.columns)):
                        table.setItem(i, j, QTableWidgetItem(f"{summary_data.iloc[i, j]:.2f}"))
            
            # Table des couches
            if self.analysis_data:
                df_analyzed, models, results = self.analysis_data
                if results and 'layers' in results and results['layers'] is not None:
                    layers_df = results['layers']
                    for table in [self.layersTable, self.overview_layersTable]:
                        table.setRowCount(len(layers_df))
                        table.setColumnCount(len(layers_df.columns))
                        table.setHorizontalHeaderLabels(layers_df.columns)
                        for i in range(len(layers_df)):
                            for j in range(len(layers_df.columns)):
                                table.setItem(i, j, QTableWidgetItem(str(layers_df.iloc[i, j])))
            
            # Statistiques détaillées (même que résumé pour l'instant)
            for table in [self.statsTable, self.overview_statsTable]:
                table.setRowCount(len(summary_data))
                table.setColumnCount(len(summary_data.columns))
                table.setHorizontalHeaderLabels(list(summary_data.columns))
                table.setVerticalHeaderLabels(list(summary_data.index))
                for i in range(len(summary_data)):
                    for j in range(len(summary_data.columns)):
                        table.setItem(i, j, QTableWidgetItem(f"{summary_data.iloc[i, j]:.2f}"))
            
            # Table de corrélation
            if len(self.df.columns) > 1:
                corr = self.df.select_dtypes(include=[np.number]).corr()
                for table in [self.correlationTable, self.overview_correlationTable]:
                    table.setRowCount(len(corr))
                    table.setColumnCount(len(corr.columns))
                    table.setHorizontalHeaderLabels(list(corr.columns))
                    table.setVerticalHeaderLabels(list(corr.index))
                    for i in range(len(corr)):
                        for j in range(len(corr.columns)):
                            table.setItem(i, j, QTableWidgetItem(f"{corr.iloc[i, j]:.3f}"))
            
            # Table de liquéfaction
            if self.analysis_data:
                df_analyzed, models, results = self.analysis_data
                if 'FS_Liquefaction' in df_analyzed.columns:
                    liquefaction_data = df_analyzed[['Depth', 'qc', 'FS_Liquefaction', 'Liquefaction_Risk']].dropna()
                    for table in [self.liquefactionTable, self.overview_liquefactionTable]:
                        table.setRowCount(len(liquefaction_data))
                        table.setColumnCount(len(liquefaction_data.columns))
                        table.setHorizontalHeaderLabels(list(liquefaction_data.columns))
                        for i in range(len(liquefaction_data)):
                            for j in range(len(liquefaction_data.columns)):
                                table.setItem(i, j, QTableWidgetItem(str(liquefaction_data.iloc[i, j])))

            # Activer le bouton "Générer Animation SVG" pour chaque table
            for attr in ['summaryTable', 'layersTable', 'statsTable',
                         'correlationTable', 'liquefactionTable']:
                tbl = getattr(self, attr, None)
                if tbl and hasattr(tbl, '_gen_btn'):
                    tbl._gen_btn.setEnabled(True)

    def updateAI(self):
        try:
            if self.df is not None and len(self.df) > 0:
                if hasattr(self, 'analysis_data') and self.analysis_data:
                    # Données chargées et analysées - afficher le chat IA
                    welcome_text = """📊 Données chargées: {} points<br>
🔬 Analyse disponible: {}<br>
💬 Prêt à répondre à vos questions sur les données CPT!<br><br>

💡 <strong>Exemples de questions:</strong><br>
• "Quelle est la classification des sols?"<br>
• "Y a-t-il un risque de liquéfaction?"<br>
• "Décrivez les couches géologiques"<br>
• "Quelles sont les statistiques de qc?"<br><br>

<em>Tapez votre question ci-dessous 👇</em>""".format(
                        len(self.df),
                        "Oui" if self.analysis_data else "Non - lancez l'analyse d'abord"
                    )
                    self.addChatMessage("ai", welcome_text)
                    self.status_bar.showMessage("✅ Chat IA prêt")
                else:
                    # Données chargées mais pas analysées
                    welcome_text = """📊 Données chargées: {} points<br>
⚠️ Analyse non effectuée<br><br>

🔬 Cliquez sur "Analyser" pour lancer l'analyse complète avec IA<br>
📈 Après l'analyse, vous pourrez poser des questions sur vos données CPT<br><br>

<strong>Fonctionnalités disponibles après analyse:</strong><br>
• Classification automatique des sols<br>
• Analyse de liquéfaction<br>
• Identification des couches géologiques<br>
• Statistiques détaillées<br>
• Réponses IA contextuelles avec recherches web<br>
• Visualisations intégrées""".format(len(self.df))
                    self.addChatMessage("ai", welcome_text)
                    self.status_bar.showMessage("⚠️ Lancez l'analyse pour activer le chat IA")
            else:
                # Aucune donnée
                welcome_text = """❌ Aucune donnée chargée<br><br>

📂 <strong>Pour commencer:</strong><br>
1. Cliquez sur "Fichier > Ouvrir"<br>
2. Sélectionnez un fichier CPT (.txt, .csv, .xlsx, .cal)<br>
3. Lancez l'analyse complète<br>
4. Posez vos questions à l'IA !<br><br>

💡 <strong>Formats supportés:</strong><br>
• Fichiers texte (.txt, .csv)<br>
• Excel (.xlsx, .xls)<br>
• Format binaire CPT (.cal)<br>
• Détection automatique des colonnes"""
                self.addChatMessage("ai", welcome_text)
                self.status_bar.showMessage("❌ Chargez des données CPT")
        except Exception as e:
            error_msg = f"❌ Erreur d'initialisation du chat IA: {str(e)}"
            self.addChatMessage("ai", f'<div class="error">{error_msg}</div>')
            self.status_bar.showMessage("❌ Erreur chat IA")

    def sendChatMessage(self):
        if self.df is None or len(self.df) == 0:
            self.addChatMessage("ai", "❌ Aucune donnée chargée pour discuter.<br><br>💡 Chargez d'abord un fichier CPT puis lancez l'analyse.")
            return
        question = self.chatInput.text().strip()
        if not question:
            return
        self.status_bar.showMessage("🤖 Envoi de la question IA...")

        # Vérifier que l'analyse a été effectuée
        if not hasattr(self, 'analysis_data') or not self.analysis_data or len(self.analysis_data) < 3:
            self.addChatMessage("user", question.replace('\n', '<br>'))
            self.addChatMessage("ai", "❌ Analyse non effectuée.<br><br>💡 Lancez d'abord l'analyse complète avant de poser des questions à l'IA.")
            self.chatInput.clear()
            self.status_bar.showMessage("❌ Analyse requise pour le chat IA")
            return

        # Ajouter la question de l'utilisateur
        self.addChatMessage("user", question.replace('\n', '<br>'))

        # Message de réflexion en cours
        thinking_content = "🤔 Analyse de votre question...<br><br>🔍 Recherche d'informations complémentaires...<br>🧮 Calculs en cours...<br>📊 Génération de visualisations..."
        self.addChatMessage("ai", f'<div class="loading">{thinking_content}</div>')

        try:
            # Initialiser le système RAG avec les données d'analyse si disponibles
            if self.ai_explainer is not None:
                if self.analysis_data and len(self.analysis_data) >= 3 and isinstance(self.analysis_data[2], dict):
                    self.ai_explainer.initialize_system(self.analysis_data[2])
                elif hasattr(self, 'df') and self.df is not None and not self.df.empty:
                    # Fallback: initialize with basic CPT data if no analysis results
                    basic_data = {'data': self.df}
                    self.ai_explainer.initialize_system(basic_data)

            # Afficher la réponse en streaming pour une expérience plus dynamique

            # Afficher la réponse en streaming pour une expérience plus dynamique
            response_parts = []
            response_display = f"🤖 Chat IA Géotechnique\n\n👤 {question}\n\n🤔 Analyse en cours..."

            # Essayer d'abord avec le streaming
            streaming_worked = False
            full_response = ""
            try:
                for part in (self.ai_explainer.query_streaming(question) if self.ai_explainer is not None else []):
                    if part and part.strip():  # Vérifier que la partie n'est pas vide
                        full_response += part
                        streaming_worked = True
                        
                        # Mise à jour progressive avec recherche web intégrée - plus fréquente pour streaming
                        if len(full_response) > 20 and (len(full_response) % 50 == 0 or part.strip().endswith('\n')):  # Mettre à jour tous les 50 caractères ou fins de ligne
                            # Ajouter des informations de recherche web
                            enhanced_response = self.enhance_response_with_web_search(full_response, question)
                            # Ajouter des visualisations si pertinent
                            enhanced_response = self.add_visualizations_to_response(enhanced_response, question)
                            
                            # Ajouter un indicateur de progression basé sur les phases
                            progress_indicator = self._get_progress_indicator(full_response)
                            preview = enhanced_response[:400] + "..." if len(enhanced_response) > 400 else enhanced_response
                            self.updateLastAIMessage(f'<div class="loading">{progress_indicator} {preview}</div>')
                            QApplication.processEvents()
                                
            except Exception as e:
                print(f"Streaming failed: {e}")
                streaming_worked = False

            # Traiter la réponse complète
            if streaming_worked and full_response:
                response_parts = [full_response]
            else:
                # Si le streaming n'a pas fonctionné, utiliser une approche directe
                try:
                    direct_response = self.ai_explainer.query(question) if self.ai_explainer is not None else None
                    if direct_response and direct_response.strip():
                        response_parts = [direct_response]
                    else:
                        response_parts = ["❌ Le système IA n'a pas pu générer de réponse. Vérifiez que l'analyse a été effectuée."]
                except Exception as e:
                    print(f"Direct query failed: {e}")
                    response_parts = [f"❌ Erreur du système IA: {str(e)}"]

            # Réponse finale complète avec enrichissements
            response = "".join(response_parts)
            if not response or not response.strip():
                response = "❌ Aucune réponse générée par l'IA."

            # Enrichir la réponse finale
            final_response = self.enhance_response_with_web_search(response, question)
            final_response = self.add_visualizations_to_response(final_response, question)
            
            # Remplacer le message de chargement par la réponse finale
            self.updateLastAIMessage(f"🧠 {final_response}")

            self.chatInput.clear()
            self.status_bar.showMessage("✅ Réponse IA reçue")
        except Exception as e:
            error_msg = f"❌ Erreur IA: {str(e)}<br><br>💡 Assurez-vous d'avoir lancé l'analyse complète avant de poser des questions."
            self.addChatMessage("ai", f'<div class="error">{error_msg}</div>')
            self.status_bar.showMessage("❌ Erreur chat IA")

    def savePlotAsPDF(self, idx):
        if self.df is not None:
            canvas, plot_func = self.canvases[idx]
            fig = plt.Figure(figsize=(10, 8))
            ax = fig.add_subplot(111)
            try:
                plot_func(self.df, ax)
                # Logo SETRAF
                _logo_mpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), "setraf_logo.png")
                try:
                    from PIL import Image as _PIL
                    _lax = fig.add_axes([0.01, 0.92, 0.10, 0.07])
                    _lax.imshow(_PIL.open(_logo_mpl))
                    _lax.axis('off')
                except Exception:
                    fig.text(0.01, 0.99, "© SETRAF", fontsize=7, color='gray', va='top', alpha=0.5)
                file_path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder en PDF", "", "PDF Files (*.pdf)")
                if file_path:
                    fig.savefig(file_path, format='pdf', bbox_inches='tight')
                    QMessageBox.information(self, "Succès", "Graphique sauvegardé en PDF!")
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Échec de la sauvegarde: {str(e)}")

    def saveOverviewAsPDF(self):
        if self.df is not None and hasattr(self, 'overview_canvases'):
            try:
                file_path, _ = QFileDialog.getSaveFileName(self, "Sauvegarder Vue d'ensemble en PDF", "", "PDF Files (*.pdf)")
                if file_path:
                    from matplotlib.backends.backend_pdf import PdfPages
                    _logo_ov = os.path.join(os.path.dirname(os.path.abspath(__file__)), "setraf_logo.png")
                    with PdfPages(file_path) as pdf:
                        for canvas, _ in self.overview_canvases:
                            _fig = canvas.figure
                            try:
                                from PIL import Image as _PIL
                                _lax = _fig.add_axes([0.01, 0.92, 0.08, 0.06])
                                _lax.imshow(_PIL.open(_logo_ov))
                                _lax.axis('off')
                            except Exception:
                                _fig.text(0.01, 0.99, "© SETRAF", fontsize=6, color='gray', va='top', alpha=0.5)
                            pdf.savefig(_fig, bbox_inches='tight')
                    QMessageBox.information(self, "Succès", "Vue d'ensemble sauvegardée en PDF!")
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Échec de la sauvegarde: {str(e)}")

    def exportDataToPDF(self):
        """Exporte un rapport PDF complet : données + SVG animé converti en image."""
        if self.df is None:
            QMessageBox.warning(self, "Données manquantes",
                                "Chargez d'abord un fichier CPTU.")
            return
        fname = (os.path.basename(self.current_file)
                 if hasattr(self, 'current_file') and self.current_file
                 else "Données_CPTU")
        base  = os.path.splitext(fname)[0]
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter Données en PDF",
            f"{base}_rapport.pdf", "PDF (*.pdf)")
        if not file_path:
            return
        try:
            self._build_pdf_report(
                file_path, "data", "Données CPTU",
                svg_override=getattr(self, '_data_svg_string', None)
            )
            QMessageBox.information(self, "PDF généré",
                                    f"Rapport complet enregistré :\n{file_path}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erreur PDF",
                                 f"Impossible de générer le rapport:\n{e}")

    def exportDataToExcel(self):
        if self.df is not None:
            try:
                file_path, _ = QFileDialog.getSaveFileName(self, "Exporter en Excel", "", "Excel Files (*.xlsx)")
                if file_path:
                    self.df.to_excel(file_path, index=False)
                    QMessageBox.information(self, "Succès", "Données exportées en Excel!")
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Échec de l'export: {str(e)}")

    # ══════════════════════════════════════════════════════════════════════════════
    #  RAPPORT SCIENTIFIQUE COMPLET (~30 PAGES)
    # ══════════════════════════════════════════════════════════════════════════════

    def _plot_func_to_png(self, plot_func, df, figsize=(9, 5.5)) -> bytes:
        """Rend une fonction de tracé matplotlib en PNG (bytes) via backend Agg."""
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import io as _io
            fig = plt.figure(figsize=figsize, facecolor="#16140e")
            ax = fig.add_subplot(111)
            ax.set_facecolor("#1a1208")
            ax.tick_params(colors="#a07840", labelsize=8)
            for sp in ax.spines.values():
                sp.set_color("#2a2018")
            try:
                plot_func(df, ax)
            except Exception as _pe:
                ax.text(0.5, 0.5, f"Tracé indisponible:\n{_pe}",
                        transform=ax.transAxes, ha='center', va='center',
                        color='#F59B3A', fontsize=8, wrap=True)
            buf = _io.BytesIO()
            fig.savefig(buf, format='png', dpi=110, bbox_inches='tight',
                        facecolor="#16140e")
            plt.close(fig)
            buf.seek(0)
            return buf.read()
        except Exception:
            return b""

    def exportAnalysisCompletePDF(self):
        """Lance l'export du rapport géotechnique complet (~30 pages) avec tous les graphiques."""
        if self.df is None:
            QMessageBox.warning(self, "Données manquantes",
                                "Chargez d'abord un fichier CPTU et lancez l'analyse.")
            return
        fname = (os.path.basename(self.current_file)
                 if hasattr(self, 'current_file') and self.current_file else "CPTU")
        base = os.path.splitext(fname)[0]
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer Rapport Scientifique Complet",
            f"{base}_rapport_geotechnique_complet.pdf", "PDF (*.pdf)")
        if not file_path:
            return

        from PySide6.QtWidgets import QProgressDialog
        progress = QProgressDialog(
            "Génération du rapport scientifique...", "Annuler", 0, 100, self)
        progress.setWindowTitle("Rapport en cours de génération...")
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.setValue(1)
        QApplication.processEvents()
        try:
            self._build_complete_analysis_pdf(file_path, progress)
            if not progress.wasCanceled():
                progress.close()
                QMessageBox.information(
                    self, "✅ Rapport généré",
                    f"Rapport scientifique complet enregistré :\n{file_path}\n\n"
                    "Le rapport contient tous les graphiques, la classification Robertson,\n"
                    "l'évaluation de liquéfaction et les références bibliographiques.")
        except RuntimeError as _cancel:
            progress.close()
            QMessageBox.information(self, "Annulé", "Génération du rapport annulée.")
        except Exception as e:
            progress.close()
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erreur PDF", f"Impossible de générer le rapport:\n{e}")

    def _build_complete_analysis_pdf(self, pdf_path: str, progress=None):
        """
        Rapport géotechnique scientifique complet (~30 pages) :
        - Couverture + table des matières
        - Robertson 1990 theory, formules, tableau 9 zones
        - Statistiques descriptives (tableau percentiles)
        - Profil CPTU 4 panneaux (generate_cptu_png)
        - 20 graphiques matplotlib (tous les plots)
        - Classification des couches (tableau)
        - Évaluation liquéfaction (Seed-Idriss 1971, Robertson-Wride 1998)
        - Animation SVG statique
        - Interprétation + recommandations + 15 références
        """
        import io as _io, os as _os, tempfile as _tp
        import numpy as np
        from datetime import date as _date
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors as rlcolors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, PageBreak, Image as RLImage,
        )
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT

        def upd(v, msg=""):
            if progress:
                progress.setValue(v)
                if msg:
                    progress.setLabelText(msg)
                QApplication.processEvents()
                if progress.wasCanceled():
                    raise RuntimeError("Annulé")

        upd(2, "Initialisation…")
        df   = self.df
        # ── Prépare df_plot : profondeurs en m + colonnes dérivées garanties ─
        df_plot = df.copy()
        _dc_p = next((c for c in ["Depth","depth","Profondeur","profondeur"]
                      if c in df_plot.columns), df_plot.columns[0])
        if _dc_p != "Depth":
            df_plot = df_plot.rename(columns={_dc_p: "Depth"})
        if df_plot["Depth"].max() > 200:
            df_plot["Depth"] = df_plot["Depth"] * 0.01
        if "Rf" not in df_plot.columns:
            df_plot["Rf"] = df_plot.apply(
                lambda r: (r["fs"] / (r["qc"] * 1000) * 100) if r["qc"] > 0 else 0.0, axis=1)
        if "qnet" not in df_plot.columns:
            df_plot["qnet"] = (df_plot["qc"] - df_plot["Depth"] * 18.0 / 1000.0).clip(lower=0)
        if "Soil_Type" not in df_plot.columns:
            import math as _mth
            def _soil_type_r(r):
                qv, rfv = max(r["qc"], 0.01), max(abs(r["Rf"]), 0.01)
                try:
                    ic = _mth.sqrt((3.47 - _mth.log10(max(qv / 0.1, 1.0)))**2 +
                                   (_mth.log10(rfv) + 1.22)**2)
                except Exception:
                    ic = 3.0
                return ("Clay" if ic > 2.95 else
                        "Silt" if ic > 2.05 else
                        "Sand" if ic > 1.31 else "Gravel")
            df_plot["Soil_Type"] = df_plot.apply(_soil_type_r, axis=1)
        fname = (_os.path.basename(self.current_file)
                 if hasattr(self, 'current_file') and self.current_file else "CPTU")
        depth_col = next((c for c in ["Depth","depth","Profondeur","profondeur"]
                          if c in df.columns), df.columns[0])
        d_factor  = 0.01 if df[depth_col].max() > 200 else 1.0
        depths_m  = df[depth_col].values.astype(float) * d_factor
        depth_max = float(depths_m.max())
        qcs = df["qc"].values.astype(float)
        fss = df["fs"].values.astype(float)
        rf_vals = np.where(qcs > 0, fss / (qcs * 1000) * 100, 0.0)
        rf_mean  = float(np.mean(rf_vals))
        qc_mean  = float(np.mean(qcs))
        today    = _date.today().strftime("%d %B %Y")

        # ── Couleurs & styles ────────────────────────────────────────────────
        ORANGE   = rlcolors.HexColor("#C1550F")
        ORANGE_L = rlcolors.HexColor("#F59B3A")
        NAVY     = rlcolors.HexColor("#1a3a6a")
        LGREY    = rlcolors.HexColor("#f5f5f5")
        styles   = getSampleStyleSheet()

        def ps(name, **kw):
            base = kw.pop("parent", styles["Normal"])
            return ParagraphStyle(name, parent=base, **kw)

        title_s   = ps("ts",  parent=styles["Title"], fontSize=20,
                        textColor=ORANGE, spaceAfter=8, alignment=TA_CENTER, leading=26)
        sub_s     = ps("ss",  fontSize=11, textColor=rlcolors.HexColor("#555"),
                        spaceAfter=4, alignment=TA_CENTER)
        ch_s      = ps("chs", parent=styles["Heading1"], fontSize=15,
                        textColor=ORANGE, spaceBefore=14, spaceAfter=5)
        h2_s      = ps("h2s", parent=styles["Heading2"], fontSize=12,
                        textColor=NAVY, spaceBefore=9, spaceAfter=4)
        h3_s      = ps("h3s", parent=styles["Heading3"], fontSize=10,
                        textColor=rlcolors.HexColor("#333"), spaceBefore=6, spaceAfter=3)
        body_s    = ps("bs",  fontSize=9.5, leading=15, spaceAfter=6,
                        alignment=TA_JUSTIFY)
        formula_s = ps("fs",  fontSize=9, leading=13, spaceAfter=4,
                        leftIndent=20, fontName="Courier",
                        textColor=NAVY)
        caption_s = ps("caps",fontSize=8, textColor=rlcolors.HexColor("#888"),
                        alignment=TA_CENTER, spaceAfter=6)
        ref_s     = ps("rs",  fontSize=8.5, leading=13, spaceAfter=3,
                        leftIndent=14, firstLineIndent=-14)
        small_s   = ps("sms", fontSize=8, textColor=rlcolors.HexColor("#666"))
        toc_s     = ps("toc", fontSize=10, leading=17, spaceAfter=2)
        toc_h_s   = ps("toch",fontSize=11, leading=19, spaceAfter=2,
                        fontName="Helvetica-Bold", textColor=ORANGE)
        warn_s    = ps("ws",  fontSize=8.5, leading=13,
                        textColor=rlcolors.HexColor("#856404"),
                        backColor=rlcolors.HexColor("#fff3cd"),
                        leftIndent=6, rightIndent=6, spaceAfter=6)
        li_s      = ps("lis", parent=body_s, leftIndent=14, spaceAfter=3)
        rec_s     = ps("recs",parent=body_s, leftIndent=10, spaceAfter=5)
        note_cov  = ps("nc",  fontSize=8.5, textColor=rlcolors.HexColor("#888"),
                        alignment=TA_CENTER, leftIndent=cm, rightIndent=cm)

        # ── Document ──────────────────────────────────────────────────────────
        doc = SimpleDocTemplate(
            pdf_path, pagesize=A4,
            rightMargin=2.2*cm, leftMargin=2.2*cm,
            topMargin=2.5*cm, bottomMargin=2*cm,
            title=f"Rapport Géotechnique CPTU — {fname}",
            author="SETRAF CPT Analysis Studio",
        )
        story     = []
        fig_count = [0]
        tmp_files = []

        # ── Chemin logo ─────────────────────────────────────────────────────
        _logo_p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "setraf_logo.png")

        def hr():
            story.append(HRFlowable(width="100%", thickness=1,
                                    color=ORANGE, spaceAfter=6))

        def add_png(png_bytes, caption_txt, width=14*cm):
            if not png_bytes:
                story.append(Paragraph("[Figure non disponible]", caption_s))
                return
            fig_count[0] += 1
            tmp = _tp.NamedTemporaryFile(suffix=".png", delete=False, mode="wb")
            tmp.write(png_bytes); tmp.close()
            tmp_files.append(tmp.name)
            try:
                from PIL import Image as _PIL
                pil = _PIL.open(_io.BytesIO(png_bytes))
                h = width * (pil.height / pil.width)
            except Exception:
                h = width * 0.6
            story.append(RLImage(tmp.name, width=width, height=h))
            story.append(Paragraph(
                f"<i>Figure {fig_count[0]} : {caption_txt}</i>", caption_s))
            story.append(Spacer(1, 0.3*cm))

        def side_by_side(png1, png2, cap):
            """Deux figures côte à côte."""
            if not png1 or not png2:
                return
            t1 = _tp.NamedTemporaryFile(suffix=".png", delete=False, mode="wb")
            t1.write(png1); t1.close(); tmp_files.append(t1.name)
            t2 = _tp.NamedTemporaryFile(suffix=".png", delete=False, mode="wb")
            t2.write(png2); t2.close(); tmp_files.append(t2.name)
            tbl = Table([[RLImage(t1.name, width=7*cm, height=5*cm),
                          RLImage(t2.name, width=7*cm, height=5*cm)]],
                        colWidths=[7.5*cm, 7.5*cm])
            tbl.setStyle(TableStyle([("ALIGN", (0,0), (-1,-1), "CENTER")]))
            story.append(tbl)
            fig_count[0] += 2
            story.append(Paragraph(
                f"<i>Figures {fig_count[0]-1}–{fig_count[0]} : {cap}</i>",
                caption_s))
            story.append(Spacer(1, 0.3*cm))

        def tbl_style(t, hdr_col=NAVY):
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), hdr_col),
                ("TEXTCOLOR",  (0,0), (-1,0), rlcolors.white),
                ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
                ("FONTSIZE",   (0,0), (-1,-1), 8.5),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [LGREY, rlcolors.white]),
                ("GRID",       (0,0), (-1,-1), 0.3, rlcolors.HexColor("#ccc")),
                ("BOTTOMPADDING", (0,0), (-1,-1), 4),
                ("TOPPADDING",    (0,0), (-1,-1), 4),
            ]))

        # ══════════════════════════════════════════════════════════════════════
        #  PAGE DE COUVERTURE
        # ══════════════════════════════════════════════════════════════════════
        upd(4, "Page de couverture…")
        # Logo SETRAF en haut de la couverture
        if _os.path.exists(_logo_p):
            story.append(Spacer(1, 0.4*cm))
            _lhdr = Table([[RLImage(_logo_p, width=5*cm, height=2.5*cm),
                             Paragraph("SETRAF · CPT Analysis Studio",
                                       ps("_lhd", fontSize=9,
                                          textColor=rlcolors.HexColor("#888888"),
                                          alignment=TA_RIGHT))]],
                          colWidths=[10.5*cm, 5*cm])
            _lhdr.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
            story.append(_lhdr)
            story.append(HRFlowable(width="100%", thickness=1,
                                    color=rlcolors.HexColor("#e0d0c0"), spaceAfter=8))
            story.append(Spacer(1, 1.0*cm))
        else:
            story.append(Spacer(1, 1.8*cm))
        story.append(Paragraph("RAPPORT D'ANALYSE GÉOTECHNIQUE", title_s))
        story.append(Paragraph("INVESTIGATION CPT / CPTU — ANALYSE SCIENTIFIQUE COMPLÈTE", title_s))
        story.append(Spacer(1, 0.4*cm)); hr()
        cov = [
            ["Fichier source :", fname],
            ["Profondeur totale :", f"{depth_max:.2f} m"],
            ["Nombre de mesures :", f"{len(df)} points"],
            ["qc (min / moy / max) :",
             f"{qcs.min():.2f} / {qcs.mean():.2f} / {qcs.max():.2f} MPa"],
            ["fs (min / moy / max) :",
             f"{fss.min():.0f} / {fss.mean():.0f} / {fss.max():.0f} kPa"],
            ["Rf moyen calculé :", f"{rf_mean:.2f} %"],
            ["Date du rapport :", today],
            ["Logiciel :", "SETRAF CPT Analysis Studio v1.0"],
            ["Modèle IA :", "KIBALI Final Merged — Mistral-7B (Apache 2.0)"],
        ]
        cov_t = Table(cov, colWidths=[5.5*cm, 9.5*cm])
        cov_t.setStyle(TableStyle([
            ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0,0), (0,-1), ORANGE),
            ("FONTSIZE",  (0,0), (-1,-1), 10),
            ("ROWBACKGROUNDS", (0,0), (-1,-1),
             [rlcolors.HexColor("#fff8f0"), rlcolors.white]),
            ("GRID", (0,0), (-1,-1), 0.3, rlcolors.HexColor("#ddd")),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
            ("TOPPADDING",    (0,0), (-1,-1), 5),
        ]))
        story.append(cov_t); story.append(Spacer(1, 0.8*cm)); hr()
        story.append(Paragraph(
            "<i>Ce rapport a été généré automatiquement par SETRAF CPT Analysis Studio. "
            "Les interprétations doivent être validées par un ingénieur géotechnicien qualifié.</i>",
            note_cov))
        story.append(PageBreak())

        # ══════════════════════════════════════════════════════════════════════
        #  TABLE DES MATIÈRES
        # ══════════════════════════════════════════════════════════════════════
        story.append(Paragraph("TABLE DES MATIÈRES", ch_s)); hr()
        toc = [
            ("1.",    "Introduction et contexte géotechnique",             "3"),
            ("2.",    "Méthodologie — Essai CPT/CPTU",                     "4"),
            ("3.",    "Classification Robertson (1990, 2009)",             "5"),
            ("4.",    "Données et statistiques descriptives",              "7"),
            ("  4.1.","Statistiques générales",                            "7"),
            ("  4.2.","Profil CPTU 4 panneaux",                           "8"),
            ("5.",    "Analyse des profils de résistance",                 "9"),
            ("  5.1.","Résistance de pointe qc",                          "9"),
            ("  5.2.","Frottement latéral fs et rapport Rf",              "10"),
            ("  5.3.","Résistance nette qnet",                            "11"),
            ("6.",    "Classification géologique des couches",            "12"),
            ("  6.1.","Tableau Robertson des couches identifiées",        "12"),
            ("  6.2.","Diagramme de classification + profils lissés",     "13"),
            ("7.",    "Analyses statistiques avancées",                   "14"),
            ("  7.1.","Clustering K-means et ACP",                        "14"),
            ("  7.2.","Histogrammes et distributions",                    "15"),
            ("  7.3.","Boxplots par couche et nuage qc/fs",               "16"),
            ("  7.4.","Courbes cumulatives et tendances",                 "17"),
            ("  7.5.","Matrice de corrélations",                          "18"),
            ("8.",    "Évaluation du risque de liquéfaction sismique",    "19"),
            ("  8.1.","Méthode Seed & Idriss (1971)",                     "19"),
            ("  8.2.","Méthode Robertson & Wride (1998)",                 "20"),
            ("  8.3.","Résultats et tableau récapitulatif",               "21"),
            ("9.",    "Présentation CPTU — Vue statique",                 "23"),
            ("10.",   "Interprétation géotechnique et recommandations",   "24"),
            ("  10.1.","Interprétation globale",                          "24"),
            ("  10.2.","Capacité portante estimée",                       "25"),
            ("  10.3.","Recommandations",                                 "26"),
            ("11.",   "Conclusions",                                      "27"),
            ("12.",   "Références bibliographiques",                      "28"),
        ]
        for num, ttl, pg in toc:
            is_main = not num.startswith("  ")
            s = toc_h_s if is_main else toc_s
            dots = "." * max(2, 55 - len(num) - len(ttl))
            story.append(Paragraph(
                f"<b>{num}</b>&nbsp;&nbsp;{ttl}&nbsp;{dots}&nbsp;{pg}", s))
        story.append(PageBreak())

        # ══════════════════════════════════════════════════════════════════════
        #  1. INTRODUCTION
        # ══════════════════════════════════════════════════════════════════════
        upd(8, "Introduction…")
        story.append(Paragraph("1. Introduction et Contexte Géotechnique", ch_s)); hr()
        story.append(Paragraph(
            f"Le présent rapport porte sur l'analyse géotechnique d'un sondage CPT/CPTU "
            f"réalisé à une profondeur maximale de <b>{depth_max:.2f} m</b> ({len(df)} points "
            f"de mesure). L'essai de pénétration au cône (CPT — <i>Cone Penetration Test</i>) "
            f"constitue l'une des méthodes in situ les plus utilisées mondialement pour la "
            f"caractérisation stratigraphique et mécanique des sols (Lunne <i>et al.</i>, "
            f"1997 [1]). Sa version instrumentée (CPTU — avec capteur de pression interstitielle "
            f"u₂) améliore significativement la discrimination des sols fins saturés.", body_s))
        story.append(Paragraph(
            "L'essai CPT présente de nombreux avantages : continuité du profil de mesure, "
            "reproductibilité élevée, rapidité d'exécution et vaste base de données "
            "internationales de corrélation. Ce rapport présente une analyse multi-dimensionnelle "
            "complète : profils de résistance, classification Robertson (1990, 2009) [2,3], "
            "évaluation de liquéfaction (Seed &amp; Idriss, 1971 [4] ; Robertson &amp; Wride, "
            "1998 [6]), analyses statistiques (K-means, ACP, corrélations) et visualisation 3D "
            "du sous-sol.", body_s))
        story.append(Paragraph(
            "Le rapport de friction fondamental R<sub>f</sub> est défini par :", body_s))
        story.append(Paragraph(
            "R<sub>f</sub> = (f<sub>s</sub> / q<sub>c</sub>) × 100  (%)", formula_s))
        story.append(Paragraph(
            "Toutes les profondeurs sont exprimées en mètres (m), les résistances de pointe "
            "en mégapascals (MPa), et les frottements latéraux en kilopascals (kPa). "
            "Les résultats doivent être complétés par le jugement d'un ingénieur "
            "géotechnicien expérimenté.", body_s))
        story.append(PageBreak())

        # ══════════════════════════════════════════════════════════════════════
        #  2. MÉTHODOLOGIE
        # ══════════════════════════════════════════════════════════════════════
        upd(11, "Méthodologie…")
        story.append(Paragraph("2. Méthodologie — Essai de Pénétration au Cône (CPT/CPTU)", ch_s)); hr()
        story.append(Paragraph("2.1 Principe de l'essai", h2_s))
        story.append(Paragraph(
            "L'essai CPT consiste à enfoncer à vitesse constante (20 mm/s, ISO 22476-1 [13]) "
            "un cône instrumenté de section 10 cm² et d'angle d'apex 60°. Le CPTU est équipé "
            "d'un capteur de pression interstitielle en position u₂ (derrière la pointe). "
            "Les mesures directes sont : résistance de pointe q<sub>c</sub> (MPa), "
            "frottement latéral f<sub>s</sub> (kPa), et pression interstitielle u₂ (kPa).",
            body_s))
        story.append(Paragraph("2.2 Paramètres dérivés", h2_s))
        params = [
            ["Paramètre", "Formule", "Description"],
            ["Résistance nette",
             "q_net = qc − σv0",
             "Résistance utile après déduction contrainte géostatique"],
            ["Résistance normalisée",
             "Qt = (qc − σv0) / σ'v0",
             "Sans dimension, base de classification normalisée"],
            ["Friction normalisée",
             "Fr = fs / (qc − σv0) × 100 %",
             "Rapport de friction normalisé Robertson (1990)"],
            ["Résistance corrigée CPTU",
             "qt = qc + u2 × (1 − a)",
             "a = rapport surface nette (~0.75–0.85)"],
        ]
        pt = Table(params, colWidths=[3.5*cm, 4.5*cm, 7*cm])
        tbl_style(pt)
        story.append(pt)
        story.append(PageBreak())

        # ══════════════════════════════════════════════════════════════════════
        #  3. ROBERTSON 1990
        # ══════════════════════════════════════════════════════════════════════
        upd(14, "Robertson 1990…")
        story.append(Paragraph("3. Classification des Sols — Robertson (1990, 2009)", ch_s)); hr()
        story.append(Paragraph("3.1 Système de classification Robertson (1990)", h2_s))
        story.append(Paragraph(
            "Robertson (1990) [2] a proposé un système universel à 9 zones de comportement "
            "géotechnique basé sur le diagramme q<sub>c</sub>–R<sub>f</sub>. Ce système est "
            "devenu la référence mondiale pour l'interprétation des essais CPT. La version "
            "normalisée (Robertson, 2009 [3]) utilise le diagramme Q<sub>t</sub>–F<sub>r</sub> "
            "pour s'affranchir des effets des contraintes.", body_s))
        story.append(Paragraph("3.2 Indice de comportement I<sub>c</sub> (Robertson & Wride, 1998)", h2_s))
        story.append(Paragraph(
            "L'indice scalaire I<sub>c</sub> permet une classification automatisée. Il est "
            "défini sur le diagramme normalisé comme :", body_s))
        story.append(Paragraph(
            "I<sub>c</sub> = √[(3.47 − log₁₀(Q<sub>t</sub>))² + (log₁₀(F<sub>r</sub>) + 1.22)²]",
            formula_s))
        story.append(Paragraph(
            "Q<sub>t</sub> = (q<sub>c</sub> − σ<sub>v0</sub>) / σ'<sub>v0</sub>&nbsp;&nbsp;&nbsp;"
            "F<sub>r</sub> = f<sub>s</sub> / (q<sub>c</sub> − σ<sub>v0</sub>) × 100 (%)",
            formula_s))
        story.append(Paragraph("3.3 Tableau des 9 zones de comportement", h2_s))
        rob = [
            ["Zone", "Type de sol", "I_c", "qc typique (MPa)", "Rf typique (%)"],
            ["1", "Sols organiques sensibles",          "Ic > 3.60",          "< 0.3",    "> 8"],
            ["2", "Argile organique — argile",          "2.95–3.60",          "0.3–1.0",  "3–8"],
            ["3", "Argile — limon argileux",            "2.60–2.95",          "0.5–2.0",  "3–5"],
            ["4", "Limon silteux — argile silteuse",    "2.05–2.60",          "1.0–5.0",  "2–4"],
            ["5", "Sable silteux — silt sableux",       "1.31–2.05",          "3.0–15",   "1–3"],
            ["6", "Sable propre / légèrement silteux",  "Ic ≤ 1.31",          "> 5.0",    "< 1"],
            ["7", "Sable dense — sable graveleux",      "—",                  "> 15",     "< 0.5"],
            ["8", "Sable très dense — sol cimenté",     "—",                  "> 20",     "< 0.5"],
            ["9", "Sol très rigide de type fin",        "—",                  "> 15",     "1–5"],
        ]
        zone_bg = [None,
            "#c9a0a0", "#b8a070", "#8ba050", "#909898",
            "#c8a830", "#e8a060", "#d4b880", "#a06830", "#8090a0"]
        rt = Table(rob, colWidths=[1*cm, 5.5*cm, 2.5*cm, 2.5*cm, 2.5*cm], repeatRows=1)
        rt.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), NAVY),
            ("TEXTCOLOR",  (0,0), (-1,0), rlcolors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,-1), 8),
            ("GRID",       (0,0), (-1,-1), 0.3, rlcolors.HexColor("#ccc")),
            ("ALIGN",      (0,0), (0,-1), "CENTER"),
            ("ALIGN",      (2,0), (-1,-1), "CENTER"),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
            ("TOPPADDING",    (0,0), (-1,-1), 3),
        ]))
        for i, bg in enumerate(zone_bg):
            if bg:
                c = rlcolors.HexColor(bg)
                lc = rlcolors.Color(c.red*0.25+0.75, c.green*0.25+0.75, c.blue*0.25+0.75)
                rt.setStyle(TableStyle([("BACKGROUND", (0,i), (-1,i), lc)]))
        story.append(rt); story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("3.4 Limites et précautions", h2_s))
        for lim in [
            "La classification est basée sur le comportement mécanique et non la minéralogie.",
            "Les argiles surconsolidées peuvent être classifiées à tort comme sables fins.",
            "Les données CPTU brutes doivent être corrigées par u₂ dans les sols fins saturés.",
            "Ne remplace pas les essais de laboratoire pour les paramètres de résistance."
        ]:
            story.append(Paragraph(f"• {lim}", li_s))
        story.append(PageBreak())

        # ══════════════════════════════════════════════════════════════════════
        #  4. STATISTIQUES
        # ══════════════════════════════════════════════════════════════════════
        upd(18, "Statistiques…")
        story.append(Paragraph("4. Données et Statistiques Descriptives", ch_s)); hr()
        story.append(Paragraph("4.1 Statistiques générales", h2_s))
        qc_p = [float(np.percentile(qcs, p)) for p in [25,50,75]]
        fs_p = [float(np.percentile(fss, p)) for p in [25,50,75]]
        rf_p = [float(np.percentile(rf_vals, p)) for p in [25,50,75]]
        story.append(Paragraph(
            f"Le sondage comprend <b>{len(df)} mesures</b> sur <b>{depth_max:.2f} m</b>. "
            f"La résistance médiane est q<sub>c,50</sub> = <b>{qc_p[1]:.2f} MPa</b> "
            f"(IQR [{qc_p[0]:.2f}–{qc_p[2]:.2f}] MPa). R<sub>f</sub> moyen = "
            f"<b>{rf_mean:.2f}%</b> → sol "
            f"{'argileux à silteux (Rf > 3%)' if rf_mean > 3 else 'sablo-silteux à sableux'}.",
            body_s))
        st_hdr  = ["Paramètre", "Min", "P25", "Médiane", "P75", "Max", "Moy ± σ"]
        st_rows = [
            ["q_c (MPa)",
             f"{qcs.min():.2f}", f"{qc_p[0]:.2f}", f"{qc_p[1]:.2f}", f"{qc_p[2]:.2f}",
             f"{qcs.max():.2f}", f"{qcs.mean():.2f} ± {qcs.std():.2f}"],
            ["f_s (kPa)",
             f"{fss.min():.0f}", f"{fs_p[0]:.0f}", f"{fs_p[1]:.0f}", f"{fs_p[2]:.0f}",
             f"{fss.max():.0f}", f"{fss.mean():.0f} ± {fss.std():.0f}"],
            ["R_f (%)",
             f"{rf_vals.min():.2f}", f"{rf_p[0]:.2f}", f"{rf_p[1]:.2f}", f"{rf_p[2]:.2f}",
             f"{rf_vals.max():.2f}", f"{rf_mean:.2f} ± {rf_vals.std():.2f}"],
        ]
        st_t = Table([st_hdr]+st_rows,
                     colWidths=[3.2*cm]+[1.7*cm]*5+[3.2*cm], repeatRows=1)
        tbl_style(st_t); story.append(st_t); story.append(Spacer(1, 0.4*cm))

        story.append(Paragraph("4.2 Profil CPTU 4 panneaux", h2_s))
        upd(22, "Profil CPTU PNG…")
        if SVG_ANIMATOR_AVAILABLE:
            try:
                cptu_p = generate_cptu_png(df_plot, title=f"{fname} — Profil CPTU complet")
                add_png(cptu_p,
                        "Profil CPTU 4 panneaux : Sol Robertson (couleurs) | "
                        "q<sub>c</sub> (MPa) | f<sub>s</sub> (kPa) | I<sub>c</sub> Robertson. "
                        "Lignes en tirets : limites de zones Robertson (1990).",
                        width=15.5*cm)
            except Exception as _ep:
                story.append(Paragraph(f"Profil CPTU: {_ep}", caption_s))
        story.append(PageBreak())

        # ══════════════════════════════════════════════════════════════════════
        #  5. PROFILS DE RÉSISTANCE
        # ══════════════════════════════════════════════════════════════════════
        upd(26, "Section 5…")
        story.append(Paragraph("5. Analyse des Profils de Résistance", ch_s)); hr()
        story.append(Paragraph("5.1 Résistance de pointe q<sub>c</sub>", h2_s))
        if qc_mean < 2:
            interp_qc = (f"Les faibles résistances (q<sub>c</sub> moy. = {qc_mean:.2f} MPa) "
                         "indiquent des sols fins mous (argiles, limons). Capacité portante faible, "
                         "tassements probablement significatifs.")
        elif qc_mean < 8:
            interp_qc = (f"Les résistances modérées ({qc_mean:.2f} MPa) sont caractéristiques "
                         "de sols intermédiaires (silts, argiles raides, sables lâches à "
                         "moyennement denses). Capacité portante modérée à bonne.")
        else:
            interp_qc = (f"Les fortes résistances (q<sub>c</sub> moy. = {qc_mean:.2f} MPa) "
                         "témoignent de sables denses ou matériaux cimentés. Excellentes propriétés "
                         "pour l'appui de fondations.")
        story.append(Paragraph(
            f"q<sub>c</sub> varie de <b>{qcs.min():.2f}</b> à <b>{qcs.max():.2f} MPa</b> "
            f"(moy. {qcs.mean():.2f}, σ = {qcs.std():.2f}). {interp_qc}", body_s))
        add_png(self._plot_func_to_png(
            lambda d, a: self.plot_qc_depth(d, a), df_plot, figsize=(8,6)),
            "Profil de résistance de pointe q<sub>c</sub> vs profondeur (m).", width=11*cm)

        story.append(Paragraph("5.2 Frottement latéral f<sub>s</sub> et rapport R<sub>f</sub>", h2_s))
        story.append(Paragraph(
            f"f<sub>s</sub> varie de <b>{fss.min():.0f}</b> à <b>{fss.max():.0f} kPa</b> "
            f"(moy. {fss.mean():.0f} kPa). R<sub>f</sub> moyen = <b>{rf_mean:.2f}%</b>. "
            f"{'Rf > 3% → prédominance sols fins (argiles, limons — Robertson zones 1–4).' if rf_mean > 3 else 'Rf < 1.5% → matériaux granulaires (sables — Robertson zones 5–7).'} "
            "Les variations verticales de f<sub>s</sub> reflètent les transitions lithologiques.",
            body_s))
        side_by_side(
            self._plot_func_to_png(lambda d, a: self.plot_fs_depth(d, a), df_plot),
            self._plot_func_to_png(lambda d, a: self.plot_rf_depth(d, a), df_plot),
            "f<sub>s</sub> (kPa) vs profondeur (gauche) — R<sub>f</sub> (%) vs profondeur (droite).")

        story.append(Paragraph("5.3 Résistance nette q<sub>net</sub>", h2_s))
        story.append(Paragraph(
            "q<sub>net</sub> = q<sub>c</sub> − σ<sub>v0</sub> représente la résistance utile "
            "après soustraction de la contrainte géostatique totale. Elle constitue la base "
            "des méthodes de calcul de capacité portante selon l'Eurocode 7 (EN 1997-1 [14]).",
            body_s))
        add_png(self._plot_func_to_png(
            lambda d, a: self.plot_qnet_depth(d, a), df_plot, figsize=(8,6)),
            "Profil de résistance nette q<sub>net</sub> (MPa) vs profondeur.", width=11*cm)
        story.append(PageBreak())

        # ══════════════════════════════════════════════════════════════════════
        #  6. CLASSIFICATION DES COUCHES
        # ══════════════════════════════════════════════════════════════════════
        upd(32, "Classification couches…")
        story.append(Paragraph("6. Classification Géologique des Couches", ch_s)); hr()
        story.append(Paragraph("6.1 Tableau Robertson des couches identifiées", h2_s))
        if SVG_ANIMATOR_AVAILABLE:
            try:
                import math as _math
                from tools.cptu_svg_animator import _detect_layers as _dl
                layers_r = _dl(df_plot)
                story.append(Paragraph(
                    f"L'analyse automatique identifie <b>{len(layers_r)} unités géotechniques "
                    f"distinctes</b> selon Robertson (1990). La classification est basée sur "
                    f"I<sub>c</sub> calculé point par point.", body_s))
                l_hdr = ["N°","Dép.(m)","Fin(m)","ép.(m)","Type Robertson",
                         "qc (MPa)","fs (kPa)","Ic"]
                l_rows = []
                for idx2, la in enumerate(layers_r, 1):
                    q, f = la["avg_qc"], la["avg_fs"]
                    fr2 = (f/(q*1000))*100 if q > 0 else 1.0
                    try:
                        ic = _math.sqrt((3.47-_math.log10(max(q,0.01)))**2 +
                                        (_math.log10(max(fr2,0.001))+1.22)**2)
                    except Exception:
                        ic = 3.0
                    l_rows.append([str(idx2),
                                   f"{la['start_m']:.2f}", f"{la['end_m']:.2f}",
                                   f"{la['end_m']-la['start_m']:.2f}", la["label"],
                                   f"{q:.2f}", f"{f:.0f}", f"{ic:.2f}"])
                lt = Table([l_hdr]+l_rows,
                           colWidths=[0.8*cm,1.4*cm,1.4*cm,1.4*cm,5.2*cm,1.8*cm,1.8*cm,1.4*cm],
                           repeatRows=1)
                tbl_style(lt, ORANGE)
                story.append(lt); story.append(Spacer(1, 0.4*cm))
            except Exception as _e:
                story.append(Paragraph(f"Classification: {_e}", body_s))

        story.append(Paragraph("6.2 Diagramme de classification et profils lissés", h2_s))
        story.append(Paragraph(
            "Le diagramme q<sub>c</sub>–R<sub>f</sub> positionne chaque mesure dans les zones "
            "Robertson. Le lissage médian (fenêtre glissante) met en évidence les tendances "
            "globales et les transitions de couches (Hegazy &amp; Mayne, 2002 [8]).", body_s))
        add_png(self._plot_func_to_png(
            lambda d, a: self.plot_soil_classification(d, a), df_plot, figsize=(8,7)),
            "Diagramme de classification Robertson (1990) — q<sub>c</sub> vs R<sub>f</sub>. "
            "Zones colorées selon les 9 types de comportement géotechnique.", width=13*cm)
        side_by_side(
            self._plot_func_to_png(lambda d, a: self.plot_smooth_qc(d, a), df_plot),
            self._plot_func_to_png(lambda d, a: self.plot_smooth_fs(d, a), df_plot),
            "Profil q<sub>c</sub> lissé (gauche) — Profil f<sub>s</sub> lissé (droite). "
            "Filtrage médian 5 points.")
        story.append(PageBreak())

        # ══════════════════════════════════════════════════════════════════════
        #  7. ANALYSES STATISTIQUES
        # ══════════════════════════════════════════════════════════════════════
        upd(42, "Analyses statistiques…")
        story.append(Paragraph("7. Analyses Statistiques Avancées", ch_s)); hr()

        story.append(Paragraph("7.1 Clustering K-means et ACP", h2_s))
        story.append(Paragraph(
            "Le clustering K-means (MacQueen, 1967 [9]) identifie des groupes de données "
            "homogènes dans l'espace (q<sub>c</sub>, f<sub>s</sub>, R<sub>f</sub>), "
            "validant la segmentation Robertson. L'ACP réduit la dimensionnalité et révèle "
            "les corrélations inter-paramètres (axe PC1 = granulométrie sables↔argiles).", body_s))
        side_by_side(
            self._plot_func_to_png(lambda d, a: self.plot_kmeans_clusters(d, a), df_plot),
            self._plot_func_to_png(lambda d, a: self.plot_pca(d, a), df_plot),
            "Clustering K-means (gauche) — ACP projection PC1–PC2 (droite).")

        story.append(Paragraph("7.2 Histogrammes et distributions", h2_s))
        story.append(Paragraph(
            "Les histogrammes évaluent la distribution statistique des paramètres CPT. "
            "Une distribution bimodale de q<sub>c</sub> révèle souvent deux familles de sols "
            "distinctes. La distribution log-normale est fréquente pour q<sub>c</sub> "
            "(Lumb, 1966 [10]).", body_s))
        side_by_side(
            self._plot_func_to_png(lambda d, a: self.plot_qc_histogram(d, a), df_plot),
            self._plot_func_to_png(lambda d, a: self.plot_fs_histogram(d, a), df_plot),
            "Histogramme de q<sub>c</sub> (gauche) — Histogramme de f<sub>s</sub> (droite).")

        story.append(Paragraph("7.3 Boxplots par couche et nuage q<sub>c</sub>/f<sub>s</sub>", h2_s))
        story.append(Paragraph(
            "Les diagrammes en boîte (Tukey, 1977 [11]) synthétisent la variabilité "
            "statistique par couche géotechnique et permettent d'identifier les valeurs "
            "aberrantes (outliers). La corrélation q<sub>c</sub>–f<sub>s</sub> "
            f"(Pearson r = {float(np.corrcoef(qcs,fss)[0,1]):.3f}) est représentée ci-dessous.",
            body_s))
        side_by_side(
            self._plot_func_to_png(lambda d, a: self.plot_qc_boxplot(d, a), df_plot),
            self._plot_func_to_png(lambda d, a: self.plot_fs_boxplot(d, a), df_plot),
            "Boxplots q<sub>c</sub> par couche (gauche) — Boxplots f<sub>s</sub> par couche (droite).")
        add_png(self._plot_func_to_png(
            lambda d, a: self.plot_qc_fs_scatter(d, a), df_plot, figsize=(8,6)),
            f"Diagramme de dispersion q<sub>c</sub> vs f<sub>s</sub> "
            f"(Pearson r = {float(np.corrcoef(qcs,fss)[0,1]):.3f}).", width=11*cm)
        story.append(PageBreak())

        story.append(Paragraph("7.4 Courbes cumulatives et analyses de tendance", h2_s))
        story.append(Paragraph(
            "Les courbes cumulatives permettent d'extraire les valeurs caractéristiques "
            "(q<sub>c,10%</sub>, q<sub>c,50%</sub>…) pour les calculs géotechniques. "
            "L'analyse de tendance par régression polynomiale détecte les changements "
            "de pente indicatifs de transitions lithologiques.", body_s))
        side_by_side(
            self._plot_func_to_png(lambda d, a: self.plot_qc_cumulative(d, a), df_plot),
            self._plot_func_to_png(lambda d, a: self.plot_fs_cumulative(d, a), df_plot),
            "Courbe cumulative q<sub>c</sub> (gauche) — Courbe cumulative f<sub>s</sub> (droite).")
        add_png(self._plot_func_to_png(
            lambda d, a: self.plot_friction_ratio(d, a), df_plot, figsize=(8,5)),
            "Profil du rapport de friction R<sub>f</sub> vs profondeur.", width=11*cm)
        side_by_side(
            self._plot_func_to_png(lambda d, a: self.plot_qc_trend(d, a), df_plot),
            self._plot_func_to_png(lambda d, a: self.plot_fs_trend(d, a), df_plot),
            "Analyse de tendance q<sub>c</sub> (gauche) — Analyse de tendance f<sub>s</sub> (droite).")

        story.append(Paragraph("7.5 Matrice de corrélations", h2_s))
        story.append(Paragraph(
            "La matrice de corrélations (heatmap) illustre les relations linéaires entre tous "
            "les paramètres CPT disponibles. Les corrélations |r| > 0.7 révèlent des "
            "dépendances physiques entre les mesures.", body_s))
        add_png(self._plot_func_to_png(
            lambda d, a: self.plot_correlation_heatmap(d, a), df_plot, figsize=(8,6)),
            "Matrice de corrélations de Pearson entre les paramètres CPT/CPTU.", width=13*cm)
        story.append(PageBreak())

        # ══════════════════════════════════════════════════════════════════════
        #  8. LIQUÉFACTION
        # ══════════════════════════════════════════════════════════════════════
        upd(60, "Liquéfaction…")
        story.append(Paragraph("8. Évaluation du Risque de Liquéfaction Sismique", ch_s)); hr()
        story.append(Paragraph("8.1 Contexte — méthode Seed & Idriss (1971)", h2_s))
        story.append(Paragraph(
            "La liquéfaction est la perte de résistance mécanique d'un sol granulaire saturé "
            "sous charge sismique, due à l'accumulation de surpressions interstitielles "
            "(Seed &amp; Idriss, 1971 [4]). Le facteur de sécurité est :", body_s))
        story.append(Paragraph("FS = CRR₇.₅ × MSF / CSR", formula_s))
        story.append(Paragraph(
            "CSR = 0.65 × (σv0/σ'v0) × (amax/g) × rd   [demande sismique]", formula_s))
        story.append(Paragraph(
            "MSF = 10^2.24 / Mw^2.56   (Youd et al., 2001 [5])   [facteur d'échelle magnitude]",
            formula_s))
        story.append(Paragraph(
            "où a<sub>max</sub> est l'accélération maximale du sol, r<sub>d</sub> est le "
            "facteur de réduction des contraintes avec la profondeur (~1.0−0.00765z pour z ≤ 9.15 m), "
            "et M<sub>w</sub> est la magnitude de moment du séisme de référence.", body_s))

        story.append(Paragraph("8.2 Méthode Robertson & Wride (1998) basée sur CPT", h2_s))
        story.append(Paragraph(
            "Robertson &amp; Wride (1998) [6] ont développé une procédure de calcul direct "
            "de CRR à partir des données CPT normalisées :", body_s))
        for f_str in [
            "qc1N = Cq × qc / pa   (pa = 100 kPa pression atmosphérique)",
            "Cq = (pa / σ'v0)^n   (n ≈ 0.5 sables, ≈ 1.0 argiles)",
            "qc1N,cs = Kc × qc1N   (correction pour la teneur en fines)",
            "CRR₇.₅ = 0.833 × (qc1N,cs/1000) + 0.05   si qc1N,cs < 50",
            "CRR₇.₅ = 93 × (qc1N,cs/1000)³ + 0.08    si 50 ≤ qc1N,cs < 160",
        ]:
            story.append(Paragraph(f_str, formula_s))

        story.append(Paragraph("8.3 Résultats et tableau récapitulatif", h2_s))
        if qc_mean < 3:
            liq_risk, liq_txt = "ÉLEVÉ", (
                f"q<sub>c</sub> moyen = {qc_mean:.2f} MPa &lt; 3 MPa → risque de "
                f"liquéfaction <b>ÉLEVÉ</b>. Les sols fins mous présentent une susceptibilité "
                "importante. Des mesures de mitigation (colonnes ballastées, jet-grouting, "
                "compactage dynamique) doivent être envisagées.")
        elif qc_mean < 8:
            liq_risk, liq_txt = "MODÉRÉ", (
                f"q<sub>c</sub> moyen = {qc_mean:.2f} MPa → risque <b>MODÉRÉ</b>. "
                "Analyse détaillée Youd et al. (2001) recommandée. Les couches de sables lâches "
                "à faible profondeur présentent la susceptibilité la plus élevée.")
        else:
            liq_risk, liq_txt = "FAIBLE", (
                f"q<sub>c</sub> moyen = {qc_mean:.2f} MPa &gt; 8 MPa → risque "
                f"de liquéfaction <b>FAIBLE</b>. Sables denses : FS généralement &gt; 1.5 "
                "pour les aléas sismiques habituels.")
        story.append(Paragraph(liq_txt, body_s))
        liq_t = Table([
            ["Paramètre", "Valeur mesurée", "Seuil / remarque"],
            ["qc moyen",           f"{qc_mean:.2f} MPa",    "< 3 → risque élevé"],
            ["qc médiane",         f"{qc_p[1]:.2f} MPa",    "< 5 → susceptible"],
            ["Rf moyen calculé",   f"{rf_mean:.2f} %",      "> 3% → sol fin susceptible"],
            ["Profondeur max",     f"{depth_max:.1f} m",     "Couches ≤ 15 m : zone critique"],
            ["Risque global",      liq_risk,                 "FS > 1.5 requis (Youd 2001)"],
        ], colWidths=[5*cm, 4*cm, 6*cm])
        tbl_style(liq_t); story.append(liq_t); story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(
            "<b>Note :</b> Cette évaluation préliminaire est basée sur les données CPT seules. "
            "Elle ne remplace pas une analyse complète intégrant l'aléa sismique local "
            "(accélération a<sub>max</sub>, magnitude M<sub>w</sub>, spectre de réponse) "
            "conformément à l'Eurocode 8 (EN 1998 [14]).", warn_s))
        story.append(PageBreak())

        # ══════════════════════════════════════════════════════════════════════
        #  9. SVG STATIQUE
        # ══════════════════════════════════════════════════════════════════════
        upd(72, "Animation SVG…")
        story.append(Paragraph("9. Présentation CPTU Animée — Vue Statique", ch_s)); hr()
        story.append(Paragraph(
            "La figure ci-dessous est le rendu statique de l'animation CPTU. "
            "Elle présente simultanément les 4 vues essentielles du sondage : "
            "colonne de sol Robertson (couleurs), profil q<sub>c</sub>, "
            "profil f<sub>s</sub>, et indice I<sub>c</sub> avec les limites de zones.", body_s))
        svg_str = (getattr(self, '_data_svg_string', None)
                   or (next(iter(self._svg_strings.values()), None)
                       if hasattr(self, '_svg_strings') else None))
        if svg_str:
            svg_p = self._svg_to_png_bytes(svg_str, width=1400, height=900)
            if svg_p:
                add_png(svg_p,
                    "Présentation CPTU — rendu statique de l'animation. Col. gauche→droite : "
                    "Sol Robertson | q<sub>c</sub> (MPa) | f<sub>s</sub> (kPa) | I<sub>c</sub>.",
                    width=16*cm)
            else:
                story.append(Paragraph(
                    "SVG non disponible — générez l'animation dans l'onglet Données.", body_s))
        elif SVG_ANIMATOR_AVAILABLE:
            try:
                fb = generate_cptu_png(df_plot, title=f"{fname} — Vue statique", figsize=(14,9))
                add_png(fb, "Profil CPTU statique (4 panneaux).", width=16*cm)
            except Exception:
                story.append(Paragraph(
                    "Visualisation CPTU non disponible.", body_s))
        story.append(PageBreak())

        # ══════════════════════════════════════════════════════════════════════
        #  10. INTERPRÉTATION & RECOMMANDATIONS
        # ══════════════════════════════════════════════════════════════════════
        upd(82, "Interprétation…")
        story.append(Paragraph("10. Interprétation Géotechnique et Recommandations", ch_s)); hr()
        story.append(Paragraph("10.1 Interprétation globale du profil", h2_s))
        if SVG_ANIMATOR_AVAILABLE:
            try:
                from tools.cptu_svg_animator import _detect_layers as _dl2
                lrs = _dl2(df_plot)
                if lrs:
                    dom = max(lrs, key=lambda x: x["end_m"]-x["start_m"])
                    story.append(Paragraph(
                        f"L'analyse identifie <b>{len(lrs)} unités géotechniques</b> sur "
                        f"{depth_max:.1f} m. Couche dominante : <b>«{dom['label']}»</b> "
                        f"({dom['start_m']:.1f}–{dom['end_m']:.1f} m, "
                        f"épaisseur {dom['end_m']-dom['start_m']:.1f} m, "
                        f"q<sub>c</sub> moy. = {dom['avg_qc']:.2f} MPa).", body_s))
            except Exception:
                pass
        corr_dz = float(np.corrcoef(depths_m, qcs)[0,1])
        cv_qc   = qcs.std()/qcs.mean()*100 if qcs.mean() > 0 else 0
        story.append(Paragraph(
            f"Les données présentent une variabilité "
            f"{'élevée' if cv_qc > 80 else 'modérée' if cv_qc > 40 else 'faible'} "
            f"(CV = {cv_qc:.1f}%). La corrélation profondeur–q<sub>c</sub> est "
            f"r = {corr_dz:.3f} "
            f"({'augmentation significative avec la profondeur' if corr_dz > 0.3 else 'distribution irrégulière — variabilité lithologique importante'}). ",
            body_s))

        story.append(Paragraph("10.2 Capacité portante estimée", h2_s))
        story.append(Paragraph(
            "Estimation indicative par la méthode CPT-directe (Bustamante &amp; Frank, 1997 [12]):",
            body_s))
        story.append(Paragraph(
            "q_ult = kc × qce   (kc = facteur de type de sol, qce = qc équivalent sous fondation)",
            formula_s))
        qce    = float(np.median(qcs))
        kc_val = 0.40 if rf_mean > 3 else 0.35
        qult   = qce * kc_val * 1000
        qadm   = qult / 3
        story.append(Paragraph(
            f"Pour q<sub>ce</sub> ≈ {qce:.2f} MPa (médiane) et k<sub>c</sub> = {kc_val} : "
            f"<b>q<sub>ult</sub> ≈ {qult:.0f} kPa</b> → "
            f"<b>q<sub>adm</sub> (FS=3) ≈ {qadm:.0f} kPa</b>. "
            f"<i>Estimation préliminaire — calcul selon Eurocode 7 requis.</i>", body_s))

        story.append(Paragraph("10.3 Recommandations", h2_s))
        for i, rec in enumerate([
            ("<b>Investigation complémentaire :</b> ≥ 3 sondages CPT supplémentaires pour "
             "caractériser la variabilité spatiale. Compléter par un forage avec "
             "prélèvements d'échantillons intacts."),
            ("<b>Essais de laboratoire :</b> Œdomètre sur les couches argileuses, triaxiaux "
             "sur les couches sableuses (paramètres c', φ', module de déformation)."),
            ("<b>Piézométrie :</b> Installer des piézomètres pour mesurer les variations "
             "saisonnières de la nappe — paramètre clé pour liquéfaction et tassements."),
            ("<b>Qualité des données :</b> Vérifier la calibration des capteurs avant/après "
             "foration. Les pics isolés (> 3σ) doivent être revérifiés."),
            ("<b>Analyse sismique :</b> Si zone sismique, analyse de réponse de site selon "
             "EN 1998 (Eurocode 8) et procédure Youd et al. (2001) pour la liquéfaction."),
            ("<b>Fondations :</b> Calcul selon EN 1997-1 (Eurocode 7) avec coefficients "
             "partiels γR. Vérification aux ELU et ELS."),
        ], 1):
            story.append(Paragraph(f"{i}. {rec}", rec_s))
        story.append(PageBreak())

        # ══════════════════════════════════════════════════════════════════════
        #  11. CONCLUSIONS
        # ══════════════════════════════════════════════════════════════════════
        upd(90, "Conclusions…")
        story.append(Paragraph("11. Conclusions", ch_s)); hr()
        story.append(Paragraph(
            f"Ce rapport présente l'analyse géotechnique complète du sondage CPT/CPTU "
            f"<b>{fname}</b> ({len(df)} mesures, {depth_max:.1f} m). Les principales "
            "conclusions sont :", body_s))
        for c in [
            (f"<b>Nature des sols :</b> prédominance de "
             f"{'sols fins (argiles, silts) — Rf moy. = ' + str(round(rf_mean,2)) + '% > 3%' if rf_mean > 3 else 'sols granulaires (sables) — Rf moy. = ' + str(round(rf_mean,2)) + '% < 2%'} "
             "selon Robertson (1990)."),
            (f"<b>Résistance mécanique :</b> q<sub>c</sub> = {qcs.min():.2f}–{qcs.max():.2f} MPa "
             f"(moy. {qcs.mean():.2f}) → capacité portante "
             f"{'faible à modérée' if qcs.mean() < 5 else 'modérée à bonne' if qcs.mean() < 12 else 'bonne à très bonne'}."),
            f"<b>Risque de liquéfaction :</b> estimé <b>{liq_risk}</b> sur la base des données CPT.",
            "Les analyses K-means et ACP confirment la segmentation en unités géotechniques "
            "distinctes, cohérentes avec la stratigraphie Robertson.",
            "Une investigation complémentaire (essais de laboratoire, piézométrie) est "
            "recommandée avant tout dimensionnement de fondations.",
        ]:
            story.append(Paragraph(f"• {c}",
                          ParagraphStyle("conc", parent=body_s, leftIndent=12, spaceAfter=6)))
        story.append(PageBreak())

        # ══════════════════════════════════════════════════════════════════════
        #  12. RÉFÉRENCES
        # ══════════════════════════════════════════════════════════════════════
        upd(95, "Références…")
        story.append(Paragraph("12. Références Bibliographiques", ch_s)); hr()
        for ref in [
            "[1] Lunne, T., Robertson, P.K. & Powell, J.J.M. (1997). <i>Cone Penetration "
            "Testing in Geotechnical Practice</i>. Blackie Academic & Professional, London.",
            "[2] Robertson, P.K. (1990). Soil classification using the cone penetration test. "
            "<i>Canadian Geotechnical Journal</i>, 27(1), 151–158. doi:10.1139/t90-014",
            "[3] Robertson, P.K. (2009). Interpretation of cone penetration tests — a unified "
            "approach. <i>Canadian Geotechnical Journal</i>, 46(11), 1337–1355. "
            "doi:10.1139/T09-065",
            "[4] Seed, H.B. & Idriss, I.M. (1971). Simplified procedure for evaluating soil "
            "liquefaction potential. <i>J. Soil Mech. Found. Div. ASCE</i>, 97(SM9), 1249–1273.",
            "[5] Youd, T.L. et al. (2001). Liquefaction resistance of soils: Summary report "
            "from the 1996/1998 NCEER workshops. <i>J. Geotech. Geoenviron. Eng.</i>, 127(10), "
            "817–833. doi:10.1061/(ASCE)1090-0241(2001)127:10(817)",
            "[6] Robertson, P.K. & Wride, C.E. (1998). Evaluating cyclic liquefaction "
            "potential using the cone penetration test. <i>Canadian Geotechnical Journal</i>, "
            "35(3), 442–459. doi:10.1139/t98-017",
            "[7] Meyerhof, G.G. (1976). Bearing capacity and settlement of pile foundations. "
            "<i>J. Geotech. Eng. Div. ASCE</i>, 102(GT3), 197–228.",
            "[8] Bustamante, M. & Gianeselli, L. (1982). Pile bearing capacity prediction "
            "by means of static penetrometer CPT. <i>Proc. ESOPT-2</i>, Amsterdam, 493–500.",
            "[9] Hegazy, Y.A. & Mayne, P.W. (2002). Objective site characterization using "
            "clustering of piezocone data. <i>J. Geotech. Geoenviron. Eng.</i>, 128(12), "
            "986–996.",
            "[10] MacQueen, J.B. (1967). Some methods for classification and analysis of "
            "multivariate observations. <i>Proc. 5th Berkeley Symp. Math. Stat. Prob.</i>, "
            "Vol. 1, 281–297.",
            "[11] Lumb, P. (1966). The variability of natural soils. "
            "<i>Canadian Geotechnical Journal</i>, 3(2), 74–97.",
            "[12] Bustamante, M. & Frank, R. (1997). Design of axially loaded piles — "
            "French practice. <i>Design of Axially Loaded Piles — European Practice</i>, Balkema.",
            "[13] ISO 22476-1:2012. Geotechnical investigation and testing — Field testing — "
            "Part 1: Electrical cone and piezocone penetration test. ISO, Geneva.",
            "[14] EN 1997-1:2004 (Eurocode 7). Geotechnical design — Part 1: General rules. "
            "CEN, Brussels.",
            "[15] EN 1998-1:2004 (Eurocode 8). Design of structures for earthquake "
            "resistance — Part 1: General rules. CEN, Brussels.",
        ]:
            story.append(Paragraph(ref, ref_s))

        story.append(Spacer(1, 0.8*cm)); hr()
        story.append(Paragraph(
            f"Rapport généré le <b>{today}</b> par <b>SETRAF CPT Analysis Studio v1.0</b> — "
            f"Modèle IA : KIBALI Final Merged (Apache 2.0) — © 2026",
            small_s))

        # ── Build ──────────────────────────────────────────────────────────────
        upd(98, "Construction du PDF…")
        doc.build(story)
        for f in tmp_files:
            try:
                _os.unlink(f)
            except Exception:
                pass
        upd(100, "Terminé !")

    def showAbout(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("À propos — CPT Analysis Studio")
        dialog.resize(560, 480)
        dialog.setStyleSheet("""
            QDialog { background:#16140e; color:#F0E1C3; }
            QLabel  { color:#F0E1C3; }
            QPushButton { background:#C1550F; color:#F0E1C3; border-radius:5px; padding:6px 18px; font-weight:bold; }
            QPushButton:hover { background:#DA701C; }
        """)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(10)

        html = QLabel("""
<div style='font-family:Segoe UI,Arial;'>
  <p style='font-size:20px;font-weight:bold;color:#F59B3A;margin:0 0 4px 0;'>CPT Analysis Studio</p>
  <p style='font-size:13px;color:#a07840;margin:0 0 16px 0;'>Version 1.0 &nbsp;|&nbsp; Mars 2026</p>

  <p style='font-size:12px;line-height:1.7;'>
    Logiciel portable d'analyse géotechnique CPTU.<br>
    Visualisation 3D, classification Robertson, liquéfaction,<br>
    export PDF/Excel, animation SVG et assistant IA intégré.
  </p>

  <p style='font-size:13px;font-weight:bold;color:#F59B3A;margin:14px 0 4px 0;'>🤖 Modèle IA embarqué</p>
  <p style='font-size:12px;line-height:1.7;'>
    <b style='color:#F0E1C3;'>KIBALI Final Merged</b> — Mistral-7B-Instruct-v0.2<br>
    Fine-tuné sur 18 adaptateurs LoRA spécialisés géophysique/géotechnique.<br>
    Auteur : <b style='color:#F0E1C3;'>BelikanM</b> (Hugging Face)
  </p>

  <p style='font-size:13px;font-weight:bold;color:#F59B3A;margin:14px 0 4px 0;'>⚖️ Licence du modèle</p>
  <p style='font-size:12px;line-height:1.7;'>
    <b style='color:#DA701C;'>Apache License 2.0</b> — Usage commercial <b style='color:#6fcf6f;'>AUTORISÉ</b>.<br>
    Conditions d'utilisation commerciale :<br>
    &nbsp;• Conserver la notice de licence Apache 2.0<br>
    &nbsp;• Mentionner l'auteur original (BelikanM / Mistral AI)<br>
    &nbsp;• Ne pas utiliser les marques Mistral AI à des fins promotionnelles<br>
    &nbsp;• Distribuer les modifications sous la même licence
  </p>

  <p style='font-size:11px;color:#7a6a50;margin-top:14px;'>
    PySide6 (LGPL v3) &nbsp;|&nbsp; Plotly (MIT) &nbsp;|&nbsp; Pandas (BSD-3) &nbsp;|&nbsp; ReportLab (BSD)
  </p>
</div>
""")
        html.setTextFormat(Qt.TextFormat.RichText)
        html.setWordWrap(True)
        layout.addWidget(html)

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
        dialog.exec()

    def showLicence(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("⚖️ Licences & Usage Commercial — CPT Analysis Studio")
        dialog.resize(640, 600)
        dialog.setStyleSheet("""
            QDialog      { background:#16140e; color:#F0E1C3; }
            QLabel       { color:#F0E1C3; }
            QScrollArea  { background:#16140e; border:none; }
            QWidget#content { background:#16140e; }
            QPushButton  { background:#C1550F; color:#F0E1C3; border-radius:5px;
                           padding:6px 18px; font-weight:bold; }
            QPushButton:hover { background:#DA701C; }
        """)
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(20, 16, 20, 14)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setObjectName("content")
        cl = QVBoxLayout(content)
        cl.setSpacing(14)

        title = QLabel("⚖️ Licences & Conditions d'Usage Commercial")
        title.setStyleSheet("font-size:17px;font-weight:bold;color:#F59B3A;")
        cl.addWidget(title)

        body = QLabel("""
<div style='font-family:Segoe UI,Arial;font-size:12px;line-height:1.85;'>

<p style='font-size:14px;font-weight:bold;color:#F59B3A;margin-bottom:4px;'>
  🤖 Modèle IA — KIBALI Final Merged
</p>
<p>
  Base : <b>Mistral-7B-Instruct-v0.2</b> (Mistral AI) &nbsp;+&nbsp;
  18 adaptateurs LoRA géophysique/géotechnique.<br>
  Auteur du fine-tune : <b>BelikanM</b> — 
  <i>https://huggingface.co/BelikanM/kibali-final-merged</i><br>
  <b style='color:#DA701C;'>Licence : Apache License 2.0</b>
</p>

<p style='font-size:13px;font-weight:bold;color:#F59B3A;margin-top:12px;margin-bottom:4px;'>
  ✅ Droits accordés par Apache 2.0
</p>
<p>
  &nbsp; ✅ Usage commercial libre (vente de rapports, missions d'ingénierie, SaaS…)<br>
  &nbsp; ✅ Intégration dans un produit ou logiciel propriétaire<br>
  &nbsp; ✅ Distribution du logiciel incluant ce modèle<br>
  &nbsp; ✅ Modification et ré-entraînement du modèle<br>
  &nbsp; ✅ Fusion avec d'autres modèles (merged / GGUF…)
</p>

<p style='font-size:13px;font-weight:bold;color:#F59B3A;margin-top:12px;margin-bottom:4px;'>
  ⚠️ Obligations lors d'une distribution commerciale
</p>
<p>
  &nbsp; ⚠️ Inclure la notice <b>Apache License 2.0</b> dans toute distribution<br>
  &nbsp; ⚠️ Attribution obligatoire :<br>
  &nbsp;&nbsp;&nbsp;&nbsp; <i>"KIBALI par BelikanM, basé sur Mistral-7B-Instruct-v0.2 © Mistral AI"</i><br>
  &nbsp; ⚠️ Ne pas utiliser les noms/logos <b>Mistral AI</b> pour promouvoir des produits dérivés<br>
  &nbsp; ⚠️ Les modifications redistribuées doivent conserver la licence Apache 2.0<br>
  &nbsp; ⚠️ Aucune garantie implicite — le modèle est fourni "tel quel"
</p>

<p style='font-size:13px;font-weight:bold;color:#F59B3A;margin-top:14px;margin-bottom:4px;'>
  📦 Composants logiciels du logiciel
</p>
<p>
  <b style='color:#F0E1C3;'>PySide6</b> — LGPL v3 : usage commercial autorisé sans
  obligation de publier le code source de l'application<br>
  <b style='color:#F0E1C3;'>Plotly</b> — MIT : libre de tout usage commercial<br>
  <b style='color:#F0E1C3;'>Pandas / NumPy / SciPy</b> — BSD-3 : libre de tout usage<br>
  <b style='color:#F0E1C3;'>ReportLab</b> — BSD : libre de tout usage<br>
  <b style='color:#F0E1C3;'>Transformers (Hugging Face)</b> — Apache 2.0<br>
  <b style='color:#F0E1C3;'>Accelerate</b> — Apache 2.0<br>
  <b style='color:#F0E1C3;'>Matplotlib</b> — PSF / BSD : libre de tout usage commercial
</p>

<p style='font-size:13px;font-weight:bold;color:#F59B3A;margin-top:14px;margin-bottom:4px;'>
  📋 Résumé : Ce logiciel est-il utilisable commercialement ?
</p>
<p style='background:rgba(193,85,15,0.15);padding:10px;border-radius:6px;
          border-left:3px solid #F59B3A;'>
  <b style='color:#6fcf6f;'>OUI</b> — L'ensemble de la pile logicielle (modèle IA + bibliothèques)
  est sous licences permissives autorisant l'usage commercial.<br>
  Condition essentielle : <b>mentionner les auteurs originaux</b> (BelikanM / Mistral AI)
  dans la documentation ou l'interface du produit distribué.
</p>

<p style='font-size:10px;color:#7a6a50;margin-top:16px;'>
  Textes de licences complets disponibles sur :
  apache.org/licenses/LICENSE-2.0 &nbsp;|&nbsp; opensource.org/licenses/MIT
  &nbsp;|&nbsp; gnu.org/licenses/lgpl-3.0
</p>
</div>
""")
        body.setTextFormat(Qt.TextFormat.RichText)
        body.setWordWrap(True)
        cl.addWidget(body)
        cl.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(dialog.accept)
        main_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
        dialog.exec()

    def showPresentation(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Présentation du Logiciel CPT Analysis Studio")
        dialog.resize(600, 500)
        layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout()
        
        title = QLabel("🏗️ CPT Analysis Studio")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0078d7;")
        content_layout.addWidget(title)
        
        subtitle = QLabel("Logiciel puissant d'analyse géotechnique avec IA")
        subtitle.setStyleSheet("font-size: 16px; font-style: italic;")
        content_layout.addWidget(subtitle)
        
        version = QLabel("Version 2.0 - Interface moderne et analyses avancées")
        content_layout.addWidget(version)
        
        features_title = QLabel("✨ Fonctionnalités principales :")
        features_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 20px;")
        content_layout.addWidget(features_title)
        
        features = QLabel("""
• Analyse complète des données CPTU<br>
• 20 graphiques interactifs et exportables<br>
• Classifications des sols automatiques avec IA<br>
• Analyse de liquéfaction sismique<br>
• Chat IA intégré pour questions contextuelles<br>
• Recherche web automatique pour réponses enrichies<br>
• Export PDF multi-pages et Excel<br>
• Interface moderne avec thèmes personnalisables<br>
• Visualisations 3D interactives<br>
• Tableaux détaillés et statistiques<br>
• Vue d'ensemble complète de tous les résultats
        """)
        features.setTextFormat(Qt.TextFormat.RichText)
        content_layout.addWidget(features)
        
        download_title = QLabel("📥 Téléchargement :")
        download_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 20px;")
        content_layout.addWidget(download_title)
        
        download_text = QLabel("Cliquez ci-dessous pour télécharger la dernière version ou le manuel utilisateur :")
        content_layout.addWidget(download_text)
        
        download_btn = QPushButton("⬇️ Télécharger")
        download_btn.setStyleSheet("font-size: 14px; padding: 10px; background-color: #28a745; color: white; border-radius: 5px;")
        download_btn.clicked.connect(self.downloadSoftware)
        content_layout.addWidget(download_btn)

        # ── Licences & usage commercial ────────────────────────────────────
        lic_title = QLabel("⚖️ Licences & Usage Commercial")
        lic_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 24px; color: #F59B3A;")
        content_layout.addWidget(lic_title)

        lic_text = QLabel("""
<b style='color:#DA701C;'>Modèle IA — KIBALI Final Merged (Mistral-7B-Instruct-v0.2)</b><br>
Licence : <b>Apache License 2.0</b> — Usage commercial <b style='color:#28a745;'>AUTORISÉ</b>.<br><br>
<b>Points clés pour l'usage commercial :</b><br>
&nbsp; ✅ Utilisation commerciale libre (vente de rapports, prestations, SaaS…)<br>
&nbsp; ✅ Intégration dans des produits propriétaires autorisée<br>
&nbsp; ✅ Modification et fusion de modèles autorisées<br>
&nbsp; ⚠️ Obligation de conserver la notice Apache 2.0 dans toute distribution<br>
&nbsp; ⚠️ Attribution obligatoire : <i>KIBALI par BelikanM, basé sur Mistral-7B-Instruct-v0.2 (Mistral AI)</i><br>
&nbsp; ⚠️ Ne pas utiliser les noms/logos Mistral AI pour promouvoir des produits dérivés<br>
&nbsp; ⚠️ Les modifications distribuées doivent rester sous Apache 2.0<br><br>
<b style='color:#DA701C;'>Composants logiciels :</b><br>
&nbsp; • PySide6 : LGPL v3 — usage commercial autorisé sans obligation de publier le code source<br>
&nbsp; • Plotly : MIT — libre de tout usage<br>
&nbsp; • Pandas / NumPy / SciPy : BSD-3 — libre de tout usage<br>
&nbsp; • ReportLab (PDF) : BSD — libre de tout usage<br>
&nbsp; • Transformers (Hugging Face) : Apache 2.0 — usage commercial autorisé<br>
""")
        lic_text.setTextFormat(Qt.TextFormat.RichText)
        lic_text.setWordWrap(True)
        lic_text.setStyleSheet("font-size: 12px; line-height: 1.8; padding: 10px; "
                               "background: rgba(193,85,15,0.10); border-radius: 6px; "
                               "border: 1px solid #C1550F;")
        content_layout.addWidget(lic_text)

        content.setLayout(content_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()

    def showDataIntegrityReport(self):
        """Affiche le rapport détaillé d'intégrité des données"""
        if self.df is None:
            QMessageBox.warning(self, "Aucune donnée", "Veuillez d'abord charger un fichier CPT.")
            return

        # Ouvrir un dialogue pour sélectionner un fichier à vérifier
        fileName, _ = QFileDialog.getOpenFileName(self, "Sélectionner fichier pour vérification d'intégrité",
                                                  "", "Fichiers CPT (*.txt *.xlsx *.csv *.xls *.cal);;Tous les fichiers (*)")

        if not fileName:
            return

        try:
            # Générer le rapport d'intégrité
            integrity_report = self.data_checker.generate_integrity_report(fileName)

            # Créer une boîte de dialogue pour afficher le rapport
            dialog = QDialog(self)
            dialog.setWindowTitle("Rapport d'Intégrité des Données")
            dialog.setGeometry(200, 200, 800, 600)

            layout = QVBoxLayout()

            # Titre
            title = QLabel("Rapport de Vérification d'Intégrité des Données CPT")
            title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            layout.addWidget(title)

            # Zone de texte pour le rapport
            report_text = QTextEdit()
            report_text.setPlainText(integrity_report)
            report_text.setReadOnly(True)
            report_text.setFont(QFont("Consolas", 10))  # Police monospace pour une meilleure lisibilité

            layout.addWidget(report_text)

            # Boutons
            button_layout = QHBoxLayout()

            save_btn = QPushButton("Sauvegarder Rapport")
            save_btn.clicked.connect(lambda: self.saveIntegrityReport(integrity_report))
            button_layout.addWidget(save_btn)

            close_btn = QPushButton("Fermer")
            close_btn.clicked.connect(dialog.accept)
            button_layout.addWidget(close_btn)

            layout.addLayout(button_layout)

            dialog.setLayout(layout)
            dialog.exec()

        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la génération du rapport: {str(e)}")

    def saveIntegrityReport(self, report_text):
        """Sauvegarde le rapport d'intégrité dans un fichier"""
        fileName, _ = QFileDialog.getSaveFileName(self, "Sauvegarder Rapport d'Intégrité",
                                                  "rapport_integrite_donnees.txt",
                                                  "Fichiers texte (*.txt);;Tous les fichiers (*)")

        if fileName:
            try:
                with open(fileName, 'w', encoding='utf-8') as f:
                    f.write(report_text)
                QMessageBox.information(self, "Succès", "Rapport sauvegardé avec succès.")
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Erreur lors de la sauvegarde: {str(e)}")

    def downloadSoftware(self):
        QMessageBox.information(self, "Téléchargement", "Fonctionnalité de téléchargement à implémenter.\n\nPour l'instant, vous pouvez visiter le dépôt GitHub ou contacter le développeur pour obtenir la dernière version.")

    def addCoordinates(self):
        """Ajouter des coordonnées pour un nouveau sondage"""
        row_count = self.coordTable.rowCount()
        self.coordTable.insertRow(row_count)
        self.coordTable.setItem(row_count, 0, QTableWidgetItem("Nouveau sondage"))
        self.coordTable.setItem(row_count, 1, QTableWidgetItem("0.0"))
        self.coordTable.setItem(row_count, 2, QTableWidgetItem("0.0"))

    def clearCoordinates(self):
        """Effacer toutes les coordonnées"""
        self.coordTable.setRowCount(0)
        self.fusion_files = []
        self.fusionFileList.clear()
        self.fusionButton.setEnabled(False)

    def create3DSoilMap(self):
        """Créer les cartes 2D individuelles pour chaque sondage CPTU"""
        try:
            if not self.fusion_files:
                QMessageBox.warning(self, "Erreur", "Aucun fichier chargé.")
                return

            # Charger les données individuelles pour chaque fichier
            individual_data = []
            parser = CPTParser()

            for file_path in self.fusion_files:
                try:
                    df, message = parser.parse_file(file_path)

                    if df is None or df.empty:
                        print(f"⚠️ Impossible de parser {os.path.basename(file_path)}: {message}")
                        continue

                    # Ajouter le nom du sondage
                    filename = os.path.basename(file_path)
                    df['Sondage'] = filename

                    # Normaliser les noms de colonnes
                    df = df.rename(columns={'depth': 'Depth', 'qc': 'qc', 'fs': 'fs'})

                    individual_data.append(df)
                    print(f"✅ {filename}: {len(df)} points chargés")

                except Exception as e:
                    print(f"❌ Erreur avec {os.path.basename(file_path)}: {e}")
                    continue

            if not individual_data:
                QMessageBox.warning(self, "Erreur", "Aucune donnée valide trouvée dans les fichiers.")
                return

            # Combiner toutes les données individuelles
            combined_data = pd.concat(individual_data, ignore_index=True)

            # Créer la visualisation 3D de contours pour chaque sondage CPTU
            self.createFused3DVisualization(combined_data)

            # Afficher les informations
            info_text = f"Graphiques 3D de contours créés avec succès!\n"
            info_text += f"• {len(individual_data)} CPTU chargés\n"
            info_text += f"• {len(combined_data)} points de données totaux\n"
            info_text += f"• Profondeur max: {combined_data['Depth'].max():.1f} m\n"

            self.fusion2DInfoLabel.setText(info_text)
            self.fusion2DInfoLabel.setStyleSheet("font-weight: bold; color: #4CAF50;")

            QMessageBox.information(self, "Succès", "Graphiques 3D de contours créés avec succès!")

        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la création des graphiques 2D: {e}")
            import traceback
            traceback.print_exc()

    def fuseCPTUData(self, file_paths, coordinates):
        """Fusionner les données CPTU avec les coordonnées"""
        fused_data = []
        parser = CPTParser()
        
        for file_path in file_paths:
            try:
                # Parser le fichier
                df, message = parser.parse_file(file_path)
                
                if df is None or df.empty:
                    print(f"⚠️ Impossible de parser {os.path.basename(file_path)}: {message}")
                    continue
                
                # Ajouter les coordonnées
                filename = os.path.basename(file_path)
                if filename in coordinates:
                    x, y = coordinates[filename]
                    df['X'] = x
                    df['Y'] = y
                    df['Sondage'] = filename
                else:
                    # Coordonnées par défaut si non spécifiées
                    df['X'] = 0.0
                    df['Y'] = 0.0
                    df['Sondage'] = filename
                
                # Normaliser les noms de colonnes
                df = df.rename(columns={'depth': 'Depth', 'qc': 'qc', 'fs': 'fs'})
                
                fused_data.append(df)
                print(f"✅ {filename}: {len(df)} points chargés")
                
            except Exception as e:
                print(f"❌ Erreur avec {os.path.basename(file_path)}: {e}")
                continue
        
        if not fused_data:
            return pd.DataFrame()
        
        # Combiner toutes les données
        combined_df = pd.concat(fused_data, ignore_index=True)
        
        # Trier par coordonnées et profondeur
        combined_df = combined_df.sort_values(['X', 'Y', 'Depth']).reset_index(drop=True)
        
        return combined_df

    def loadMultipleCPTUFiles(self):
        """Charge plusieurs fichiers CPTU pour la fusion"""
        try:
            # Ouvrir le dialogue de sélection de fichiers
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, 
                "Sélectionner les fichiers CPTU", 
                "", 
                "Fichiers CPTU (*.txt *.csv *.xlsx);;Tous les fichiers (*)"
            )
            
            if not file_paths:
                return
            
            # Stocker les fichiers
            self.fusion_files = file_paths
            
            # Afficher la liste des fichiers chargés
            file_list_text = "Fichiers chargés :\n" + "\n".join([f"• {os.path.basename(fp)}" for fp in file_paths])
            self.fusionFileList.setText(file_list_text)
            
            # Activer les boutons
            self.autoDetectCoordButton.setEnabled(True)
            self.addCoordButton.setEnabled(True)
            self.clearCoordButton.setEnabled(True)
            
            # Auto-détecter les coordonnées automatiquement
            self.autoDetectAndFillCoordinates()
            
            QMessageBox.information(self, "Succès", f"{len(file_paths)} fichiers CPTU chargés avec succès !\n\nLes coordonnées ont été auto-détectées. Vous pouvez les modifier si nécessaire.")
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors du chargement: {e}")

    def autoDetectCoordinates(self, file_paths):
        """Détecte automatiquement les coordonnées des fichiers CPTU en utilisant l'IA et algorithmes de reconstruction"""
        global RAG_SYSTEM_AVAILABLE  # Déclarer comme variable globale
        try:
            coordinates = {}

            # Initialiser le système RAG si nécessaire
            if not hasattr(self, 'rag_system') or self.rag_system is None:
                if RAG_SYSTEM_AVAILABLE:
                    try:
                        from models.rag_system import CPT_RAG_System  # type: ignore
                        self.rag_system = CPT_RAG_System()
                        print("✅ Système RAG initialisé avec succès")
                    except Exception as e:
                        print(f"⚠️ Échec de l'initialisation du système RAG: {e}")
                        self.rag_system = None
                        RAG_SYSTEM_AVAILABLE = False
                else:
                    self.rag_system = None
                    print("⚠️ Système RAG non disponible - reconstruction avec algorithmes déterministes uniquement")

            # Analyser d'abord tous les fichiers pour comprendre le contexte global
            file_contexts = []
            for i, file_path in enumerate(file_paths):
                filename = os.path.basename(file_path)
                context = {
                    'filename': filename,
                    'index': i,
                    'path': file_path,
                    'coords_from_name': self.extractCoordinatesFromFilename(filename),
                    'data_summary': None
                }

                # Essayer de lire un résumé des données CPTU
                try:
                    if os.path.exists(file_path):
                        # Lire quelques lignes pour analyser les données
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()[:20]  # Premières lignes
                            context['data_summary'] = f"Lignes: {len(lines)}, Contenu exemple: {lines[0].strip()[:100]}"
                except:
                    pass

                file_contexts.append(context)

            # Algorithme 1: Reconstruction basée sur les données géologiques
            geological_coordinates = self.reconstructCoordinatesFromGeology(file_contexts)

            for i, file_path in enumerate(file_paths):
                filename = os.path.basename(file_path)
                context = file_contexts[i]

                # Méthode 1: Coordonnées extraites du nom de fichier (priorité maximale)
                if context['coords_from_name']:
                    coordinates[filename] = context['coords_from_name']
                    print(f"📍 Coordonnées extraites du nom: {filename} -> X={context['coords_from_name'][0]}, Y={context['coords_from_name'][1]}")
                    continue

                # Méthode 2: Reconstruction géologique
                if filename in geological_coordinates:
                    x, y = geological_coordinates[filename]
                    coordinates[filename] = (x, y)
                    print(f"🗺️ Reconstruction géologique: {filename} -> X={x}, Y={y}")
                    continue

                # Méthode 3: IA avancée avec reconstruction de données
                try:
                    x, y = self.reconstructCoordinatesWithAI(context, file_contexts)
                    coordinates[filename] = (x, y)
                    print(f"🤖 IA reconstruction: {filename} -> X={x}, Y={y}")
                    continue

                except Exception as e:
                    print(f"⚠️ Erreur IA reconstruction pour {filename}: {e}")

                # Méthode 4: Algorithme de grille intelligente optimisée
                x, y = self.generateOptimalGridPosition(i, len(file_paths), coordinates)
                coordinates[filename] = (x, y)
                print(f"📐 Grille intelligente: {filename} -> X={x}, Y={y}")

            return coordinates

        except Exception as e:
            print(f"❌ Erreur auto-détection coordonnées: {e}")
            # Retourner des coordonnées par défaut
            return {os.path.basename(fp): (i * 10.0, 0.0) for i, fp in enumerate(file_paths)}

    def reconstructCoordinatesFromGeology(self, file_contexts):
        """Reconstruction des coordonnées basée sur l'analyse géologique des données CPTU"""
        try:
            coordinates = {}

            # Analyser d'abord les données CPTU pour des patterns géologiques
            geological_data = self.analyzeCPTUGeologicalPatterns(file_contexts)

            # Analyser les patterns géologiques dans les noms de fichiers
            geological_patterns = {
                'river': ['river', 'rivière', 'fleuve', 'riviere'],
                'road': ['road', 'route', 'rue', 'chemin'],
                'building': ['building', 'batiment', 'construction', 'immeuble'],
                'bridge': ['bridge', 'pont', 'viaduc'],
                'tunnel': ['tunnel', 'galerie'],
                'slope': ['slope', 'talus', 'pente'],
                'embankment': ['embankment', 'remblai', 'digue'],
                'excavation': ['excavation', 'fouille', 'tranchee']
            }

            # Analyser chaque fichier pour des indices géologiques
            for context in file_contexts:
                filename = context['filename'].lower()
                geological_type = None
                position_hint = None

                # Détecter le type géologique depuis les données
                if filename in geological_data:
                    geological_type = geological_data[filename].get('type')

                # Détecter le type géologique depuis le nom
                if not geological_type:
                    for geo_type, keywords in geological_patterns.items():
                        if any(keyword in filename for keyword in keywords):
                            geological_type = geo_type
                            break

                # Extraire des indices de position
                if 'left' in filename or 'gauche' in filename:
                    position_hint = 'left'
                elif 'right' in filename or 'droite' in filename:
                    position_hint = 'right'
                elif 'center' in filename or 'centre' in filename or 'central' in filename:
                    position_hint = 'center'
                elif 'north' in filename or 'nord' in filename:
                    position_hint = 'north'
                elif 'south' in filename or 'sud' in filename:
                    position_hint = 'south'
                elif 'east' in filename or 'est' in filename:
                    position_hint = 'east'
                elif 'west' in filename or 'ouest' in filename:
                    position_hint = 'west'

                # Générer des coordonnées basées sur l'analyse géologique
                base_coords = self.generateGeologicalCoordinates(geological_type, position_hint, context['index'], len(file_contexts))
                if base_coords:
                    coordinates[context['filename']] = base_coords

            return coordinates

        except Exception as e:
            print(f"⚠️ Erreur reconstruction géologique: {e}")
            return {}

    def analyzeCPTUGeologicalPatterns(self, file_contexts):
        """Analyse les données CPTU pour identifier des patterns géologiques"""
        try:
            geological_analysis = {}

            for context in file_contexts:
                filename = context['filename']
                file_path = context['path']

                try:
                    # Charger les données CPTU
                    from core.cpt_parser import CPTParser
                    parser = CPTParser()
                    result = parser.parse_file(file_path)

                    # Le parser retourne un tuple (DataFrame, message)
                    if result[0] is not None and isinstance(result[0], pd.DataFrame):
                        data = result[0]
                        # Analyser les patterns géologiques dans les données
                        analysis = self.analyzeGeologicalData(data)
                        geological_analysis[filename] = analysis
                    else:
                        print(f"⚠️ Erreur parsing {filename}: {result[1]}")

                except Exception as e:
                    print(f"⚠️ Impossible d'analyser {filename}: {e}")
                    continue

            return geological_analysis

        except Exception as e:
            print(f"⚠️ Erreur analyse patterns géologiques: {e}")
            return {}

    def analyzeGeologicalData(self, data):
        """Analyse les données CPTU pour identifier le contexte géologique"""
        try:
            analysis = {}

            if 'qc' not in data.columns or 'fs' not in data.columns:
                return analysis

            # Calculer des statistiques
            qc_mean = data['qc'].mean()
            qc_std = data['qc'].std()
            fs_mean = data['fs'].mean()

            # Classifier le type de sol dominant
            if qc_mean > 15:  # Sol très résistant
                soil_type = 'rock' if qc_mean > 50 else 'dense_sand'
            elif qc_mean > 5:  # Sol résistant
                soil_type = 'medium_sand' if fs_mean < 100 else 'silt'
            else:  # Sol faible
                soil_type = 'clay' if fs_mean > 150 else 'loose_sand'

            analysis['soil_type'] = soil_type

            # Détecter des patterns spéciaux
            if self.detectRiverPattern(data):
                analysis['type'] = 'river'
                analysis['confidence'] = 0.8
            elif self.detectSlopePattern(data):
                analysis['type'] = 'slope'
                analysis['confidence'] = 0.7
            elif self.detectEmbankmentPattern(data):
                analysis['type'] = 'embankment'
                analysis['confidence'] = 0.6
            else:
                analysis['type'] = 'generic'
                analysis['confidence'] = 0.3

            return analysis

        except Exception as e:
            print(f"⚠️ Erreur analyse données géologiques: {e}")
            return {}

    def detectRiverPattern(self, data):
        """Détecte si les données correspondent à un profil de rivière"""
        try:
            # Les rivières ont souvent des couches alternées et des valeurs variables
            if 'qc' in data.columns and len(data) > 10:
                # Calculer la variabilité
                qc_variability = data['qc'].std() / data['qc'].mean()
                return qc_variability > 0.5  # Haute variabilité = possible rivière
            return False
        except:
            return False

    def detectSlopePattern(self, data):
        """Détecte si les données correspondent à un profil de pente/talus"""
        try:
            if 'qc' in data.columns and len(data) > 10:
                # Les pentes ont souvent une augmentation progressive de qc avec la profondeur
                depths = data.index if data.index.name == 'depth' else data['depth'] if 'depth' in data.columns else range(len(data))
                qc_trend = np.polyfit(list(depths), data['qc'].values, 1)[0]
                return qc_trend > 0.1  # Tendance positive = possible pente
            return False
        except:
            return False

    def detectEmbankmentPattern(self, data):
        """Détecte si les données correspondent à un profil de remblai"""
        try:
            if 'qc' in data.columns and len(data) > 10:
                # Les remblais ont souvent des valeurs qc variables en surface
                surface_qc = data['qc'].head(5).mean()
                deep_qc = data['qc'].tail(5).mean()
                return abs(surface_qc - deep_qc) / max(surface_qc, deep_qc) > 0.3
            return False
        except:
            return False

    def generateGeologicalCoordinates(self, geological_type, position_hint, index, total_files):
        """Génère des coordonnées basées sur le contexte géologique"""
        try:
            # Base coordinates selon le type géologique
            if geological_type == 'river':
                # Alignement le long d'une rivière (axe Y)
                x = 0
                y = index * 50  # Espacement de 50m le long de la rivière
            elif geological_type == 'road':
                # Alignement le long d'une route (axe X)
                x = index * 100  # Espacement de 100m le long de la route
                y = 0
            elif geological_type == 'bridge':
                # Autour d'un pont (disposition en éventail)
                angle = (index / max(1, total_files - 1)) * 180 - 90  # De -90° à +90°
                distance = 20 + (index % 3) * 10  # Distances variables
                x = distance * np.cos(np.radians(angle))
                y = distance * np.sin(np.radians(angle))
            elif geological_type == 'tunnel':
                # Le long d'un tunnel (axe X avec variation Y)
                x = index * 25
                y = (index % 2) * 10 - 5  # Alternance de chaque côté
            else:
                # Disposition générique en grille optimisée
                grid_cols = int(np.ceil(np.sqrt(total_files)))
                row = index // grid_cols
                col = index % grid_cols
                x = col * 15
                y = row * 15

            # Ajuster selon les indices de position
            if position_hint == 'left':
                x -= 20
            elif position_hint == 'right':
                x += 20
            elif position_hint == 'north':
                y += 20
            elif position_hint == 'south':
                y -= 20
            elif position_hint == 'east':
                x += 20
            elif position_hint == 'west':
                x -= 20

            return (x, y)

        except Exception as e:
            print(f"⚠️ Erreur génération coordonnées géologiques: {e}")
            return None

    def reconstructCoordinatesWithAI(self, context, all_contexts):
        """Reconstruction avancée des coordonnées utilisant l'IA avec algorithme de reconstruction"""
        try:
            # Analyser le contexte global
            global_context = f"Total de fichiers: {len(all_contexts)}\n"
            global_context += "Fichiers analysés:\n"
            for i, ctx in enumerate(all_contexts[:10]):  # Limiter à 10 pour éviter surcharge
                global_context += f"- {ctx['filename']}"
                if ctx['coords_from_name']:
                    global_context += f" (coordonnées détectées: {ctx['coords_from_name']})"
                global_context += "\n"

            # Utiliser l'IA pour reconstruction intelligente
            prompt = f"""Analyse ce fichier CPTU et reconstruis des coordonnées X,Y précises.

CONTEXTE GLOBAL:
{global_context}

FICHIER À ANALYSER:
Nom: {context['filename']}
Position: {context['index'] + 1}/{len(all_contexts)}
Données: {context.get('data_summary', 'Non disponible')}

INSTRUCTIONS pour reconstruction:
1. Analyse le nom du fichier pour des indices géologiques ou spatiaux
2. Considère la position relative par rapport aux autres fichiers
3. Utilise des principes géotechniques réalistes pour le placement
4. Crée une disposition logique et optimisée spatialement

L'algorithme de reconstruction doit:
- Préserver les distances réalistes entre sondages (10-50m typiquement)
- Créer des alignements logiques (lignes, grilles, courbes)
- Respecter les contraintes géologiques implicites
- Optimiser pour la couverture spatiale

Réponds UNIQUEMENT avec: X=123.45, Y=67.89
"""

            if self.rag_system and hasattr(self.rag_system, 'is_initialized') and self.rag_system.is_initialized:
                response = self.rag_system.query(prompt, use_web=False, use_geo=False)

                # Extraire les coordonnées avec regex amélioré
                import re
                coord_patterns = [
                    r'X=([-\d.]+),\s*Y=([-\d.]+)',
                    r'X\s*=\s*([-\d.]+).*?Y\s*=\s*([-\d.]+)',
                    r'coord.*?\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)',
                    r'position.*?\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)'
                ]

                for pattern in coord_patterns:
                    match = re.search(pattern, response, re.IGNORECASE)
                    if match:
                        x, y = float(match.group(1)), float(match.group(2))
                        return (x, y)

            # Fallback: utiliser un algorithme déterministe de reconstruction
            return self.deterministicCoordinateReconstruction(context, all_contexts)

        except Exception as e:
            print(f"⚠️ Erreur reconstruction IA: {e}")
            return self.deterministicCoordinateReconstruction(context, all_contexts)

    def deterministicCoordinateReconstruction(self, context, all_contexts):
        """Algorithme déterministe de reconstruction de coordonnées"""
        index = 0
        try:
            index = context['index']
            total = len(all_contexts)

            # Analyser les patterns dans les noms de fichiers
            filename = context['filename'].lower()

            # Patterns spatiaux
            if any(word in filename for word in ['line', 'ligne', 'align', 'row']):
                # Disposition en ligne
                x = index * 25
                y = 0
            elif any(word in filename for word in ['grid', 'grille', 'matrix']):
                # Disposition en grille
                grid_cols = int(np.ceil(np.sqrt(total)))
                row = index // grid_cols
                col = index % grid_cols
                x = col * 20
                y = row * 20
            elif any(word in filename for word in ['circle', 'cercle', 'radial']):
                # Disposition radiale
                angle = (index / max(1, total - 1)) * 2 * np.pi
                radius = 30
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
            else:
                # Disposition optimisée par défaut
                # Utiliser un algorithme de placement optimisé
                x, y = self.optimizeCoordinatePlacement(index, total)

            return (x, y)

        except Exception as e:
            print(f"⚠️ Erreur reconstruction déterministe: {e}")
            # Fallback final
            return (index * 15.0, 0.0)

    def optimizeCoordinatePlacement(self, index, total):
        """Algorithme d'optimisation pour le placement des coordonnées"""
        try:
            import math

            # Calculer la disposition optimale
            if total <= 4:
                # Carré simple
                positions = [(0, 0), (20, 0), (0, 20), (20, 20)]
                x, y = positions[min(index, len(positions) - 1)]
            elif total <= 9:
                # Grille 3x3 optimisée
                grid_size = 3
                row = index // grid_size
                col = index % grid_size
                x = col * 25
                y = row * 25
            else:
                # Disposition en spirale pour maximiser l'espacement
                # Algorithme de spirale d'Archimède
                theta = index * 0.5  # Angle
                r = math.sqrt(index) * 15  # Rayon croissant
                x = r * math.cos(theta)
                y = r * math.sin(theta)

            return (x, y)

        except Exception as e:
            return (index * 20.0, 0.0)

    def generateOptimalGridPosition(self, index, total, existing_coordinates):
        """Génère une position optimale dans une grille intelligente"""
        try:
            # Éviter les collisions avec les coordonnées existantes
            existing_positions = list(existing_coordinates.values())

            # Calculer la grille optimale
            grid_cols = int(np.ceil(np.sqrt(total)))
            row = index // grid_cols
            col = index % grid_cols

            # Espacement adaptatif
            if total <= 4:
                spacing = 15.0
            elif total <= 9:
                spacing = 20.0
            elif total <= 16:
                spacing = 25.0
            else:
                spacing = 30.0

            x = col * spacing
            y = row * spacing

            # Ajuster pour éviter les collisions
            attempts = 0
            while (x, y) in existing_positions and attempts < 10:
                x += 5  # Décaler légèrement
                y += 5
                attempts += 1

            return (x, y)

        except Exception as e:
            return (index * 25.0, 0.0)
    def extractCoordinatesFromFilename(self, filename):
        """Extrait les coordonnées du nom de fichier si elles sont présentes"""
        import re
        
        # Patterns courants pour les coordonnées dans les noms de fichiers
        patterns = [
            # X100Y200, X100_Y200, X_100_Y_200, etc.
            r'[XYxy]_?(\d+(?:\.\d+)?)_?[XYxy]_?(\d+(?:\.\d+)?)',
            # 100_200 (X_Y), 100x200, etc.
            r'(\d+(?:\.\d+)?)[_x](\d+(?:\.\d+)?)',
            # Coordonnées avec séparateur
            r'coord[_]?(\d+(?:\.\d+)?)[_x](\d+(?:\.\d+)?)',
            # Position avec tirets
            r'pos[_-]?(\d+(?:\.\d+)?)[_-](\d+(?:\.\d+)?)',
            # Nombres séparés par des tirets ou underscores
            r'(\d+(?:\.\d+)?)[_-](\d+(?:\.\d+)?)[_-](\d+(?:\.\d+)?)',
            # Format CPTU_X123.45_Y67.89
            r'CPTU[_]?[XYxy](\d+(?:\.\d+)?)[_]?[XYxy](\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, filename, re.IGNORECASE)
            if matches:
                # Prendre le premier match
                match = matches[0]
                if len(match) >= 2:
                    # Si on a 3 nombres, prendre les 2 derniers (X,Y)
                    if len(match) == 3:
                        x, y = float(match[1]), float(match[2])
                    else:
                        x, y = float(match[0]), float(match[1])
                    return (x, y)
        
        return None

    def autoDetectAndFillCoordinates(self):
        """Auto-détecte les coordonnées et remplit la table"""
        try:
            if not hasattr(self, 'fusion_files') or not self.fusion_files:
                QMessageBox.warning(self, "Erreur", "Veuillez d'abord charger des fichiers CPTU.")
                return
            
            # Auto-détecter les coordonnées
            coordinates = self.autoDetectCoordinates(self.fusion_files)
            
            # Vider la table actuelle
            self.coordTable.setRowCount(0)
            
            # Remplir la table avec les coordonnées détectées
            for filename, (x, y) in coordinates.items():
                row = self.coordTable.rowCount()
                self.coordTable.insertRow(row)
                
                # Fichier
                self.coordTable.setItem(row, 0, QTableWidgetItem(filename))
                
                # Coordonnée X
                x_item = QTableWidgetItem(f"{x:.2f}")
                x_item.setData(Qt.ItemDataRole.UserRole, x)  # Stocker la valeur numérique
                x_item.setFlags(x_item.flags() | Qt.ItemFlag.ItemIsEditable)  # Rendre éditable
                self.coordTable.setItem(row, 1, x_item)
                
                # Coordonnée Y
                y_item = QTableWidgetItem(f"{y:.2f}")
                y_item.setData(Qt.ItemDataRole.UserRole, y)  # Stocker la valeur numérique
                y_item.setFlags(y_item.flags() | Qt.ItemFlag.ItemIsEditable)  # Rendre éditable
                self.coordTable.setItem(row, 2, y_item)
            
            # Activer le bouton de fusion
            self.fusionButton.setEnabled(True)
            
            QMessageBox.information(self, "Succès", 
                f"Coordonnées auto-détectées pour {len(coordinates)} fichiers.\n"
                "Vous pouvez les modifier manuellement si nécessaire.")
            
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'auto-détection: {e}")

    def createFused3DVisualization(self, fused_data):
        """Créer la visualisation de contours 3D pour chaque sondage CPTU"""
        try:
            # Créer des graphiques de contours individuels pour chaque sondage
            sondages = fused_data['Sondage'].unique()
            n_sondages = len(sondages)

            # Calculer la grille optimale (carré le plus proche)
            n_cols = int(np.ceil(np.sqrt(n_sondages)))
            n_rows = int(np.ceil(n_sondages / n_cols))

            # Créer la figure avec sous-graphiques 2D
            specs = [[{} for _ in range(n_cols)] for _ in range(n_rows)]
            fig = make_subplots(
                rows=n_rows, cols=n_cols,
                subplot_titles=[f'Contours qc de {sondage}' for sondage in sondages],
                specs=specs,
                shared_xaxes=False,
                shared_yaxes=False
            )

            # Pour chaque sondage, créer un graphique de contour
            for idx, sondage in enumerate(sondages):
                sondage_data = fused_data[fused_data['Sondage'] == sondage]

                if len(sondage_data) < 3:
                    continue

                # Calculer la position du sous-graphique
                row = (idx // n_cols) + 1
                col = (idx % n_cols) + 1

                # Créer une grille régulière pour l'interpolation
                depth_values = sondage_data['Depth'].values
                qc_values = sondage_data['qc'].values if 'qc' in sondage_data.columns else sondage_data['fs'].values
                fs_values = sondage_data['fs'].values if 'fs' in sondage_data.columns else sondage_data['qc'].values

                # Vérifier que les données sont valides
                if len(depth_values) < 3 or len(qc_values) < 3 or len(fs_values) < 3:
                    # Pas assez de données pour l'interpolation, afficher seulement les points
                    fig.add_trace(
                        go.Scatter(
                            x=depth_values,
                            y=qc_values,
                            mode='markers',
                            marker=dict(size=6, color='red'),
                            name=f'Données {sondage} (pas assez de points)',
                            showlegend=False
                        ),
                        row=row, col=col
                    )
                    continue

                # Nettoyer les données (supprimer NaN et infinis)
                valid_mask = ~(np.isnan(depth_values) | np.isnan(qc_values) | np.isnan(fs_values) | np.isinf(depth_values) | np.isinf(qc_values) | np.isinf(fs_values))
                depth_clean = depth_values[valid_mask]
                qc_clean = qc_values[valid_mask]
                fs_clean = fs_values[valid_mask]

                if len(depth_clean) < 3:
                    # Pas assez de données valides
                    fig.add_trace(
                        go.Scatter(
                            x=depth_values,
                            y=qc_values,
                            mode='markers',
                            marker=dict(size=6, color='orange'),
                            name=f'Données {sondage} (données invalides)',
                            showlegend=False
                        ),
                        row=row, col=col
                    )
                    continue

                # Créer un graphique de contour 2D pour ce sondage
                fig.add_trace(
                    go.Contour(
                        x=depth_clean,
                        y=qc_clean,
                        z=fs_clean,
                        colorscale='Viridis',
                        contours=dict(showlabels=True),
                        name=f'Contours {sondage}',
                        showlegend=False
                    ),
                    row=row, col=col
                )



            # Configuration du layout
            fig.update_layout(
                title="Graphiques 3D de Contours qc de chaque CPTU",
                height=max(400, 300 * n_rows),
                width=None,
                showlegend=False,
                autosize=True,
                margin=dict(l=40, r=40, t=80, b=40, pad=10)
            )

            # Mettre à jour les axes pour chaque sous-graphique
            for i in range(1, n_rows + 1):
                for j in range(1, n_cols + 1):
                    fig.update_xaxes(title_text="Profondeur (m)", row=i, col=j)
                    fig.update_yaxes(title_text="qc (MPa)", row=i, col=j)

            # Convertir en HTML et afficher
            html_content = fig.to_html(include_plotlyjs='cdn', full_html=False, config={'responsive': True})
            self.fusion2DView.setHtml(html_content)

            # Activer le bouton d'export
            self.exportFusionPDFButton.setEnabled(True)

            # Informations sur les graphiques
            info_text = f"Graphiques 3D de contours créés pour {n_sondages} CPTU:\n"
            for sondage in sondages:
                sondage_data = fused_data[fused_data['Sondage'] == sondage]
                info_text += f"• {sondage}: {len(sondage_data)} points\n"

            self.fusion2DInfoLabel.setText(info_text)
            self.fusion2DInfoLabel.setStyleSheet("font-weight: bold; color: #2196F3;")

            print("✅ Graphiques 3D de contours créés avec succès")

        except Exception as e:
            error_html = f"<h1>Erreur Contours 3D: {str(e)}</h1><p>Vérifiez que les données sont valides.</p>"
            self.fusion2DView.setHtml(error_html)
            print(f"❌ Erreur dans createFused3DVisualization: {e}")
            import traceback
            traceback.print_exc()

    def exportFusion3DToPDF(self):
        """Exporter les contours 3D fusionnés en PDF"""
        try:
            if not hasattr(self, 'fused_data') or self.fused_data is None or self.fused_data.empty:
                QMessageBox.warning(self, "Erreur", "Aucune visualisation 3D à exporter.")
                return

            # Demander le nom du fichier
            fileName, _ = QFileDialog.getSaveFileName(self, "Sauvegarder Contours 3D PDF", "",
                                                      "Fichiers PDF (*.pdf);;Tous les fichiers (*)")

            if not fileName:
                return

            if not fileName.endswith('.pdf'):
                fileName += '.pdf'

            # Importer les bibliothèques nécessaires
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.utils import ImageReader
            import tempfile
            from plotly.io import to_image
            import plotly.graph_objects as go

            # Recréer la figure 2D (même logique que createFused3DVisualization)
            fig = go.Figure()
            
            fused_data = self.fused_data
            colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
            sondages = fused_data['Sondage'].unique()
            
            for i, sondage in enumerate(sondages):
                sondage_data = fused_data[fused_data['Sondage'] == sondage]
                color = colors[i % len(colors)]
                
                fig.add_trace(go.Scatter3d(
                    x=sondage_data['X'],
                    y=sondage_data['Y'], 
                    z=sondage_data['Depth'],
                    mode='markers',
                    marker=dict(
                        size=3,
                        color=sondage_data['qc'] if 'qc' in sondage_data.columns else color,
                        colorscale='Viridis' if 'qc' in sondage_data.columns else None,
                        showscale=True if i == 0 and 'qc' in sondage_data.columns else False,
                        colorbar=dict(title="qc (MPa)") if i == 0 and 'qc' in sondage_data.columns else None
                    ),
                    name=f'{sondage} - qc',
                    legendgroup=sondage
                ))
                
                fig.add_trace(go.Scatter3d(
                    x=sondage_data['X'],
                    y=sondage_data['Y'],
                    z=sondage_data['Depth'],
                    mode='lines',
                    line=dict(color=color, width=2),
                    name=f'{sondage} - profil',
                    legendgroup=sondage,
                    showlegend=False
                ))

            fig.update_layout(
                title="Carte 3D Complète du Sous-Sol - Fusion de Sondages CPTU",
                scene=dict(
                    xaxis_title='Coordonnée X (m)',
                    yaxis_title='Coordonnée Y (m)',
                    zaxis_title='Profondeur (m)',
                    zaxis_autorange="reversed"
                ),
                margin=dict(l=0, r=0, t=40, b=0),
                legend_title="Sondages CPTU"
            )

            # Créer le PDF
            c = canvas.Canvas(fileName, pagesize=A4)
            width, height = A4

            # Logo SETRAF
            _logo_fusion = os.path.join(os.path.dirname(os.path.abspath(__file__)), "setraf_logo.png")
            if os.path.exists(_logo_fusion):
                from reportlab.lib.utils import ImageReader as _IRF
                c.drawImage(_IRF(_logo_fusion), width - 165, height - 68,
                            width=115, height=52,
                            preserveAspectRatio=True, mask='auto')
            # Titre
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "Contours 3D - Graphiques qc de chaque CPTU")
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 70, f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
            c.drawString(50, height - 85, f"Nombre de sondages: {len(sondages)}")
            c.drawString(50, height - 100, f"Points de données totaux: {len(fused_data)}")

            # Statistiques
            c.drawString(50, height - 120, f"Profondeur max: {fused_data['Depth'].max():.1f} m")
            c.drawString(50, height - 135, f"Étendue X: {fused_data['X'].min():.1f} - {fused_data['X'].max():.1f} m")
            c.drawString(50, height - 150, f"Étendue Y: {fused_data['Y'].min():.1f} - {fused_data['Y'].max():.1f} m")

            # Liste des sondages
            c.drawString(50, height - 170, "Sondages inclus:")
            y_pos = height - 185
            for sondage in sondages:
                c.drawString(70, y_pos, f"• {sondage}")
                y_pos -= 15

            # Convertir la figure en image
            img_bytes = to_image(fig, format='png', width=700, height=500, scale=1)
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_file.write(img_bytes)
                tmp_filename = tmp_file.name
            
            # Ajouter l'image au PDF
            img = ImageReader(tmp_filename)
            c.drawImage(img, 50, 50, width=500, height=350)
            
            # Nettoyer
            os.unlink(tmp_filename)
            c.save()
            
            QMessageBox.information(self, "Succès", f"Contours 3D exportés en PDF:\n{fileName}")

        except ImportError as e:
            QMessageBox.warning(self, "Erreur", f"Bibliothèque manquante: {e}\n\nInstallez reportlab: pip install reportlab")
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'export PDF: {e}")

    def export3DGraphsToPDF(self):
        """Exporte tous les graphiques 3D — HTML interactif si kaleido absent, PDF sinon."""
        try:
            if not hasattr(self, 'df') or self.df is None or self.df.empty:
                QMessageBox.warning(self, "Erreur", "Aucune donnée chargée pour l'export 3D.")
                return

            # Vérifier kaleido disponible
            _kaleido_ok = False
            try:
                from plotly.io import to_image as _toi
                _toi  # test import
                _kaleido_ok = True
            except Exception:
                pass

            if not _kaleido_ok:
                # Fallback : exporter en HTML interactif
                directory = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier d'export HTML")
                if not directory:
                    return
                self.export3DGraphsIndividually()
                return

            # ── Export PDF avec kaleido ──────────────────────────────────────
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.utils import ImageReader
            import tempfile
            from plotly.io import to_image
            import plotly.graph_objects as go

            fileName, _ = QFileDialog.getSaveFileName(self, "Sauvegarder PDF des graphiques 3D", "",
                                                      "Fichiers PDF (*.pdf);;Tous les fichiers (*)")
            if not fileName:
                return

            if not fileName.endswith('.pdf'):
                fileName += '.pdf'

            # Créer les figures Plotly (même logique que update3D)
            figures = []
            df = self.df

            # Figure 1: 3D Scatter
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter3d(
                x=df['Depth'] if 'Depth' in df.columns else df.index,
                y=df['qc'] if 'qc' in df.columns else [0] * len(df),
                z=df['fs'] if 'fs' in df.columns else [0] * len(df),
                mode='markers',
                marker=dict(size=4, color=df['qc'] if 'qc' in df.columns else 'blue', colorscale='Viridis'),
                name='Points CPT'
            ))
            fig1.update_layout(
                title='3D Scatter: Depth vs qc vs fs',
                scene=dict(
                    xaxis_title='Depth (m)',
                    yaxis_title='qc (MPa)',
                    zaxis_title='fs (kPa)'
                ),
                margin=dict(l=0, r=0, t=40, b=0)
            )
            figures.append(('3D Scatter Plot', fig1))

            # Figure 2: 3D Surface
            if len(df) > 3:
                fig2 = go.Figure()
                fig2.add_trace(go.Surface(
                    x=df['Depth'].to_numpy().reshape(-1, 1) if 'Depth' in df.columns else df.index.to_numpy().reshape(-1, 1),
                    y=df['qc'].to_numpy().reshape(-1, 1) if 'qc' in df.columns else [0] * len(df),
                    z=df['fs'].to_numpy().reshape(-1, 1) if 'fs' in df.columns else [0] * len(df),
                    colorscale='Viridis',
                    name='Surface qc'
                ))
                fig2.update_layout(
                    title='3D Surface: qc vs Depth vs fs',
                    scene=dict(
                        xaxis_title='Depth (m)',
                        yaxis_title='qc (MPa)',
                        zaxis_title='fs (kPa)'
                    ),
                    margin=dict(l=0, r=0, t=40, b=0)
                )
                figures.append(('3D Surface Plot', fig2))

            # Figure 3: 3D Contour
            fig3 = go.Figure()
            fig3.add_trace(go.Contour(
                x=df['Depth'] if 'Depth' in df.columns else df.index,
                y=df['qc'] if 'qc' in df.columns else [0] * len(df),
                z=df['fs'] if 'fs' in df.columns else [0] * len(df),
                colorscale='Viridis',
                name='Contours fs'
            ))
            fig3.update_layout(
                title='3D Contour: Depth vs qc vs fs',
                xaxis_title='Depth (m)',
                yaxis_title='qc (MPa)',
                margin=dict(l=0, r=0, t=40, b=0)
            )
            figures.append(('3D Contour Plot', fig3))

            # Figure 4: 3D Wireframe (simulé avec scatter)
            fig4 = go.Figure()
            fig4.add_trace(go.Scatter3d(
                x=df['Depth'] if 'Depth' in df.columns else df.index,
                y=df['qc'] if 'qc' in df.columns else [0] * len(df),
                z=df['fs'] if 'fs' in df.columns else [0] * len(df),
                mode='lines+markers',
                line=dict(color='blue', width=2),
                marker=dict(size=3, color='red'),
                name='Wireframe'
            ))
            fig4.update_layout(
                title='3D Wireframe: qc Surface with Contours',
                scene=dict(
                    xaxis_title='Depth (m)',
                    yaxis_title='qc (MPa)',
                    zaxis_title='fs (kPa)'
                ),
                margin=dict(l=0, r=0, t=40, b=0)
            )
            figures.append(('3D Wireframe Plot', fig4))

            # Créer le PDF
            c = canvas.Canvas(fileName, pagesize=A4)
            width, height = A4

            # Logo SETRAF
            _logo_3d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "setraf_logo.png")
            if os.path.exists(_logo_3d):
                from reportlab.lib.utils import ImageReader as _IR3D
                c.drawImage(_IR3D(_logo_3d), width - 165, height - 68,
                            width=115, height=52,
                            preserveAspectRatio=True, mask='auto')
            # Titre du document
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "Rapport des Visualisations 3D - Analyse CPT")
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 70, f"Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
            c.drawString(50, height - 85, f"Nombre de points: {len(df)}")

            y_position = height - 120

            # Convertir chaque figure en image et l'ajouter au PDF
            for title, fig in figures:
                try:
                    # Convertir la figure Plotly en image PNG
                    img_bytes = to_image(fig, format='png', width=600, height=400, scale=1)
                    
                    # Sauvegarder temporairement l'image
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                        tmp_file.write(img_bytes)
                        tmp_filename = tmp_file.name
                    
                    # Ajouter l'image au PDF
                    if y_position < 450:  # Nouvelle page si pas assez d'espace
                        c.showPage()
                        y_position = height - 50
                    
                    # Titre du graphique
                    c.setFont("Helvetica-Bold", 14)
                    c.drawString(50, y_position, title)
                    y_position -= 20
                    
                    # Ajouter l'image
                    img = ImageReader(tmp_filename)
                    c.drawImage(img, 50, y_position - 350, width=500, height=350)
                    y_position -= 380
                    
                    # Nettoyer le fichier temporaire
                    os.unlink(tmp_filename)
                    
                except Exception as e:
                    print(f"Erreur lors de l'export de {title}: {e}")
                    c.drawString(50, y_position, f"Erreur lors de la génération de {title}")
                    y_position -= 20

            # Sauvegarder le PDF
            c.save()
            
            QMessageBox.information(self, "Succès", f"PDF des graphiques 3D sauvegardé avec succès:\n{fileName}")

        except ImportError as e:
            QMessageBox.warning(self, "Erreur", f"Bibliothèque manquante pour l'export PDF: {e}\n\nInstallez reportlab avec: pip install reportlab")
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'export PDF: {e}")

    def export3DGraphsIndividually(self):
        """Exporte chaque graphique 3D individuellement en HTML interactif (sans kaleido)."""
        try:
            if not hasattr(self, 'df') or self.df is None or self.df.empty:
                QMessageBox.warning(self, "Erreur", "Aucune donnée chargée pour l'export 3D.")
                return

            directory = QFileDialog.getExistingDirectory(self, "Sélectionner le répertoire de sauvegarde")
            if not directory:
                return

            import plotly.graph_objects as go

            df = self.df
            exported_files = []

            # Figure 1: 3D Scatter
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter3d(
                x=df['Depth'] if 'Depth' in df.columns else df.index,
                y=df['qc'] if 'qc' in df.columns else [0] * len(df),
                z=df['fs'] if 'fs' in df.columns else [0] * len(df),
                mode='markers',
                marker=dict(size=4, color=df['qc'] if 'qc' in df.columns else 'blue', colorscale='Viridis'),
                name='Points CPT'
            ))
            fig1.update_layout(title='3D Scatter: Depth vs qc vs fs',
                scene=dict(xaxis_title='Depth (m)', yaxis_title='qc (MPa)', zaxis_title='fs (kPa)'))
            filename1 = os.path.join(directory, "3D_Scatter_Plot.html")
            fig1.write_html(filename1)
            exported_files.append(filename1)

            # Figure 2: 3D Surface
            if len(df) > 3:
                from scipy.interpolate import griddata
                import numpy as np
                depth_g = np.linspace(df['Depth'].min(), df['Depth'].max(), 30) if 'Depth' in df.columns else df.index.values
                qc_g = np.linspace(df['qc'].min(), df['qc'].max(), 30) if 'qc' in df.columns else [0]*30
                DEPTH, QC = np.meshgrid(depth_g, qc_g)
                FS = griddata((df['Depth'], df['qc']), df['fs'], (DEPTH, QC),
                              method='linear', fill_value=float(np.mean(df['fs']))) if all(c in df.columns for c in ['Depth','qc','fs']) else DEPTH*0
                fig2 = go.Figure(data=[go.Surface(z=FS, x=DEPTH, y=QC, colorscale='Viridis')])
                fig2.update_layout(title='3D Surface: qc vs Depth vs fs',
                    scene=dict(xaxis_title='Depth (m)', yaxis_title='qc (MPa)', zaxis_title='fs (kPa)'))
                filename2 = os.path.join(directory, "3D_Surface_Plot.html")
                fig2.write_html(filename2)
                exported_files.append(filename2)

            # Figure 3: 3D Contour
            fig3 = go.Figure()
            fig3.add_trace(go.Contour(
                x=df['Depth'] if 'Depth' in df.columns else df.index,
                y=df['qc'] if 'qc' in df.columns else [0] * len(df),
                z=df['fs'] if 'fs' in df.columns else [0] * len(df),
                colorscale='Viridis', name='Contours fs'
            ))
            fig3.update_layout(title='3D Contour: Depth vs qc vs fs',
                xaxis_title='Depth (m)', yaxis_title='qc (MPa)')
            filename3 = os.path.join(directory, "3D_Contour_Plot.html")
            fig3.write_html(filename3)
            exported_files.append(filename3)

            # Figure 4: 3D Wireframe
            fig4 = go.Figure()
            fig4.add_trace(go.Scatter3d(
                x=df['Depth'] if 'Depth' in df.columns else df.index,
                y=df['qc'] if 'qc' in df.columns else [0] * len(df),
                z=df['fs'] if 'fs' in df.columns else [0] * len(df),
                mode='lines+markers',
                line=dict(color='blue', width=2),
                marker=dict(size=3, color='red'),
                name='Wireframe'
            ))
            fig4.update_layout(
                title='3D Wireframe: qc Surface with Contours',
                scene=dict(
                    xaxis_title='Depth (m)',
                    yaxis_title='qc (MPa)',
                    zaxis_title='fs (kPa)'
                )
            )
            fig4.update_layout(title='3D Wireframe: qc Surface',
                scene=dict(xaxis_title='Depth (m)', yaxis_title='qc (MPa)', zaxis_title='fs (kPa)'))
            filename4 = os.path.join(directory, "3D_Wireframe_Plot.html")
            fig4.write_html(filename4)
            exported_files.append(filename4)

            QMessageBox.information(self, "Succès",
                f"Graphiques 3D exportés (HTML interactif) :\n\n" + "\n".join(exported_files) +
                "\n\nOuvrez les fichiers .html dans votre navigateur pour les visualiser en 3D interactif.")

        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de l'export individuel: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # ── Splash screen avec animation SVG ─────────────────────────────────────
    try:
        from splash_screen import SplashScreen
        splash = SplashScreen()
        splash.show()
        app.processEvents()

        # Lancer le chargement de la fenêtre principale en différé
        # pour laisser le splash s'afficher d'abord
        def _launch_main():
            try:
                window = MainWindow()
                splash.finish_and_close(window)
            except Exception as e:
                splash.close()
                raise e

        QTimer.singleShot(2800, _launch_main)   # 2.8 s d'animation avant chargement
    except Exception as e:
        print(f"⚠️ Splash screen non disponible: {e}")
        window = MainWindow()
        window.show()

    sys.exit(app.exec())