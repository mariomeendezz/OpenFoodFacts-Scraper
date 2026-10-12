from scraper_utils import (
    ATTRIBUTES,
    extract_product,
    get_page_product_urls,
    inject_cookies_to_selenium,
    login_with_requests,
    save_dataset_to_csv,
    save_robots_txt,
)
from selenium import webdriver

BASE_URL = "https://world.openfoodfacts.org"
EMAIL = "mariomendez2003@gmail.com"
PASSWORD = "Ze3_kdN#4nXygzJ"
N_PAGES = 2 # Nº de páginas a recorrer


def main():
    # 1. Autenticación y descarga de robots.txt
    session = login_with_requests(EMAIL, PASSWORD) # Iniciar sesion por que sino hay limite de peticiones
    save_robots_txt(session, BASE_URL)

    # 2. Configuración e inicio de Selenium
    driver = webdriver.Chrome()
    #driver.get(url) # Inicializar el driver y hacer solicitud GET con la url
    
    try:
        inject_cookies_to_selenium(driver, session, BASE_URL)
        dataset = [] # Inicializar diccionario vacio para cada producto

        # 3. Recorrido de las URLS (páginas y productos)
        for page in range(N_PAGES):
            urls, next_url = get_page_product_urls(driver)


            for i, product_url in enumerate(urls):
                # Inicializar diccionario vacío para cada producto (mismo formato original)
                data = {attribute: None for attribute in ATTRIBUTES}

                # Extraer los atributos y guardarlos
                extract_product(driver, product_url, data)
                dataset.append(data)

                # Imprimir el nombre extraído para verificar que coge datos reales
                print(f"Página {page + 1}, Producto {i + 1}/{len(urls)}: {data['product_name']} ({product_url})")

            if not next_url:
                break

            # Siguiente página
            driver.get(next_url)

        # 4. Exportar el dataset final
        save_dataset_to_csv(dataset)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()