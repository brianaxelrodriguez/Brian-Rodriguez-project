import os

import pandas as pd
from sqlalchemy import create_engine

# --- CONFIGURACIÓN ---
engine = create_engine(
    "postgresql+psycopg2://postgres:cure_1982@localhost:5432/local_db"
)
RAW_DIR = r"C:\Users\brian\Documents\Proyectos_IA\data_raw"
CLEAN_DIR = r"C:\Users\brian\Documents\Proyectos_IA\clean_data"


def build_clean_master():
    print("--- Iniciando Integración de Master Panel V2 ---")

    # 1. Crear carpetas si no existen
    os.makedirs(CLEAN_DIR, exist_ok=True)
    os.makedirs("scripts_r", exist_ok=True)

    # 2. Cargar el Master de SQL (el que tiene gasto, mortalidad general y establecimientos)
    # Ignoramos el error de la columna porque la traemos de Julia
    df_sql = pd.read_sql("SELECT * FROM master_panel_analytics", engine)

    # 3. Cargar el resultado de Julia para recuperar el Score DEA
    julia_output = (
        r"C:\Users\brian\Documents\Proyectos_IA\resultados_eficiencia_final.csv"
    )
    if os.path.exists(julia_output):
        df_julia = pd.read_csv(julia_output)[["anio", "provincia", "eficiencia_dea"]]
        # Unimos para recuperar el score
        df_master = pd.merge(df_sql, df_julia, on=["anio", "provincia"], how="left")
    else:
        print(
            "⚠️ No se encontró resultados_eficiencia_final.csv, el score quedará nulo."
        )
        df_master = df_sql
        df_master["eficiencia_dea"] = None

    # 4. Ajustar Scoring (Farrell 0 a 1)
    df_master["score_farrell"] = 1.0 / df_master["eficiencia_dea"].replace(0, pd.NA)

    # 5. INTEGRACIÓN DE NUEVOS DATOS (Experimento Natural / Instrumentos)
    # Aquí puedes añadir la carga de Mortalidad Infantil o Médicos si ya tienes los CSVs limpios
    # Ejemplo con Médicos (si existiera stg_medicos):
    # df_medicos = pd.read_sql("SELECT anio, provincia, medicos_pcapita FROM stg_macro_recursos", engine)
    # df_master = pd.merge(df_master, df_medicos, on=['anio', 'provincia'], how='left')

    # 6. Guardar Master Final para R
    master_path = os.path.join(CLEAN_DIR, "master_panel_r.csv")
    df_master.to_csv(master_path, index=False)

    # También lo subimos a SQL para tenerlo persistente
    df_master.to_sql("master_panel_clean", engine, if_exists="replace", index=False)

    print(f"✅ Master Panel V2 creado en: {master_path}")
    print(f"📊 Columnas disponibles: {df_master.columns.tolist()}")


if __name__ == "__main__":
    build_clean_master()
