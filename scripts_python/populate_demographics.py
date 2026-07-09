import pandas as pd
from sqlalchemy import create_engine

# --- CONFIGURACIÓN ---
DB_CONNECTION = "postgresql+psycopg2://postgres:cure_1982@localhost:5432/local_db"
engine = create_engine(DB_CONNECTION)


def inyectar_poblacion():
    print("--- Generando Serie Histórica de Población (INDEC Proy) ---")

    # Datos base aproximados (Censo 2010 y 2022 interpolados)
    # Para un rigor extremo se usarían las tablas de proyecciones por año,
    # aquí creamos el motor de crecimiento.
    provincias = [
        "BUENOS AIRES",
        "CABA",
        "CATAMARCA",
        "CHACO",
        "CHUBUT",
        "CORDOBA",
        "CORRIENTES",
        "ENTRE RIOS",
        "FORMOSA",
        "JUJUY",
        "LA PAMPA",
        "LA RIOJA",
        "MENDOZA",
        "MISIONES",
        "NEUQUEN",
        "RIO NEGRO",
        "SALTA",
        "SAN JUAN",
        "SAN LUIS",
        "SANTA CRUZ",
        "SANTA FE",
        "SANTIAGO DEL ESTERO",
        "TIERRA DEL FUEGO",
        "TUCUMAN",
    ]

    # Población aproximada 2022 (Censo)
    pob_2022 = {
        "BUENOS AIRES": 17569053,
        "CABA": 3120612,
        "CATAMARCA": 429556,
        "CHACO": 1142963,
        "CHUBUT": 603120,
        "CORDOBA": 3978984,
        "CORRIENTES": 1197553,
        "ENTRE RIOS": 1426426,
        "FORMOSA": 606041,
        "JUJUY": 797955,
        "LA PAMPA": 366022,
        "LA RIOJA": 384607,
        "MENDOZA": 2014533,
        "MISIONES": 1280960,
        "NEUQUEN": 726590,
        "RIO NEGRO": 762067,
        "SALTA": 1440672,
        "SAN JUAN": 818234,
        "SAN LUIS": 540905,
        "SANTA CRUZ": 333473,
        "SANTA FE": 3556522,
        "SANTIAGO DEL ESTERO": 1054028,
        "TIERRA DEL FUEGO": 190641,
        "TUCUMAN": 1703186,
    }

    data = []
    for anio in range(2011, 2027):
        for prov in provincias:
            # Estimación simple por tasa de crecimiento intercensal (~1% anual variable)
            # Gasto per cápita requiere un denominador suave
            factor = 1 + (anio - 2022) * 0.0105
            poblacion_estimada = int(pob_2022[prov] * factor)
            data.append(
                {"anio": anio, "provincia": prov, "poblacion": poblacion_estimada}
            )

    df_pob = pd.DataFrame(data)
    df_pob.to_sql("stg_macro_poblacion", engine, if_exists="replace", index=False)
    print("✅ Tabla 'stg_macro_poblacion' creada con éxito.")


if __name__ == "__main__":
    inyectar_poblacion()
