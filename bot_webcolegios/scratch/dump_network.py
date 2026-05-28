import time
import os
from playwright.sync_api import sync_playwright

from modules.driver_setup import crear_driver
from modules.autenticacion import autenticar
from modules.navegacion import _ir_a_pagina_formulario, _marcar_checkbox_no_retirados, _click_siguiente, _seleccionar_tomar_datos_de

def test():
    with sync_playwright() as p:
        browser, context, page = crear_driver(p)
        try:
            if not autenticar(page):
                print("Fallo autenticacion")
                return

            _ir_a_pagina_formulario(page)
            _seleccionar_tomar_datos_de(page, "Docentes")
            _marcar_checkbox_no_retirados(page)
            _click_siguiente(page)
            
            print("Interceptando respuestas...")
            
            def handle_response(response):
                try:
                    content_type = response.headers.get("content-type", "")
                    url = response.url
                    # ignore some obvious static assets
                    if "text/html" in content_type or "application/pdf" in content_type or "php" in url:
                        print(f"[{content_type}] URL: {url}")
                        # if it's html or pdf, save it
                        if "imprimir" in url.lower() or "pdf" in content_type or "uso_general" in url.lower() or "listas_" in url.lower():
                            safe_name = url.split("/")[-1].split("?")[0]
                            if not safe_name: safe_name = "index.html"
                            ext = ".pdf" if "pdf" in content_type else ".html"
                            # solo guardamos las ultimas respuestas q nos interesan
                            with open(f"scratch/dump_{safe_name}{ext}", "wb") as f:
                                f.write(response.body())
                            print(f" -> Guardado en scratch/dump_{safe_name}{ext}")
                except Exception as e:
                    pass
                    
            page.on("response", handle_response)
            context.on("response", handle_response)
            
            print("Presionando Imprimir...")
            try:
                with context.expect_page(timeout=15000) as new_page_info:
                    page.locator("input[value*='Imprimir' i], input[value*='imprimir' i], button:has-text('Imprimir'), input.btn-dark").first.click()
                new_page = new_page_info.value
                new_page.wait_for_load_state(timeout=10000)
                time.sleep(5)
                new_page.screenshot(path="scratch/popup.png")
            except Exception as e:
                print(f"Error expect_page: {e}")
                time.sleep(5)

        finally:
            browser.close()

if __name__ == "__main__":
    test()
