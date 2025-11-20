import ollama
import os
import glob
import time
from PIL import Image
import io

# --- CONFIGURACIÓN ---
CARPETA_IMAGENES = "imagenes_curso"
CARPETA_TEMPORAL = "temp_ocr"
CARPETA_SALIDA = "libros"
MODELO = "deepseek-ocr"
PREFIJO = "interaccionismo"  # ← CAMBIAR AQUÍ SEGÚN EL TEMA
TIMEOUT = 180  # 3 minutos máximo por imagen (1024x1024 es máximo soportado)

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
    """Redimensiona imagen a resolución válida (Gundam: n×640×640 + 1×1024×1024)
    Mínimo: 640×640, Máximo: 1024×1024"""
    try:
        img = Image.open(ruta_imagen)
        original_w, original_h = img.size
        
        # Si ya está dentro de límites válidos (640-1024), no redimensionar
        if 640 <= original_w <= 1024 and 640 <= original_h <= 1024:
            return ruta_imagen
        
        # Redimensionar: primero limitar al máximo (1024)
        ratio = min(1024 / original_w, 1024 / original_h)
        nuevo_w = int(original_w * ratio)
        nuevo_h = int(original_h * ratio)
        
        # Si quedó menor a 640 en alguna dimensión, escalar a mínimo 640
        if nuevo_w < 640 or nuevo_h < 640:
            ratio = max(640 / nuevo_w, 640 / nuevo_h)
            nuevo_w = int(nuevo_w * ratio)
            nuevo_h = int(nuevo_h * ratio)
            
            # Pero asegurar que no supere 1024
            if nuevo_w > 1024:
                nuevo_w = 1024
            if nuevo_h > 1024:
                nuevo_h = 1024
        
        # Redondear a múltiplos de 32
        nuevo_w = max(32, (nuevo_w // 32) * 32)
        nuevo_h = max(32, (nuevo_h // 32) * 32)
        
        img.thumbnail((nuevo_w, nuevo_h), Image.Resampling.LANCZOS)
        
        # Guardar en archivo temporal
        temp_path = os.path.join(CARPETA_TEMPORAL, "temp_resized.jpg")
        img.save(temp_path, "JPEG", quality=90)
        print(f"   🔄 Redimensionada: {original_w}x{original_h} → {nuevo_w}x{nuevo_h}")
        return temp_path
    except Exception as e:
        pass
    
    # Si falla, retornar original
    return ruta_imagen


# Buscar imágenes
tipos = ('*.png', '*.jpg', '*.jpeg')
imagenes = []
for tipo in tipos:
    imagenes.extend(glob.glob(os.path.join(CARPETA_IMAGENES, tipo)))

# Filtrar solo con el prefijo especificado
imagenes = [img for img in imagenes if PREFIJO.lower() in os.path.basename(img).lower()]
imagenes.sort()

print(f"📸 Encontré {len(imagenes)} imágenes con prefijo '{PREFIJO}'\n")

if len(imagenes) == 0:
    print("❌ No se encontraron imágenes. Abortando.")
    exit(1)

# ============ FASE 1: PROCESAR IMÁGENES ============
print("=" * 80)
print("FASE 1: Procesando imágenes...")
print("=" * 80 + "\n")

procesadas = 0
saltadas = 0
errores = 0

for idx, img in enumerate(imagenes, 1):
    nombre = os.path.basename(img)
    nombre_base = os.path.splitext(nombre)[0]
    txt_file = os.path.join(CARPETA_TEMPORAL, f"{nombre_base}.txt")
    
    # Saltar si ya existe
    if os.path.exists(txt_file):
        print(f"[{idx:02d}/{len(imagenes)}] ⏭️  {nombre:<40} (ya procesada)")
        saltadas += 1
        continue
    
    print(f"[{idx:02d}/{len(imagenes)}] 🔄 {nombre:<40}", end="", flush=True)
    
    try:
        inicio = time.time()
        
        # Redimensionar si es muy grande
        img_procesada = redimensionar_imagen(img)
        
        # Llamar a Ollama con la imagen redimensionada
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
        
        if texto and len(texto) > 10:  # Validar que tiene contenido real
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write(texto)
            
            chars = len(texto)
            print(f" ✅ ({tiempo_proc:.1f}s, {chars} chars)")
            procesadas += 1
        else:
            print(f" ⚠️  (resultado vacío)")
            errores += 1
    
    except TimeoutError:
        print(f" ⏱️  TIMEOUT (>5min) - SALTADA")
        errores += 1
    except ConnectionError as e:
        print(f" 🔌 ERROR CONEXIÓN - SALTADA")
        errores += 1
    except Exception as e:
        msg = str(e)[:30]
        print(f" ❌ ERROR: {msg}")
        errores += 1

print(f"\n{'=' * 80}")
print(f"Resumen FASE 1:")
print(f"  ✅ Procesadas:  {procesadas}")
print(f"  ⏭️  Saltadas:   {saltadas}")
print(f"  ❌ Errores:     {errores}")
print(f"  📊 Total:       {len(imagenes)}")
print(f"{'=' * 80}\n")

# ============ FASE 2: CONSOLIDAR ARCHIVOS ============
print("=" * 80)
print("FASE 2: Consolidando archivos TXT...")
print("=" * 80 + "\n")

txt_files = sorted(glob.glob(os.path.join(CARPETA_TEMPORAL, "*.txt")))
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

print(f"\n{'=' * 80}")
print(f"Resumen FASE 2:")
print(f"  📄 Documentos consolidados: {contador}")
print(f"  📊 Caracteres totales:      {len(contenido_total):,}")
print(f"{'=' * 80}\n")

# ============ FASE 3: GUARDAR ARCHIVO FINAL ============
print("=" * 80)
print("FASE 3: Guardando archivo final...")
print("=" * 80 + "\n")

salida = os.path.join(CARPETA_SALIDA, f"{PREFIJO}.txt")

if contenido_total.strip():
    # Agregar header
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
    print(f"✅ PROCESO COMPLETADO!\n")
    print(f"📄 Archivo guardado: {salida}")
    print(f"📊 Tamaño: {tamaño_kb:.1f} KB")
    print(f"📈 Documentos: {contador}")
    print(f"📝 Caracteres: {len(contenido_total):,}\n")
    print(f"{'=' * 80}")
else:
    print(f"❌ Error: No se generó contenido para guardar")
    print(f"{'=' * 80}")
