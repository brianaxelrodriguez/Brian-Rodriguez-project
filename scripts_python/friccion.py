import os

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

PATH_DATA = (
    r"C:\Users\brian\Documents\Proyectos_IA\clean_data\master_final_geografico.csv"
)


def test_friccion_geografica_v15():
    if not os.path.exists(PATH_DATA):
        print(f"❌ No se encuentra el archivo en {PATH_DATA}")
        return

    df = pd.read_csv(PATH_DATA)

    # 1. Pre-procesamiento: Logaritmos fuera de la fórmula para evitar errores de patsy
    # Usamos +1e-6 para evitar log(0) por seguridad
    df["log_tasa"] = np.log(df["tasa_infantil"] + 1e-6)
    df["log_gasto"] = np.log(df["gasto_real_pcapita"] + 1e-6)

    # 2. Definir zona de fricción (Umbral por mediana de Voronoi)
    umbral = df["dispersion_hospitalaria"].median()
    df["zona_friccion"] = (df["dispersion_hospitalaria"] > umbral).astype(int)

    # 3. Regresiones segmentadas
    # Grupo 0: Baja Dispersión (Nodos cercanos / "Poca Fricción")
    df_baja = df[df["zona_friccion"] == 0].copy()
    # Grupo 1: Alta Dispersión (Nodos lejanos / "Alta Fricción")
    df_alta = df[df["zona_friccion"] == 1].copy()

    print(f"📊 Análisis de Fricción Geográfica (Umbral Voronoi: {umbral:.2e})")
    print(
        f"Muestra: {len(df_baja)} obs en Baja Fricción, {len(df_alta)} obs en Alta Fricción\n"
    )

    try:
        mod_baja = smf.ols("log_tasa ~ log_gasto + score_farrell", data=df_baja).fit()
        mod_alta = smf.ols("log_tasa ~ log_gasto + score_farrell", data=df_alta).fit()

        print("--- RESULTADOS: ZONA DE BAJA FRICCIÓN ---")
        print(
            f"Coef. Gasto: {mod_baja.params['log_gasto']:.4f} | P-valor: {mod_baja.pvalues['log_gasto']:.4f}"
        )
        print(f"R-squared: {mod_baja.rsquared:.4f}")

        print("\n--- RESULTADOS: ZONA DE ALTA FRICCIÓN ---")
        print(
            f"Coef. Gasto: {mod_alta.params['log_gasto']:.4f} | P-valor: {mod_alta.pvalues['log_gasto']:.4f}"
        )
        print(f"R-squared: {mod_alta.rsquared:.4f}")

    except Exception as e:
        print(f"⚠️ Error en la regresión: {e}")


if __name__ == "__main__":
    test_friccion_geografica_v15()
