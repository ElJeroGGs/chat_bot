# EuroBot - Chatbot de Integración Regional 🌍

Sistema RAG (Retrieval-Augmented Generation) para consultas sobre el curso de Integración Regional de Europa y América.

## 🚀 Características

- ✅ Procesamiento automático de PDFs y archivos de texto
- ✅ Sistema RAG con ChromaDB para búsqueda semántica
- ✅ Interfaz web interactiva con Streamlit
- ✅ Menú de navegación por unidades
- ✅ Preguntas frecuentes predefinidas
- ✅ Campo de texto para preguntas abiertas
- ✅ Mensajes motivacionales aleatorios
- ✅ Modo nocturno con mensajes de apoyo
- ✅ Historial de conversación
- ✅ Referencias a fuentes consultadas

## 📋 Requisitos Previos

1. **Ollama instalado y corriendo**
   ```bash
   # Descargar modelos necesarios
   ollama pull llama3.2
   ollama pull nomic-embed-text
   ```

2. **Python 3.8+**

## 🔧 Instalación

1. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Agregar documentos del curso:
   - Coloca todos los PDFs y archivos de texto en la carpeta `documentos/`

3. Ejecutar la aplicación:
   ```bash
   streamlit run chatbot_rag.py
   ```

## 📁 Estructura del Proyecto

```
Proyecto_ChatBot/
├── chatbot_rag.py          # Aplicación principal
├── app.py                  # Script de prueba inicial
├── requirements.txt        # Dependencias
├── documentos/            # PDFs y documentos del curso
│   └── README.md
├── chroma_db/             # Base de datos vectorial (se crea automáticamente)
└── datos_curso.txt        # Documento de ejemplo
```

## 🎯 Uso

1. **Primera vez:**
   - Abre la aplicación
   - Haz clic en "🔄 Procesar Documentos" en el menú lateral
   - Espera a que se procesen todos los archivos

2. **Navegar:**
   - Usa los botones de unidades en el menú lateral
   - Haz clic en preguntas frecuentes
   - O escribe tu propia pregunta en el campo de texto

3. **Funcionalidades:**
   - Ver fuentes consultadas (expandir sección)
   - Limpiar historial de chat
   - Mensajes motivacionales aleatorios
   - Mensajes especiales en horario nocturno (10 PM - 6 AM)

## 🌐 Despliegue

### Opción 1: Streamlit Cloud (Recomendado para pruebas)
1. Sube el proyecto a GitHub
2. Conecta con Streamlit Cloud
3. **Nota:** Necesitas configurar Ollama en un servidor accesible

### Opción 2: Servidor VPS
1. Instala Ollama en el servidor
2. Despliega con Docker o directamente
3. Configura nginx como reverse proxy

## 🎨 Personalización

- **Agregar más preguntas frecuentes:** Edita la lista `preguntas_freq` en `chatbot_rag.py`
- **Cambiar unidades:** Modifica el diccionario `unidades`
- **Ajustar mensajes motivacionales:** Edita la función `get_mensaje_motivacional()`
- **Cambiar modelo:** Modifica `model='llama3.2'` por otro modelo de Ollama

## 📊 Componentes Técnicos

- **Frontend:** Streamlit
- **LLM:** Ollama con llama3.2
- **Embeddings:** nomic-embed-text
- **Vector Store:** ChromaDB
- **Procesamiento PDF:** pypdf

## 🐛 Troubleshooting

**Error: "Ollama no está disponible"**
- Verifica que Ollama esté corriendo
- Ejecuta: `ollama list` para ver modelos instalados

**Error: "No se encontraron documentos"**
- Asegúrate de tener archivos en la carpeta `documentos/`
- Formatos soportados: PDF, TXT

**Respuestas lentas:**
- Normal en CPU, considera usar GPU
- Reduce el número de resultados en búsqueda (n_results)

## 👥 Créditos

Proyecto desarrollado para el curso de Integración Regional de Europa y América.

## 📝 Licencia

Proyecto académico - Universidad Autónoma del Estado de México
