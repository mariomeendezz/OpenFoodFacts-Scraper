import time
from selenium import webdriver

from scraper_utils import (
    ATTRIBUTES,
    parse_arguments,
    extract_product,
    get_page_product_urls,
    inject_cookies_to_selenium,
    login_with_requests,
    save_dataset_to_csv,
    save_robots_txt,
)


BASE_URL = "https://world.openfoodfacts.org"

def main():
    # 1. Parsear argumentos de línea de comandos
    args = parse_arguments()

    # 2. Autenticación y descarga de robots.txt
    session = login_with_requests(args.gmail, args.password)
    save_robots_txt(session, BASE_URL)

    # 3. Configuración e inicio de Selenium
    driver = webdriver.Chrome()
    
    try:
        user_agent = driver.execute_script("return navigator.userAgent;")
        print(f"User-Agent de Selenium: {user_agent}")

        inject_cookies_to_selenium(driver, session, BASE_URL)
        # Abrir el listado elegido después de cargar las cookies de la sesión.
        driver.get(args.url)
        dataset = [] # Inicializar diccionario vacio para cada producto

        # 4. Recorrido de las URLS (páginas y productos)
        for page in range(args.n_pages):
            urls, next_url = get_page_product_urls(driver)

            for i, product_url in enumerate(urls):
                # Inicializar diccionario vacío para cada producto (mismo formato original)
                t0 = time.monotonic()
                data = {attribute: None for attribute in ATTRIBUTES}

                # Extraer los atributos y guardarlos
                extract_product(driver, product_url, data)
                dataset.append(data)

                # Imprimir el nombre extraído para verificar que coge datos reales
                print(f"Página {page + 1}, Producto {i + 1}/{len(urls)}: {data['product_name']} ({product_url})")

                dt = time.monotonic() - t0

                # Completar un mínimo de 6 segundos por producto.
                time.sleep(max(0, 6 - dt))

            if not next_url or page + 1 >= args.n_pages:
                break

            # Siguiente página
            driver.get(next_url)

        # 5. Exportar el dataset final
        save_dataset_to_csv(dataset)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
