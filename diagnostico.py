#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para verificar la configuración del chatbot
"""

import os
import sys
from pathlib import Path

def check_env_variable():
    """Verifica si la variable de entorno GROQ_API_KEY está configurada"""
    print("🔍 Verificando GROQ_API_KEY...")
    api_key = os.getenv("GROQ_API_KEY")
    
    if api_key:
        print(f"✅ GROQ_API_KEY encontrada (longitud: {len(api_key)} caracteres)")
        if api_key.startswith("gsk_"):
            print("✅ El formato de la API key parece correcto (comienza con 'gsk_')")
        else:
            print("⚠️ La API key no comienza con 'gsk_', verifica que sea correcta")
        return True
    else:
        print("❌ GROQ_API_KEY no está configurada")
        print("\n💡 Configúrala usando una de estas opciones:")
        print("   1. Crea un archivo .env con: GROQ_API_KEY=tu_clave")
        print("   2. PowerShell: $env:GROQ_API_KEY = 'tu_clave'")
        print("   3. Crea .streamlit/secrets.toml con: GROQ_API_KEY = 'tu_clave'")
        return False

def check_dotenv():
    """Verifica si python-dotenv está instalado"""
    print("\n🔍 Verificando python-dotenv...")
    try:
        import dotenv
        print(f"✅ python-dotenv instalado (versión: {dotenv.__version__})")
        
        # Cargar .env
        dotenv.load_dotenv()
        
        env_file = Path(".env")
        if env_file.exists():
            print(f"✅ Archivo .env encontrado en: {env_file.absolute()}")
        else:
            print("⚠️ Archivo .env no encontrado (puedes crearlo desde .env.example)")
        
        return True
    except ImportError:
        print("⚠️ python-dotenv no está instalado")
        print("   Instálalo con: pip install python-dotenv")
        return False

def check_groq_library():
    """Verifica si la librería groq está instalada"""
    print("\n🔍 Verificando librería groq...")
    try:
        import groq
        print(f"✅ groq instalado (versión: {groq.__version__})")
        return True
    except ImportError:
        print("❌ groq no está instalado")
        print("   Instálalo con: pip install groq")
        return False

def check_groq_connection():
    """Verifica la conexión con la API de Groq"""
    print("\n🔍 Verificando conexión con Groq API...")
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("⚠️ No se puede verificar la conexión sin API key")
        return False
    
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        
        # Hacer una petición simple
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Responde solo 'OK'"}],
            max_tokens=10
        )
        
        print("✅ Conexión exitosa con Groq API")
        print(f"   Respuesta del modelo: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ Error al conectar con Groq: {str(e)}")
        
        error_str = str(e).lower()
        if "auth" in error_str or "api key" in error_str:
            print("   💡 Tu API key parece ser inválida")
        elif "rate" in error_str or "limit" in error_str:
            print("   💡 Has excedido el límite de peticiones")
        elif "timeout" in error_str:
            print("   💡 Timeout - verifica tu conexión a internet")
        
        return False

def check_chromadb():
    """Verifica que ChromaDB esté instalado y tenga datos"""
    print("\n🔍 Verificando ChromaDB...")
    
    try:
        import chromadb
        print(f"✅ chromadb instalado (versión: {chromadb.__version__})")
        
        # Verificar base de datos
        db_path = Path("./chroma_db")
        if db_path.exists():
            print(f"✅ Base de datos encontrada en: {db_path.absolute()}")
            
            try:
                client = chromadb.PersistentClient(path="./chroma_db")
                collection = client.get_collection("documentos_curso")
                count = collection.count()
                
                if count > 0:
                    print(f"✅ Base de datos tiene {count} documentos/fragmentos")
                    
                    # Mostrar algunos documentos
                    sample = collection.get(limit=5)
                    unique_sources = set([m['source'] for m in sample['metadatas']])
                    print(f"   Fuentes encontradas: {', '.join(list(unique_sources)[:3])}...")
                else:
                    print("⚠️ Base de datos vacía (0 documentos)")
                    print("   Ejecuta: python preprocess_embeddings.py")
                
                return True
                
            except Exception as e:
                print(f"⚠️ Error al acceder a la colección: {e}")
                print("   Ejecuta: python preprocess_embeddings.py")
                return False
        else:
            print("⚠️ Base de datos no encontrada")
            print("   Ejecuta: python preprocess_embeddings.py")
            return False
            
    except ImportError:
        print("❌ chromadb no está instalado")
        print("   Instálalo con: pip install chromadb")
        return False

def check_streamlit():
    """Verifica que Streamlit esté instalado"""
    print("\n🔍 Verificando Streamlit...")
    try:
        import streamlit
        print(f"✅ streamlit instalado (versión: {streamlit.__version__})")
        return True
    except ImportError:
        print("❌ streamlit no está instalado")
        print("   Instálalo con: pip install streamlit")
        return False

def check_documents():
    """Verifica que existan documentos fuente"""
    print("\n🔍 Verificando documentos fuente...")
    
    docs_path = Path("./documentos")
    if docs_path.exists():
        txt_files = list(docs_path.glob("*.txt"))
        if txt_files:
            print(f"✅ Encontrados {len(txt_files)} archivos .txt en documentos/")
            print(f"   Ejemplos: {', '.join([f.name for f in txt_files[:3]])}")
            return True
        else:
            print("⚠️ No se encontraron archivos .txt en documentos/")
            return False
    else:
        print("⚠️ Carpeta documentos/ no encontrada")
        return False

def main():
    print("=" * 70)
    print("🔧 DIAGNÓSTICO DEL SISTEMA - ECOBOT CHATBOT")
    print("=" * 70)
    
    results = {
        "Python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "Streamlit": check_streamlit(),
        "Groq Library": check_groq_library(),
        "Python-dotenv": check_dotenv(),
        "GROQ_API_KEY": check_env_variable(),
        "Groq Connection": check_groq_connection(),
        "ChromaDB": check_chromadb(),
        "Documentos": check_documents(),
    }
    
    print("\n" + "=" * 70)
    print("📊 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 70)
    
    print(f"\nPython: {results['Python']}")
    
    passed = sum(1 for k, v in results.items() if k != "Python" and v is True)
    total = len(results) - 1
    
    for key, value in results.items():
        if key == "Python":
            continue
        status = "✅" if value else "❌"
        print(f"{status} {key}")
    
    print(f"\n📈 Score: {passed}/{total} checks pasados")
    
    if passed == total:
        print("\n🎉 ¡Todo está configurado correctamente! Puedes ejecutar:")
        print("   streamlit run chatbot_groq.py")
    else:
        print("\n⚠️ Hay problemas que necesitan ser resueltos.")
        print("   Ver detalles arriba y consultar SOLUCION_ERRORES.md")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
