# RISKIA - CPT Analysis Studio (Version Portable)

Logiciel d'analyse géotechnique CPTU avec IA intégrée.

## Premier démarrage

**Étape 1 — Installer l'environnement Python + Modèle IA** *(une seule fois)*
```
setup.bat
```
> Copie ~23 Go de données (Python 8.5 Go + modèle IA 14.5 Go). Durée : 10–30 min.

**Étape 2 — Lancer l'application**
```
launch.bat
```

---

## Structure du dossier

```
RISKIA_PORTABLE/
├── launch.bat              ← Lanceur principal
├── setup.bat               ← Installation unique (copie Python + IA)
├── run.py                  ← Script de démarrage Python
├── app/                    ← Code source de l'application
│   ├── main.py             ← Application principale PySide6
│   ├── analysis/           ← Moteur d'analyse géotechnique
│   ├── core/               ← Parseur CPTU + vérification intégrité
│   ├── tools/              ← Outils de calcul
│   ├── utils/              ← Générateur de documents
│   ├── visualization/      ← Graphiques CPT
│   └── requirements.txt    ← Dépendances Python
├── python/                 ← Environnement Python portable (après setup)
└── models/
    └── kibali-final-merged/ ← Modèle IA LLM (après setup)
```

---

## Ce que fait le logiciel

**CPT Analysis Studio** est un logiciel de bureau Windows pour l'analyse géotechnique de sondages CPTU (Cone Penetration Test) :

- **Chargement de fichiers** : `.txt`, `.xlsx`, `.csv`, `.xls`, `.cal`
- **Analyse géotechnique** : classification des couches, zones de sol, résistance de pointe `qc`, frottement `fs`
- **Analyse de liquéfaction** : calcul du facteur de sécurité FS et cartographie des risques
- **Corrélations** : matrice de corrélation entre paramètres CPTU
- **Visualisations 2D/3D** : graphiques interactifs Plotly, profils de sol, cartes 3D
- **Fusion multi-sondages** : comparaison et fusion de plusieurs fichiers CPTU avec coordonnées XY
- **IA géotechnique** : chat interactif basé sur un LLM local (Kibali) pour poser des questions sur les résultats
- **Export PDF** : génération de rapports complets

---

## Démarrage sans setup (mode sans IA)

Si vous ne souhaitez pas copier les 23 Go, vous pouvez lancer directement depuis le répertoire source :
```
C:\Users\Admin\Desktop\RISKIA\RISKIA\riskIA\environment\python.exe app\main.py
```
