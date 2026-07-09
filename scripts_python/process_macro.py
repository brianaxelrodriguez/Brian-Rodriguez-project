import datetime
import os

import pandas as pd
from sqlalchemy import create_engine

# --- CONFIGURACIÓN ---
DB_CONNECTION = "postgresql+psycopg2://postgres:cure_1982@localhost:5432/local_db"
engine = create_engine(DB_CONNECTION)
MACRO_DIR = r"C:\Users\brian\Documents\Proyectos_IA\data_raw\MACRO"


def procesar_ipc_final():
    # Usamos el que ya sabemos que tiene datos
    f_path = os.path.join(MACRO_DIR, "sh_ipc_01_26.xls")
    print(f"--- Procesando: {f_path} ---")

    if not os.path.exists(f_path):
        print("❌ No existe el archivo.")
        return

    try:
        # 1. Cargamos el excel completo sin cabeceras
        df_raw = pd.read_excel(f_path, header=None)

        fila_fechas = -1
        fila_valores = -1

        # 2. Localizamos las filas por contenido
        for i, row in df_raw.iterrows():
            row_list = [str(x).lower() for x in row.tolist()]

            # Buscamos la fila que tiene las fechas (buscamos un patrón de fecha o "total nacional")
            if "total nacional" in row_list:
                fila_fechas = i

            # Buscamos la fila del Nivel General
            if "nivel general" in row_list:
                fila_valores = i
                break

        if fila_fechas == -1 or fila_valores == -1:
            print(
                "❌ No se detectaron las filas de 'Total nacional' o 'Nivel general'."
            )
            return

        # 3. Extraer columnas de datos
        fechas = df_raw.iloc[fila_fechas, :]
        valores = df_raw.iloc[fila_valores, :]

        series = []
        for f, v in zip(fechas, valores):
            # Intentamos convertir f a fecha y v a número
            try:
                # Validamos que f sea una fecha (Timestamp) y v un número
                if isinstance(f, (pd.Timestamp, datetime.date)) and (
                    isinstance(v, (int, float))
                ):
                    series.append({"fecha": f, "inflacion_mensual": float(v)})
            except:
                continue

        df_clean = pd.DataFrame(series)

        if df_clean.empty:
            print(
                "❌ El mapeo de fechas/valores resultó vacío. Revisa el formato de celdas."
            )
            return

        # 4. Calcular Inflación Anual Acumulada
        df_clean["anio"] = df_clean["fecha"].dt.year
        df_clean["factor"] = (df_clean["inflacion_mensual"] / 100) + 1

        # Multiplicamos los factores mensuales para obtener el anual
        ipc_anual = df_clean.groupby("anio")["factor"].prod().reset_index()
        ipc_anual.columns = ["anio", "inflacion_anual_acumulada"]

        # 5. Guardar en SQL
        ipc_anual.to_sql("stg_macro_ipc", engine, if_exists="replace", index=False)
        print("✅ ¡IPC cargado exitosamente!")
        print(ipc_anual)

    except Exception as e:
        print(f"❌ Error crítico: {e}")


if __name__ == "__main__":
    procesar_ipc_final()
