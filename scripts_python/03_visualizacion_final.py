import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.api as sm

INPUT_FILE = r"C:\Users\brian\Documents\Proyectos_IA\clean_data\DATA_TESIS_FINAL.csv"


def generar_graficos():
    print("🎨 GENERANDO GRÁFICOS PARA LA DEFENSA...")

    if not os.path.exists(INPUT_FILE):
        print("❌ Error: Ejecuta primero script_01_procesamiento.py")
        return

    df = pd.read_csv(INPUT_FILE)

    # 1. GRÁFICO DE ELASTICIDAD CAUSAL (Regresión Parcial)
    # Queremos mostrar ln_rho vs ln_tmi LIMPIANDO el efecto de otros factores
    vars_plot = ["ln_tmi", "ln_rho", "ln_friccion", "ln_medicos"]
    df_plot = df[vars_plot].replace([np.inf, -np.inf], np.nan).dropna()

    # Residualizamos
    exog = sm.add_constant(df_plot[["ln_friccion", "ln_medicos"]])
    y_res = sm.OLS(df_plot["ln_tmi"], exog).fit().resid
    x_res = sm.OLS(df_plot["ln_rho"], exog).fit().resid

    plt.figure(figsize=(10, 7))
    sns.regplot(
        x=x_res,
        y=y_res,
        scatter_kws={"alpha": 0.5, "color": "steelblue"},
        line_kws={"color": "darkred", "linewidth": 2},
    )

    plt.title(
        "Impacto Causal Aislado: Saturación vs. Mortalidad Infantil\n(Controlando por Recursos y Geografía)",
        fontsize=14,
    )
    plt.xlabel("Log(Índice de Estrés Operativo) | Residualizado", fontsize=12)
    plt.ylabel("Log(Tasa Mortalidad Infantil) | Residualizado", fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("GRAFICO_ELASTICIDAD_FINAL.png", dpi=300)
    print("✅ Gráfico de Elasticidad guardado.")

    # 2. RANKING DE RIESGO (Año 2019)
    df_2019 = df[df["anio"] == 2019].copy()
    if not df_2019.empty:
        # Score simple normalizado
        def norm(s):
            return (s - s.min()) / (s.max() - s.min())

        # Usamos logs para el score
        score = (
            0.4 * norm(df_2019["ln_rho"])
            + 0.3 * norm(df_2019["ln_friccion"])
            + 0.3 * (1 - norm(df_2019["ln_medicos"]))
        ) * 100

        df_2019["RIESGO"] = score
        top5 = df_2019.sort_values("RIESGO", ascending=False).head(5)

        plt.figure(figsize=(8, 5))
        sns.barplot(data=top5, x="RIESGO", y="provincia", palette="Reds_r")
        plt.title("Provincias con Mayor Riesgo de Colapso (2019)", fontsize=14)
        plt.xlabel("Índice de Riesgo (0-100)")
        plt.tight_layout()
        plt.savefig("GRAFICO_RANKING_RIESGO.png", dpi=300)
        print("✅ Gráfico de Ranking guardado.")
    else:
        print("⚠️ No hay datos para 2019 para el ranking.")


if __name__ == "__main__":
    generar_graficos()
