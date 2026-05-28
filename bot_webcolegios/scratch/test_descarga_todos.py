import time
import os
from playwright.sync_api import sync_playwright
from modules.driver_setup import crear_driver
from modules.autenticacion import autenticar

def test():
    with sync_playwright() as p:
        browser, context, page = crear_driver(p)
        try:
            if not autenticar(page): return
            page.goto("https://www.webcolegios.com/admin_lista_uso_general.php")
            time.sleep(2)
            page.locator("//label[contains(normalize-space(.), 'Docentes')]//input[@type='radio']").first.check()
            time.sleep(1)
            page.locator("input[value='Siguiente']").click()
            time.sleep(3)
            
            # Limpiar descargas
            if os.path.exists("downloads/test_docentes.pdf"):
                os.remove("downloads/test_docentes.pdf")

            with page.expect_download() as download_info:
                page.locator("input[value='Imprimir Todos']").click()
            download = download_info.value
            download.save_as("downloads/test_docentes.pdf")
            print("Guardado en downloads/test_docentes.pdf")

        finally:
            browser.close()

if __name__ == "__main__":
    test()
