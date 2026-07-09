import os

import numpy as np
import pandas as pd

# --- CONFIGURACIÓN ---
INPUT_FILE = r"C:\Users\brian\Documents\Proyectos_IA\clean_data\MASTER_CON_FRICCION.csv"  # Asegúrate de que este archivo esté en la misma carpeta
OUTPUT_FILE = r"C:\Users\brian\Documents\Proyectos_IA\clean_data\DATA_TESIS_FINAL.csv"


def procesar_datos():
    print("⚙️ INICIANDO PROCESAMIENTO DE DATOS...")

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: No se encuentra {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE)

    # 1. ORDENAMIENTO (Vital para rezagos)
    df.sort_values(["provincia", "anio"], inplace=True)

    # 2. VARIABLES CALCULADAS
    # Médicos por mil habitantes
    if "medicos_cada_1000" not in df.columns:
        df["medicos_cada_1000"] = (df["medicos"] / df["poblacion_estimada"]) * 1000

    # Gasto Real per cápita (si falta, estimamos con total)
    if "gasto_real_pcapita" not in df.columns:
        if "gasto_total_real_2023" in df.columns:
            df["gasto_real_pcapita"] = (
                df["gasto_total_real_2023"] / df["poblacion_estimada"]
            )
        else:
            df["gasto_real_pcapita"] = 1  # Dummy de emergencia

    # 3. INSTRUMENTOS (REZAGOS)
    # Gasto Rezagado (t-1) -> Instrumento "Limpio"
    df["gasto_rezagado"] = df.groupby("provincia")["gasto_real_pcapita"].shift(1)

    # Migración (Asegurar que existe)
    if "migracion_neta_est" not in df.columns:
        df["migracion_neta_est"] = 0

    # 4. TRANSFORMACIÓN LOGARÍTMICA (Log-Log para Elasticidades)
    # Sumamos 1 para evitar log(0) o log(negativos)
    vars_log = {
        "tasa_mortalidad_infantil": "ln_tmi",
        "rho_estres": "ln_rho",
        "friccion_km2_por_centro": "ln_friccion",
        "medicos_cada_1000": "ln_medicos",
        "tasa_hacinamiento_critico": "ln_hacin",
        "gasto_rezagado": "ln_gasto_rez",
        "migracion_neta_est": "ln_migracion",
    }

    for orig, new in vars_log.items():
        if orig in df.columns:
            # Tratamiento especial para migración (puede ser negativa)
            if orig == "migracion_neta_est":
                min_val = df[orig].min()
                # Shift para hacerla positiva antes del log
                df[new] = np.log(df[orig] - min_val + 1)
            else:
                df[new] = np.log(df[orig].clip(lower=0) + 1)
        else:
            print(f"⚠️ Advertencia: Variable {orig} no encontrada.")

    # 5. GUARDAR
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Datos procesados y guardados en: {OUTPUT_FILE}")


if __name__ == "__main__":
    procesar_datos()
