import os
from pathlib import Path
import pypdf

def convertir_pdfs_a_txt(carpeta_origen="./documentos", carpeta_destino="./doc_convertidos"):
    """
    Convierte todos los PDFs de una carpeta a TXT
    
    Args:
        carpeta_origen: Carpeta donde están los PDFs
        carpeta_destino: Carpeta donde se guardarán los TXT
    """
    
    # Crear carpeta destino si no existe
    Path(carpeta_destino).mkdir(exist_ok=True)
    
    # Obtener todos los PDFs
    carpeta = Path(carpeta_origen)
    pdfs = list(carpeta.glob("*.pdf"))
    
    if not pdfs:
        print(f"❌ No se encontraron PDFs en {carpeta_origen}")
        return
    
    print(f"📄 Se encontraron {len(pdfs)} archivos PDF\n")
    
    for idx, pdf_path in enumerate(pdfs, 1):
        print(f"[{idx}/{len(pdfs)}] Convirtiendo: {pdf_path.name}...")
        
        try:
            # Leer PDF
            with open(pdf_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                texto = ""
                
                # Extraer texto de todas las páginas
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    texto += f"\n--- PÁGINA {page_num} ---\n"
                    texto += page.extract_text() + "\n"
            
            # Guardar como TXT
            txt_filename = pdf_path.stem + ".txt"  # Usa el nombre del PDF sin extensión
            txt_path = Path(carpeta_destino) / txt_filename
            
            with open(txt_path, 'w', encoding='utf-8') as file:
                file.write(texto)
            
            print(f"   ✅ Guardado en: {txt_path}")
            print(f"   📊 Páginas: {len(pdf_reader.pages)}\n")
        
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
    
    print(f"\n✨ ¡Conversión completada!")
    print(f"📁 Archivos guardados en: {carpeta_destino}")

if __name__ == "__main__":
    print("=" * 50)
    print("🔄 CONVERSOR DE PDF A TXT")
    print("=" * 50 + "\n")
    
    convertir_pdfs_a_txt()
    
    print("\n⚠️  PRÓXIMO PASO:")
    print("1. Revisa los archivos en la carpeta 'doc_convertidos'")
    print("2. Abre cada TXT y limpia el contenido a mano si es necesario")
    print("3. Cuando estén limpios, cópijalos a la carpeta 'documentos'")
    print("4. Usa el chatbot para procesar los documentos")