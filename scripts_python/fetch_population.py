import pandas as pd
from sqlalchemy import create_engine

# --- CONFIGURACIÓN ---
DB_CONNECTION = "postgresql+psycopg2://postgres:cure_1982@localhost:5432/local_db"
engine = create_engine(DB_CONNECTION)


def inyectar_poblacion_oficial():
    print("--- Inyectando Series de Población Oficiales (INDEC) ---")

    # Datos oficiales (Censo 2010 y 2022) para calibrar la serie
    pob_data = {
        "BUENOS AIRES": [15625084, 17569053],
        "CABA": [2890151, 3120612],
        "CATAMARCA": [367828, 429556],
        "CHACO": [1055259, 1142963],
        "CHUBUT": [509108, 603120],
        "CORDOBA": [3308876, 3978984],
        "CORRIENTES": [992595, 1197553],
        "ENTRE RIOS": [1235994, 1426426],
        "FORMOSA": [530162, 606041],
        "JUJUY": [673307, 797955],
        "LA PAMPA": [318951, 366022],
        "LA RIOJA": [333642, 384607],
        "MENDOZA": [1738929, 2014533],
        "MISIONES": [1101593, 1280960],
        "NEUQUEN": [551266, 726590],
        "RIO NEGRO": [638645, 762067],
        "SALTA": [1214441, 1440672],
        "SAN JUAN": [681055, 818234],
        "SAN LUIS": [432310, 540905],
        "SANTA CRUZ": [273964, 333473],
        "SANTA FE": [3194537, 3556522],
        "SANTIAGO DEL ESTERO": [874006, 1054028],
        "TIERRA DEL FUEGO": [127205, 190641],
        "TUCUMAN": [1448188, 1703186],
    }

    final_data = []
    for prov, values in pob_data.items():
        v2010, v2022 = values
        # Calculamos el crecimiento anual compuesto (CAGR) para esa provincia
        cagr = (v2022 / v2010) ** (1 / 12) - 1

        for anio in range(2011, 2026):
            # Proyectamos cada año con la tasa específica de la provincia
            poblacion_anio = int(v2010 * ((1 + cagr) ** (anio - 2010)))
            final_data.append(
                {"anio": anio, "provincia": prov, "poblacion": poblacion_anio}
            )

    df_pob = pd.DataFrame(final_data)
    df_pob.to_sql("stg_macro_poblacion", engine, if_exists="replace", index=False)
    print(f"✅ Cargadas {len(df_pob)} filas de población calibrada (2011-2025).")
    print(df_pob.query("anio == 2022").head())


if __name__ == "__main__":
    inyectar_poblacion_oficial()
