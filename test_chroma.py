import chromadb

print("="*60)
print("DIAGNÓSTICO CHROMADB")
print("="*60)

# Conectar
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection("documentos_curso")

print(f"\n✓ Colección encontrada: documentos_curso")
print(f"✓ Total documentos: {collection.count()}")

# Intentar búsqueda
query = "Procesos de Integración en Europa"
print(f"\n🔍 Probando búsqueda: '{query}'")

try:
    results = collection.query(
        query_texts=[query],
        n_results=5
    )
    
    print(f"\n✓ Búsqueda completada sin errores")
    print(f"  - Tipo results: {type(results)}")
    print(f"  - Keys: {list(results.keys())}")
    print(f"  - Docs encontrados: {len(results['documents'][0])}")
    
    if results['documents'][0]:
        print(f"\n✓ ÉXITO: Se encontraron {len(results['documents'][0])} documentos")
        print(f"\nPrimer resultado (200 chars):")
        print(results['documents'][0][0][:200])
    else:
        print(f"\n❌ PROBLEMA: Lista vacía aunque colección tiene {collection.count()} docs")
        print("\nPosibles causas:")
        print("1. Falta instalar: pip install sentence-transformers")
        print("2. Problema de compatibilidad de embeddings")
        
except Exception as e:
    print(f"\n❌ ERROR en búsqueda: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
