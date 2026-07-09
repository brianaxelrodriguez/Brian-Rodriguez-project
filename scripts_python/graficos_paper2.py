import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

print("=== INICIANDO CAPA DE SERVING: GRÁFICOS PAPER 2 (PDF) ===")

plt.style.use("seaborn-v0_8-ticks")
sns.set_context("paper", font_scale=1.2)
plt.rcParams["font.family"] = "serif"
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False

PATH_STATA = r"C:\Users\brian\Documents\Proyectos_IA\data_raw\PAPER 2\stata_output"
PATH_OUT = r"C:\Users\brian\Documents\Proyectos_IA\data_raw\PAPER 2\graficos"
os.makedirs(PATH_OUT, exist_ok=True)


# -----------------------------------------------------------------------------
# GRÁFICO 1: Event Study del Shift-Share (Pre-Trends del Instrumento)
# -----------------------------------------------------------------------------
def grafico_1_iv_pretrends():
    archivo = os.path.join(PATH_STATA, "iv_pretrends.csv")
    if not os.path.exists(archivo):
        print("[ERROR] No se encuentra iv_pretrends.csv")
        return

    df = pd.read_csv(archivo)

    plt.figure(figsize=(8, 5))
    plt.errorbar(
        df["anio"],
        df["coef_iv"],
        yerr=[df["coef_iv"] - df["ci_low"], df["ci_high"] - df["coef_iv"]],
        fmt="-o",
        color="darkred",
        capsize=4,
        ecolor="black",
        markerfacecolor="black",
        markeredgecolor="black",
    )
    plt.axhline(0, color="black", linestyle="--", linewidth=1.2)
    plt.axvline(2017.5, color="gray", linestyle=":", alpha=0.7)

    # Anotaciones tácticas
    plt.text(
        2014,
        0.15,
        "Período Pre-Shock:\nInstrumento NO correlacionado\ncon Mortalidad",
        color="dimgray",
        ha="center",
        fontsize=9,
    )
    plt.text(
        2018.5,
        -0.15,
        "Devaluación 2018:\nDescapitalización\nEfectiva",
        color="darkred",
        ha="center",
        fontsize=9,
    )

    plt.title(
        "Validez del Instrumento: Pre-Trends del Shift-Share (Reduced Form)", pad=15
    )
    plt.ylabel(r"Coeficiente Marginal ($\beta_{IV}$)")
    plt.xlabel("Año")

    plt.tight_layout()
    plt.savefig(os.path.join(PATH_OUT, "Fig1_Instrument_Pretrends.pdf"))
    plt.close()
    print("[*] Gráfico 1 (Pre-trends del IV) generado.")


grafico_1_iv_pretrends()
print("[ÉXITO] Capa gráfica del Paper 2 completada.")
