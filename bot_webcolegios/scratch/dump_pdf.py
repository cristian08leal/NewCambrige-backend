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
            pdf_data = []
            def handle_response(response):
                content_type = response.headers.get("content-type", "")
                if "application/pdf" in content_type:
                    print(f"PDF encontrado en URL: {response.url}")
                    pdf_data.append(response.body())
                    
            page.on("response", handle_response)
            
            print("Presionando Imprimir...")
            try:
                with context.expect_page() as new_page_info:
                    page.locator("input[value*='Imprimir' i], input[value*='imprimir' i], button:has-text('Imprimir'), input.btn-dark").first.click()
                new_page = new_page_info.value
                new_page.on("response", handle_response)
                time.sleep(5)
            except Exception as e:
                print(f"Error expect_page: {e}")
                time.sleep(5)

            if pdf_data:
                with open("scratch/docentes_generado.pdf", "wb") as f:
                    f.write(pdf_data[-1])
                print("PDF guardado en scratch/docentes_generado.pdf")
            else:
                print("No se interceptó PDF. Generando screenshot del main page.")
                page.screenshot(path="scratch/main_after_print.png")

        finally:
            browser.close()

if __name__ == "__main__":
    test()
