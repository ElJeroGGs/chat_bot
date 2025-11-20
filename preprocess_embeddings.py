"""
Script para preprocesar embeddings una sola vez.
Corre esto ANTES de desplegar en Streamlit Cloud.
"""

import chromadb
from pathlib import Path
import hashlib

def get_documents_hash(folder_path="./documentos"):
    """Genera un hash de los documentos actuales"""
    try:
        folder = Path(folder_path)
        if not folder.exists():
            print(f"⚠️ La carpeta {folder_path} no existe")
            return None
        
        files = sorted(folder.glob("*.txt"))
        file_info = []
        
        for f in files:
            stat = f.stat()
            file_info.append(f"{f.name}_{stat.st_size}_{stat.st_mtime}")
        
        info_str = "|".join(file_info)
        return hashlib.md5(info_str.encode()).hexdigest()
    except Exception as e:
        print(f"Error generando hash: {e}")
        return None

def chunk_text(text, chunk_size=1000, overlap=200):
    """Divide el texto en chunks"""
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
        
    return chunks

def load_txt(txt_path):
    """Carga texto de un archivo TXT"""
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error al leer TXT {txt_path}: {e}")
        return None

def preprocess_embeddings(folder_path="./documentos"):
    """Procesa y guarda embeddings en ChromaDB de forma persistente"""
    
    print("🚀 Iniciando preprocesamiento de embeddings...")
    
    # Conectar a ChromaDB
    client = chromadb.PersistentClient(path="./chroma_db")
    collection_name = "documentos_curso"
    
    # Eliminar colección anterior si existe
    try:
        client.delete_collection(collection_name)
        print("♻️ Colección anterior eliminada")
    except:
        pass
    
    # Crear nueva colección
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    print("📚 Nueva colección creada")
    
    # Procesar documentos
    folder = Path(folder_path)
    if not folder.exists():
        print(f"❌ La carpeta {folder_path} no existe")
        return 0
    
    files = list(folder.glob("*.txt"))
    if not files:
        print(f"❌ No se encontraron archivos TXT en {folder_path}")
        return 0
    
    documents = []
    metadatas = []
    ids = []
    
    print(f"📄 Procesando {len(files)} archivos...")
    
    for file_path in files:
        print(f"  • {file_path.name}...", end=" ", flush=True)
        
        content = load_txt(file_path)
        if content:
            chunks = chunk_text(content)
            
            for chunk_idx, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "source": file_path.name,
                    "chunk": chunk_idx,
                    "total_chunks": len(chunks)
                })
                ids.append(f"{file_path.stem}_{chunk_idx}")
            
            print(f"✓ ({len(chunks)} fragmentos)")
        else:
            print(f"✗ (error)")
    
    # Agregar a ChromaDB
    if documents:
        print(f"\n💾 Guardando {len(documents)} fragmentos en ChromaDB...")
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print("✅ Embeddings guardados exitosamente")
        
        # Guardar hash
        current_hash = get_documents_hash(folder_path)
        if current_hash:
            with open(".doc_hash", "w") as f:
                f.write(current_hash)
            print(f"📌 Hash guardado: {current_hash}")
        
        return len(documents)
    else:
        print("❌ No se procesaron documentos")
        return 0

if __name__ == "__main__":
    count = preprocess_embeddings()
    print(f"\n{'='*50}")
    print(f"✨ Preprocesamiento completado: {count} fragmentos")
    print(f"{'='*50}")
    print("\n📝 PRÓXIMOS PASOS:")
    print("1. Verifica que chroma_db/ tenga archivos")
    print("2. Sube todo a GitHub: git add . && git commit && git push")
    print("3. Streamlit Cloud cargará los embeddings una sola vez")
    print("4. ¡Los usuarios tendrán acceso instantáneo!")
