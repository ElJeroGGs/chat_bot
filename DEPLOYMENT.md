# 🌍 EcoBot - Asistente de Integración Regional

## Despliegue con Groq en Streamlit Cloud

### Pasos para desplegar:

#### 1. **Obtener API Key de Groq**
   - Ve a https://console.groq.com
   - Crea una cuenta gratuita
   - Genera una API key en Settings → API Keys
   - Copia la API key (la necesitarás en el paso 3)

#### 2. **Subir proyecto a GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: EcoBot with Groq"
   git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
   git push -u origin main
   ```

#### 3. **Desplegar en Streamlit Cloud**
   - Ve a https://share.streamlit.io
   - Haz clic en "Create app"
   - Conecta tu cuenta de GitHub
   - Selecciona:
     - Repository: `tu_usuario/tu_repo`
     - Branch: `main`
     - Main file path: `chatbot_groq.py`
   - Haz clic en "Deploy"

#### 4. **Configurar Secretos en Streamlit Cloud**
   - En tu app de Streamlit Cloud, ve a Settings (⚙️)
   - Ve a "Secrets"
   - Copia este contenido:
   ```toml
   GROQ_API_KEY = "gsk_xxxxxxxxxxxxx"
   ```
   - Reemplaza con tu API key real
   - Haz clic en "Save"

#### 5. **¡Listo!**
   - Tu app se volverá a desplegar automáticamente
   - Ahora puedes compartir el link con otros usuarios

### Ejecución Local

**Con Ollama (versión local):**
```bash
streamlit run chatbot_rag.py
```

**Con Groq (versión cloud):**
```bash
# Primero, configura tu API key local en .streamlit/secrets.toml
# Luego:
streamlit run chatbot_groq.py
```

### Estructura del Proyecto

```
Proyecto_ChatBot/
├── chatbot_rag.py           # Versión local con Ollama
├── chatbot_groq.py          # Versión para Groq (Streamlit Cloud)
├── ocr_txt.py               # Script OCR (local)
├── ocr_txt_mejorado.py      # Script OCR mejorado (múltiples temas)
├── requirements.txt         # Dependencias
├── .streamlit/
│   └── secrets.toml        # API keys (NO subir a GitHub!)
├── documentos/              # Carpeta con TXT para procesar
├── chroma_db/               # Base de datos ChromaDB (generada)
└── .gitignore              # Para no subir archivos sensibles
```

### .gitignore (crear si no existe)

```
.env
.streamlit/secrets.toml
chroma_db/
.doc_hash
temp_ocr/
__pycache__/
*.pyc
.DS_Store
```

### Características

✅ RAG con ChromaDB  
✅ Búsqueda semántica de 10 fragmentos  
✅ Generación con Groq (MixtralAI)  
✅ Quiz interactivo (5 preguntas)  
✅ Modo nocturno con motivación  
✅ Fuentes consultadas  
✅ 5 unidades + 8 FAQ  
✅ Detección automática de cambios en documentos  

### Presupuesto Groq

- **Plan gratuito:** 30 requests/minuto (suficiente para demostración)
- **Modelos disponibles:** mixtral-8x7b-32768 (gratuito)
- Ideal para prototipos y proyectos pequeños

### Troubleshooting

**Error: "GROQ_API_KEY not set"**
→ Configura el secreto en Streamlit Cloud

**Embedding lento**
→ ChromaDB usa embeddings locales (más lento pero gratuito)

**Límite de rate (30/min)**
→ Espera 2 segundos entre preguntas

---

**Fecha de creación:** 2025-11-19  
**Última actualización:** 2025-11-19  
**Versión:** 1.0.0
