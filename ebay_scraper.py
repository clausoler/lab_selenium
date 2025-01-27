from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import requests
import os
from dotenv import load_dotenv
 
# Cargar variables de entorno
load_dotenv()
 
# Configuración de Selenium WebDriver
service = Service(ChromeDriverManager().install())
options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=service, options=options)
 
# URL base de eBay
base_url = "https://www.ebay.es"
 
# Inicialización de variables
products = []
current_page = 1
search_query = "Star Wars"
 
try:
    # Abrir la página base
    driver.get(base_url)
    wait = WebDriverWait(driver, 10)

    # Lista de posibles selectores para el campo de búsqueda
    search_selectors = [
        "input#gh-ac",  # ID principal de búsqueda en eBay
        "input[name='_nkw']",  # Nombre alternativo del campo
        "input.search-box",  # Clase genérica de búsqueda
        "input[type='text']",  # Selector genérico
        "input[placeholder='Buscar artículos']"  # Placeholder en español
    ]

    search_box = None
    for selector in search_selectors:
        try:
            search_box = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            print(f"Search box found with selector: {selector}")
            break
        except TimeoutException:
            continue

    if not search_box:
        print("Debug info:")
        print(f"Current URL: {driver.current_url}")
        print("Page source preview:", driver.page_source[:500])
        raise Exception("No se pudo encontrar el campo de búsqueda usando ningún selector conocido")

    search_box.send_keys(search_query)
    search_box.send_keys(Keys.RETURN)

    while True:
        print(f"Scraping página {current_page}...")

        # Esperar a que los productos se carguen
        wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".s-item"))
        )

        # Extraer información de los productos
        items = driver.find_elements(By.CSS_SELECTOR, ".s-item")
        for item in items:
            try:
                title = item.find_element(By.CSS_SELECTOR, ".s-item__title").text
            except:
                title = None

            try:
                price = item.find_element(By.CSS_SELECTOR, ".s-item__price").text
            except:
                price = None

            try:
                sales = item.find_element(By.CSS_SELECTOR, ".s-item__hotness").text
            except:
                sales = None

            products.append({
                "Title": title,
                "Price": price,
                "Sales": sales
            })

        # Intentar encontrar el botón "Siguiente"
        try:
            # Esperar a que el botón "Siguiente" esté presente y sea clickeable
            next_button = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".pagination__next"))
            )
            
            if "disabled" in next_button.get_attribute("class"):
                print("Se alcanzó la última página")
                break
                
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".pagination__next")))
            next_button.click()
            current_page += 1
            
            # Esperar a que la nueva página se cargue
            wait.until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException as e:
            print(f"Timeout esperando el botón 'Siguiente' o la carga de la página: {str(e)}")
            break
        except Exception as e:
            print(f"Error al navegar a la siguiente página: {str(e)}")
            break

finally:
    driver.quit()

# Convertir los datos en un DataFrame
df = pd.DataFrame(products)
df.to_csv("star_wars_ebay.csv", index=False)
print("Scraping completado. Datos guardados en 'star_wars_ebay.csv'.")
 
import pandas as pd
 
# Cargar el archivo csv
 
df = pd.read_csv("star_wars_ebay.csv")
 
import pandas as pd
import matplotlib.pyplot as plt

# Eliminar filas con valores faltantes en la columna de precios
df_clean = df.dropna(subset=['Price'])

# Limpiar y convertir la columna 'Price' a valores numéricos
df_clean['Price'] = df_clean['Price'].str.replace(' EUR', '', regex=False)
df_clean['Price'] = df_clean['Price'].str.replace('.', '').str.replace(',', '.')
df_clean['Price'] = pd.to_numeric(df_clean['Price'], errors='coerce')

# Eliminar valores NaN restantes después de la conversión
df_clean = df_clean.dropna(subset=['Price'])

# Estadísticas descriptivas
price_summary = df_clean['Price'].describe()

# Graficar la distribución de precios
plt.figure(figsize=(10, 5))
plt.hist(df_clean['Price'], bins=20, edgecolor='black')
plt.title('Distribución de Precios de Productos Star Wars en eBay')
plt.xlabel('Precio (€)')
plt.ylabel('Frecuencia')
plt.grid(True)
plt.show()

# Identificar los 5 precios más altos
top_prices = df_clean.nlargest(5, 'Price')

# Imprimir resultados
print(price_summary)
print(top_prices)

# Guardar gráfico 
plt.savefig('precio_distribucion.png')
