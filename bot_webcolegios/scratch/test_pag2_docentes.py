import time
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
            with open("scratch/pagina2_docentes.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            page.screenshot(path="scratch/pagina2_docentes.png")
            print("Guardado en scratch/pagina2_docentes.html")
        finally:
            browser.close()

if __name__ == "__main__":
    test()
