import ollama
import os

def cargar_contexto(archivo):
    """Carga el contenido del archivo de texto para usar como contexto"""
    with open(archivo, 'r', encoding='utf-8') as f:
        return f.read()

def consultar_con_contexto(pregunta, contexto):
    """Realiza una consulta a Ollama usando el contexto del documento"""
    
    # Crear el prompt con el contexto
    prompt = f"""Basándote ÚNICAMENTE en el siguiente documento, responde la pregunta.
Si la información no está en el documento, indica que no la encontraste.

DOCUMENTO:
{contexto}

PREGUNTA: {pregunta}

RESPUESTA:"""
    
    # Llamar a Ollama
    response = ollama.chat(
        model='llama3.2',
        messages=[{
            'role': 'user',
            'content': prompt
        }]
    )
    
    return response['message']['content']

def main():
    # Cargar el documento
    archivo_datos = 'datos_curso.txt'
    
    print("Cargando documento...")
    contexto = cargar_contexto(archivo_datos)
    print(f"✓ Documento cargado: {len(contexto)} caracteres\n")
    
    print("=" * 60)
    print("Chat con documento usando Ollama + llama3.2")
    print("Escribe 'salir' para terminar")
    print("=" * 60)
    
    while True:
        pregunta = input("\n📝 Tu pregunta: ").strip()
        
        if pregunta.lower() in ['salir', 'exit', 'quit']:
            print("¡Hasta luego!")
            break
        
        if not pregunta:
            continue
        
        print("\n🤖 Consultando a llama3.2...\n")
        
        try:
            respuesta = consultar_con_contexto(pregunta, contexto)
            print(f"💡 Respuesta:\n{respuesta}")
        except Exception as e:
            print(f"❌ Error: {e}")
            print("\nAsegúrate de que:")
            print("  1. Ollama esté instalado y corriendo")
            print("  2. El modelo llama3.2 esté descargado (ollama pull llama3.2)")

if __name__ == "__main__":
    main()
