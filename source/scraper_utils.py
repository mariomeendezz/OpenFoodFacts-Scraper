import argparse
from pathlib import Path

import pandas as pd
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Definir campos y atributos finales del dataset
FIELDS = [
    "quantity",
    "packaging",
    "brands",
    "categories",
    "labels",
    "countries"
]
ATTRIBUTES = [
    "code",
    "product_name",
    "nutri_score",
    "nova_group",
    "green_score"
] + FIELDS + ["image_url"]


def parse_arguments() -> argparse.Namespace:
    """
    Parsea los argumentos de línea de comandos.
    """
    parser = argparse.ArgumentParser(description="Extrae productos de OpenFoodFacts.")

    parser.add_argument(
        "--url",
        type=str,
        default="https://world.openfoodfacts.org",
        help="URL del listado de OpenFoodFacts que se va a extraer (por ejemplo, una categoría).",
    )

    parser.add_argument(
        "--n-pages",
        type=int,
        default=2,
        help="Número de páginas que se van a recorrer.",
    )

    parser.add_argument(
        "--gmail",
        type=str,
        required=True,
        help="Correo electrónico para iniciar sesión en OpenFoodFacts.",
    )

    parser.add_argument(
        "--password",
        type=str,
        required=True,
        help="Contraseña para iniciar sesión en OpenFoodFacts.",
    )

    return parser.parse_args()


def login_with_requests(
    email: str,
    password: str,
) -> requests.Session:
    """
    Realiza el login en OpenFoodFacts con requests y retorna una sesión autenticada.
    """
    session = requests.Session()
    
    # Modificacion de las cabeceras para simular una petición de navegador real
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": "https://world.openfoodfacts.org/cgi/session.pl"
    })
    
    login_url = "https://world.openfoodfacts.org/cgi/session.pl"
    
    # 1. Petición GET inicial para recibir cookies de sesión previas
    session.get(login_url, timeout=20)
    
    # 2. Atributos y campos del formulario
    payload = {
        "user_id": email,
        "password": password,
        ".submit": "Sign in"
    }
    
    # 3. Envío de las credenciales mediante POST
    response = session.post(login_url, data=payload, timeout=20)
    response.raise_for_status()
    
    # 4. Comprobar que se ha recibido una cookie de sesión.
    authenticated = any(
        cookie.name == "session"
        and bool(cookie.value)
        and not cookie.is_expired()
        for cookie in session.cookies
    )

    if not authenticated:
        session.close()
        raise RuntimeError(
            "No se pudo confirmar el inicio de sesión. "
            "Revisa las credenciales."
        )

    print("Sesión iniciada correctamente.")
    return session


def save_robots_txt(
    session: requests.Session,
    base_url: str,
) -> None:
    """
    Descarga y guarda el archivo robots.txt del sitio web.
    """
    robots_url = f"{base_url}/robots.txt"
    response = session.get(
        robots_url,
        headers={"User-Agent": "Local learning project)"},
        timeout=20,
    )
    response.raise_for_status()

    output_path = Path(__file__).resolve().parent.parent / "robots.txt"
    output_path.write_text(response.text)
    print(f"Archivo robots.txt guardado en: {output_path}")


def inject_cookies_to_selenium(
    driver: WebDriver,
    session: requests.Session,
    base_url: str,
) -> None:
    """
    Inyecta las cookies de la sesión autenticada de requests en el navegador Selenium.
    """
    driver.get(base_url)  # Cargar el dominio para establecer cookies

    for cookie in session.cookies:
        driver.add_cookie({
            "name": cookie.name,
            "value": cookie.value,
            "domain": cookie.domain,
            "path": cookie.path
        })
    
    print("Cookies inyectadas en Selenium.")


def extract_product(
    driver: WebDriver,
    url: str,
    data: dict[str, str | None],
) -> dict[str, str | None]:
    """
    Realiza la extracción de datos de un producto en OpenFoodFacts.
    """
    driver.get(url)

    # Sacar el code directamente de la url
    code = driver.current_url.split("/product/")[1].split("/")[0]
    data["code"] = code

    # Esperar a obtener el HTML (pausa hasta que encuentra el nombre)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'h2[itemprop="name"]')
        )
    )

    # Obtener todos los atributos de fields
    for field in FIELDS:
        # ----------------------------------------------
        # EJEMPLO DE HTML:
        # ----------------------------------------------
        # <p id="field_quantity">
        #     <span class="field">Quantity: </span>
        #     <span class="field_value" id="field_quantity_value">1 kg</span>
        # </p>
        # ----------------------------------------------

        elements = driver.find_elements(
            By.ID, f"field_{field}_value"
        )

        if elements:
            data[field] = elements[0].text.strip()


    # Obtener el nombre

    # ----------------------------------------------
    # EJEMPLO DE HTML:
    # ----------------------------------------------
    # <h2 class="title-1" property="food:name" itemprop="name">
    #     Fromage Blanc Nature - Milky Food Professional - 1 kg
    # </h2>   
    # ----------------------------------------------

    name = driver.find_elements(
        By.CSS_SELECTOR, 'h2[itemprop="name"]'
    )

    data["product_name"] = name[0].text.strip()

    

    # Obtener "nutri_score", "nova_group" y "green_score"

    # ----------------------------------------------
    # EJEMPLO DE HTML:
    # ----------------------------------------------
    # <h4 class="grade_c_title attr_title">Nutri-Score C</h4>

    # <h4 class="grade_e_title attr_title">Ultra-processed foods</h4>
    # <span>1 ultra-processing marker</span>

    # <h4 class="grade_b_title attr_title">Green-Score B</h4>
    # ----------------------------------------------

    cards = driver.find_elements(
        By.CSS_SELECTOR, ".attribute_card"
    )

    for card in cards:
        titles = card.find_elements(By.CSS_SELECTOR, "h4.attr_title")

        if not titles:
            continue

        title = titles[0].text.strip()

        if title.startswith("Nutri-Score"):
            data["nutri_score"] = title

        elif "processed" in card.text.lower():
            data["nova_group"] = title

        elif title.startswith("Green-Score"):
            data["green_score"] = title

    # Obtener url de la imagen

    # ----------------------------------------------
    # EJEMPLO DE HTML:
    # ----------------------------------------------
    # <img style="border-radius:10px;margin-bottom:0.5rem;" id="og_image" 
    #  class="product_image" src="https://images.openfoodfacts.org/images/products/848/000/016/8832/front_es.217.400.jpg"
    #  width="261" height="400" alt="Crema de cacahuetes 100% - Product - es" itemprop="thumbnail" loading="lazy">
    # ----------------------------------------------

    image = driver.find_elements(
        By.ID, "og_image"
    )
    if image:
        data["image_url"] = image[0].get_attribute("src")

    return data


def get_page_product_urls(driver: WebDriver) -> tuple[list[str | None], str | None]:
    """
    Obtiene las URLs de los productos en la página actual y la URL de la siguiente página.
    """
    # Esperar a que aparezcan los links
    links = WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "a.list_product_a")
        )
    )

    # Extraer todas las URLs
    urls = [link.get_attribute("href") for link in links]

    # Boton de siguiente pagina
    next_button = driver.find_elements(
        By.CSS_SELECTOR, 'a[rel^="next"]'
    )
    next_url = next_button[0].get_attribute("href") if next_button else None

    return urls, next_url


def save_dataset_to_csv(dataset: list[dict[str, str | None]]) -> None:
    """
    Guarda el dataset final en un archivo CSV.
    """
    output_path = Path(__file__).resolve().parent.parent / "dataset" / "dataset.csv"
    output_path.parent.mkdir(exist_ok=True)
    df = pd.DataFrame(dataset, columns=ATTRIBUTES)
    df.to_csv(output_path, index=False)

    print(f"Dataset guardado: {len(df)} productos en {output_path}")

