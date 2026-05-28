import time
import os
from playwright.sync_api import sync_playwright

from modules.driver_setup import crear_driver
from modules.autenticacion import autenticar
from modules.navegacion import _ir_a_pagina_formulario, _marcar_checkbox_no_retirados, _click_siguiente, _seleccionar_tomar_datos_de, _click_imprimir

def test():
    with sync_playwright() as p:
        browser, context, page = crear_driver(p)
        try:
            if not autenticar(page):
                print("Fallo autenticacion")
                return

            _ir_a_pagina_formulario(page)
            _marcar_checkbox_no_retirados(page)
            _click_siguiente(page)
            
            time.sleep(2)
            html_pag2 = page.content()
            with open("scratch/pagina2.html", "w", encoding="utf-8") as f:
                f.write(html_pag2)
            page.screenshot(path="scratch/pagina2.png")
            print("Página 2 HTML guardado en scratch/pagina2.html")
            
            _ir_a_pagina_formulario(page)
            _seleccionar_tomar_datos_de(page, "Docentes")
            _marcar_checkbox_no_retirados(page)
            _click_siguiente(page)
            
            new_page = _click_imprimir(context, page)
            if new_page:
                try:
                    new_page.wait_for_load_state("networkidle", timeout=15000)
                except Exception as e:
                    print(f"Error esperando networkidle: {e}")
                time.sleep(10)
                html_imp = new_page.content()
                with open("scratch/imprimir_docentes.html", "w", encoding="utf-8") as f:
                    f.write(html_imp)
                new_page.screenshot(path="scratch/imprimir_docentes.png")
                print("Imprimir HTML guardado en scratch/imprimir_docentes.html")
            else:
                print("Fallo abrir nueva pestaña")
                
        finally:
            browser.close()

if __name__ == "__main__":
    test()
