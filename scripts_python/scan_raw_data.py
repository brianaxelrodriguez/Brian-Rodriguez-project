import os
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

# Ajustamos a tus rutas
RAW_DIR = r"C:\Users\brian\Documents\Proyectos_IA\data_raw"
CLEAN_DIR = r"C:\Users\brian\Documents\Proyectos_IA\clean_data"


def analyze_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    info = {"path": file_path, "type": ext, "columns": "N/A"}

    try:
        if ext == ".csv":
            # Solo leemos la primera fila para no saturar la RAM
            df = pd.read_csv(file_path, nrows=0)
            info["columns"] = "|".join(df.columns.tolist())
        elif ext in [".xls", ".xlsx"]:
            df = pd.read_excel(file_path, nrows=0)
            info["columns"] = "|".join(df.columns.astype(str).tolist())
    except Exception as e:
        info["columns"] = f"Error: {str(e)[:50]}"

    return info


def scan_laboratory():
    print("--- Iniciando Escaneo Profundo ---")
    os.makedirs(CLEAN_DIR, exist_ok=True)

    file_list = []
    for root, _, files in os.walk(RAW_DIR):
        for file in files:
            if not file.startswith("~$") and os.path.splitext(file)[1].lower() in [
                ".csv",
                ".xlsx",
                ".xls",
            ]:
                file_list.append(os.path.join(root, file))

    print(
        f"🚀 {len(file_list)} archivos encontrados. Utilizando hilos para procesar..."
    )

    # Aquí el Ryzen 9 5950X hará la magia
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(analyze_file, file_list))

    df_index = pd.DataFrame(results)
    index_path = os.path.join(CLEAN_DIR, "index_raw_files.csv")
    df_index.to_csv(index_path, index=False)

    print(f"✅ Índice creado en: {index_path}")

    # Búsqueda de variables críticas para tu paper
    keywords = [
        "mortalidad",
        "infantil",
        "medico",
        "profesional",
        "cama",
        "establecimiento",
        "clinica",
    ]
    matches = df_index[
        df_index["path"].str.contains("|".join(keywords), case=False)
        | df_index["columns"].str.contains("|".join(keywords), case=False)
    ]

    print("\n--- POSIBLES VARIABLES PARA 2SLS / OLS / CUANTILES ---")
    if not matches.empty:
        # Mostramos solo los primeros 15 hallazgos para no saturar la terminal
        print(matches[["path", "type"]].head(15).to_string())
    else:
        print("No se encontraron coincidencias directas. Revisa el CSV de índice.")


if __name__ == "__main__":
    scan_laboratory()
