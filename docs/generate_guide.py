# -*- coding: utf-8 -*-
"""
CPT Analysis Studio — Générateur du Guide Utilisateur PDF
Exécuter : python\python.exe docs\generate_guide.py
Produit   : docs\CPT_Analysis_Studio_Guide_Utilisateur_v1.pdf
"""

import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python', 'Lib', 'site-packages'))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas

# ── Palette ──────────────────────────────────────────────────────────────────
BG          = HexColor("#16140e")
ORANGE_D    = HexColor("#C1550F")
ORANGE_M    = HexColor("#DA701C")
ORANGE_L    = HexColor("#F59B3A")
CREAM       = HexColor("#F0E1C3")
DARK_PANEL  = HexColor("#1e1b10")
DARK_CARD   = HexColor("#252014")
GREY_TEXT   = HexColor("#c8b89a")
WHITE       = HexColor("#ffffff")

W, H = A4

OUT = os.path.join(os.path.dirname(__file__), "CPT_Analysis_Studio_Guide_Utilisateur_v1.pdf")


# ══════════════════════════════════════════════════════════════════════════════
# Custom flowables
# ══════════════════════════════════════════════════════════════════════════════

class ColorBox(Flowable):
    """Colored background box with title + body text."""
    def __init__(self, title, body, bg=DARK_CARD, title_color=ORANGE_L,
                 body_color=CREAM, width=None, padding=10):
        super().__init__()
        self._title      = title
        self._body       = body
        self._bg         = bg
        self._tc         = title_color
        self._bc         = body_color
        self._width      = width or (W - 4*cm)
        self._padding    = padding

    def wrap(self, availWidth, availHeight):
        self.width = self._width
        lines = self._body.count('\n') + 1
        self.height = 14 + lines * 13 + 2 * self._padding + 6
        return self.width, self.height

    def draw(self):
        c = self.canv
        p = self._padding
        c.setFillColor(self._bg)
        c.roundRect(0, 0, self.width, self.height, 6, fill=1, stroke=0)
        # title
        c.setFillColor(self._tc)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(p, self.height - p - 11, self._title)
        # separator line
        c.setStrokeColor(self._tc)
        c.setLineWidth(0.5)
        c.line(p, self.height - p - 16, self.width - p, self.height - p - 16)
        # body
        c.setFillColor(self._bc)
        c.setFont("Helvetica", 9)
        y = self.height - p - 30
        for line in self._body.split('\n'):
            c.drawString(p + 4, y, line)
            y -= 13


class SectionHeader(Flowable):
    """Full-width section header bar."""
    def __init__(self, number, title, width=None):
        super().__init__()
        self._num   = number
        self._title = title
        self._width = width or (W - 4*cm)

    def wrap(self, aw, ah):
        self.width  = self._width
        self.height = 28
        return self.width, self.height

    def draw(self):
        c = self.canv
        # background gradient simulation — two rectangles
        c.setFillColor(ORANGE_D)
        c.rect(0, 0, 36, self.height, fill=1, stroke=0)
        c.setFillColor(DARK_CARD)
        c.rect(36, 0, self.width - 36, self.height, fill=1, stroke=0)
        # number
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(18, 7, str(self._num))
        # title
        c.setFillColor(ORANGE_L)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(44, 8, self._title)


# ══════════════════════════════════════════════════════════════════════════════
# Page templates (header/footer)
# ══════════════════════════════════════════════════════════════════════════════

def cover_page(c: canvas.Canvas, doc):
    """Render the full cover page."""
    c.saveState()
    # Dark background
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # Orange accent strip — left
    c.setFillColor(ORANGE_D)
    c.rect(0, 0, 12, H, fill=1, stroke=0)

    # Orange accent strip — top
    c.setFillColor(ORANGE_M)
    c.rect(0, H - 10, W, 10, fill=1, stroke=0)

    # ── Large RISKIA wordmark ──
    c.setFillColor(ORANGE_L)
    c.setFont("Helvetica-Bold", 64)
    c.drawCentredString(W/2, H - 120, "RISKIA")

    # Sub-brand
    c.setFillColor(CREAM)
    c.setFont("Helvetica", 16)
    c.drawCentredString(W/2, H - 150, "Ingénierie Géotechnique & Analyse des Données")

    # Divider
    c.setStrokeColor(ORANGE_M)
    c.setLineWidth(1.5)
    c.line(3*cm, H - 170, W - 3*cm, H - 170)

    # ── Product name ──
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(W/2, H - 215, "CPT Analysis Studio")

    c.setFillColor(ORANGE_L)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(W/2, H - 242, "Version 1.0")

    # Subtitle
    c.setFillColor(GREY_TEXT)
    c.setFont("Helvetica", 13)
    c.drawCentredString(W/2, H - 270, "Guide Utilisateur & Documentation Technique")

    # ── Decorative CPT schematic ──
    draw_cpt_schematic(c, W/2, H/2 - 20, scale=1.0)

    # ── Bottom info box ──
    c.setFillColor(DARK_CARD)
    c.roundRect(2*cm, 2.5*cm, W - 4*cm, 3.5*cm, 8, fill=1, stroke=0)
    c.setStrokeColor(ORANGE_M)
    c.setLineWidth(0.8)
    c.roundRect(2*cm, 2.5*cm, W - 4*cm, 3.5*cm, 8, fill=0, stroke=1)

    c.setFillColor(ORANGE_L)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(W/2, 5.4*cm, "Logiciel de bureau portable pour Windows")

    c.setFillColor(GREY_TEXT)
    c.setFont("Helvetica", 9)
    c.drawCentredString(W/2, 4.8*cm,
        "Classification Robertson 1990  •  3D Interactif  •  IA Mistral intégrée  •  Export PDF/Excel")
    c.drawCentredString(W/2, 4.2*cm,
        "Analyse CPTU mono & multi-forage  •  Contours 3D  •  Nuage de points  •  Animation SVG")
    c.drawCentredString(W/2, 3.5*cm, "© 2025 RISKIA — Tous droits réservés")

    c.restoreState()


def draw_cpt_schematic(c: canvas.Canvas, cx, cy, scale=1.0):
    """Decorative CPT cone schematic diagram."""
    s = scale
    c.saveState()
    c.translate(cx, cy)

    # Borehole tube
    c.setFillColor(DARK_PANEL)
    c.setStrokeColor(ORANGE_D)
    c.setLineWidth(1.5 * s)
    c.rect(-12*s, -80*s, 24*s, 160*s, fill=1, stroke=1)

    # Cone tip
    from reportlab.graphics.shapes import Polygon
    c.setFillColor(ORANGE_M)
    c.beginPath()
    c.moveTo(-12*s, -80*s)
    c.lineTo(12*s, -80*s)
    c.lineTo(0, -110*s)
    c.closePath()
    c.fill()

    # Depth measurement lines
    c.setStrokeColor(ORANGE_L)
    c.setLineWidth(0.6 * s)
    for i in range(5):
        y = -60*s + i * 30*s
        c.line(-24*s, y, 24*s, y)

    # Arrows indicating penetration
    c.setStrokeColor(CREAM)
    c.setLineWidth(1.2 * s)
    for x_off in [-40*s, 40*s]:
        c.line(x_off, 30*s, x_off, -20*s)
        c.line(x_off, -20*s, x_off - 6*s, -8*s)
        c.line(x_off, -20*s, x_off + 6*s, -8*s)

    # Labels
    c.setFillColor(GREY_TEXT)
    c.setFont("Helvetica", 7 * s)
    c.drawString(28*s, 60*s,  "qc")
    c.drawString(28*s, 30*s,  "fs")
    c.drawString(28*s, 0,     "u2")
    c.drawString(28*s, -30*s, "Rf")

    c.restoreState()


def normal_page(c: canvas.Canvas, doc):
    """Header/footer for normal pages."""
    c.saveState()
    # Background
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    # Left accent
    c.setFillColor(ORANGE_D)
    c.rect(0, 0, 6, H, fill=1, stroke=0)
    # Top header bar
    c.setFillColor(DARK_CARD)
    c.rect(6, H - 32, W - 6, 32, fill=1, stroke=0)
    c.setFillColor(ORANGE_L)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(18, H - 20, "CPT Analysis Studio v1.0")
    c.setFillColor(GREY_TEXT)
    c.setFont("Helvetica", 9)
    c.drawRightString(W - 1*cm, H - 20, "Guide Utilisateur")
    # Footer
    c.setFillColor(DARK_PANEL)
    c.rect(6, 0, W - 6, 22, fill=1, stroke=0)
    c.setFillColor(GREY_TEXT)
    c.setFont("Helvetica", 8)
    c.drawCentredString(W/2, 7, f"Page {doc.page}")
    c.setFillColor(ORANGE_D)
    c.drawString(18, 7, "RISKIA")
    c.restoreState()


# ══════════════════════════════════════════════════════════════════════════════
# Style helpers
# ══════════════════════════════════════════════════════════════════════════════

def make_styles():
    base = getSampleStyleSheet()

    def s(name, **kw):
        return ParagraphStyle(name, **kw)

    h1 = s("H1Guide",
            fontName="Helvetica-Bold", fontSize=18,
            textColor=ORANGE_L, spaceAfter=6, spaceBefore=4,
            alignment=TA_LEFT, backColor=None)

    h2 = s("H2Guide",
            fontName="Helvetica-Bold", fontSize=13,
            textColor=ORANGE_M, spaceAfter=4, spaceBefore=8,
            alignment=TA_LEFT)

    h3 = s("H3Guide",
            fontName="Helvetica-Bold", fontSize=10,
            textColor=CREAM, spaceAfter=3, spaceBefore=6,
            alignment=TA_LEFT)

    body = s("BodyGuide",
             fontName="Helvetica", fontSize=9.5,
             textColor=GREY_TEXT, leading=14,
             spaceAfter=4, alignment=TA_JUSTIFY)

    bullet = s("BulletGuide",
               fontName="Helvetica", fontSize=9.5,
               textColor=GREY_TEXT, leading=13,
               spaceAfter=2, leftIndent=14, bulletIndent=4,
               alignment=TA_LEFT)

    code = s("CodeGuide",
             fontName="Courier", fontSize=8.5,
             textColor=ORANGE_L, leading=13,
             spaceAfter=3, leftIndent=10, backColor=DARK_CARD,
             borderPad=4, alignment=TA_LEFT)

    caption = s("CaptionGuide",
                fontName="Helvetica-Oblique", fontSize=8,
                textColor=GREY_TEXT, spaceAfter=6,
                alignment=TA_CENTER)

    intro = s("IntroGuide",
              fontName="Helvetica", fontSize=11,
              textColor=CREAM, leading=16,
              spaceAfter=6, alignment=TA_JUSTIFY)

    return {
        "h1": h1, "h2": h2, "h3": h3,
        "body": body, "bullet": bullet,
        "code": code, "caption": caption, "intro": intro
    }


def P(text, style):
    return Paragraph(text, style)

def SP(n=6):
    return Spacer(1, n)

def HR():
    return HRFlowable(width="100%", thickness=0.5, color=ORANGE_D, spaceAfter=6, spaceBefore=4)


# ══════════════════════════════════════════════════════════════════════════════
# Table of Contents
# ══════════════════════════════════════════════════════════════════════════════

def toc_section(st):
    items = [
        ("1", "Introduction & Plus-value du logiciel", "3"),
        ("2", "Installation & Lancement", "4"),
        ("3", "Format des données CPTU", "5"),
        ("4", "Onglet Données", "6"),
        ("5", "Onglet Contours 3D", "7"),
        ("6", "Onglet Analyse Géotechnique", "8"),
        ("7", "Onglet Graphiques (20)", "10"),
        ("8", "Onglet 3D Interactif", "12"),
        ("9", "Onglet Tableaux", "13"),
        ("10", "Vue d'ensemble", "14"),
        ("11", "Assistant IA Géotechnique", "15"),
        ("12", "Classification Robertson 1990", "17"),
        ("13", "Évaluation du risque de liquéfaction", "18"),
        ("14", "Export PDF & Excel", "19"),
        ("15", "Dépannage & FAQ", "20"),
    ]
    elems = []
    elems.append(P("Table des Matières", st["h1"]))
    elems.append(HR())
    elems.append(SP(4))

    data = []
    for num, title, page in items:
        row = [
            Paragraph(f'<font color="#F59B3A"><b>{num}.</b></font>', st["body"]),
            Paragraph(f'<font color="#c8b89a">{title}</font>', st["body"]),
            Paragraph(f'<font color="#DA701C">{page}</font>', st["body"]),
        ]
        data.append(row)

    tbl = Table(data, colWidths=[1*cm, 12*cm, 1.5*cm])
    tbl.setStyle(TableStyle([
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("TOPPADDING",  (0,0), (-1,-1), 3),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [DARK_PANEL, DARK_CARD]),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    elems.append(tbl)
    return elems


# ══════════════════════════════════════════════════════════════════════════════
# Content sections
# ══════════════════════════════════════════════════════════════════════════════

def sec1(st):
    """Introduction & Plus-value"""
    e = []
    e.append(SectionHeader(1, "Introduction & Plus-value du logiciel"))
    e.append(SP(8))
    e.append(P(
        "CPT Analysis Studio est un logiciel de bureau portable développé par <b>RISKIA</b> "
        "pour l'analyse avancée des données de sondages pressiométriques de type CPTU (Cone "
        "Penetration Test with pore water pressure measurement). Il réunit en un seul outil "
        "la visualisation interactive, la classification automatique des sols, l'évaluation "
        "du risque de liquéfaction et un assistant IA spécialisé.",
        st["intro"]))
    e.append(SP(4))
    e.append(HR())
    e.append(P("Points forts du logiciel :", st["h2"]))

    features = [
        ("🧠 Intelligence Artificielle intégrée",
         "Modèle Mistral kibali (4-bit NF4) embarqué localement — aucune connexion Internet "
         "requise. Répondez à toutes vos questions géotechniques directement dans l'application."),
        ("📊 20 Graphiques automatisés",
         "Profils de résistance qc et frottement fs, diagrammes de Robertson, courbes de "
         "rigidité, cartographies des zones, histogrammes de distribution, etc."),
        ("🌐 Visualisation 3D Interactive",
         "4 vues Plotly 3D (surface, wireframe, scatter, nuage de points dense par couche) "
         "avec rotation libre, zoom, export PNG."),
        ("🗺️ Contours Multi-forages",
         "Compilation de plusieurs fichiers CPTU en une carte de contours 3D — idéal pour "
         "les études de site à plusieurs points d'investigation."),
        ("🎬 Animation SVG",
         "Visualisation animée du profil CPTU : la courbe se trace en temps réel, couche "
         "par couche, avec classification des sols colorée."),
        ("📄 Export professionnel",
         "Génération de rapports PDF avec graphiques haute résolution et exportation Excel "
         "(.xlsx) des données et tableaux récapitulatifs."),
        ("🔬 Classification Robertson 1990",
         "Identification automatique des 9 zones de comportement (SBT) — de l'argile "
         "sensible au gravier dense — à partir du ratio de friction Rf et de qc normalisé."),
        ("💧 Risque de liquéfaction",
         "Calcul du CRR (Cyclic Resistance Ratio) et CSR (Cyclic Stress Ratio) selon les "
         "méthodes normalisées. Détermination automatique des couches à risque."),
        ("🚀 Portable — Zéro installation",
         "Python 3.11 embarqué, toutes dépendances incluses. Double-cliquez sur "
         "launch.bat et travaillez — aucun Python système requis."),
    ]

    for title, desc in features:
        e.append(KeepTogether([
            ColorBox(title, desc, bg=DARK_CARD, title_color=ORANGE_L, body_color=GREY_TEXT,
                     width=W - 4*cm),
            SP(4),
        ]))

    return e


def sec2(st):
    """Installation & Lancement"""
    e = []
    e.append(SectionHeader(2, "Installation & Lancement"))
    e.append(SP(8))
    e.append(P(
        "CPT Analysis Studio est un logiciel <b>100% portable</b>. Aucune installation, "
        "aucun Python système, aucune connexion Internet n'est requise. "
        "Tout est contenu dans le dossier <code>CPT_Analysis_Studio_PORTABLE</code>.",
        st["body"]))
    e.append(SP(6))

    e.append(P("Structure du dossier :", st["h3"]))
    data = [
        ["Dossier / Fichier", "Description"],
        ["launch.bat", "Script de lancement principal — double-clic pour démarrer"],
        ["setup.bat", "Installation initiale des dépendances Python (exécuter une fois)"],
        ["python/", "Python 3.11 portable avec toutes les bibliothèques"],
        ["models/kibali-final-merged/", "Modèle IA Mistral quantifié (4-bit NF4, ~5 Go)"],
        ["app/main.py", "Application principale PySide6"],
        ["app/tools/", "Outils d'analyse (calculateur, recherche, géodésie…)"],
        ["app/core/", "Parseur CPTU et vérification d'intégrité"],
        ["app/visualization/", "Moteurs de rendu Plotly et Matplotlib"],
        ["docs/", "Documentation et guide utilisateur (ce PDF)"],
    ]
    tbl = Table(data, colWidths=[5.5*cm, 10*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), ORANGE_D),
        ("TEXTCOLOR",     (0,0), (-1,0), WHITE),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8.5),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [DARK_PANEL, DARK_CARD]),
        ("TEXTCOLOR",     (0,1), (-1,-1), GREY_TEXT),
        ("GRID",          (0,0), (-1,-1), 0.3, ORANGE_D),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
    ]))
    e.append(tbl)
    e.append(SP(8))

    e.append(P("Procédure de démarrage :", st["h3"]))
    steps = [
        ("Étape 1 — Première utilisation",
         "Double-cliquez sur  setup.bat  pour installer les dépendances Python manquantes.\n"
         "Cette étape n'est nécessaire qu'une seule fois."),
        ("Étape 2 — Lancer l'application",
         "Double-cliquez sur  launch.bat\n"
         "Le chargement du modèle IA prend 30–60 secondes (barre de progression visible)."),
        ("Étape 3 — Charger vos données",
         "Menu  Fichier > Ouvrir  ou glisser-déposer un fichier .txt CPTU.\n"
         "Plusieurs fichiers peuvent être chargés simultanément (fusion automatique)."),
        ("Étape 4 — Analyser",
         "Naviguez entre les onglets : Données, Graphiques, 3D, Analyse, IA…\n"
         "Tous les graphiques se génèrent automatiquement à l'ouverture."),
    ]
    for title, body in steps:
        e.append(KeepTogether([ColorBox(title, body), SP(4)]))

    e.append(SP(4))
    e.append(P("Configuration minimale requise :", st["h3"]))
    e.append(P("• Windows 10 / 11 (64-bit)", st["bullet"]))
    e.append(P("• RAM : 8 Go minimum (16 Go recommandé pour le modèle IA)", st["bullet"]))
    e.append(P("• Espace disque : 12 Go (modèle IA + Python portable)", st["bullet"]))
    e.append(P("• Processeur : Intel/AMD x64 — GPU optionnel (accélère l'IA)", st["bullet"]))
    return e


def sec3(st):
    """Format des données"""
    e = []
    e.append(SectionHeader(3, "Format des données CPTU"))
    e.append(SP(8))
    e.append(P(
        "Le logiciel accepte les fichiers texte (.txt) délimités par tabulations ou virgules, "
        "exportés depuis les appareils de sondage CPTU standards (Fugro, Geomil, Pagani, etc.).",
        st["body"]))
    e.append(SP(6))

    e.append(P("Colonnes reconnues automatiquement :", st["h3"]))
    cols = [
        ["Nom de colonne", "Unité", "Description"],
        ["Depth / depth / Profondeur / profondeur", "m", "Profondeur de pénétration"],
        ["qc / QC / cone_resistance", "MPa", "Résistance en pointe du cône"],
        ["fs / FS / sleeve_friction", "MPa ou kPa", "Frottement latéral unitaire"],
        ["u / u2 / pore_pressure", "kPa", "Pression interstitielle (optionnel)"],
        ["Rf / rf", "%", "Rapport de friction fs/qc × 100 (calculé si absent)"],
        ["Ic / ic", "—", "Indice de comportement Robertson (calculé si absent)"],
    ]
    tbl = Table(cols, colWidths=[5.5*cm, 2.5*cm, 7.5*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), ORANGE_D),
        ("TEXTCOLOR",     (0,0), (-1,0), WHITE),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8.5),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [DARK_PANEL, DARK_CARD]),
        ("TEXTCOLOR",     (0,1), (-1,-1), GREY_TEXT),
        ("GRID",          (0,0), (-1,-1), 0.3, ORANGE_D),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
    ]))
    e.append(tbl)
    e.append(SP(8))

    e.append(P("Exemple de fichier valide :", st["h3"]))
    e.append(P(
        "Depth\tqc\tfs\tu2\n"
        "0.00\t0.00\t0.000\t0.0\n"
        "0.02\t0.42\t0.008\t10.2\n"
        "0.04\t0.85\t0.012\t15.4\n"
        "0.06\t1.23\t0.018\t18.1\n"
        "...",
        st["code"]))
    e.append(SP(4))

    e.append(ColorBox(
        "Détection automatique des unités",
        "Le logiciel détecte automatiquement si les profondeurs sont en cm ou en m\n"
        "selon l'ordre de grandeur des valeurs (seuil : max > 50 → supposé en cm).\n"
        "Toutes les profondeurs sont converties et affichées en mètres (m).",
        bg=DARK_CARD, title_color=ORANGE_L))
    e.append(SP(4))
    e.append(ColorBox(
        "Fusion multi-forages",
        "Plusieurs fichiers CPTU peuvent être chargés simultanément via\n"
        "Fichier > Ouvrir (sélection multiple). Le logiciel les fusionne\n"
        "automatiquement pour les vues Contours 3D.",
        bg=DARK_CARD, title_color=ORANGE_M))
    return e


def sec4(st):
    """Onglet Données"""
    e = []
    e.append(SectionHeader(4, "Onglet Données"))
    e.append(SP(8))
    e.append(P(
        "L'onglet <b>Données</b> est le point d'entrée principal. Il affiche le tableau "
        "brut de toutes les mesures CPTU et une animation SVG du profil.",
        st["body"]))
    e.append(SP(6))

    e.append(P("Panneau gauche — Tableau de données :", st["h3"]))
    e.append(P("• Toutes les colonnes du fichier importé (Depth, qc, fs, u2, Rf, Ic…)", st["bullet"]))
    e.append(P("• Lignes colorées selon la classification Robertson (zones 1–9)", st["bullet"]))
    e.append(P("• Tri par colonne, défilement fluide", st["bullet"]))
    e.append(P("• Résumé statistique : min, max, moyenne, écart-type", st["bullet"]))
    e.append(SP(4))

    e.append(P("Panneau droit — Animation SVG :", st["h3"]))
    e.append(P("• Profil animé qc vs profondeur qui se trace progressivement", st["bullet"]))
    e.append(P("• Couches géologiques identifiées colorées en temps réel", st["bullet"]))
    e.append(P("• Étiquettes Robertson (ex: « Sable propre dense »)", st["bullet"]))
    e.append(P("• Bouton <b>« Sauvegarder SVG »</b> : export du graphique animé (.svg)", st["bullet"]))
    e.append(SP(4))

    e.append(ColorBox(
        "Astuce — Export SVG",
        "Le fichier SVG exporté est autonome et s'ouvre dans tout navigateur web.\n"
        "L'animation se rejoue à chaque ouverture. Idéal pour les présentations\n"
        "et rapports interactifs.",
        bg=DARK_CARD, title_color=ORANGE_L))
    return e


def sec5(st):
    """Contours 3D"""
    e = []
    e.append(SectionHeader(5, "Onglet Contours 3D"))
    e.append(SP(8))
    e.append(P(
        "L'onglet <b>Contours 3D</b> génère une carte de contours stratigraphiques "
        "à partir de plusieurs sondages CPTU chargés simultanément. C'est l'outil "
        "privilégié pour les études de site multi-points.",
        st["body"]))
    e.append(SP(6))

    e.append(P("Fonctionnalités :", st["h3"]))
    e.append(P("• Un sous-graphe par fichier CPTU chargé", st["bullet"]))
    e.append(P("• Contours de résistance de pointe qc (MPa) en profondeur", st["bullet"]))
    e.append(P("• Palette de couleurs adaptée (cold-warm) sur fond sombre", st["bullet"]))
    e.append(P("• Axe Y : Profondeur en mètres (inverti, surface en haut)", st["bullet"]))
    e.append(P("• Interaction Plotly : zoom, panoramique, export PNG haute résolution", st["bullet"]))
    e.append(SP(6))

    e.append(P("Utilisation recommandée :", st["h3"]))
    steps = [
        "Charger ≥ 2 fichiers CPTU via Fichier > Ouvrir (sélection multiple)",
        "Naviguer vers l'onglet Contours 3D",
        "Les contours se génèrent automatiquement",
        "Survol avec la souris : valeurs qc précises à chaque profondeur",
        "Clic-droit > Save image pour exporter en PNG",
    ]
    for i, s_ in enumerate(steps, 1):
        e.append(P(f"<b>{i}.</b>  {s_}", st["bullet"]))

    e.append(SP(6))
    e.append(ColorBox(
        "Interprétation des contours",
        "Zones bleues froides  →  sol mou (argile, limon)  →  qc faible\n"
        "Zones rouges chaudes →  sol dense (sable, gravier) →  qc élevé\n"
        "Les discontinuités horizontales indiquent des changements de couche.",
        bg=DARK_CARD, title_color=ORANGE_L))
    return e


def sec6(st):
    """Analyse Géotechnique"""
    e = []
    e.append(SectionHeader(6, "Onglet Analyse Géotechnique"))
    e.append(SP(8))
    e.append(P(
        "L'onglet <b>Analyse</b> combine un rapport textuel automatique avec un nuage "
        "de points 3D dense représentant la distribution spatiale des propriétés du sol.",
        st["body"]))
    e.append(SP(6))

    e.append(P("Panneau supérieur — Rapport textuel :", st["h3"]))
    e.append(P("• Classification automatique des couches (Robertson 1990)", st["bullet"]))
    e.append(P("• Profondeur, épaisseur et type de sol pour chaque couche", st["bullet"]))
    e.append(P("• Valeurs moyennes qc, fs, Ic, Rf par couche", st["bullet"]))
    e.append(P("• Score de risque de liquéfaction par couche (CRR/CSR)", st["bullet"]))
    e.append(P("• Recommandations géotechniques (fondations, amélioration, drainage)", st["bullet"]))
    e.append(SP(6))

    e.append(P("Panneau inférieur — Nuage de points 3D :", st["h3"]))
    e.append(P("• ~600 points par mètre, distribués radialement par couche de sol", st["bullet"]))
    e.append(P("• Rayon proportionnel à qc : argile → nuage fin, sable → nuage large", st["bullet"]))
    e.append(P("• Plans de limite de couche (surfaces Mesh3d semi-transparentes)", st["bullet"]))
    e.append(P("• Axe du forage visible, profils qc sur XZ, fs sur YZ", st["bullet"]))
    e.append(P("• Étiquettes de couche flottantes en 3D", st["bullet"]))
    e.append(P("• Interaction complète : rotation, zoom, survol avec valeurs", st["bullet"]))
    e.append(SP(6))

    e.append(ColorBox(
        "Comment lire le nuage de points",
        "Chaque couche est représentée par une couleur distincte.\n"
        "La dispersion radiale (largeur du cylindre) traduit la résistance du sol :\n"
        "  • Cylindre étroit  →  sol cohésif, argile (faible qc)\n"
        "  • Cylindre large   →  sol frottant, sable dense (fort qc)\n"
        "Les plans orange semi-transparents délimitent les interfaces de couches.",
        bg=DARK_CARD, title_color=ORANGE_L))
    return e


def sec7(st):
    """Graphiques (20)"""
    e = []
    e.append(SectionHeader(7, "Onglet Graphiques (20)"))
    e.append(SP(8))
    e.append(P(
        "L'onglet <b>Graphiques</b> réunit 20 visualisations Matplotlib couvrant "
        "l'ensemble des aspects de l'interprétation CPTU.",
        st["body"]))
    e.append(SP(6))

    graphs = [
        ("G01", "Profil qc vs Profondeur", "Résistance de pointe brute, bande de confiance ±σ"),
        ("G02", "Profil fs vs Profondeur", "Frottement latéral sur toute la hauteur"),
        ("G03", "Profil u2 vs Profondeur", "Pression interstitielle, ligne u0 hydrostatique"),
        ("G04", "Rapport de friction Rf", "Rf = fs/qc × 100 (%), profil complet"),
        ("G05", "Indice de comportement Ic", "Ic Robertson, zones < 2.6 (granulaires) délimitées"),
        ("G06", "Diagramme Robertson qc–Rf", "Nuage de points, 9 zones colorées, ellipses"),
        ("G07", "Diagramme Robertson normalisé", "Qt1 vs Fr, classification normalisée"),
        ("G08", "qc moyenné par couche", "Valeurs moyennes par horizon géologique"),
        ("G09", "fs moyenné par couche", "Variation du frottement par couche"),
        ("G10", "Profil de rigidité G0", "Module élastique initial estimé"),
        ("G11", "Histogramme qc", "Distribution statistique, courbe normale ajustée"),
        ("G12", "Histogramme fs", "Distribution du frottement, percentiles"),
        ("G13", "Profil CSR vs CRR", "Cyclic Stress Ratio vs Cyclic Resistance Ratio"),
        ("G14", "Évaluation liquéfaction", "FS = CRR/CSR par couche, seuil FS < 1.0"),
        ("G15", "qc vs fs (scatter)", "Corrélation résistance pointe / frottement"),
        ("G16", "Profil Bq", "Rapport de pression interstitielle normalisé"),
        ("G17", "Densité de probabilité Ic", "KDE de l'indice de comportement"),
        ("G18", "Profil de perméabilité estimée", "k estimé selon Robertson & Cabal 2015"),
        ("G19", "Rapport qc/σv0'", "Normalisation par contrainte effective"),
        ("G20", "Récapitulatif multi-paramètres", "Sous-graphes juxtaposés qc / fs / u2 / Rf"),
    ]

    data = [["#", "Titre", "Description"]]
    for gid, gtitle, gdesc in graphs:
        data.append([gid, gtitle, gdesc])

    tbl = Table(data, colWidths=[1.2*cm, 5.5*cm, 9*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), ORANGE_D),
        ("TEXTCOLOR",     (0,0), (-1,0), WHITE),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [DARK_PANEL, DARK_CARD]),
        ("TEXTCOLOR",     (0,1), (-1,-1), GREY_TEXT),
        ("TEXTCOLOR",     (0,1), (0,-1), ORANGE_M),
        ("FONTNAME",      (0,1), (0,-1), "Helvetica-Bold"),
        ("GRID",          (0,0), (-1,-1), 0.3, ORANGE_D),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
    ]))
    e.append(tbl)
    e.append(SP(6))
    e.append(ColorBox(
        "Navigation dans les graphiques",
        "Utilisez la barre de défilement ou la molette de la souris pour parcourir les\n"
        "20 graphiques. Chaque graphique est interactif (zoom, export PNG via clic-droit).",
        bg=DARK_CARD, title_color=ORANGE_M))
    return e


def sec8(st):
    """3D Interactif"""
    e = []
    e.append(SectionHeader(8, "Onglet 3D Interactif"))
    e.append(SP(8))
    e.append(P(
        "L'onglet <b>3D Interactif</b> propose quatre vues tridimensionnelles générées "
        "avec Plotly, permettant l'exploration spatiale du profil CPTU depuis tous les angles.",
        st["body"]))
    e.append(SP(6))

    views = [
        ("Surface 3D lissée",
         "Surface qc interpolée, palette de couleurs Plasma.\n"
         "Visualisation continue des variations de résistance en 3D."),
        ("Wireframe 3D",
         "Grille filaire (lignes uniquement) de la surface qc.\n"
         "Permet de voir la structure interne sans occlusion."),
        ("Scatter 3D",
         "Nuage de points bruts (x=qc, y=fs, z=profondeur).\n"
         "Coloré par Ic — robuste aux données irregulières."),
        ("Nuage de points dense par couche",
         "Distribution cylindrique gaussienne par horizon.\n"
         "Représentation la plus réaliste de la stratigraphie 3D."),
    ]
    for title, desc in views:
        e.append(KeepTogether([
            ColorBox(title, desc, bg=DARK_CARD, title_color=ORANGE_L),
            SP(4),
        ]))

    e.append(SP(4))
    e.append(P("Interactions disponibles :", st["h3"]))
    e.append(P("• Rotation 3D libre par clic-glisser", st["bullet"]))
    e.append(P("• Zoom avec la molette de la souris", st["bullet"]))
    e.append(P("• Double-clic pour réinitialiser la vue", st["bullet"]))
    e.append(P("• Survol pour afficher les valeurs exactes (tooltip)", st["bullet"]))
    e.append(P("• Barre d'outils Plotly : export PNG, box select, lasso select", st["bullet"]))
    e.append(P("• Clic sur la légende pour masquer/afficher des couches", st["bullet"]))
    return e


def sec9(st):
    """Tableaux"""
    e = []
    e.append(SectionHeader(9, "Onglet Tableaux"))
    e.append(SP(8))
    e.append(P(
        "L'onglet <b>Tableaux</b> centralise les résultats calculés et les outils "
        "d'exportation. Il comprend un tableau récapitulatif, une animation SVG dédiée "
        "et les boutons d'export PDF et Excel.",
        st["body"]))
    e.append(SP(6))

    e.append(P("Tableau récapitulatif :", st["h3"]))
    e.append(P("• Une ligne par couche géologique identifiée", st["bullet"]))
    e.append(P("• Colonnes : profondeur, épaisseur, type SBT, qc moy., fs moy., Rf, Ic", st["bullet"]))
    e.append(P("• Score de liquéfaction FS par couche", st["bullet"]))
    e.append(P("• Recommandation géotechnique synthétique", st["bullet"]))
    e.append(SP(4))

    e.append(P("Animation SVG :", st["h3"]))
    e.append(P("• Identique à celle de l'onglet Données mais dans le contexte Tableaux", st["bullet"]))
    e.append(P("• Bouton « Sauvegarder SVG » pour exporter", st["bullet"]))
    e.append(SP(4))

    e.append(P("Export PDF :", st["h3"]))
    e.append(P("• Génère un rapport PDF professionnel avec :", st["bullet"]))
    e.append(P("  – Page de titre avec métadonnées du sondage", st["bullet"]))
    e.append(P("  – Graphique PNG haute résolution (300 dpi) intégré", st["bullet"]))
    e.append(P("  – Tableau récapitulatif des couches", st["bullet"]))
    e.append(P("  – Date, nom du fichier, statistiques globales", st["bullet"]))
    e.append(SP(4))

    e.append(P("Export Excel :", st["h3"]))
    e.append(P("• Fichier .xlsx avec deux feuilles : Données brutes + Récapitulatif couches", st["bullet"]))
    e.append(P("• En-têtes formatés, unités dans la première ligne", st["bullet"]))
    return e


def sec10(st):
    """Vue d'ensemble"""
    e = []
    e.append(SectionHeader(10, "Vue d'ensemble"))
    e.append(SP(8))
    e.append(P(
        "L'onglet <b>Vue d'ensemble</b> combine les visualisations clés sur une seule page "
        "pour offrir une lecture rapide et globale du profil CPTU.",
        st["body"]))
    e.append(SP(6))
    e.append(P("Cette vue juxtapose :", st["h3"]))
    e.append(P("• Profils qc et fs côte à côte (comparaison directe)", st["bullet"]))
    e.append(P("• Diagramme Robertson (nuage qc–Rf avec zones colorées)", st["bullet"]))
    e.append(P("• Colonnes stratigraphiques simplifiées", st["bullet"]))
    e.append(P("• Indicateurs visuels liquéfaction (barres rouges = risque élevé)", st["bullet"]))
    e.append(SP(6))
    e.append(ColorBox(
        "Usage conseillé",
        "La Vue d'ensemble est idéale pour une première interprétation rapide.\n"
        "Importez vos données, passez directement à cet onglet pour une lecture\n"
        "globale, puis affinez l'analyse dans les onglets spécialisés.",
        bg=DARK_CARD, title_color=ORANGE_M))
    return e


def sec11(st):
    """Assistant IA"""
    e = []
    e.append(SectionHeader(11, "Assistant IA Géotechnique"))
    e.append(SP(8))
    e.append(P(
        "CPT Analysis Studio intègre un assistant IA spécialisé en géotechnique basé sur "
        "<b>Mistral kibali</b>, un modèle de langage quantifié (4-bit NF4) fonctionnant "
        "<b>100% localement</b> — aucune donnée n'est envoyée sur Internet.",
        st["intro"]))
    e.append(SP(6))

    e.append(P("Capacités de l'assistant :", st["h3"]))
    e.append(P("• Analyse et interprétation des données CPTU chargées", st["bullet"]))
    e.append(P("• Réponses aux questions géotechniques générales", st["bullet"]))
    e.append(P("• Explication de la classification Robertson (zones SBT)", st["bullet"]))
    e.append(P("• Aide à l'interprétation des profils de résistance", st["bullet"]))
    e.append(P("• Recommandations fondations, améliorations de sol", st["bullet"]))
    e.append(P("• Questions sur la liquéfaction sismique", st["bullet"]))
    e.append(P("• Soutien pédagogique et explications des méthodes", st["bullet"]))
    e.append(SP(6))

    e.append(P("Utilisation du chat IA :", st["h3"]))
    e.append(P("1. Chargez vos données CPTU", st["bullet"]))
    e.append(P("2. Cliquez sur le panneau Chat IA (panneau latéral droit)", st["bullet"]))
    e.append(P("3. Tapez votre question dans la zone de saisie et appuyez Entrée", st["bullet"]))
    e.append(P("4. L'IA répond avec le contexte de vos données actuelles", st["bullet"]))
    e.append(SP(6))

    e.append(P("Exemples de questions :", st["h3"]))
    questions = [
        "« Quelle est la nature du sol entre 5 et 10 mètres de profondeur ? »",
        "« Y a-t-il un risque de liquéfaction sur ce site ? »",
        "« Quelle fondation recommandes-tu pour une charge de 500 kN ? »",
        "« Explique la zone Robertson 5 avec mes valeurs qc actuelles. »",
        "« Calcule la résistance de base d'un pieu de 40 cm à 15 m. »",
    ]
    for q in questions:
        e.append(P(f"• {q}", st["bullet"]))

    e.append(SP(6))
    e.append(ColorBox(
        "Modèle IA — Mistral kibali (4-bit NF4)",
        "Famille : Mistral 7B  •  Quantification : 4 bits NF4 (bitsandbytes)\n"
        "Taille : ~4.5 Go  •  Inférence CPU/GPU  •  Latence : 2–15 s/réponse\n"
        "Entraîné sur corpus géotechnique français et anglais.\n"
        "Fonctionne hors ligne — vos données restent confidentielles.",
        bg=DARK_CARD, title_color=ORANGE_L))
    return e


def sec12(st):
    """Robertson 1990"""
    e = []
    e.append(SectionHeader(12, "Classification Robertson 1990"))
    e.append(SP(8))
    e.append(P(
        "La classification Robertson (1990) est la méthode de référence mondiale pour "
        "l'identification des types de comportement du sol (SBT — Soil Behaviour Type) "
        "à partir des données CPTU. Elle définit 9 zones dans le diagramme qc–Rf.",
        st["body"]))
    e.append(SP(6))

    zones = [
        ["Zone", "Type de sol", "Rf (%)", "qc (MPa)", "Ic"],
        ["1", "Sol fins sensibles / organique", "< 1.0", "< 0.2", "> 3.6"],
        ["2", "Sol organique — tourbe", "< 2.0", "< 0.5", "> 3.22"],
        ["3", "Argile — argile silteuse", "1–4", "< 1.0", "2.82–3.22"],
        ["4", "Limon argileux — argile silteuse", "2–5", "0.5–2.0", "2.54–2.82"],
        ["5", "Limon sableux — sable fin", "1.5–4.5", "1.0–6.0", "2.05–2.54"],
        ["6", "Sable propre à sableux", "0.5–2.0", "5.0–20", "1.31–2.05"],
        ["7", "Sable graveleux dense", "< 1.0", "> 15", "< 1.31"],
        ["8", "Sable très dense / ciment léger", "< 0.5", "> 20", "N/A"],
        ["9", "Sol très dur / cimenté", "< 1.0", "> 25", "N/A"],
    ]

    tbl = Table(zones, colWidths=[1.2*cm, 5.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), ORANGE_D),
        ("TEXTCOLOR",     (0,0), (-1,0), WHITE),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8.5),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [DARK_PANEL, DARK_CARD]),
        ("TEXTCOLOR",     (0,1), (-1,-1), GREY_TEXT),
        ("TEXTCOLOR",     (0,1), (0,-1), ORANGE_M),
        ("FONTNAME",      (0,1), (0,-1), "Helvetica-Bold"),
        ("GRID",          (0,0), (-1,-1), 0.3, ORANGE_D),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
    ]))
    e.append(tbl)
    e.append(SP(6))
    e.append(P(
        "<b>Rf</b> = fs / qc × 100 (%)  —  le rapport de friction est le premier "
        "discriminant entre sols fins (Rf élevé) et granulaires (Rf faible).<br/>"
        "<b>Ic</b> = √[(3.47 − log Qt1)² + (1.22 + log Fr)²]  —  indice de comportement "
        "de Robertson & Wride (1998). Ic > 2.6 → comportement fin (cohésif).",
        st["body"]))
    return e


def sec13(st):
    """Liquéfaction"""
    e = []
    e.append(SectionHeader(13, "Évaluation du Risque de Liquéfaction"))
    e.append(SP(8))
    e.append(P(
        "La liquéfaction est un phénomène où un sol saturé perd sa résistance sous "
        "chargement cyclique sismique. CPT Analysis Studio implémente la méthode "
        "<b>Robertson & Wride (1998)</b> simplifiée, éprouvée à l'échelle internationale.",
        st["body"]))
    e.append(SP(6))

    e.append(P("Paramètres calculés :", st["h3"]))
    e.append(P(
        "<b>CSR</b> (Cyclic Stress Ratio) = 0.65 × (σv0/σv0') × amax/g × rd",
        st["body"]))
    e.append(P(
        "<b>CRR</b> (Cyclic Resistance Ratio) = f(qc1N) selon la courbe de résistance à la liquéfaction",
        st["body"]))
    e.append(P(
        "<b>FS</b> (Facteur de sécurité) = CRR / CSR",
        st["body"]))
    e.append(SP(6))

    e.append(ColorBox(
        "Interprétation du facteur de sécurité FS",
        "FS < 1.0   →  Risque élevé de liquéfaction  (couche rouge dans graphique G14)\n"
        "FS 1.0–1.3 →  Zone de transition / risque modéré\n"
        "FS > 1.3   →  Stable, liquéfaction improbable\n"
        "\nLe logiciel identifie automatiquement toutes les couches à FS < 1.0.",
        bg=DARK_CARD, title_color=ORANGE_M))
    e.append(SP(6))
    e.append(P(
        "Les couches à risque de liquéfaction sont signalées dans le rapport textuel "
        "(onglet Analyse), le tableau récapitulatif (onglet Tableaux) et le graphique G14.",
        st["body"]))
    return e


def sec14(st):
    """Export PDF & Excel"""
    e = []
    e.append(SectionHeader(14, "Export PDF & Excel"))
    e.append(SP(8))
    e.append(P(
        "CPT Analysis Studio peut générer deux types de fichiers de sortie depuis "
        "l'onglet <b>Tableaux</b> : un rapport PDF clé en main et un tableur Excel.",
        st["body"]))
    e.append(SP(6))

    e.append(P("Rapport PDF :", st["h2"]))
    e.append(P("Le PDF généré inclut :", st["body"]))
    e.append(P("• Page de titre avec nom du sondage, date et statistiques", st["bullet"]))
    e.append(P("• Graphique matplotlib en PNG 300 dpi (profils qc et fs)", st["bullet"]))
    e.append(P("• Tableau des couches avec classification Robertson", st["bullet"]))
    e.append(P("• Résumé de l'évaluation de liquéfaction", st["bullet"]))
    e.append(SP(4))
    e.append(P("Format : A4 paysage, thème sombre, logo RISKIA.", st["body"]))
    e.append(SP(6))

    e.append(P("Export Excel :", st["h2"]))
    e.append(P("• Feuille 1 « Données » : toutes les mesures brutes (Depth, qc, fs, u2…)", st["bullet"]))
    e.append(P("• Feuille 2 « Couches » : récapitulatif par horizon géologique", st["bullet"]))
    e.append(P("• Feuille 3 « Statistiques » : min, max, moyenne, percentiles", st["bullet"]))
    e.append(P("• Mise en forme Excel : en-têtes gras, unités en ligne 2, largeur auto", st["bullet"]))
    return e


def sec15(st):
    """Dépannage"""
    e = []
    e.append(SectionHeader(15, "Dépannage & FAQ"))
    e.append(SP(8))

    faqs = [
        ("L'application ne démarre pas",
         "Vérifiez que setup.bat a été exécuté au moins une fois.\n"
         "Assurez-vous que Python est disponible dans python\\python.exe.\n"
         "Consultez la console pour les messages d'erreur."),
        ("Le modèle IA prend très longtemps à charger",
         "Normal lors du premier lancement (30–120 s selon le matériel).\n"
         "Sur GPU: activer CUDA_VISIBLE_DEVICES dans launch.bat.\n"
         "Sans GPU: CPU seul → réponses plus lentes (5–30 s/requête)."),
        ("Mon fichier CPTU ne se charge pas",
         "Vérifiez que le séparateur est une tabulation ou une virgule.\n"
         "La première ligne doit être un en-tête (noms de colonnes).\n"
         "Les colonnes Depth et qc sont obligatoires."),
        ("Les graphiques 3D s'affichent mal",
         "QWebEngineView requiert un GPU fonctionnel.\n"
         "Mettez à jour les pilotes graphiques.\n"
         "Solution de contournement : export PNG depuis Plotly."),
        ("Erreur 'out of memory' avec le modèle IA",
         "Le modèle nécessite ~6 Go de RAM libre.\n"
         "Fermez les autres applications et relancez.\n"
         "Possibilité de réduire max_new_tokens dans app/main.py."),
        ("Les profondeurs semblent incorrectes",
         "Le logiciel détecte automatiquement cm vs m.\n"
         "Si vos profondeurs sont en cm, elles seront converties.\n"
         "Tous les axes affichent des profondeurs en mètres (m)."),
        ("Comment fusionner plusieurs forages ?",
         "Fichier > Ouvrir → sélectionner plusieurs fichiers .txt\n"
         "Maintenir Ctrl pour sélection multiple.\n"
         "La fusion apparaît dans l'onglet Contours 3D."),
    ]

    for question, answer in faqs:
        e.append(KeepTogether([
            ColorBox(question, answer, bg=DARK_CARD,
                     title_color=ORANGE_L, body_color=GREY_TEXT),
            SP(4),
        ]))

    e.append(SP(8))
    e.append(HR())
    e.append(SP(4))
    e.append(P(
        "Pour toute question non couverte par ce guide, consultez le fichier "
        "<b>README.md</b> dans le dossier d'installation ou contactez l'équipe RISKIA.",
        st["body"]))
    return e


# ══════════════════════════════════════════════════════════════════════════════
# Main builder
# ══════════════════════════════════════════════════════════════════════════════

class PageNumDoc(SimpleDocTemplate):
    def __init__(self, *args, **kwargs):
        self._is_cover = True
        super().__init__(*args, **kwargs)

    def handle_pageBegin(self):
        self._is_cover = (self.page == 1)
        super().handle_pageBegin()

    def afterPage(self):
        if self._is_cover:
            cover_page(self.canv, self)
        else:
            normal_page(self.canv, self)
        self._is_cover = False


def build_pdf():
    doc = PageNumDoc(
        OUT,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
    )

    st = make_styles()

    story = []

    # ── Cover (blank flowable — template draws everything) ──
    story.append(Spacer(1, H))  # push to next page
    story.append(PageBreak())

    # ── Table of Contents ──
    story += toc_section(st)
    story.append(PageBreak())

    # ── Sections ──
    sections = [sec1, sec2, sec3, sec4, sec5, sec6,
                sec7, sec8, sec9, sec10, sec11, sec12, sec13, sec14, sec15]

    for i, sec_fn in enumerate(sections):
        story += sec_fn(st)
        if i < len(sections) - 1:
            story.append(PageBreak())

    doc.build(story)
    print(f"\n✅  PDF généré : {OUT}\n")


if __name__ == "__main__":
    build_pdf()
