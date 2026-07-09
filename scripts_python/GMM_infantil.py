import pandas as pd
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql+psycopg2://postgres:cure_1982@localhost:5432/local_db"
)


def build_advanced_master():
    # 1. Cargar base actual
    df = pd.read_sql("SELECT * FROM master_panel_clean", engine)

    # 2. Simulación de carga de nuevas variables (ajusta con tus rutas de scan_raw)
    # Aquí integraríamos los hallazgos del scan: mortalidad_infantil, medicos, enfermeros
    # Por ahora, aseguramos la estructura para los modelos espaciales

    # Coordenadas de capitales para Voronoi/Hotelling (Centroides aproximados)
    coords = {
        "CABA": [-34.60, -58.38],
        "BUENOS AIRES": [-34.92, -57.95],
        "CORDOBA": [-31.42, -64.18],
        "SANTA FE": [-31.63, -60.70],
        "MENDOZA": [-32.88, -68.84],
        "SALTA": [-24.78, -65.41],
        "RIO NEGRO": [-40.81, -63.00],  # Viedma
        # ... completar el resto en el script final
    }

    # Imputación de mortalidad infantil (DEIS) y profesionales (SISA)
    # df = pd.merge(df, df_infantil, on=['anio', 'provincia'], how='left')

    df.to_csv("clean_data/master_advanced.csv", index=False)
    print("✅ Master Advanced V3 creado para análisis espacial y sintético.")


build_advanced_master()
