import glob
import os
import re

import pandas as pd
from sqlalchemy import create_engine

# --- CONFIGURACIÓN ---
BASE_DIR = r"C:\Users\brian\Documents\Proyectos_IA\data_raw"
DB_HOST = "localhost"
DB_NAME = "local_db"
DB_USER = "postgres"
DB_PASS = "cure_1982"
DB_PORT = "5432"

DB_CONNECTION = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

try:
    engine = create_engine(DB_CONNECTION)
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    exit()


# --- 1. PROCESADOR FISCAL (APNF) - ESTRATEGIA UNPIVOT ---
def procesar_fiscal_provincial():
    print("\n--- Procesando FISCAL (APNF - Modo Unpivot) ---")
    path_fiscal = os.path.join(BASE_DIR, "FISCAL", "APNF_Trimestral")
    all_files = glob.glob(os.path.join(path_fiscal, "*.xls*"))

    if not all_files:
        return

    dfs = []
    print(f"Procesando {len(all_files)} archivos...")

    for f in all_files:
        try:
            nombre = os.path.basename(f)
            parts = nombre.replace(".xls", "").split("_")
            if len(parts) < 3:
                continue

            anio = int(parts[1])
            trimestre = parts[2]

            # 1. BUSCAR LA FILA "CONCEPTO"
            df_preview = pd.read_excel(f, header=None, nrows=20)
            header_idx = -1

            for i, row in df_preview.iterrows():
                row_str = (
                    row.astype(str).str.lower().replace(r"\n", " ", regex=True).tolist()
                )
                # Buscamos "concepto"
                if any("concepto" in str(x).lower() for x in row_str):
                    header_idx = i
                    break

            if header_idx == -1:
                print(f"⚠️ OMITIENDO {nombre}: No se encontró 'Concepto'.")
                continue

            # 2. LEER CON LA CABECERA CORRECTA
            df = pd.read_excel(f, header=header_idx)

            # 3. LIMPIEZA DE NOMBRES DE COLUMNAS (Quitar \n y espacios)
            # Ejemplo: "CIUDAD DE \nBUENOS AIRES" -> "caba"
            new_cols = []
            for c in df.columns:
                c_clean = str(c).lower().replace("\n", " ").strip()
                # Mapeos manuales para estandarizar provincias
                if "ciudad de" in c_clean or "caba" in c_clean:
                    c_clean = "caba"
                elif "buenos aires" in c_clean and "ciudad" not in c_clean:
                    c_clean = "buenos_aires"
                elif "concepto" in c_clean:
                    c_clean = "concepto"
                else:
                    c_clean = re.sub(r"[^a-z0-9_]", "", c_clean.replace(" ", "_"))
                new_cols.append(c_clean)

            df.columns = new_cols

            # 4. UNPIVOT (MELT)
            # Transformamos columnas de provincias en filas
            # Identificamos columnas que NO son provincias
            id_vars = ["concepto"]
            value_vars = [
                c
                for c in df.columns
                if c not in id_vars
                and "unnamed" not in c
                and "total" not in c
                and "consolidado" not in c
            ]

            if not value_vars:
                print(f"⚠️ {nombre}: No se detectaron columnas de provincias.")
                continue

            df_melted = df.melt(
                id_vars=id_vars,
                value_vars=value_vars,
                var_name="provincia_origen",
                value_name="monto",
            )

            # 5. FINALIZAR
            df_melted["anio"] = anio
            df_melted["trimestre"] = trimestre
            df_melted["monto"] = pd.to_numeric(
                df_melted["monto"], errors="coerce"
            ).fillna(0)

            dfs.append(df_melted)

        except Exception as e:
            print(f"❌ Error en {nombre}: {e}")

    if dfs:
        print("Consolidando Fiscal...")
        df_final = pd.concat(dfs, ignore_index=True)
        # Guardamos en una tabla NUEVA diseñada para formato largo
        df_final.to_sql(
            "stg_fiscal_apnf_long", engine, if_exists="replace", index=False
        )
        print(f"✅ ¡Éxito! {len(df_final)} filas procesadas (Formato Largo).")
    else:
        print("❌ No se procesaron datos fiscales.")


# --- 2. DEIS Y REFES (Sin cambios, mantener igual) ---
def procesar_mortalidad_deis():
    pass  # Ya cargado, descomenta si necesitas recargar


def procesar_oferta_refes():
    pass  # Ya cargado, descomenta si necesitas recargar


if __name__ == "__main__":
    procesar_fiscal_provincial()
    # procesar_mortalidad_deis()
    # procesar_oferta_refes()
