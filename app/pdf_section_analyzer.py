"""
Analyseur spécialisé pour les sections du PDF d'étude des dangers
Permet d'extraire et analyser les différentes parties du document
"""

import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

class PDFSectionAnalyzer:
    """
    Analyseur spécialisé pour traiter chaque type de section du PDF
    """

    def __init__(self, sections_index_file: str = "sections_index.json"):
        self.sections_index_file = sections_index_file
        self.sections_data = {}
        self.analysis_results = {}

        # Charger les données des sections
        self.load_sections_data()

    def load_sections_data(self):
        """Charger les données des sections depuis l'index"""
        try:
            with open(self.sections_index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.sections_data = data.get('sections', {})
        except FileNotFoundError:
            print(f"Fichier {self.sections_index_file} non trouvé")
        except Exception as e:
            print(f"Erreur lors du chargement: {e}")

    def analyze_all_sections(self) -> Dict[str, Any]:
        """
        Analyser toutes les sections par type
        """
        lightning_stats = self.analyze_lightning_statistics()
        flumilog_reports = self.analyze_flumilog_reports()
        modeling_results = self.analyze_modeling_results()

        results = {
            'lightning_stats': lightning_stats,
            'flumilog_reports': flumilog_reports,
            'modeling_results': modeling_results,
            'summary': self.generate_analysis_summary(lightning_stats, flumilog_reports, modeling_results)
        }

        self.analysis_results = results
        return results

    def analyze_lightning_statistics(self) -> List[Dict[str, Any]]:
        """
        Analyser les sections sur les statistiques de foudre
        """
        lightning_sections = []

        for section_id, section_data in self.sections_data.items():
            if 'foudre' in section_data.get('title', '').lower() or 'impact' in section_data.get('title', '').lower():
                content = section_data.get('content', '')

                # Extraire les statistiques
                stats = self._extract_lightning_stats(content)

                if stats:
                    lightning_sections.append({
                        'section_id': section_id,
                        'title': section_data['title'],
                        'stats': stats,
                        'raw_content': content[:500]  # Aperçu
                    })

        return lightning_sections

    def _extract_lightning_stats(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Extraire les statistiques de foudre du contenu
        """
        stats = {}

        # NSG (Nombre de Strikes au Ground)
        nsg_match = re.search(r'N\s*:\s*([\d,]+)\s*impacts/km²/an', content)
        if nsg_match:
            stats['nsg_impacts_per_km2_per_year'] = float(nsg_match.group(1).replace(',', '.'))

        # Indice de confiance
        confidence_match = re.search(r'Indice de confiance statistique\s*:\s*(\w+)', content)
        if confidence_match:
            stats['confidence_index'] = confidence_match.group(1)

        # Intervalle de confiance
        interval_match = re.search(r'intervalle de confiance.*?:\s*\[([\d,]+)\s*-\s*([\d,]+)\]', content)
        if interval_match:
            stats['confidence_interval'] = [
                float(interval_match.group(1).replace(',', '.')),
                float(interval_match.group(2).replace(',', '.'))
            ]

        # Nombre de jours d'orage
        storm_days_match = re.search(r'Nombre de jours d\'orage\s*:\s*(\d+)\s*jours par an', content)
        if storm_days_match:
            stats['storm_days_per_year'] = int(storm_days_match.group(1))

        # Records
        year_record_match = re.search(r'Année record\s*:\s*(\d+)', content)
        if year_record_match:
            stats['record_year'] = int(year_record_match.group(1))

        month_record_match = re.search(r'Mois record\s*:\s*([^J]+)', content)
        if month_record_match:
            stats['record_month'] = month_record_match.group(1).strip()

        return stats if stats else None

    def analyze_flumilog_reports(self) -> List[Dict[str, Any]]:
        """
        Analyser les rapports FLUMILOG
        """
        flumilog_sections = []

        for section_id, section_data in self.sections_data.items():
            content = section_data.get('content', '')

            if 'flumilog' in content.lower() or 'flux' in section_data.get('title', '').lower():
                # Analyser le rapport FLUMILOG
                report_data = self._extract_flumilog_data(content)

                if report_data:
                    flumilog_sections.append({
                        'section_id': section_id,
                        'title': section_data['title'],
                        'report_data': report_data,
                        'pages': f"{section_data['start_page']}-{section_data['end_page']}"
                    })

        return flumilog_sections

    def _extract_flumilog_data(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Extraire les données d'un rapport FLUMILOG
        """
        data = {}

        # Nom du projet
        project_match = re.search(r'Nom du Projet\s*:\s*([^\n]+)', content)
        if project_match:
            data['project_name'] = project_match.group(1).strip()

        # Cellule
        cell_match = re.search(r'Cellule\s*:\s*([^\n]+)', content)
        if cell_match:
            data['cell'] = cell_match.group(1).strip()

        # Durée de l'incendie
        duration_match = re.search(r'Durée de.*incendie.*?:\s*([\d,]+)\s*min', content)
        if duration_match:
            data['fire_duration_minutes'] = float(duration_match.group(1).replace(',', '.'))

        # Flux thermiques
        flux_matches = re.findall(r'Flux \(kW/m²\)\s*([\d\s]+)', content)
        if flux_matches:
            # Extraire les valeurs numériques
            flux_values = []
            for match in flux_matches:
                values = re.findall(r'\d+', match)
                flux_values.extend([int(v) for v in values])
            data['thermal_fluxes_kw_m2'] = sorted(list(set(flux_values)))

        # Distances d'effets
        distance_section = re.search(r'Distance d\'effets des flux maximum(.*?)(?=\n\n|\nFLUMILOG|\n===|$)', content, re.DOTALL)
        if distance_section:
            data['effects_distances_info'] = distance_section.group(1).strip()

        # Société et utilisateur
        company_match = re.search(r'Société\s*:\s*([^\n]+)', content)
        if company_match:
            data['company'] = company_match.group(1).strip()

        user_match = re.search(r'Utilisateur\s*:\s*([^\n]+)', content)
        if user_match:
            data['user'] = user_match.group(1).strip()

        # Date de création
        date_match = re.search(r'Date de création.*?:\s*([\d/]+)', content)
        if date_match:
            data['creation_date'] = date_match.group(1)

        return data if data else None

    def analyze_modeling_results(self) -> List[Dict[str, Any]]:
        """
        Analyser les résultats de modélisation
        """
        modeling_sections = []

        for section_id, section_data in self.sections_data.items():
            if section_data.get('type') in ['alea_technologique', 'modelisation']:
                content = section_data.get('content', '')

                # Identifier le type de modélisation
                if 'flumilog' in content.lower():
                    model_type = 'fire_modeling'
                elif 'foudre' in content.lower():
                    model_type = 'lightning_modeling'
                else:
                    model_type = 'unknown'

                modeling_sections.append({
                    'section_id': section_id,
                    'title': section_data['title'],
                    'model_type': model_type,
                    'pages': f"{section_data['start_page']}-{section_data['end_page']}",
                    'word_count': section_data.get('word_count', 0)
                })

        return modeling_sections

    def analyze_sections_by_type(self) -> Dict[str, List[Dict]]:
        """
        Analyser les sections par type
        """
        types_analysis = {}

        for section_id, section_data in self.sections_data.items():
            section_type = section_data.get('type', 'unknown')
            if section_type not in types_analysis:
                types_analysis[section_type] = []

            types_analysis[section_type].append({
                'id': section_id,
                'title': section_data['title'],
                'pages': f"{section_data['start_page']}-{section_data['end_page']}",
                'word_count': section_data.get('word_count', 0)
            })

        return types_analysis

    def generate_analysis_summary(self, lightning_stats: List, flumilog_reports: List, modeling_results: List) -> Dict[str, Any]:
        """
        Générer un résumé de l'analyse
        """
        total_sections = len(self.sections_data)

        # Compter par type
        type_counts = {}
        for section_data in self.sections_data.values():
            section_type = section_data.get('type', 'unknown')
            type_counts[section_type] = type_counts.get(section_type, 0) + 1

        # Statistiques générales
        total_words = sum(section.get('word_count', 0) for section in self.sections_data.values())

        return {
            'total_sections': total_sections,
            'sections_by_type': type_counts,
            'total_words': total_words,
            'lightning_stats_count': len(lightning_stats),
            'flumilog_reports_count': len(flumilog_reports),
            'modeling_results_count': len(modeling_results),
            'analysis_date': datetime.now().isoformat()
        }

    def export_analysis_results(self, output_file: str = "pdf_analysis_results.json"):
        """
        Exporter les résultats d'analyse
        """
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)

        print(f"Résultats d'analyse exportés vers {output_file}")

    def create_danger_study_template(self) -> Dict[str, Any]:
        """
        Créer un template pour une étude des dangers basé sur l'analyse
        """
        template = {
            'metadata': {
                'template_version': '1.0',
                'based_on_pdf': '3-Etude-dangers-avec-annexes_v2.pdf',
                'creation_date': datetime.now().isoformat()
            },
            'sections': {
                'lightning_analysis': {
                    'description': 'Analyse des risques liés à la foudre',
                    'data_structure': {
                        'nsg_impacts_per_km2_per_year': 'float',
                        'confidence_index': 'string',
                        'confidence_interval': 'array[float]',
                        'storm_days_per_year': 'int'
                    },
                    'sample_data': self.analysis_results.get('lightning_stats', [{}])[0].get('stats', {}) if self.analysis_results.get('lightning_stats') else {}
                },
                'fire_modeling': {
                    'description': 'Modélisation des incendies avec FLUMILOG',
                    'data_structure': {
                        'project_name': 'string',
                        'cell': 'string',
                        'fire_duration_minutes': 'float',
                        'thermal_fluxes_kw_m2': 'array[int]',
                        'effects_distances_info': 'string'
                    },
                    'sample_data': self.analysis_results.get('flumilog_reports', [{}])[0].get('report_data', {}) if self.analysis_results.get('flumilog_reports') else {}
                },
                'environmental_characterization': {
                    'description': 'Caractérisation de l\'environnement',
                    'sections': ['aléas_naturels', 'aléas_technologiques', 'population', 'environnement']
                },
                'risk_scenarios': {
                    'description': 'Scénarios d\'accidents et évaluation des risques',
                    'methodology': 'Analyse préliminaire des risques (ERC) puis quantitative'
                }
            },
            'implementation_plan': {
                'phase_1': 'Extraction et analyse des données environnementales',
                'phase_2': 'Implémentation des modèles de calcul (foudre, incendie)',
                'phase_3': 'Développement de l\'interface utilisateur',
                'phase_4': 'Validation et tests avec données réelles'
            }
        }

        return template

def main():
    """
    Fonction principale de test
    """
    analyzer = PDFSectionAnalyzer()

    print("Analyse des sections du PDF...")
    results = analyzer.analyze_all_sections()

    print(f"\nStatistiques de foudre trouvées: {len(results['lightning_stats'])}")
    for stat in results['lightning_stats'][:2]:  # Afficher les 2 premiers
        print(f"  - {stat['title']}: {stat['stats']}")

    print(f"\nRapports FLUMILOG trouvés: {len(results['flumilog_reports'])}")
    for report in results['flumilog_reports'][:2]:  # Afficher les 2 premiers
        print(f"  - {report['title']}: {report['report_data'].get('project_name', 'N/A')}")

    print("\nRésumé de l'analyse:")
    print(json.dumps(results['summary'], indent=2, ensure_ascii=False))

    # Exporter les résultats
    analyzer.export_analysis_results()

    # Créer le template
    template = analyzer.create_danger_study_template()
    with open('danger_study_template.json', 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)

    print("\nTemplate d'étude des dangers créé: danger_study_template.json")

if __name__ == "__main__":
    main()