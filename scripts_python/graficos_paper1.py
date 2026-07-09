import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

print("=== INICIANDO CAPA DE SERVING: GRÁFICOS PAPER 1 (PDF) ===")

# =============================================================================
# 0. CONFIGURACIÓN INICIAL Y ESTÉTICA (Standard JPubE)
# =============================================================================
np.random.seed(42)
plt.style.use("seaborn-v0_8-ticks")
sns.set_context("paper", font_scale=1.2)
plt.rcParams["font.family"] = "serif"
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False

PATH_DATA = r"C:\Users\brian\Documents\Proyectos_IA\data_raw\Procesados\BASE_FUSIONADA_VITALES_MASTER.csv"
PATH_STATA = r"C:\Users\brian\Documents\Proyectos_IA\data_raw\PAPER 1\stata_output"
PATH_OUT = r"C:\Users\brian\Documents\Proyectos_IA\data_raw\PAPER 1\graficos"

os.makedirs(PATH_STATA, exist_ok=True)
os.makedirs(PATH_OUT, exist_ok=True)

# =============================================================================
# 1. CARGA DE DATOS Y FEATURE ENGINEERING ESTRUCTURAL
# =============================================================================
df = pd.read_csv(PATH_DATA)

# Estandarización estricta de variables dependientes
if "GASTO_SALUD_PC_REAL" in df.columns and "LN_GASTO_SALUD_PC_REAL" not in df.columns:
    df["LN_GASTO_SALUD_PC_REAL"] = np.log(df["GASTO_SALUD_PC_REAL"].replace(0, np.nan))

df["medicos_pc"] = (df["MEDICOS"] / df["POBLACION_LAGRANGE"]) * 1000
df["ln_medicos_pc"] = np.log(df["medicos_pc"].replace(0, np.nan))

# Generación de la proxy de Rigidez Laboral si no existe
if "prop_planta_perm" not in df.columns:
    df["prop_planta_perm"] = df["MEDICOS"] / (df["MEDICOS"] + df["ENFERMEROS"])

# Cálculo de la Exposición Fiscal Basal (promedio pre-shock 2011-2015)
df_pre = (
    df[df["ANIO"] < 2016]
    .groupby("PROV_ID")["INDICE_DEPENDENCIA_FISCAL"]
    .mean()
    .reset_index()
)
df_pre.rename(columns={"INDICE_DEPENDENCIA_FISCAL": "tau_i"}, inplace=True)
df = pd.merge(df, df_pre, on="PROV_ID", how="left")

# Calcular terciles para agrupaciones visuales
df_unique_prov = df[["PROV_ID", "tau_i"]].drop_duplicates()
df_unique_prov["tercil_tau"] = pd.qcut(
    df_unique_prov["tau_i"], 3, labels=["Baja", "Media", "Alta Exposición"]
)
df = pd.merge(df, df_unique_prov[["PROV_ID", "tercil_tau"]], on="PROV_ID", how="left")


# =============================================================================
# 2. FUNCIONES GENERADORAS DE GRÁFICOS
# =============================================================================


# -----------------------------------------------------------------------------
# GRÁFICO 1: Distribución Exposición Fiscal Basal
# -----------------------------------------------------------------------------
def grafico_1_distribucion(df):
    plt.figure(figsize=(6, 4))
    df_cross = df[df["ANIO"] == 2017].copy()

    sns.histplot(
        df_cross["tau_i"],
        bins=8,
        kde=False,
        color="dimgray",
        alpha=0.7,
        edgecolor="black",
    )
    media_tau = df_cross["tau_i"].mean()
    plt.axvline(
        media_tau, color="red", linestyle="--", label=f"Media ({media_tau:.2f})"
    )

    plt.title("Distribución de la Exposición Fiscal Basal (2017)", pad=15)
    plt.xlabel(r"Proporción de Transferencias Nacionales ($\tau_i$)")
    plt.ylabel("Frecuencia (Provincias)")
    plt.text(
        0.95, 0.85, f"N = {len(df_cross)}", transform=plt.gca().transAxes, ha="right"
    )

    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(PATH_OUT, "Fig1_Distribucion_Tau.pdf"))
    plt.close()
    print("[*] Gráfico 1 (Distribución Exposición Fiscal) generado.")


# -----------------------------------------------------------------------------
# GRÁFICO 2: Distribución de Rigidez Institucional (Pre-Shock)
# -----------------------------------------------------------------------------
def grafico_2_distribucion_rigidez(df):
    plt.figure(figsize=(6, 4))
    df_cross = df[df["ANIO"] == 2017].copy()

    sns.histplot(
        df_cross["prop_planta_perm"],
        bins=8,
        kde=False,
        color="steelblue",
        alpha=0.7,
        edgecolor="black",
    )
    media_rig = df_cross["prop_planta_perm"].mean()
    plt.axvline(
        media_rig, color="red", linestyle="--", label=f"Media ({media_rig:.2f})"
    )

    plt.title("Distribución de la Rigidez Laboral Basal (2017)", pad=15)
    plt.xlabel(r"Proporción de Planta Permanente ($Rigidez_i$)")
    plt.ylabel("Frecuencia (Provincias)")
    plt.text(
        0.95, 0.85, f"N = {len(df_cross)}", transform=plt.gca().transAxes, ha="right"
    )

    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(PATH_OUT, "Fig2_Distribucion_Rigidez.pdf"))
    plt.close()
    print("[*] Gráfico 2 (Distribución Rigidez) generado.")


# -----------------------------------------------------------------------------
# GRÁFICO 3: Pre-trends crudos (Validación visual de parallel trends)
# -----------------------------------------------------------------------------
def grafico_3_pre_trends(df):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    df_trend = (
        df.groupby(["ANIO", "tercil_tau"], observed=True)[
            ["LN_GASTO_SALUD_PC_REAL", "ln_medicos_pc"]
        ]
        .mean()
        .reset_index()
    )

    # Panel A: Gasto
    sns.lineplot(
        data=df_trend,
        x="ANIO",
        y="LN_GASTO_SALUD_PC_REAL",
        hue="tercil_tau",
        marker="o",
        ax=axes[0],
        palette="Greys_r",
    )
    axes[0].axvline(2017.5, color="red", linestyle="--", alpha=0.5)
    axes[0].set_title("Evolución del Log Gasto Salud PC Real")
    axes[0].set_ylabel("Log Gasto Real")
    axes[0].set_xlabel("Año")

    # Panel B: Médicos
    sns.lineplot(
        data=df_trend,
        x="ANIO",
        y="ln_medicos_pc",
        hue="tercil_tau",
        marker="o",
        ax=axes[1],
        palette="Greys_r",
    )
    axes[1].axvline(2017.5, color="red", linestyle="--", alpha=0.5)
    axes[1].set_title("Evolución del Log Médicos PC")
    axes[1].set_ylabel("Log Médicos por 1000 hab.")
    axes[1].set_xlabel("Año")

    plt.tight_layout()
    plt.savefig(os.path.join(PATH_OUT, "Fig3_PreTrends.pdf"))
    plt.close()
    print("[*] Gráfico 3 (Pre-trends) generado.")


# -----------------------------------------------------------------------------
# GRÁFICO 4: Event Study Estructural (Lectura de Coeficientes de Stata)
# -----------------------------------------------------------------------------
def grafico_4_event_study():
    archivo_stata = os.path.join(PATH_STATA, "event_study_results.csv")
    if not os.path.exists(archivo_stata):
        raise FileNotFoundError(
            f"[ADVERTENCIA] No se encontró {archivo_stata}. Ejecute el script de Stata primero. Se omitirá el Gráfico 4."
        )

    df_es = pd.read_csv(archivo_stata)
    req_cols = [
        "anio",
        "coef_gasto",
        "ci_lower_gasto",
        "ci_upper_gasto",
        "coef_medicos",
        "ci_lower_medicos",
        "ci_upper_medicos",
    ]
    assert all(c in df_es.columns for c in req_cols), (
        "[ERROR FATAL]: Faltan columnas en el CSV de Stata."
    )

    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)

    # Panel A: Médicos
    axes[0].errorbar(
        df_es["anio"],
        df_es["coef_medicos"],
        yerr=[
            df_es["coef_medicos"] - df_es["ci_lower_medicos"],
            df_es["ci_upper_medicos"] - df_es["coef_medicos"],
        ],
        fmt="-o",
        color="black",
        capsize=4,
    )
    axes[0].axhline(0, color="red", linestyle="--")
    axes[0].axvline(2017.5, color="gray", linestyle=":")
    axes[0].set_title(r"Panel A: Personal Médico ($\beta_{\tau, Pers}$)")
    axes[0].set_ylabel("Efecto Marginal Logarítmico")

    # Panel B: Gasto
    axes[1].errorbar(
        df_es["anio"],
        df_es["coef_gasto"],
        yerr=[
            df_es["coef_gasto"] - df_es["ci_lower_gasto"],
            df_es["ci_upper_gasto"] - df_es["coef_gasto"],
        ],
        fmt="-o",
        color="black",
        capsize=4,
    )
    axes[1].axhline(0, color="red", linestyle="--")
    axes[1].axvline(2017.5, color="gray", linestyle=":")
    axes[1].set_title(r"Panel B: Gasto Total ($\beta_{\tau, Gasto}$)")

    plt.tight_layout()
    plt.savefig(os.path.join(PATH_OUT, "Fig4_EventStudy.pdf"))
    plt.close()
    print("[*] Gráfico 4 (Event Study Causal) generado con datos validados de Stata.")


# -----------------------------------------------------------------------------
# GRÁFICO 5: Trayectorias relativas por tercil de rigidez (Event Study Descriptivo)
# -----------------------------------------------------------------------------
def grafico_5_heterogeneidad_rigidez(df):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=False)

    # Terciles de rigidez basados estrictamente en 2017
    df_2017 = df[df["ANIO"] == 2017].copy()
    df_2017["tercil_rig"] = pd.qcut(
        df_2017["prop_planta_perm"], 3, labels=["Baja", "Media", "Alta Rigidez"]
    )
    df_plot = pd.merge(
        df, df_2017[["PROV_ID", "tercil_rig"]], on="PROV_ID", how="inner"
    )

    # Medias anuales por tercil
    df_mean = (
        df_plot.groupby(["ANIO", "tercil_rig"], observed=True)[
            ["LN_GASTO_SALUD_PC_REAL", "ln_medicos_pc"]
        ]
        .mean()
        .reset_index()
    )

    # Normalización: Restamos el valor de 2017 a toda la serie
    df_base = df_mean[df_mean["ANIO"] == 2017][
        ["tercil_rig", "LN_GASTO_SALUD_PC_REAL", "ln_medicos_pc"]
    ].rename(
        columns={
            "LN_GASTO_SALUD_PC_REAL": "base_gasto",
            "ln_medicos_pc": "base_medicos",
        }
    )
    df_mean = pd.merge(df_mean, df_base, on="tercil_rig")
    df_mean["rel_gasto"] = df_mean["LN_GASTO_SALUD_PC_REAL"] - df_mean["base_gasto"]
    df_mean["rel_medicos"] = df_mean["ln_medicos_pc"] - df_mean["base_medicos"]

    # Panel A: Médicos
    sns.lineplot(
        data=df_mean,
        x="ANIO",
        y="rel_medicos",
        hue="tercil_rig",
        marker="o",
        ax=axes[0],
        palette="Blues",
    )
    axes[0].axvline(2017.5, color="red", linestyle="--", alpha=0.5)
    axes[0].axhline(0, color="black", linewidth=0.8)
    axes[0].set_title("Panel A: Personal Médico (Trayectoria vs 2017)")
    axes[0].set_ylabel(r"$\Delta$ Log Personal")
    axes[0].set_xlabel("Año")

    # Panel B: Gasto
    sns.lineplot(
        data=df_mean,
        x="ANIO",
        y="rel_gasto",
        hue="tercil_rig",
        marker="o",
        ax=axes[1],
        palette="Blues",
    )
    axes[1].axvline(2017.5, color="red", linestyle="--", alpha=0.5)
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[1].set_title("Panel B: Gasto en Salud (Trayectoria vs 2017)")
    axes[1].set_ylabel(r"$\Delta$ Log Gasto Real")
    axes[1].set_xlabel("Año")

    plt.tight_layout()
    plt.savefig(os.path.join(PATH_OUT, "Fig5_HeterogeneidadRigidez.pdf"))
    plt.close()
    print("[*] Gráfico 5 (Heterogeneidad por Rigidez) generado.")


# -----------------------------------------------------------------------------
# GRÁFICO 6: Mecanismo Inmediato (Scatterplot 2018 vs 2017)
# -----------------------------------------------------------------------------
def grafico_6_rigidez_scatter(df):
    plt.figure(figsize=(6, 5))

    cols_necesarias = ["PROV_ID", "ANIO", "LN_GASTO_SALUD_PC_REAL", "ln_medicos_pc"]
    df_dyn = df[df["ANIO"].isin([2017, 2018])][cols_necesarias].copy()
    df_pivot = df_dyn.pivot(index="PROV_ID", columns="ANIO")

    df_diff = pd.DataFrame(index=df_pivot.index)
    df_diff["delta_gasto"] = (
        df_pivot[("LN_GASTO_SALUD_PC_REAL", 2018)]
        - df_pivot[("LN_GASTO_SALUD_PC_REAL", 2017)]
    )
    df_diff["delta_personal"] = (
        df_pivot[("ln_medicos_pc", 2018)] - df_pivot[("ln_medicos_pc", 2017)]
    )

    df_rigidez = df[df["ANIO"] == 2017].set_index("PROV_ID")[["prop_planta_perm"]]
    df_final = df_diff.join(df_rigidez).dropna()

    sns.scatterplot(
        data=df_final,
        x="delta_gasto",
        y="delta_personal",
        size="prop_planta_perm",
        sizes=(40, 200),
        color="black",
        alpha=0.6,
        legend=False,
    )

    plt.axhline(0, color="red", linestyle="--")
    plt.axvline(0, color="red", linestyle="--")
    plt.xlabel(r"$\Delta$ Log Gasto Real (2017-2018)")
    plt.ylabel(r"$\Delta$ Log Personal Médico (2017-2018)")
    plt.title("Asimetría del Ajuste y Rigidez Laboral (2018 vs 2017)", pad=15)

    plt.text(
        0.05,
        0.95,
        "Ajustan Gasto,\nMantienen Personal",
        transform=plt.gca().transAxes,
        fontsize=9,
        color="gray",
    )

    plt.tight_layout()
    plt.savefig(os.path.join(PATH_OUT, "Fig6_RigidezScatter.pdf"))
    plt.close()
    print("[*] Gráfico 6 (Scatter Asimetría) generado.")


# =============================================================================
# 3. EJECUCIÓN DEL PIPELINE
# =============================================================================
grafico_1_distribucion(df)
grafico_2_distribucion_rigidez(df)
grafico_3_pre_trends(df)

try:
    grafico_4_event_study()
except FileNotFoundError as e:
    print(e)

grafico_5_heterogeneidad_rigidez(df)
grafico_6_rigidez_scatter(df)

print(
    f"[ÉXITO] Ejecución de capa gráfica finalizada. Se generaron todos los gráficos en {PATH_OUT}"
)
