#!/usr/bin/env python3
# =============================================================================
# main.py — Punto de entrada del bot WebColegios
# =============================================================================

import os
import sys
import time
import glob
from playwright.sync_api import sync_playwright
from utils.logger import get_logger
from modules.driver_setup import crear_driver
from modules.autenticacion import autenticar
from modules.navegacion import navegar_y_generar_listado, navegar_pagina2_y_descargar_pdfs, navegar_y_descargar_docentes
from modules.extraccion import (
    extraer_estudiantes,
    extraer_docentes,
    extraer_titulares_de_pdfs,
    extraer_desde_pdf,
    guardar_json,
    guardar_csv_respaldo,
)
from modules.database import insertar_estudiantes, insertar_docentes, get_credentials_scraping
from config.settings import DOWNLOAD_DIR

logger = get_logger("main")


# =============================================================================
#  RUTA: ESTUDIANTES  (no modificar)
# =============================================================================

def run_scrape_estudiantes(exec_id=None):
    logger.info("=" * 60)
    logger.info("Bot WebColegios - iniciando (Ruta: Estudiantes)")
    logger.info("=" * 60)

    inicio = time.time()
    try:
        logger.info("[1/7] Iniciando Playwright Chromium...")
        
        # Limpiar PDFs anteriores para no confundir la extracción
        pdfs_viejos = glob.glob(os.path.join(DOWNLOAD_DIR, "*.pdf"))
        for f in pdfs_viejos:
            try:
                os.remove(f)
            except Exception:
                pass

        with sync_playwright() as p:
            browser, context, page = crear_driver(p)
            try:
                logger.info("[2/7] Obteniendo credenciales y autenticando en WebColegios...")
                creds = get_credentials_scraping()
                if creds:
                    auth_ok = autenticar(page, url=creds["url"], usuario=creds["usuario"],
                                         password=creds["password"], tipo_usuario=creds["tipo_usuario"])
                else:
                    logger.warning("⚠️  No hay credenciales en tabla login, usando variables de entorno como fallback.")
                    auth_ok = autenticar(page)
                if not auth_ok:
                    raise Exception("Autenticación fallida.")

                dashboard_url = page.url
                logger.info(f"Dashboard URL guardada: {dashboard_url}")

                logger.info("[3/7] Navegando al listado de estudiantes (Fase 1: Código)...")
                listado_page_fase1 = navegar_y_generar_listado(context, page, "Estudiantes", usar_documento=False)
                if not listado_page_fase1:
                    raise Exception("Navegación fallida Fase 1.")

                logger.info("[4/7] Extrayendo datos del listado HTML (Fase 1)...")
                estudiantes_fase1 = extraer_estudiantes(listado_page_fase1)
                if listado_page_fase1:
                    listado_page_fase1.close()
                
                logger.info("[4.5/7] Navegando al listado de estudiantes (Fase 2: Documento)...")
                listado_page_fase2 = navegar_y_generar_listado(context, page, "Estudiantes", usar_documento=True)
                if not listado_page_fase2:
                    raise Exception("Navegación fallida Fase 2.")
                
                logger.info("[4.6/7] Extrayendo datos del listado HTML (Fase 2)...")
                estudiantes_fase2 = extraer_estudiantes(listado_page_fase2)
                if listado_page_fase2:
                    listado_page_fase2.close()

                # Cruce de datos (Merge)
                logger.info("[4.8/7] Cruzando Fase 1 (Código) y Fase 2 (Documento)...")
                map_estudiantes = {}
                for est in estudiantes_fase1:
                    nombre = est['nombre']
                    codigo = est['documento']  # En fase 1, esto es el código
                    map_estudiantes[nombre] = {
                        **est,
                        "codigo_interno": codigo,
                        "documento": None
                    }
                
                for est2 in estudiantes_fase2:
                    nombre = est2['nombre']
                    doc_real = est2['documento']  # En fase 2, esto es el documento real
                    if nombre in map_estudiantes:
                        map_estudiantes[nombre]['documento'] = doc_real
                    else:
                        map_estudiantes[nombre] = {
                            **est2,
                            "codigo_interno": None,
                            "documento": doc_real
                        }

                # Aplicar reglas de nulidad y fallback
                estudiantes = []
                for nombre, datos in map_estudiantes.items():
                    cod = datos.get("codigo_interno")
                    doc = datos.get("documento")
                    
                    if not cod and not doc:
                        logger.warning(f"❌ Rechazado (Sin código ni doc): {nombre}")
                        continue
                    
                    if cod and not doc:
                        datos['documento'] = None
                    elif doc and not cod:
                        datos['codigo_interno'] = doc
                        
                    estudiantes.append(datos)

                if not estudiantes:
                    raise Exception("No se extrajeron estudiantes válidos tras el cruce.")

                logger.info(f"Estudiantes extraídos combinados: {len(estudiantes)}")

                logger.info("[5/7] Guardando JSON y CSV de respaldo...")
                guardar_json(estudiantes)
                guardar_csv_respaldo(estudiantes)

                logger.info("[6/7] Insertando en base de datos PostgreSQL...")
                logs_insercion = insertar_estudiantes(estudiantes, exec_id=exec_id)
                # Opcional: imprimir un resumen de los logs de inserción
                conflictos = sum(1 for l in logs_insercion.get("detalles", []) if l["accion"] == "CONFLICTO")
                logger.info(f"Terminado insert: Conflictos={conflictos}")

                duracion = time.time() - inicio
                logger.info("=" * 60)
                logger.info(f"[7/7] Bot finalizado correctamente en {duracion:.1f}s")
                logger.info("=" * 60)
                return True
            finally:
                browser.close()
    except Exception as e:
        logger.error(f"Error en ejecución: {e}", exc_info=True)
        return False


# =============================================================================
#  RUTA: DOCENTES (2 fases separadas)
# =============================================================================

def run_scrape_docentes(exec_id=None):
    """
    Flujo de scraping de docentes en 2 fases:

    FASE A — Descarga de PDFs por grado (titulares):
      1. Ir a la página del formulario (modo Estudiantes, default)
      2. Marcar "No incluir retirados"
      3. Click "Siguiente" → Página 2 con listado de grados + PDFs individuales
      4. Descargar TODOS los PDFs por grado
      5. Extraer el nombre del docente TITULAR de cada PDF

    FASE B — Lista general de docentes (código/documento):
      6. Volver al formulario
      7. Seleccionar "Docentes" en el selector de tipo
      8. Marcar "No incluir retirados"
      9. Click "Siguiente" → Click "Imprimir"
      10. Extraer docentes (consecutivo, documento, nombre)

    CRUCE:
      11. Combinar docentes (Fase B) con titulares (Fase A) por nombre
      12. Insertar en tabla `docentes` de PostgreSQL
    """
    logger.info("=" * 60)
    logger.info("Bot WebColegios - iniciando (Ruta: Docentes)")
    logger.info("=" * 60)

    inicio = time.time()
    try:
        with sync_playwright() as p:
            browser, context, page = crear_driver(p)
            try:
                # ── Autenticación ──────────────────────────────────────────
                logger.info("[1/9] Iniciando Playwright Chromium...")
                logger.info("[2/9] Obteniendo credenciales y autenticando en WebColegios...")
                creds = get_credentials_scraping()
                if creds:
                    auth_ok = autenticar(page, url=creds["url"], usuario=creds["usuario"],
                                         password=creds["password"], tipo_usuario=creds["tipo_usuario"])
                else:
                    logger.warning("⚠️  No hay credenciales en tabla login, usando variables de entorno como fallback.")
                    auth_ok = autenticar(page)
                if not auth_ok:
                    raise Exception("Autenticación fallida.")

                # ── FASE A: Limpiar PDFs anteriores ────────────────────────
                logger.info("[3/9] Limpiando PDFs de titulares anteriores...")
                pdfs_viejos = glob.glob(os.path.join(DOWNLOAD_DIR, "titulares_grado_*.pdf"))
                eliminados = 0
                for f in pdfs_viejos:
                    try:
                        os.remove(f)
                        eliminados += 1
                    except Exception:
                        pass
                if eliminados:
                    logger.info(f"🗑️  {eliminados} PDF(s) antiguo(s) eliminados")

                # ── FASE A: Descargar PDFs de grados ───────────────────────
                logger.info("[4/9] FASE A — Navegando a Página 2 para descargar PDFs de titulares...")
                rutas_pdfs = navegar_pagina2_y_descargar_pdfs(context, page)

                if not rutas_pdfs:
                    logger.warning(
                        "⚠️  No se descargaron PDFs de titulares. "
                        "Los docentes serán insertados sin asignación de titular."
                    )

                # ── FASE A: Extraer titulares de los PDFs ──────────────────
                logger.info(f"[5/9] FASE A — Extrayendo titulares de {len(rutas_pdfs)} PDF(s)...")
                titulares = extraer_titulares_de_pdfs(rutas_pdfs)
                logger.info(f"      Titulares encontrados: {len(titulares)}")

                # ── FASE B: Limpiar PDF de estudiantes anterior ──────────────
                logger.info("[5b/9] Limpiando PDF de estudiantes del directorio de descargas...")
                pdfs_viejos_est = glob.glob(os.path.join(DOWNLOAD_DIR, "*.pdf"))
                for f in pdfs_viejos_est:
                    fname = os.path.basename(f)
                    if "titulares" not in fname:  # No borrar los PDFs de titulares ya descargados
                        try:
                            os.remove(f)
                            logger.info(f"🗑️  PDF antiguo eliminado: {fname}")
                        except Exception:
                            pass

                # ── FASE B: Navegar y descargar PDF de listado de docentes ─────────
                logger.info("[6/9] FASE B — Descargando PDF del listado de Docentes...")
                pdf_docentes = navegar_y_descargar_docentes(page)
                if not pdf_docentes:
                    raise Exception("No se pudo descargar el PDF del listado de docentes.")

                # ── FASE B: Extraer docentes del PDF ──────────────────────────────
                logger.info("[7/9] FASE B — Extrayendo datos de Docentes del PDF...")
                registros_raw = extraer_desde_pdf(pdf_docentes, "docentes")
                if not registros_raw:
                    raise Exception("No se extrajeron docentes del PDF.")

                # Enriquecer con datos de titulares
                docentes = extraer_docentes(None, titulares, registros_raw=registros_raw)

                if not docentes:
                    raise Exception("No se extrajeron docentes del listado.")

                logger.info(f"      Docentes extraídos: {len(docentes)}")

                # ── Log de estadísticas de cruce ────────────────────────────
                con_titular = sum(1 for d in docentes if d.get("grado_titular"))
                sin_titular = len(docentes) - con_titular
                logger.info(f"      Con asignación titular: {con_titular} | Sin asignación: {sin_titular}")

                # ── Guardar respaldos ───────────────────────────────────────
                logger.info("[8/9] Guardando JSON y CSV de respaldo...")
                guardar_json(docentes, os.path.join(DOWNLOAD_DIR, "docentes.json"))
                guardar_csv_respaldo(docentes, os.path.join(DOWNLOAD_DIR, "docentes_respaldo.csv"))

                # ── Insertar en base de datos ───────────────────────────────
                logger.info("[9/9] Insertando docentes en base de datos PostgreSQL...")
                resumen = insertar_docentes(docentes, exec_id=exec_id)

                duracion = time.time() - inicio
                logger.info("=" * 60)
                logger.info(
                    f"Bot Docentes finalizado en {duracion:.1f}s — "
                    f"Insertados: {resumen.get('insertados', 0)} | "
                    f"Omitidos: {resumen.get('omitidos', 0)} | "
                    f"Errores: {resumen.get('errores', 0)}"
                )
                logger.info("=" * 60)
                return True

            finally:
                browser.close()

    except Exception as e:
        logger.error(f"Error en ejecución de docentes: {e}", exc_info=True)
        return False


# =============================================================================
#  ENTRY POINT CLI
# =============================================================================

def main():
    if len(sys.argv) > 1 and sys.argv[1].lower() == "docentes":
        run_scrape_docentes()
    else:
        run_scrape_estudiantes()

if __name__ == "__main__":
    main()
