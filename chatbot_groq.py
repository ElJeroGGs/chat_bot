import streamlit as st
import os
from pathlib import Path
import chromadb
from datetime import datetime
import random
from groq import Groq

# Configurar página
st.set_page_config(
    page_title="EcoBot - Asistente de Integración Regional",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CONFIGURACIÓN RAG CON GROQ ====================

class RAGSystem:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection_name = "documentos_curso"
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.doc_hash_file = ".doc_hash"
        
        # Inicializar cliente Groq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            st.error("❌ GROQ_API_KEY no está configurada. Configúrala en Streamlit Secrets o variables de entorno.")
            st.stop()
        self.groq_client = Groq(api_key=api_key)
    
    def get_documents_hash(self, folder_path="./documentos"):
        """Genera un hash de los documentos actuales"""
        try:
            folder = Path(folder_path)
            if not folder.exists():
                return None
            
            files = sorted(folder.glob("*.txt"))
            file_info = []
            
            for f in files:
                stat = f.stat()
                file_info.append(f"{f.name}_{stat.st_size}_{stat.st_mtime}")
            
            import hashlib
            info_str = "|".join(file_info)
            return hashlib.md5(info_str.encode()).hexdigest()
        except:
            return None
    
    def documents_changed(self, folder_path="./documentos"):
        """Verifica si los documentos han cambiado"""
        try:
            current_hash = self.get_documents_hash(folder_path)
            
            if Path(self.doc_hash_file).exists():
                with open(self.doc_hash_file, 'r') as f:
                    saved_hash = f.read().strip()
            else:
                saved_hash = None
            
            if current_hash:
                with open(self.doc_hash_file, 'w') as f:
                    f.write(current_hash)
            
            return current_hash != saved_hash
        except:
            return True
        
    def get_or_create_collection(self):
        """Obtiene o crea la colección de ChromaDB"""
        try:
            collection = self.client.get_collection(self.collection_name)
        except:
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return collection
    
    def chunk_text(self, text, chunk_size=1000, overlap=200):
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
    
    def load_txt(self, txt_path):
        """Carga texto de un archivo TXT"""
        try:
            with open(txt_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            st.error(f"Error al leer TXT {txt_path}: {e}")
            return None
    
    def process_documents(self, folder_path="./documentos"):
        """Procesa todos los documentos de la carpeta"""
        collection = self.get_or_create_collection()
        
        folder = Path(folder_path)
        if not folder.exists():
            st.warning(f"La carpeta {folder_path} no existe")
            return 0
        
        documents = []
        metadatas = []
        ids = []
        
        files = list(folder.glob("*.txt"))
        
        if not files:
            st.warning("No se encontraron archivos TXT en la carpeta documentos/")
            return 0
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, file_path in enumerate(files):
            status_text.text(f"Procesando: {file_path.name}...")
            
            if file_path.suffix.lower() == '.txt':
                content = self.load_txt(file_path)
            else:
                continue
            
            if content:
                chunks = self.chunk_text(content)
                
                for chunk_idx, chunk in enumerate(chunks):
                    documents.append(chunk)
                    metadatas.append({
                        "source": file_path.name,
                        "chunk": chunk_idx,
                        "total_chunks": len(chunks)
                    })
                    ids.append(f"{file_path.stem}_{chunk_idx}")
            
            progress_bar.progress((idx + 1) / len(files))
        
        # Agregar a ChromaDB (ChromaDB genera embeddings internamente)
        if documents:
            status_text.text("Creando embeddings y guardando en la base de datos...")
            
            try:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                status_text.text(f"✓ Procesados {len(documents)} fragmentos de {len(files)} archivos")
                progress_bar.empty()
            except Exception as e:
                st.error(f"Error al guardar en ChromaDB: {e}")
                progress_bar.empty()
                return 0
        
        return len(documents)
    
    def search(self, query, n_results=10):
        """Busca documentos relevantes"""
        collection = self.get_or_create_collection()
        
        try:
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results
        except Exception as e:
            st.error(f"Error en búsqueda: {e}")
            return None
    
    def generate_response(self, query, context_docs):
        """Genera respuesta usando Groq"""
        context = "\n\n".join(context_docs)
        
        system_instruction = """Eres EcoBot, un asistente académico experto en la Integración Regional de Europa y América.
Tu objetivo es ayudar a estudiantes basándote EXCLUSIVAMENTE en el contexto proporcionado.

INSTRUCCIONES ESTRICTAS:
1. Usa SOLO la información del apartado [CONTEXTO] para responder.
2. Si la respuesta NO está en el contexto, di exactamente: "Lo siento, esa información específica no se encuentra en los materiales del curso consultados." y NO añadas información externa.
3. Estructura tu respuesta en formato Markdown (usa negritas para conceptos clave y listas para enumerar).
4. Sé didáctico, formal pero accesible.
"""

        user_content = f"""
[CONTEXTO]
{context}

[PREGUNTA]
{query}
"""

        try:
            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        'role': 'system',
                        'content': system_instruction
                    },
                    {
                        'role': 'user',
                        'content': user_content
                    }
                ],
                temperature=0.1,
                max_tokens=1000,
                stream=True
            )
            
            return response
        except Exception as e:
            st.error(f"Error al generar respuesta: {e}")
            return None

# ==================== FUNCIONES DE UTILIDAD ====================

def get_mensaje_motivacional():
    """Retorna mensajes motivacionales"""
    mensajes = [
        "¡Excelente pregunta! Vamos a explorar ese tema. 💡",
        "¡Me encanta tu curiosidad! Aquí va la respuesta. 📚",
        "¡Muy bien! Esa es una pregunta clave del curso. 🎯",
        "¡Perfecto! Déjame explicarte ese concepto. 🌟",
        "¡Sigue así! El aprendizaje continuo es la clave. 🚀"
    ]
    return random.choice(mensajes)

def get_mensaje_nocturno():
    """Mensaje especial para horario nocturno"""
    hora = datetime.now().hour
    if hora >= 21 or hora < 6:
        return "🌙 Veo que estudias tarde. ¡Ánimo! El esfuerzo vale la pena."
    return None

def get_frase_del_dia():
    """Retorna una frase motivacional"""
    frases = [
        "La educación es el arma más poderosa para cambiar el mundo. - Nelson Mandela",
        "El aprendizaje es un tesoro que te seguirá a todas partes. - Proverbio Chino",
        "La curiosidad es la brújula que guía a los grandes pensadores. - Albert Einstein",
        "El éxito es la suma de pequeños esfuerzos realizados día tras día. - Robert Collier",
        "Quien deja de aprender, deja de crecer. - Brian Tracy"
    ]
    return random.choice(frases)

def get_consejo_estudio():
    """Retorna un consejo de estudio"""
    consejos = [
        "💡 Tip: Relaciona conceptos de diferentes unidades para mejor comprensión.",
        "📝 Consejo: Haz mapas mentales de las instituciones de la UE.",
        "🔍 Técnica: Usa la búsqueda de fuentes para profundizar en temas.",
        "🎯 Estrategia: Repasa regularmente, no dejes todo para el día anterior.",
        "📚 Recomendación: Toma notas mientras estudias con EcoBot."
    ]
    return random.choice(consejos)

def generar_preguntas_quiz():
    """Genera preguntas de quiz"""
    preguntas_quiz = [
        {
            "pregunta": "¿En qué año se firmó el Tratado de Roma que originó la CEE?",
            "opciones": ["A) 1951", "B) 1957", "C) 1986", "D) 1992"],
            "respuesta_correcta": 1,
            "explicacion": "El Tratado de Roma de 1957 creó la Comunidad Económica Europea (CEE)."
        },
        {
            "pregunta": "¿Cuál es el objetivo principal de la Unión Europea?",
            "opciones": ["A) Control militar", "B) Unión política y económica", "C) Expansión territorial", "D) Competencia comercial"],
            "respuesta_correcta": 1,
            "explicacion": "La UE busca la unión política y económica de sus estados miembros."
        },
        {
            "pregunta": "¿Cuántos estados miembros tiene actualmente la Unión Europea?",
            "opciones": ["A) 15", "B) 20", "C) 27", "D) 32"],
            "respuesta_correcta": 2,
            "explicacion": "La UE tiene 27 estados miembros después de la salida del Reino Unido en 2020."
        },
        {
            "pregunta": "¿Qué tratado creó la Unión Política Europea en 1992?",
            "opciones": ["A) Tratado de Roma", "B) Acta Única Europea", "C) Tratado de Maastricht", "D) Tratado de Lisboa"],
            "respuesta_correcta": 2,
            "explicacion": "El Tratado de Maastricht de 1992 transformó la CEE en la UE."
        },
        {
            "pregunta": "¿Cuál es la principal diferencia entre TLCAN y Mercosur?",
            "opciones": ["A) Ubicación geográfica", "B) Nivel de institucionalización", "C) Número de miembros", "D) Objetivos económicos"],
            "respuesta_correcta": 1,
            "explicacion": "La UE tiene mayor institucionalización. Mercosur está entre ambos niveles."
        }
    ]
    return preguntas_quiz

def mostrar_bienvenida():
    """Muestra mensaje de bienvenida"""
    st.title("🌍 EcoBot - Tu Asistente de Integración Regional")
    st.markdown("""
    ¡Bienvenido! Soy tu asistente personal para el curso de **Integración Regional de Europa y América**.
    
    Puedo ayudarte con:
    - 📚 Conceptos clave y definiciones
    - 🔍 Ejemplos prácticos
    - 📊 Comparaciones entre temas
    - ❓ Preguntas frecuentes de examen
    
    **¿Cómo usar el chatbot?**
    1. Usa el menú lateral para navegar por unidades
    2. Haz clic en preguntas frecuentes
    3. O escribe tu propia pregunta en el campo de texto
    """)

# ==================== MAIN APP ====================

def main():
    # Inicializar sistema RAG
    if 'rag' not in st.session_state:
        st.session_state.rag = RAGSystem()
    
    # Inicializar historial de chat
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Inicializar estado de procesamiento
    if 'docs_processed' not in st.session_state:
        st.session_state.docs_processed = False
    
    # Inicializar flag para generar respuesta
    if 'generate_response_flag' not in st.session_state:
        st.session_state.generate_response_flag = False
    
    # Inicializar quiz
    if 'quiz_activo' not in st.session_state:
        st.session_state.quiz_activo = False
    
    if 'quiz_preguntas' not in st.session_state:
        st.session_state.quiz_preguntas = []
    
    if 'quiz_pregunta_actual' not in st.session_state:
        st.session_state.quiz_pregunta_actual = 0
    
    if 'quiz_puntuacion' not in st.session_state:
        st.session_state.quiz_puntuacion = 0
    
    # ==================== SIDEBAR ====================
    with st.sidebar:
        st.header("📋 Menú de Navegación")
        
        # Verificar si documentos han cambiado
        docs_changed = st.session_state.rag.documents_changed()
        
        # Botón para procesar documentos
        if not st.session_state.docs_processed or docs_changed:
            if docs_changed and st.session_state.docs_processed:
                st.warning("⚠️ Se detectaron cambios en los documentos")
            elif not st.session_state.docs_processed:
                st.info("⚠️ Primero debes procesar los documentos")
            
            if st.button("🔄 Procesar Documentos", type="primary"):
                with st.spinner("Procesando documentos..."):
                    count = st.session_state.rag.process_documents()
                    if count > 0:
                        st.session_state.docs_processed = True
                        st.success(f"✓ {count} fragmentos procesados")
                        st.rerun()
        
        if st.session_state.docs_processed and not docs_changed:
            st.success("✓ Base de datos actualizada")
        
        st.divider()
        
        # Unidades del curso
        st.subheader("📚 Unidades del Curso")
        
        unidades = {
            "Unidad 1": "Teoría de la Integración Regional",
            "Unidad 2": "Procesos de Integración en Europa",
            "Unidad 3": "Instituciones de la Unión Europea",
            "Unidad 4": "Integración Europea Actual",
            "Unidad 5": "Integración en América"
        }
        
        for unidad, tema in unidades.items():
            if st.button(f"{unidad}: {tema}", use_container_width=True):
                st.session_state.messages.append({
                    "role": "user",
                    "content": f"Explícame sobre {tema}"
                })
                st.session_state.generate_response_flag = True
                st.rerun()
        
        st.divider()
        
        # Preguntas frecuentes
        st.subheader("❓ Preguntas Frecuentes")
        
        preguntas_freq = [
            "¿Qué es la integración regional?",
            "¿Cuáles son las etapas de integración económica?",
            "¿Qué es la Unión Europea?",
            "¿Cuáles son los objetivos del TLCAN?",
            "¿Qué es el Mercosur?",
            "Diferencias entre zona de libre comercio y unión aduanera",
            "¿Qué instituciones tiene la UE?",
            "Ejemplos de integración en América Latina"
        ]
        
        for pregunta in preguntas_freq:
            if st.button(pregunta, use_container_width=True):
                st.session_state.messages.append({
                    "role": "user",
                    "content": pregunta
                })
                st.session_state.generate_response_flag = True
                st.rerun()
        
        st.divider()
        
        # Información de documentos procesados
        if st.session_state.docs_processed:
            st.subheader("📊 Base de Datos")
            collection = st.session_state.rag.get_or_create_collection()
            total_chunks = collection.count()
            
            if total_chunks > 0:
                all_metadata = collection.get(limit=total_chunks)['metadatas']
                unique_docs = set([m['source'] for m in all_metadata])
                
                st.metric("Fragmentos totales", total_chunks)
                st.metric("Documentos", len(unique_docs))
                
                with st.expander("📄 Ver documentos"):
                    for doc in sorted(unique_docs):
                        st.text(f"• {doc}")
        
        st.divider()
        
        # Botón limpiar chat
        if st.button("🗑️ Limpiar Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        
        st.divider()
        
        # Sección de herramientas de estudio
        st.subheader("🎯 Herramientas de Estudio")
        
        if st.button("📝 Mini Quiz (5 preguntas)", use_container_width=True, type="secondary"):
            st.session_state.quiz_activo = True
            st.session_state.quiz_preguntas = generar_preguntas_quiz()
            st.session_state.quiz_pregunta_actual = 0
            st.session_state.quiz_puntuacion = 0
            st.rerun()
        
        st.divider()
        st.subheader("✨ Frase del Día")
        st.markdown(f"*{get_frase_del_dia()}*")
        
        st.subheader("💡 Consejo de Hoy")
        st.info(get_consejo_estudio())
    
    # ==================== MAIN CONTENT ====================
    
    if not st.session_state.messages:
        mostrar_bienvenida()
        
        msg_nocturno = get_mensaje_nocturno()
        if msg_nocturno:
            st.info(msg_nocturno)
    
    # Mostrar QUIZ si está activo
    if st.session_state.quiz_activo:
        st.title("🎯 MINI QUIZ - Integración Regional")
        
        if st.session_state.quiz_pregunta_actual < len(st.session_state.quiz_preguntas):
            pregunta = st.session_state.quiz_preguntas[st.session_state.quiz_pregunta_actual]
            num_pregunta = st.session_state.quiz_pregunta_actual + 1
            total_preguntas = len(st.session_state.quiz_preguntas)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"Pregunta {num_pregunta} de {total_preguntas}")
            with col2:
                st.metric("Puntuación", f"{st.session_state.quiz_puntuacion}/{total_preguntas}")
            
            st.divider()
            
            st.markdown(f"### {pregunta['pregunta']}")
            
            respuesta_seleccionada = st.radio(
                "Selecciona tu respuesta:",
                pregunta['opciones'],
                key=f"quiz_pregunta_{st.session_state.quiz_pregunta_actual}"
            )
            
            idx_respuesta = pregunta['opciones'].index(respuesta_seleccionada)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✓ Confirmar", use_container_width=True, type="primary"):
                    if idx_respuesta == pregunta['respuesta_correcta']:
                        st.success("✅ ¡Correcto!")
                        st.session_state.quiz_puntuacion += 1
                    else:
                        st.error("❌ Incorrecto")
                    
                    st.info(f"📖 {pregunta['explicacion']}")
                    
                    st.session_state.quiz_pregunta_actual += 1
                    st.sleep(2)
                    st.rerun()
            
            with col3:
                if st.button("Terminar Quiz", use_container_width=True):
                    st.session_state.quiz_activo = False
                    st.rerun()
        
        else:
            st.success("🏁 ¡Quiz completado!")
            
            col1, col2, col3 = st.columns(3)
            with col2:
                st.metric("Puntuación Final", f"{st.session_state.quiz_puntuacion}/5")
            
            porcentaje = (st.session_state.quiz_puntuacion / 5) * 100
            
            if porcentaje >= 80:
                st.balloons()
                st.success(f"¡Excelente! {porcentaje:.0f}% de respuestas correctas")
            elif porcentaje >= 60:
                st.info(f"Buen trabajo. {porcentaje:.0f}% de respuestas correctas")
            else:
                st.warning(f"Necesitas repasar. {porcentaje:.0f}% de respuestas correctas")
            
            if st.button("Volver al Chat", use_container_width=True, type="primary"):
                st.session_state.quiz_activo = False
                st.rerun()
        
        return
    
    # Mostrar historial de chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Generar respuesta automática si fue activada
    if st.session_state.generate_response_flag and st.session_state.messages:
        st.session_state.generate_response_flag = False
        prompt = st.session_state.messages[-1]["content"]
        
        if not st.session_state.docs_processed:
            st.warning("⚠️ Por favor, procesa los documentos primero")
        else:
            with st.chat_message("assistant"):
                with st.spinner("Buscando información..."):
                    try:
                        results = st.session_state.rag.search(prompt, n_results=10)
                        
                        if results and results['documents'] and results['documents'][0]:
                            context_docs = results['documents'][0]
                            
                            st.markdown(f"*{get_mensaje_motivacional()}*")
                            
                            response_placeholder = st.empty()
                            full_response = ""
                            
                            response = st.session_state.rag.generate_response(prompt, context_docs)
                            
                            if response:
                                for chunk in response:
                                    if chunk.choices[0].delta.content:
                                        full_response += chunk.choices[0].delta.content
                                        response_placeholder.markdown(full_response + "▌")
                            
                            response_placeholder.markdown(full_response)
                            
                            with st.expander("📄 Fuentes consultadas"):
                                for metadata in results['metadatas'][0]:
                                    st.text(f"• {metadata['source']} (fragmento {metadata['chunk']+1}/{metadata['total_chunks']})")
                            
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": full_response
                            })
                        else:
                            st.error("No se encontró información relevante.")
                    except Exception as e:
                        st.error(f"Error: {e}")
    
    # Input de usuario
    if prompt := st.chat_input("Escribe tu pregunta aquí..."):
        if not st.session_state.docs_processed:
            st.warning("⚠️ Por favor, procesa los documentos primero")
            return
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Buscando información..."):
                try:
                    results = st.session_state.rag.search(prompt, n_results=10)
                    
                    if results and results['documents'] and results['documents'][0]:
                        context_docs = results['documents'][0]
                        
                        st.markdown(f"*{get_mensaje_motivacional()}*")
                        
                        response_placeholder = st.empty()
                        full_response = ""
                        
                        response = st.session_state.rag.generate_response(prompt, context_docs)
                        
                        if response:
                            for chunk in response:
                                if chunk.choices[0].delta.content:
                                    full_response += chunk.choices[0].delta.content
                                    response_placeholder.markdown(full_response + "▌")
                        
                        response_placeholder.markdown(full_response)
                        
                        with st.expander("📄 Fuentes consultadas"):
                            for metadata in results['metadatas'][0]:
                                st.text(f"• {metadata['source']} (fragmento {metadata['chunk']+1}/{metadata['total_chunks']})")
                        
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": full_response
                        })
                    else:
                        st.error("No se encontró información relevante.")
                except Exception as e:
                    st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
