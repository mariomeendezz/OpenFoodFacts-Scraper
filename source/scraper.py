from pathlib import Path

import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
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


def login_with_requests(email, password):
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
    
    # 4. Verificación de autenticación, asigna la cookie 'user_id'
    if "user_id" in session.cookies or "session" in response.text.lower():
        print("Sesión iniciada correctamente.")
    else:
        print("Advertencia: No se pudo verificar la sesión. Revisa las credenciales.")
        
    return session


def extract_product(driver, url, data):
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
        # <p id="field_quantity">
        #     <span class="field">Quantity: </span>
        #     <span class="field_value" id="field_quantity_value">1 kg</span>
        # </p>

        elements = driver.find_elements(
            By.ID, f"field_{field}_value"
        )

        if elements:
            data[field] = elements[0].text.strip()


    # Obtener el nombre

    # <h2 class="title-1" property="food:name" itemprop="name">
    #     Fromage Blanc Nature - Milky Food Professional - 1 kg
    # </h2>   

    name = driver.find_elements(
        By.CSS_SELECTOR, 'h2[itemprop="name"]'
    )

    data["product_name"] = name[0].text.strip()

    # Obtener "nutri_score", "nova_group" y "green_score"

    # <h4 class="grade_c_title attr_title">Nutri-Score C</h4>

    # <h4 class="grade_e_title attr_title">Ultra-processed foods</h4>
    # <span>1 ultra-processing marker</span>

    # <h4 class="grade_b_title attr_title">Green-Score B</h4>

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

    # <img style="border-radius:10px;margin-bottom:0.5rem;" id="og_image" class="product_image" src="https://images.openfoodfacts.org/images/products/848/000/016/8832/front_es.217.400.jpg"
    #  width="261" height="400" alt="Crema de cacahuetes 100% - Product - es" itemprop="thumbnail" loading="lazy">

    image = driver.find_elements(
        By.ID, "og_image"
    )
    if image:
        data["image_url"] = image[0].get_attribute("src")

    return data


# Inicializar el driver y hacer solicitud GET con la url
url = "https://world.openfoodfacts.org"
driver = webdriver.Chrome()
driver.get(url)

# Iniciar sesion por que sino hay limite de peticiones
session = login_with_requests("mariomendez2003@gmail.com", "Ze3_kdN#4nXygzJ")

############# Extracción de robots.txt con la sesion autenticada
robots = session.get(
    url + "/robots.txt",
    headers={"User-Agent": "Local learning project)"},
    timeout=20,
)
robots.raise_for_status()
# Guardamos robots.txt en la carpeta raíz del proyecto
output_path = Path(__file__).resolve().parent.parent / "robots.txt"
output_path.write_text(robots.text)
#############

############# link Selenium y la sesion loggeada
# Para añadir cookies en Selenium cargamos el dominio en el navegador
driver.get(url)
# Inyectmos las cookies autenticadas de la sesión de requests
for cookie in session.cookies:
    driver.add_cookie({
        "name": cookie.name,
        "value": cookie.value,
        "domain": cookie.domain,
        "path": cookie.path
    })
driver.get(url)
#############


# Numero de paginas a recorrer
n_pages = 2  

dataset = []

for page in range(n_pages):

    # Esperar a que aparezcan los links
    links = WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "a.list_product_a")
        )
    )

    # <a href="https://world.openfoodfacts.org/product/6111246721261/fromage-blanc-nature-milky-food-professional" class="list_product_a" 
    # title="Fromage Blanc Nature – Milky Food Professional – 1&nbsp;kg"> ...
    # </div></div></a>   

    # Extraer todas las URLs
    urls = [link.get_attribute("href") for link in links]

    # <a href="/2" rel="next$nofollow">Next</a>

    # Boton de siguiente pagina
    next_button = driver.find_elements(
        By.CSS_SELECTOR, 'a[rel^="next"]'
    )
    next_url = next_button[0].get_attribute("href") if next_button else None

    # Recorrer todas las URLs (productos)
    for i, product_url in enumerate(urls):
        # Inicializar diccionario vacio para cada producto
        data = {attribute: None for attribute in ATTRIBUTES}

        # Extraer los atributos y guardarlos
        extract_product(driver, product_url, data)
        dataset.append(data)

        print(f"Página {page + 1}, Producto {i + 1}: {product_url}")
    
    if next_url is None:
        break

    # Siguiente página
    driver.get(next_url)


############# Guardar dataset final en CSV
output_path = Path(__file__).resolve().parent.parent / "data" / "dataset.csv"
output_path.parent.mkdir(exist_ok=True)
df = pd.DataFrame(dataset, columns=ATTRIBUTES)
df.to_csv(output_path, index=False)

print(f"Dataset guardado: {len(df)} productos en {output_path}")
#############


driver.quit()
