import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

# --- CONFIGURACIÓN DE RUTAS ---
BASE_PATH = r"C:\Users\brian\Documents\Proyectos_IA\data_raw\Demografia"
URLS = {
    "Defunciones": "https://www.argentina.gob.ar/salud/deis/datos/defunciones",
    "Nacimientos": "https://www.argentina.gob.ar/salud/deis/datos/nacidosvivos"
}

def download_file(url, folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    local_filename = os.path.join(folder, url.split('/')[-1])
    
    # Evitar descargar si ya existe
    if os.path.exists(local_filename):
        print(f"   ⏩ Saltando (ya existe): {url.split('/')[-1]}")
        return local_filename

    try:
        with requests.get(url, stream=True, timeout=20) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"   ✅ Descargado: {url.split('/')[-1]}")
        return local_filename
    except Exception as e:
        print(f"   ❌ Error al descargar {url}: {e}")
        return None

def scrape_deis_data():
    print("🕸️ Iniciando Scraping de Microdatos DEIS...")
    
    for category, url in URLS.items():
        print(f"\n📂 Procesando sección: {category}")
        folder = os.path.join(BASE_PATH, category)
        
        try:
            response = requests.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscamos todos los enlaces que terminen en extensiones de datos
            links_found = 0
            for link in soup.find_all('a', href=True):
                href = link['href']
                if any(href.lower().endswith(ext) for ext in ['.zip', '.csv', '.xlsx', '.rar', '.7z']):
                    file_url = urljoin(url, href)
                    download_file(file_url, folder)
                    links_found += 1
                    time.sleep(1) # Respeto al servidor
            
            if links_found == 0:
                print(f"   ⚠️ No se encontraron enlaces de descarga directos en {category}.")
                
        except Exception as e:
            print(f"   ❌ Error al acceder a {url}: {e}")

if __name__ == "__main__":
    scrape_deis_data()