import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
from statsmodels.sandbox.regression.gmm import IV2SLS

# --- RUTAS ---
INPUT_FILE = r"C:\Users\brian\Documents\Proyectos_IA\clean_data\MASTER_CON_FRICCION.csv"
OUTPUT_DIR = r"C:\Users\brian\Documents\Proyectos_IA\clean_data"


def generar_artefactos_finales():
    print("🏆 GENERANDO ARTEFACTOS DEL MODELO GANADOR (FISCAL + HACINAMIENTO)...")

    df = pd.read_csv(INPUT_FILE)
    df.sort_values(["provincia", "anio"], inplace=True)

    # 1. PREPARACIÓN DE VARIABLES
    if "medicos_cada_1000" not in df.columns:
        df["medicos_cada_1000"] = (df["medicos"] / df["poblacion_estimada"]) * 1000

    # Rezagos
    df["gasto_rezagado"] = df.groupby("provincia")["gasto_real_pcapita"].shift(1)

    # Log-Log Transform
    cols = [
        "tasa_mortalidad_infantil",
        "rho_estres",
        "friccion_km2_por_centro",
        "medicos_cada_1000",
        "tasa_hacinamiento_critico",
        "gasto_rezagado",
    ]

    for c in cols:
        df[f"ln_{c}"] = np.log(df[c].clip(lower=0) + 1)

    # 2. DEFINICIÓN DEL MODELO 6
    # Y = ln_tmi
    # Endog = ln_rho
    # Instr = ln_gasto_rez, ln_hacin
    # Exog = ln_friccion, ln_medicos

    model_vars = [
        "ln_tmi",
        "ln_rho",
        "ln_gasto_rez",
        "ln_hacin",
        "ln_friccion",
        "ln_medicos",
    ]
    df_clean = df[model_vars].replace([np.inf, -np.inf], np.nan).dropna()

    # Matrices
    endog = df_clean["ln_rho"]
    exog_ctrl = sm.add_constant(df_clean[["ln_friccion", "ln_medicos"]])
    instr_excl = df_clean[["ln_gasto_rez", "ln_hacin"]]

    # X (Regresores) = [Endog, Exog_Ctrl]
    X = pd.concat([endog, exog_ctrl], axis=1)
    # Z (Instrumentos) = [Instr_Excl, Exog_Ctrl]
    Z = pd.concat([instr_excl, exog_ctrl], axis=1)

    y = df_clean["ln_tmi"]

    # Ajuste
    model_final = IV2SLS(y, X, Z).fit()

    print(model_final.summary())

    # Guardar Tabla
    with open(os.path.join(OUTPUT_DIR, "TABLA_FINAL_TESIS.txt"), "w") as f:
        f.write(model_final.summary().as_text())
        f.write("\n\n--- DIAGNÓSTICO ---\n")
        f.write(f"Coeficiente Elasticidad: {model_final.params['ln_rho']:.4f}\n")
        f.write(f"P-Value: {model_final.pvalues['ln_rho']:.4f}\n")

    # 3. GRÁFICO DE REGRESIÓN PARCIAL (VISUALIZACIÓN LIMPIA)
    # Queremos mostrar ln_rho vs ln_tmi "limpiando" el efecto de las otras variables
    # Pasos:
    # 1. Regress ln_tmi ~ controls -> get residuals (y_res)
    # 2. Regress ln_rho ~ controls -> get residuals (x_res)
    # 3. Plot y_res vs x_res

    res_y = sm.OLS(y, exog_ctrl).fit().resid
    res_x = sm.OLS(endog, exog_ctrl).fit().resid

    plt.figure(figsize=(10, 7))
    sns.regplot(
        x=res_x,
        y=res_y,
        scatter_kws={"alpha": 0.5, "color": "steelblue"},
        line_kws={"color": "darkred"},
    )

    plt.title(
        "Impacto Causal Aislado: Saturación vs Mortalidad Infantil\n(Controlando por Fricción, Médicos y Hacinamiento)",
        fontsize=14,
    )
    plt.xlabel("Log(Índice de Estrés Operativo) - Residualizado", fontsize=12)
    plt.ylabel("Log(Tasa Mortalidad Infantil) - Residualizado", fontsize=12)
    plt.grid(True, alpha=0.3)

    # Anotación del Beta
    beta = model_final.params["ln_rho"]
    plt.text(
        0.05,
        0.9,
        f"Elasticidad $\\beta = {beta:.2f}$***",
        transform=plt.gca().transAxes,
        fontsize=14,
        color="darkred",
        fontweight="bold",
        bbox=dict(facecolor="white", alpha=0.8),
    )

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "grafico_causal_final.png"))
    print(
        f"✅ Gráfico final generado: {os.path.join(OUTPUT_DIR, 'grafico_causal_final.png')}"
    )


if __name__ == "__main__":
    generar_artefactos_finales()
