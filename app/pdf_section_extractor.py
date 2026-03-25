import fitz  # PyMuPDF
import os
import json
from typing import Dict, List, Tuple

class PDFSectionExtractor:
    """
    Extracteur de sections pour l'étude des dangers
    Basé sur l'analyse du PDF d'étude des dangers
    """

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = None
        self.toc = []
        self.sections = {}

    def open_pdf(self):
        """Ouvrir le PDF"""
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"Le fichier {self.pdf_path} n'existe pas.")

        self.doc = fitz.open(self.pdf_path)
        self.toc = self.doc.get_toc()
        print(f"PDF ouvert: {len(self.doc)} pages")
        print(f"Table des matières: {len(self.toc)} entrées")

    def extract_sections(self) -> Dict[str, Dict]:
        """
        Extraire toutes les sections du PDF
        """
        if self.doc is None:
            raise ValueError("PDF non ouvert. Appelez open_pdf() d'abord.")

        sections = {}

        # Traiter la table des matières
        for i, entry in enumerate(self.toc):
            level, title, page_num = entry
            section_id = f"section_{i+1:03d}"

            # Déterminer les pages de début et fin
            start_page = page_num - 1  # 0-based
            if i + 1 < len(self.toc):
                end_page = self.toc[i + 1][2] - 1
            else:
                end_page = len(self.doc) - 1

            # Extraire le texte de la section
            section_text = self._extract_section_text(start_page, end_page)

            # Classifier le type de section
            section_type = self._classify_section(title, section_text)

            sections[section_id] = {
                'title': title,
                'level': level,
                'start_page': start_page + 1,  # 1-based pour affichage
                'end_page': end_page + 1,
                'type': section_type,
                'content': section_text,
                'word_count': len(section_text.split())
            }

        self.sections = sections
        return sections

    def _extract_section_text(self, start_page: int, end_page: int) -> str:
        """Extraire le texte d'une plage de pages"""
        if self.doc is None:
            return ""

        text = ""
        for page_num in range(start_page, min(end_page + 1, len(self.doc))):
            page = self.doc.load_page(page_num)
            page_text = page.get_text()
            text += f"\n=== PAGE {page_num + 1} ===\n{page_text}\n"

        return text.strip()

    def _classify_section(self, title: str, content: str) -> str:
        """
        Classifier le type de section basé sur le titre et le contenu
        """
        title_lower = title.lower()
        content_lower = content.lower()

        # Classification basée sur les mots-clés
        if any(word in title_lower for word in ['résumé', 'sommaire']):
            return 'resume'
        elif any(word in title_lower for word in ['présentation', 'introduction']):
            return 'presentation'
        elif any(word in title_lower for word in ['environnement', 'caractérisation']):
            return 'environnement'
        elif any(word in title_lower for word in ['danger', 'risque', 'aléa']):
            return 'analyse_risques'
        elif any(word in title_lower for word in ['scénario', 'accident']):
            return 'scenarios'
        elif any(word in title_lower for word in ['modélisation', 'modeling', 'flumilog']):
            return 'modelisation'
        elif any(word in title_lower for word in ['carte', 'cartographie', 'mapping']):
            return 'cartographie'
        elif any(word in title_lower for word in ['annexe', 'appendix']):
            return 'annexe'
        elif 'séisme' in content_lower or 'inondation' in content_lower:
            return 'alea_naturel'
        elif 'incendie' in content_lower or 'explosion' in content_lower:
            return 'alea_technologique'
        else:
            return 'general'

    def save_sections_to_files(self, output_dir: str = "pdf_sections"):
        """
        Sauvegarder chaque section dans un fichier séparé
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for section_id, section_data in self.sections.items():
            # Nom de fichier basé sur le titre
            safe_title = "".join(c for c in section_data['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_')[:50]  # Limiter la longueur

            filename = f"{section_id}_{safe_title}.txt"
            filepath = os.path.join(output_dir, filename)

            # Contenu du fichier
            content = f"""SECTION: {section_data['title']}
TYPE: {section_data['type']}
NIVEAU: {section_data['level']}
PAGES: {section_data['start_page']}-{section_data['end_page']}
MOTS: {section_data['word_count']}

================================================================================

{section_data['content']}
"""

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"Section sauvegardée: {filepath}")

    def create_sections_index(self, output_file: str = "sections_index.json"):
        """
        Créer un index JSON de toutes les sections
        """
        index = {
            'pdf_info': {
                'filename': os.path.basename(self.pdf_path),
                'total_pages': len(self.doc) if self.doc else 0,
                'total_sections': len(self.sections)
            },
            'sections': self.sections
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        print(f"Index créé: {output_file}")

    def analyze_sections_by_type(self) -> Dict[str, List[Dict]]:
        """
        Analyser les sections par type
        """
        types_analysis = {}

        for section_id, section_data in self.sections.items():
            section_type = section_data['type']
            if section_type not in types_analysis:
                types_analysis[section_type] = []

            types_analysis[section_type].append({
                'id': section_id,
                'title': section_data['title'],
                'pages': f"{section_data['start_page']}-{section_data['end_page']}",
                'word_count': section_data['word_count']
            })

        return types_analysis

    def close(self):
        """Fermer le PDF"""
        if self.doc:
            self.doc.close()

def main():
    """
    Fonction principale pour tester l'extraction des sections
    """
    pdf_path = r"c:\Users\Admin\Desktop\logiciel\uploads\3-Etude-dangers-avec-annexes_v2.pdf"

    extractor = PDFSectionExtractor(pdf_path)

    try:
        # Ouvrir et analyser
        extractor.open_pdf()

        # Extraire les sections
        print("Extraction des sections...")
        sections = extractor.extract_sections()

        # Sauvegarder les sections
        print("Sauvegarde des sections...")
        extractor.save_sections_to_files("pdf_sections")

        # Créer l'index
        extractor.create_sections_index("sections_index.json")

        # Analyser par type
        types_analysis = extractor.analyze_sections_by_type()

        print("\n=== ANALYSE PAR TYPE ===")
        for section_type, sections_list in types_analysis.items():
            print(f"\n{section_type.upper()}: {len(sections_list)} sections")
            for section in sections_list:
                print(f"  - {section['title']} ({section['pages']} pages, {section['word_count']} mots)")

        print(f"\nTotal: {len(sections)} sections extraites")

    except Exception as e:
        print(f"Erreur: {e}")
    finally:
        extractor.close()

if __name__ == "__main__":
    main()