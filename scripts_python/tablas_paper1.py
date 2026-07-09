import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

print("=== INICIANDO CAPA DE SERVING: TABLAS PAPER 1 (LATEX, TXT, PDF) ===")

# 0. Semilla y Configuración
np.random.seed(42)
PATH_DATA = r"C:\Users\brian\Documents\Proyectos_IA\data_raw\Procesados\BASE_FUSIONADA_VITALES_MASTER.csv"
PATH_STATA = r"C:\Users\brian\Documents\Proyectos_IA\data_raw\PAPER 1\stata_output"
PATH_OUT = r"C:\Users\brian\Documents\Proyectos_IA\data_raw\PAPER 1\tablas"
os.makedirs(PATH_OUT, exist_ok=True)

# 1. Cargar Base Maestra
df = pd.read_csv(PATH_DATA)

# 2. Estandarización
if "GASTO_SALUD_PC_REAL" in df.columns and "LN_GASTO_SALUD_PC_REAL" not in df.columns:
    df["LN_GASTO_SALUD_PC_REAL"] = np.log(df["GASTO_SALUD_PC_REAL"].replace(0, np.nan))

df["medicos_pc"] = (df["MEDICOS"] / df["POBLACION_LAGRANGE"]) * 1000
df["ln_medicos_pc"] = np.log(df["medicos_pc"].replace(0, np.nan))

if "prop_planta_perm" not in df.columns:
    df["prop_planta_perm"] = df["MEDICOS"] / (df["MEDICOS"] + df["ENFERMEROS"])

df_pre = (
    df[df["ANIO"] < 2016]
    .groupby("PROV_ID")["INDICE_DEPENDENCIA_FISCAL"]
    .mean()
    .reset_index()
)
df_pre.rename(columns={"INDICE_DEPENDENCIA_FISCAL": "tau_i"}, inplace=True)
df = pd.merge(df, df_pre, on="PROV_ID", how="left")

df_unique_prov = df[["PROV_ID", "tau_i"]].drop_duplicates()
df_unique_prov["tercil_tau"] = pd.qcut(
    df_unique_prov["tau_i"], 3, labels=["Baja", "Media", "Alta"]
)
df = pd.merge(df, df_unique_prov[["PROV_ID", "tercil_tau"]], on="PROV_ID", how="left")

df = df.set_index(["PROV_ID", "ANIO"]).sort_index()


# -----------------------------------------------------------------------------
# FUNCIÓN AUXILIAR: Exportar a TXT y PDF
# -----------------------------------------------------------------------------
def guardar_tabla_txt_pdf(df_tabla, nombre_archivo, titulo):
    # 1. Exportar a TXT (Alineado)
    ruta_txt = os.path.join(PATH_OUT, f"{nombre_archivo}.txt")
    with open(ruta_txt, "w", encoding="utf-8") as f:
        f.write(f"{titulo}\n")
        f.write("=" * 80 + "\n")
        f.write(df_tabla.to_string())
        f.write("\n" + "=" * 80 + "\n")

    # 2. Exportar a PDF usando Matplotlib
    # Aplanamos MultiIndexes para que Matplotlib no explote
    df_plot = df_tabla.copy()
    if isinstance(df_plot.index, pd.MultiIndex):
        df_plot.index = [" | ".join(map(str, idx)) for idx in df_plot.index]
    if isinstance(df_plot.columns, pd.MultiIndex):
        df_plot.columns = [" | ".join(map(str, col)) for col in df_plot.columns]

    # Tamaño dinámico según filas y columnas
    fig_width = max(10, len(df_plot.columns) * 1.5)
    fig_height = max(3, len(df_plot.index) * 0.5 + 1)

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.axis("off")
    ax.axis("tight")

    tabla_pdf = ax.table(
        cellText=df_plot.astype(str).values,
        rowLabels=df_plot.index,
        colLabels=df_plot.columns,
        loc="center",
        cellLoc="center",
    )

    tabla_pdf.auto_set_font_size(False)
    tabla_pdf.set_fontsize(10)
    tabla_pdf.scale(1.2, 1.5)

    plt.title(titulo, pad=20, weight="bold", size=12)
    plt.tight_layout()

    ruta_pdf = os.path.join(PATH_OUT, f"{nombre_archivo}.pdf")
    plt.savefig(ruta_pdf, format="pdf", bbox_inches="tight")
    plt.close()


# -----------------------------------------------------------------------------
# TABLA 1: Estadísticos Descriptivos (Pre-Shock)
# -----------------------------------------------------------------------------
def generar_tabla_1(df):
    df_2017 = df.xs(2017, level="ANIO")
    vars_desc = ["LN_GASTO_SALUD_PC_REAL", "medicos_pc", "prop_planta_perm", "tau_i"]
    nombres_limpios = {
        "LN_GASTO_SALUD_PC_REAL": "Log Gasto Salud PC (Real)",
        "medicos_pc": "Médicos (por 1,000 hab.)",
        "prop_planta_perm": "Proporción Planta Permanente",
        "tau_i": "Exposición Fiscal ($\\tau_i$)",
    }

    tabla1 = (
        df_2017.groupby("tercil_tau", observed=True)[vars_desc].agg(["mean", "std"]).T
    )
    tabla1.rename(index=nombres_limpios, inplace=True)

    # Exportar LaTeX
    latex_code = tabla1.to_latex(
        float_format="%.3f",
        caption="Estadísticos Descriptivos Pre-Shock (2017) por Exposición Fiscal",
        label="tab:desc_pre_shock",
        column_format="lccc",
        escape=False,
    )
    with open(
        os.path.join(PATH_OUT, "Tabla_1_Descriptivas.tex"), "w", encoding="utf-8"
    ) as f:
        f.write(latex_code)

    # Exportar TXT y PDF
    guardar_tabla_txt_pdf(
        tabla1, "Tabla_1_Descriptivas", "Estadísticos Descriptivos Pre-Shock (2017)"
    )
    print("[*] Tabla 1 (Descriptivas) exportada (TEX, TXT, PDF).")


# -----------------------------------------------------------------------------
# TABLA 2: Matriz de Correlaciones Estructurales (Pre-Shock)
# -----------------------------------------------------------------------------
def generar_tabla_2_correlaciones(df):
    # Usamos la foto previa al shock
    df_2017 = df.xs(2017, level="ANIO").copy()

    # Seleccionamos variables clave para descartar colinealidad espuria
    vars_corr = {
        "prop_planta_perm": "Rigidez Laboral",
        "tau_i": "Exposición Fiscal",
        "LN_GASTO_SALUD_PC_REAL": "Log Gasto Salud PC",
        "medicos_pc": "Médicos (por 1k hab.)",
    }

    # Si tenés controles de vulnerabilidad en la base (ej. HACINAMIENTO_CRITICO o INGRESO_PC_REAL), los sumamos
    if "HACINAMIENTO_CRITICO" in df_2017.columns:
        vars_corr["HACINAMIENTO_CRITICO"] = "Vulnerabilidad Social"

    cols_disp = [c for c in vars_corr.keys() if c in df_2017.columns]
    nombres = {c: vars_corr[c] for c in cols_disp}

    # Calculamos matriz de correlación de Pearson
    df_corr = df_2017[cols_disp].rename(columns=nombres)
    matriz_corr = df_corr.corr(method="pearson")

    # Formateamos a 3 decimales
    matriz_fmt = matriz_corr.apply(lambda x: x.map(lambda y: f"{y:.3f}"))

    # Exportar LaTeX
    latex_code = matriz_fmt.to_latex(
        caption="Matriz de Correlación de Variables Estructurales (Cross-section 2017)",
        label="tab:corr_pre_shock",
        column_format="l" + "c" * len(matriz_fmt.columns),
        escape=False,
    )
    with open(
        os.path.join(PATH_OUT, "Tabla_2_Correlaciones.tex"), "w", encoding="utf-8"
    ) as f:
        f.write(latex_code)

    # Exportar TXT y PDF
    guardar_tabla_txt_pdf(
        matriz_fmt, "Tabla_2_Correlaciones", "Matriz de Correlación Pre-Shock (2017)"
    )
    print("[*] Tabla 2 (Correlaciones) exportada (TEX, TXT, PDF).")


# -----------------------------------------------------------------------------
# TABLA 3: Event Study Estructural (Desde CSV de Stata)
# -----------------------------------------------------------------------------
def generar_tabla_3_event_study():
    archivo_stata = os.path.join(PATH_STATA, "event_study_results.csv")

    if not os.path.exists(archivo_stata):
        print(f"[ADVERTENCIA] No se encontró {archivo_stata}. Falta correr Stata.")
        return

    df_es = pd.read_csv(archivo_stata)
    df_es = df_es.set_index("anio")

    tabla3 = pd.DataFrame(index=df_es.index)

    # Formato: Coeficiente [CI_lower, CI_upper]
    tabla3["Gasto / Inversión"] = df_es.apply(
        lambda row: (
            f"{row['coef_gasto']:.3f} [{row['ci_lower_gasto']:.3f}, {row['ci_upper_gasto']:.3f}]"
            if row.name != 2017
            else "0 (Base)"
        ),
        axis=1,
    )

    tabla3["Personal Médico"] = df_es.apply(
        lambda row: (
            f"{row['coef_medicos']:.3f} [{row['ci_lower_medicos']:.3f}, {row['ci_upper_medicos']:.3f}]"
            if row.name != 2017
            else "0 (Base)"
        ),
        axis=1,
    )

    tabla3 = tabla3.T

    # Exportar LaTeX
    latex_code = tabla3.to_latex(
        caption=r"Dinámica del Event Study: Efecto del Shock en Gasto vs. Personal Médico (95\% CI)",
        label="tab:event_study_results",
        column_format="l" + "c" * len(tabla3.columns),
        escape=False,
    )
    with open(
        os.path.join(PATH_OUT, "Tabla_3_EventStudy.tex"), "w", encoding="utf-8"
    ) as f:
        f.write(latex_code)

    # Exportar TXT y PDF
    guardar_tabla_txt_pdf(
        tabla3, "Tabla_3_EventStudy", "Dinámica del Event Study (95% CI)"
    )
    print("[*] Tabla 3 (Event Study) exportada desde Stata (TEX, TXT, PDF).")


# Ejecución
generar_tabla_1(df)
generar_tabla_2_correlaciones(df)  # <--- NUEVA LLAMADA
generar_tabla_3_event_study()
print(f"[ÉXITO] Ejecución de capa de tablas finalizada en {PATH_OUT}")
