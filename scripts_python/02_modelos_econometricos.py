import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import chi2
from statsmodels.sandbox.regression.gmm import IV2SLS

INPUT_FILE = r"C:\Users\brian\Documents\Proyectos_IA\clean_data\DATA_TESIS_FINAL.csv"
OUTPUT_FILE = (
    r"C:\Users\brian\Documents\Proyectos_IA\clean_data\TABLA_RESULTADOS_FINAL.txt"
)


def correr_modelo_ganador():
    print("🧮 EJECUTANDO MODELO ECONOMÉTRICO (IV-2SLS)...")

    if not os.path.exists(INPUT_FILE):
        print("❌ Error: Ejecuta primero script_01_procesamiento.py")
        return

    df = pd.read_csv(INPUT_FILE)

    # DEFINICIÓN DEL MODELO GANADOR
    # Dependiente: ln_tmi
    # Endógena: ln_rho (Saturación)
    # Instrumentos: ln_gasto_rez (Fiscal t-1) + ln_hacin (Estructural)
    # Controles Exógenos: ln_friccion, ln_medicos

    vars_modelo = [
        "ln_tmi",
        "ln_rho",
        "ln_gasto_rez",
        "ln_hacin",
        "ln_friccion",
        "ln_medicos",
    ]
    df_clean = df[vars_modelo].replace([np.inf, -np.inf], np.nan).dropna()

    print(f"   Observaciones válidas para el modelo: {len(df_clean)}")

    # MATRICES
    Y = df_clean["ln_tmi"]
    endog = df_clean["ln_rho"]
    exog_ctrl = sm.add_constant(df_clean[["ln_friccion", "ln_medicos"]])
    instr_excl = df_clean[["ln_gasto_rez", "ln_hacin"]]

    # Matriz X (Regresores) = [Endog, Exog_Ctrl]
    X = pd.concat([endog, exog_ctrl], axis=1)
    # Matriz Z (Instrumentos) = [Instr_Excl, Exog_Ctrl]
    Z = pd.concat([instr_excl, exog_ctrl], axis=1)

    # 1. ETAPA 1: RELEVANCIA (Fuerza del Instrumento)
    stage1 = sm.OLS(endog, Z).fit()
    f_stat = stage1.fvalue
    print("\n--- FUERZA DEL INSTRUMENTO ---")
    print(f"F-Statistic (1ra Etapa): {f_stat:.2f}")

    # 2. ETAPA 2: ESTIMACIÓN IV-2SLS
    model_iv = IV2SLS(Y, X, Z).fit()
    print("\n--- RESULTADOS DEL MODELO ---")
    print(model_iv.summary())

    # 3. TEST DE SARGAN (Validez / Exogeneidad)
    resid = model_iv.resid
    sargan_reg = sm.OLS(resid, Z).fit()
    sargan_stat = len(df_clean) * sargan_reg.rsquared
    # Grados de libertad = num_instrumentos_excluidos - num_endogenas = 2 - 1 = 1
    pval_sargan = 1 - chi2.cdf(sargan_stat, df=1)

    print("\n--- TEST DE SARGAN ---")
    print(f"P-Value: {pval_sargan:.4f}")
    if pval_sargan > 0.05:
        print("✅ INSTRUMENTOS VÁLIDOS (No se rechaza H0 de exogeneidad)")
    else:
        print("⚠️ Advertencia: Posible endogeneidad")

    # GUARDAR
    with open(OUTPUT_FILE, "w") as f:
        f.write(model_iv.summary().as_text())
        f.write("\n\nDIAGNÓSTICO:\n")
        f.write(f"F-Stat First Stage: {f_stat:.2f}\n")
        f.write(f"Sargan P-Value: {pval_sargan:.4f}\n")
    print(f"📄 Resultados guardados en {OUTPUT_FILE}")


if __name__ == "__main__":
    correr_modelo_ganador()
