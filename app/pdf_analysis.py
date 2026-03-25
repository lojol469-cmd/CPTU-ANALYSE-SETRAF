import fitz  # PyMuPDF
import os

def analyze_pdf(pdf_path):
    if not os.path.exists(pdf_path):
        print(f"Le fichier {pdf_path} n'existe pas.")
        return

    doc = fitz.open(pdf_path)
    print(f"Nombre de pages: {len(doc)}")

    for page_num in range(min(10, len(doc))):  # Analyser les 10 premières pages
        page = doc.load_page(page_num)
        text = page.get_text()
        print(f"\n--- Page {page_num + 1} ---\n")
        print(text[:1000])  # Afficher les 1000 premiers caractères
        if len(text) > 1000:
            print("... (texte tronqué)")

    # Essayer d'extraire la structure (titres, etc.)
    print("\n--- Structure du document ---")
    toc = doc.get_toc()
    if toc:
        for item in toc:
            print(f"Niveau {item[0]}: {item[1]} (page {item[2]})")
    else:
        print("Aucune table des matières trouvée.")

    doc.close()

if __name__ == "__main__":
    pdf_path = r"c:\Users\Admin\Desktop\logiciel\uploads\3-Etude-dangers-avec-annexes_v2.pdf"
    analyze_pdf(pdf_path)