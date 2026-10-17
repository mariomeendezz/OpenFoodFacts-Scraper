# Extracción de productos de OpenFoodFacts

Este proyecto extrae datos de productos de [OpenFoodFacts](https://es.openfoodfacts.org/) y los guarda en un archivo CSV.
Usa Requests para iniciar sesión, Selenium para consultar las páginas y pandas para guardar los datos.

## Integrantes

- Mario Méndez.
- Adrián Moreno.

## Archivos

```text
.
├── source/
│   ├── main.py           # Ejecuta la extracción y recorre las páginas.
│   └── scraper_utils.py  # Autenticación, extracción y exportación.
├── dataset/
│   └── dataset.csv       # Datos incluidos en el repositorio.
├── requirements.txt      # Dependencias y versiones.
├── robots.txt            # Reglas de acceso descargadas del sitio.
├── LICENCE.txt           # Licencia MIT del código.
├── README.md             # Descripción e instrucciones de uso.
└── .gitignore            # Archivos excluidos del control de versiones.
```

## Uso

Requisitos: Python, Google Chrome, conexión a Internet y una cuenta de OpenFoodFacts.

1. Abre una terminal en la carpeta raíz del repositorio.
2. Instala las dependencias:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Ejecuta `source/main.py` con los parámetros de la tabla.

| Parámetro | Descripción |
| --- | --- |
| `--url` | URL del listado que se va a extraer en `world.openfoodfacts.org`. Por defecto se usa la portada. |
| `--n-pages` | Número de páginas que se consultan. Valor predeterminado: `2`. |
| `--gmail` | Correo electrónico de la cuenta de OpenFoodFacts. |
| `--password` | Contraseña de la cuenta de OpenFoodFacts. |

Sustituye `TU_CORREO` y `TU_CONTRASEÑA` por las credenciales de tu cuenta de OpenFoodFacts.


El programa inicia sesión con las credenciales indicadas en el comando. Carga las cookies en Chrome y abre el listado seleccionado. Extrae los productos y sigue el enlace a la página siguiente. El proceso termina cuando alcanza el límite de `--n-pages` o cuando no hay más páginas.

Cada ejecución guarda el resultado en `dataset/dataset.csv` y actualiza `robots.txt`. El archivo CSV nuevo sustituye al archivo anterior.
El programa establece un tiempo mínimo de 6 segundos para procesar cada producto. Si la extracción tarda menos, espera el tiempo restante antes de continuar.

El CSV contiene el código, el nombre, las puntuaciones nutricionales y ambientales y el grupo NOVA.
También contiene cantidad, envase, marcas, categorías, etiquetas, países y URL de imagen.
Los campos sin datos quedan vacíos.

### Ejemplos replicables de uso

Listado principal. Primeras dos páginas:

```powershell
python source/main.py --n-pages 2 --gmail "TU_CORREO" --password "TU_CONTRASEÑA"
```

Marca Hacendado. Primeras diez páginas:

```powershell
python source/main.py --url "https://world.openfoodfacts.org/facets/brands/Hacendado" --n-pages 10 --gmail "TU_CORREO" --password "TU_CONTRASEÑA"
```

Categoría Cheeses (quesos). Primeras cuatro páginas:

```powershell
python source/main.py --url "https://world.openfoodfacts.org/facets/categories/Cheeses" --n-pages 4 --gmail "TU_CORREO" --password "TU_CONTRASEÑA"
```

## DOI de Zenodo

[https://doi.org/10.5281/zenodo.23438186](https://doi.org/10.5281/zenodo.23438186)
