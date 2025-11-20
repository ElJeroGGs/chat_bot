import ollama
import os
import glob
import time
from PIL import Image

# --- CONFIGURACIÓN ---
CARPETA_IMAGENES = "imagenes_curso"
CARPETA_TEMPORAL = "temp_ocr"
CARPETA_SALIDA = "libros"
MODELO = "deepseek-ocr"

# PREFIJOS A PROCESAR (cambiar según tus temas)
PREFIJOS = ["tratado", "interaccionismo"]  # ← Agregar más si necesario

TIMEOUT = 180  # 3 minutos máximo por imagen

# Crear carpetas
for carpeta in [CARPETA_IMAGENES, CARPETA_TEMPORAL, CARPETA_SALIDA]:
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

# ============ CARGAR MODELO UNA SOLA VEZ ============
print("⏳ Cargando modelo deepseek-ocr en memoria...")
print("   (esto toma 1-2 minutos la primera vez)\n")
try:
    ollama.chat(
        model=MODELO,
        messages=[{'role': 'user', 'content': 'hola', 'images': []}],
        stream=False
    )
    print("✅ Modelo cargado\n")
except Exception as e:
    print(f"⚠️  Advertencia al cargar modelo: {str(e)[:50]}\n")

def redimensionar_imagen(ruta_imagen):
    """Redimensiona imagen a resolución válida (Gundam: n×640×640 + 1×1024×1024)"""
    try:
        img = Image.open(ruta_imagen)
        original_w, original_h = img.size
        
        if 640 <= original_w <= 1024 and 640 <= original_h <= 1024:
            return ruta_imagen
        
        ratio = min(1024 / original_w, 1024 / original_h)
        nuevo_w = int(original_w * ratio)
        nuevo_h = int(original_h * ratio)
        
        if nuevo_w < 640 or nuevo_h < 640:
            ratio = max(640 / nuevo_w, 640 / nuevo_h)
            nuevo_w = int(nuevo_w * ratio)
            nuevo_h = int(nuevo_h * ratio)
            
            if nuevo_w > 1024:
                nuevo_w = 1024
            if nuevo_h > 1024:
                nuevo_h = 1024
        
        nuevo_w = max(32, (nuevo_w // 32) * 32)
        nuevo_h = max(32, (nuevo_h // 32) * 32)
        
        img.thumbnail((nuevo_w, nuevo_h), Image.Resampling.LANCZOS)
        
        temp_path = os.path.join(CARPETA_TEMPORAL, "temp_resized.jpg")
        img.save(temp_path, "JPEG", quality=90)
        print(f"   🔄 Redimensionada: {original_w}x{original_h} → {nuevo_w}x{nuevo_h}")
        return temp_path
    except Exception as e:
        pass
    
    return ruta_imagen


# ============ PROCESAR CADA PREFIJO POR SEPARADO ============
print("=" * 80)
print("PROCESANDO MÚLTIPLES TEMAS")
print("=" * 80 + "\n")

prefijos_procesados = set()

for PREFIJO in PREFIJOS:
    print(f"\n{'='*80}")
    print(f"📌 TEMA: {PREFIJO.upper()}")
    print(f"{'='*80}\n")
    
    # Buscar imágenes con este prefijo
    tipos = ('*.png', '*.jpg', '*.jpeg')
    imagenes = []
    for tipo in tipos:
        imagenes.extend(glob.glob(os.path.join(CARPETA_IMAGENES, tipo)))
    
    imagenes = [img for img in imagenes if PREFIJO.lower() in os.path.basename(img).lower()]
    imagenes.sort()
    
    # Guardar qué imágenes se procesaron
    for img in imagenes:
        prefijos_procesados.add(os.path.basename(img))
    
    if len(imagenes) == 0:
        print(f"⏭️  No se encontraron imágenes con prefijo '{PREFIJO}'\n")
        continue
    
    print(f"📸 Encontré {len(imagenes)} imágenes\n")
    
    # ============ FASE 1: PROCESAR IMÁGENES ============
    print("FASE 1: Procesando imágenes...")
    
    procesadas = 0
    saltadas = 0
    errores = 0
    
    for idx, img in enumerate(imagenes, 1):
        nombre = os.path.basename(img)
        nombre_base = os.path.splitext(nombre)[0]
        txt_file = os.path.join(CARPETA_TEMPORAL, f"{nombre_base}.txt")
        
        if os.path.exists(txt_file):
            print(f"[{idx:02d}/{len(imagenes)}] ⏭️  {nombre:<40} (ya procesada)")
            saltadas += 1
            continue
        
        print(f"[{idx:02d}/{len(imagenes)}] 🔄 {nombre:<40}", end="", flush=True)
        
        try:
            inicio = time.time()
            img_procesada = redimensionar_imagen(img)
            
            resp = ollama.chat(
                model=MODELO,
                messages=[{
                    'role': 'user',
                    'content': 'Extract the text in the image.',
                    'images': [img_procesada]
                }],
                stream=False
            )
            
            tiempo_proc = time.time() - inicio
            texto = resp['message']['content'].strip()
            
            if texto and len(texto) > 5:
                with open(txt_file, "w", encoding="utf-8") as f:
                    f.write(texto)
                
                chars = len(texto)
                print(f" ✅ ({tiempo_proc:.1f}s, {chars} chars)")
                procesadas += 1
            else:
                print(f" ⚠️  (texto vacío)")
                errores += 1
        
        except Exception as e:
            error_msg = str(e)[:40]
            if "timeout" in error_msg.lower():
                print(f" ⏱️  TIMEOUT - SALTADA")
            else:
                print(f" ❌ {error_msg}")
            errores += 1
    
    print(f"\nResumen FASE 1:")
    print(f"  ✅ Procesadas:  {procesadas}")
    print(f"  ⏭️  Saltadas:   {saltadas}")
    print(f"  ❌ Errores:     {errores}\n")
    
    # ============ FASE 2: CONSOLIDAR SOLO ARCHIVOS DE ESTE PREFIJO ============
    print("FASE 2: Consolidando archivos TXT...")
    
    # Buscar solo los TXT que corresponden a este prefijo
    txt_files = sorted(glob.glob(os.path.join(CARPETA_TEMPORAL, "*.txt")))
    txt_files = [t for t in txt_files if PREFIJO.lower() in os.path.basename(t).lower()]
    
    contenido_total = ""
    contador = 0
    
    print(f"Encontré {len(txt_files)} archivos TXT para consolidar\n")
    
    for idx, txt in enumerate(txt_files, 1):
        nombre = os.path.basename(txt)
        try:
            with open(txt, "r", encoding="utf-8") as f:
                texto = f.read()
            
            if texto.strip():
                if contador > 0:
                    contenido_total += "\n\n" + "=" * 80 + "\n\n"
                
                contenido_total += f"📄 Fuente: {nombre}\n{'-' * 40}\n{texto}"
                contador += 1
                chars = len(texto)
                print(f"[{idx:02d}] ✅ {nombre:<40} ({chars:,} chars)")
        except Exception as e:
            print(f"[{idx:02d}] ❌ {nombre:<40} (error al leer)")
    
    print(f"\nResumen FASE 2:")
    print(f"  📄 Documentos consolidados: {contador}")
    print(f"  📊 Caracteres totales:      {len(contenido_total):,}\n")
    
    # ============ FASE 3: GUARDAR ARCHIVO FINAL ============
    print("FASE 3: Guardando archivo final...")
    
    salida = os.path.join(CARPETA_SALIDA, f"{PREFIJO}.txt")
    
    if contenido_total.strip():
        header = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                     EXTRACCIÓN OCR DE IMÁGENES DEL CURSO                   ║
║                                                                            ║
║  Tema: {PREFIJO.upper():<56} ║
║  Documentos: {contador:<54} ║
║  Caracteres: {len(contenido_total):,}  ║
║  Fecha: {time.strftime('%Y-%m-%d %H:%M:%S'):<52} ║
╚════════════════════════════════════════════════════════════════════════════╝

""".lstrip()
        
        contenido_final = header + contenido_total
        
        with open(salida, "w", encoding="utf-8") as f:
            f.write(contenido_final)
        
        tamaño_kb = os.path.getsize(salida) / 1024
        print(f"✅ COMPLETADO!\n")
        print(f"📄 Archivo guardado: {salida}")
        print(f"📊 Tamaño: {tamaño_kb:.1f} KB")
        print(f"📈 Documentos: {contador}")
        print(f"📝 Caracteres: {len(contenido_total):,}\n")
    else:
        print(f"❌ Error: No se generó contenido para guardar\n")

print("\n" + "=" * 80)
print("✅ PROCESO COMPLETADO PARA TODOS LOS TEMAS")
print("=" * 80)

# ============ PROCESAR IMÁGENES NO CATEGORIZADAS COMO "APUNTES" ============
print(f"\n{'='*80}")
print(f"📌 TEMA: APUNTES (imágenes sin categoría)")
print(f"{'='*80}\n")

# Buscar todas las imágenes que NO estén categorizadas
tipos = ('*.png', '*.jpg', '*.jpeg')
todas_imagenes = []
for tipo in tipos:
    todas_imagenes.extend(glob.glob(os.path.join(CARPETA_IMAGENES, tipo)))

# Filtrar solo las que NO están en prefijos_procesados
imagenes_sin_categoria = [img for img in todas_imagenes 
                          if os.path.basename(img) not in prefijos_procesados]
imagenes_sin_categoria.sort()

if len(imagenes_sin_categoria) == 0:
    print(f"✅ No hay imágenes sin categoría\n")
else:
    print(f"📸 Encontré {len(imagenes_sin_categoria)} imágenes sin categoría\n")
    
    PREFIJO = "apuntes"
    
    # ============ FASE 1: PROCESAR IMÁGENES ============
    print("FASE 1: Procesando imágenes...")
    
    procesadas = 0
    saltadas = 0
    errores = 0
    
    for idx, img in enumerate(imagenes_sin_categoria, 1):
        nombre = os.path.basename(img)
        nombre_base = os.path.splitext(nombre)[0]
        txt_file = os.path.join(CARPETA_TEMPORAL, f"{nombre_base}.txt")
        
        if os.path.exists(txt_file):
            print(f"[{idx:02d}/{len(imagenes_sin_categoria)}] ⏭️  {nombre:<40} (ya procesada)")
            saltadas += 1
            continue
        
        print(f"[{idx:02d}/{len(imagenes_sin_categoria)}] 🔄 {nombre:<40}", end="", flush=True)
        
        try:
            inicio = time.time()
            img_procesada = redimensionar_imagen(img)
            
            resp = ollama.chat(
                model=MODELO,
                messages=[{
                    'role': 'user',
                    'content': 'Extract the text in the image.',
                    'images': [img_procesada]
                }],
                stream=False
            )
            
            tiempo_proc = time.time() - inicio
            texto = resp['message']['content'].strip()
            
            if texto and len(texto) > 5:
                with open(txt_file, "w", encoding="utf-8") as f:
                    f.write(texto)
                
                chars = len(texto)
                print(f" ✅ ({tiempo_proc:.1f}s, {chars} chars)")
                procesadas += 1
            else:
                print(f" ⚠️  (texto vacío)")
                errores += 1
        
        except Exception as e:
            error_msg = str(e)[:40]
            if "timeout" in error_msg.lower():
                print(f" ⏱️  TIMEOUT - SALTADA")
            else:
                print(f" ❌ {error_msg}")
            errores += 1
    
    print(f"\nResumen FASE 1:")
    print(f"  ✅ Procesadas:  {procesadas}")
    print(f"  ⏭️  Saltadas:   {saltadas}")
    print(f"  ❌ Errores:     {errores}\n")
    
    # ============ FASE 2: CONSOLIDAR ARCHIVOS SIN CATEGORÍA ============
    print("FASE 2: Consolidando archivos TXT...")
    
    # Buscar todos los TXT de imágenes sin categoría
    txt_files = [os.path.join(CARPETA_TEMPORAL, os.path.splitext(os.path.basename(img))[0] + ".txt") 
                 for img in imagenes_sin_categoria]
    txt_files = [t for t in txt_files if os.path.exists(t)]
    txt_files.sort()
    
    contenido_total = ""
    contador = 0
    
    print(f"Encontré {len(txt_files)} archivos TXT para consolidar\n")
    
    for idx, txt in enumerate(txt_files, 1):
        nombre = os.path.basename(txt)
        try:
            with open(txt, "r", encoding="utf-8") as f:
                texto = f.read()
            
            if texto.strip():
                if contador > 0:
                    contenido_total += "\n\n" + "=" * 80 + "\n\n"
                
                contenido_total += f"📄 Fuente: {nombre}\n{'-' * 40}\n{texto}"
                contador += 1
                chars = len(texto)
                print(f"[{idx:02d}] ✅ {nombre:<40} ({chars:,} chars)")
        except Exception as e:
            print(f"[{idx:02d}] ❌ {nombre:<40} (error al leer)")
    
    print(f"\nResumen FASE 2:")
    print(f"  📄 Documentos consolidados: {contador}")
    print(f"  📊 Caracteres totales:      {len(contenido_total):,}\n")
    
    # ============ FASE 3: GUARDAR ARCHIVO FINAL ============
    print("FASE 3: Guardando archivo final...")
    
    salida = os.path.join(CARPETA_SALIDA, f"{PREFIJO}.txt")
    
    if contenido_total.strip():
        header = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                     EXTRACCIÓN OCR DE IMÁGENES DEL CURSO                   ║
║                                                                            ║
║  Tema: {PREFIJO.upper():<56} ║
║  Documentos: {contador:<54} ║
║  Caracteres: {len(contenido_total):,}  ║
║  Fecha: {time.strftime('%Y-%m-%d %H:%M:%S'):<52} ║
╚════════════════════════════════════════════════════════════════════════════╝

""".lstrip()
        
        contenido_final = header + contenido_total
        
        with open(salida, "w", encoding="utf-8") as f:
            f.write(contenido_final)
        
        tamaño_kb = os.path.getsize(salida) / 1024
        print(f"✅ COMPLETADO!\n")
        print(f"📄 Archivo guardado: {salida}")
        print(f"📊 Tamaño: {tamaño_kb:.1f} KB")
        print(f"📈 Documentos: {contador}")
        print(f"📝 Caracteres: {len(contenido_total):,}\n")
    else:
        print(f"❌ Error: No se generó contenido para guardar\n")

print("\n" + "=" * 80)
print("✅ PROCESO COMPLETADO - TODOS LOS TEMAS PROCESADOS")
print("=" * 80)
