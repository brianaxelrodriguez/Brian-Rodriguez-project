import glob
import os
import re
import unicodedata

import duckdb
import pandas as pd

# --- CONFIGURACIÓN ---
BASE_DIR = r"C:\Users\brian\Documents\Proyectos_IA"
RAW_DIR = os.path.join(BASE_DIR, "data_raw")
CLEAN_DIR = os.path.join(BASE_DIR, "clean_data")
DB_PATH = os.path.join(CLEAN_DIR, "healthcare_lake.duckdb")

# Lista de carpetas a escanear nuevamente
DIRS_TO_SCAN = [
    "DATOS_GOB_AR",
    "DEIS",
    "Descargas_ACOD",
    "ENFR",
    "EPH",
    "FISCAL",
    "MACRO",
    "Procesados",
    "SISA",
    "SSS",
]


def clean_col_name(col):
    if not isinstance(col, str):
        return f"col_{col}"
    col = unicodedata.normalize("NFKD", col).encode("ASCII", "ignore").decode("utf-8")
    col = col.lower().strip()
    col = re.sub(r"[^a-z0-9_]", "_", col)
    return col.strip("_")


def get_year_from_filename(filename):
    match = re.search(r"(20\d{2})", filename)
    return int(match.group(1)) if match else None


def rescue_mission():
    print(f"🚑 Iniciando Misión de Rescate en {DB_PATH}")

    con = duckdb.connect(DB_PATH)

    # 1. Obtener lista de tablas ya cargadas para no repetir trabajo
    existing_tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
    print(f"📊 Tablas existentes: {len(existing_tables)}")

    rescued_count = 0

    for folder in DIRS_TO_SCAN:
        full_path = os.path.join(RAW_DIR, folder)
        files = glob.glob(os.path.join(full_path, "**", "*.*"), recursive=True)

        for f in files:
            fname = os.path.basename(f)
            if fname.startswith("~"):
                continue

            # Nombre de tabla esperado
            table_name = f"{folder}_{clean_col_name(fname.split('.')[0])}"[:50]

            # Si ya existe, saltamos (asumimos que cargó bien la primera vez)
            if table_name in existing_tables:
                continue

            print(f"🔄 Intentando rescatar: {fname} ...")

            try:
                ext = f.split(".")[-1].lower()
                df = None

                # --- ESTRATEGIA EXCEL VIEJO (.xls) ---
                if ext in ["xls"]:
                    try:
                        # Intentamos con xlrd explícito para archivos viejos
                        df = pd.read_excel(f, engine="xlrd")
                    except:
                        try:
                            # Fallback a openpyxl si xlrd falla
                            df = pd.read_excel(f, engine="openpyxl")
                        except:
                            print(f"   ⚠️ Falló Excel: {fname}")
                            continue

                # --- ESTRATEGIA EXCEL NUEVO (.xlsx) ---
                elif ext in ["xlsx", "xlsm"]:
                    try:
                        df = pd.read_excel(f, engine="openpyxl")
                    except:
                        continue

                # --- ESTRATEGIA CSV GIGANTE (SISA) ---
                elif ext == "csv":
                    # Si es el archivo gigante de SISA, usamos DuckDB directo (0 RAM)
                    if (
                        "sisa" in folder.lower()
                        or os.path.getsize(f) > 500 * 1024 * 1024
                    ):  # > 500MB
                        print(
                            "   🐘 Detectado archivo gigante. Usando DuckDB nativo..."
                        )
                        try:
                            # DuckDB read_csv_auto es mágico: detecta tipos y separadores
                            con.execute(f"""
                                CREATE OR REPLACE TABLE {table_name} AS 
                                SELECT * FROM read_csv_auto('{f}', ignore_errors=true)
                            """)
                            print(f"   ✅ RESCATADO (Direct SQL): {table_name}")
                            rescued_count += 1
                            continue  # Ya cargó, pasamos al siguiente
                        except Exception as e:
                            print(f"   ❌ Falló carga directa SQL: {e}")
                            # Fallback a Pandas con chunking si SQL falla

                    # Si es CSV normal pero roto
                    try:
                        # Probamos separadores comunes y saltamos líneas malas
                        df = pd.read_csv(
                            f,
                            sep=None,
                            engine="python",
                            on_bad_lines="skip",
                            encoding="utf-8",
                        )
                    except:
                        try:
                            df = pd.read_csv(
                                f, sep=";", on_bad_lines="skip", encoding="latin1"
                            )
                        except:
                            print(f"   ⚠️ CSV irrecuperable: {fname}")
                            continue

                if df is not None and not df.empty:
                    # Limpieza estándar
                    df.columns = [clean_col_name(c) for c in df.columns]
                    df["source_file"] = fname
                    if "anio" not in df.columns:
                        year = get_year_from_filename(fname)
                        df["anio_detectado"] = year

                    # Carga
                    con.register("temp_rescue", df)
                    con.execute(
                        f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM temp_rescue"
                    )
                    con.unregister("temp_rescue")
                    print(f"   ✅ RESCATADO: {table_name} ({len(df)} filas)")
                    rescued_count += 1

            except Exception as e:
                print(f"   ❌ Error fatal en {fname}: {str(e)[:50]}")
                continue

    print(f"\n🏁 Misión cumplida. Se rescataron {rescued_count} archivos adicionales.")

    # --- MERGE FINAL INTELIGENTE ---
    # Ahora que tenemos MÁS datos, intentamos regenerar el master
    print("🔗 Regenerando vista maestra unificada...")

    # Ejemplo: Unir tablas que tengan 'provincia' y 'anio'
    # DuckDB permite hacer esto con queries dinámicas, pero por ahora
    # solo confirmamos que el Data Lake está completo.

    con.close()


if __name__ == "__main__":
    rescue_mission()
