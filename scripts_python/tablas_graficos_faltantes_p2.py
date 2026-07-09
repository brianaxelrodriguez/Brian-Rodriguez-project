import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

print("=== GENERANDO FALTANTES PAPER 2 ===")

PATH_DATA = r"C:\Users\brian\Documents\Proyectos_IA\data_raw\Procesados\BASE_FUSIONADA_VITALES_MASTER.csv"
PATH_OUT_TABLAS = r"C:\Users\brian\Documents\Proyectos_IA\data_raw\PAPER 2\tablas"
PATH_OUT_GRAFICOS = r"C:\Users\brian\Documents\Proyectos_IA\data_raw\PAPER 2\graficos"
os.makedirs(PATH_OUT_TABLAS, exist_ok=True)
os.makedirs(PATH_OUT_GRAFICOS, exist_ok=True)

df = pd.read_csv(PATH_DATA)


# 1. Función auxiliar para PDFs
def guardar_tabla_txt_pdf(df_tabla, nombre_archivo, titulo, path_out):
    ruta_txt = os.path.join(path_out, f"{nombre_archivo}.txt")
    with open(ruta_txt, "w", encoding="utf-8") as f:
        f.write(f"{titulo}\n")
        f.write("=" * 80 + "\n")
        f.write(df_tabla.to_string())
        f.write("\n" + "=" * 80 + "\n")

    df_plot = df_tabla.copy()
    fig_width = max(8, len(df_plot.columns) * 1.8)
    fig_height = max(2, len(df_plot.index) * 0.5 + 1)
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
    plt.savefig(
        os.path.join(path_out, f"{nombre_archivo}.pdf"),
        format="pdf",
        bbox_inches="tight",
    )
    plt.close()


# 2. Variables
df["tasa_cancer"] = (df["M_CANCER_x"] / df["POBLACION_LAGRANGE"]) * 1000
df_pre_obra = (
    df[df["ANIO"] < 2016]
    .groupby("PROV_ID")["OBRA_PUBLICA_PC_REAL"]
    .mean()
    .reset_index()
)
df_pre_obra.rename(columns={"OBRA_PUBLICA_PC_REAL": "obra_hist_pc"}, inplace=True)
df = pd.merge(df, df_pre_obra, on="PROV_ID", how="left")

# 3. TABLA DESCRIPTIVA (2017)
df_2017 = df[df["ANIO"] == 2017].copy()
desc_vars = ["TASA_PERINATAL", "tasa_cancer", "OBRA_PUBLICA_PC_REAL", "obra_hist_pc"]
nombres_limpios = {
    "TASA_PERINATAL": "Tasa Mortalidad Perinatal",
    "tasa_cancer": "Tasa Mortalidad Cáncer",
    "OBRA_PUBLICA_PC_REAL": "Obra Pública PC Real",
    "obra_hist_pc": "Obra Histórica PC (Instrumento)",
}

tabla_desc = df_2017[desc_vars].agg(["mean", "std", "min", "max"]).T
tabla_desc = tabla_desc.rename(index=nombres_limpios)

latex_code = tabla_desc.to_latex(
    float_format="%.3f",
    caption="Estadísticos Descriptivos Pre-Shock (2017)",
    label="tab:desc_paper2",
    column_format="lcccc",
    escape=False,
)
with open(
    os.path.join(PATH_OUT_TABLAS, "Tabla_0_Descriptivas.tex"), "w", encoding="utf-8"
) as f:
    f.write(latex_code)
tabla_desc_str = tabla_desc.applymap(lambda x: f"{x:.3f}")
guardar_tabla_txt_pdf(
    tabla_desc_str,
    "Tabla_0_Descriptivas",
    "Estadísticos Descriptivos Pre-Shock (2017)",
    PATH_OUT_TABLAS,
)

# 4. GRÁFICO SCATTER DE FORMA REDUCIDA
df["ln_tasa_perinatal"] = np.log(df["TASA_PERINATAL"].replace(0, np.nan))
df_2017["ln_obra_hist"] = np.log(df_2017["obra_hist_pc"])

df_pre = (
    df[df["ANIO"].isin([2015, 2016, 2017])]
    .groupby("PROV_ID")["ln_tasa_perinatal"]
    .mean()
)
df_post = (
    df[df["ANIO"].isin([2018, 2019])].groupby("PROV_ID")["ln_tasa_perinatal"].mean()
)

df_diff = (df_post - df_pre).reset_index()
df_diff.rename(columns={"ln_tasa_perinatal": "delta_mort"}, inplace=True)
df_scatter = pd.merge(df_diff, df_2017[["PROV_ID", "ln_obra_hist"]], on="PROV_ID")

plt.figure(figsize=(6, 5))
plt.style.use("seaborn-v0_8-ticks")
sns.set_context("paper", font_scale=1.2)
plt.rcParams["font.family"] = "serif"
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False

sns.regplot(
    data=df_scatter,
    x="ln_obra_hist",
    y="delta_mort",
    scatter_kws={"color": "black", "s": 50, "alpha": 0.7},
    line_kws={"color": "red", "linewidth": 2},
)
plt.axhline(0, color="gray", linestyle="--", linewidth=1)
plt.xlabel("Exposición al Shock: Log Obra Histórica (Pre-2016)")
plt.ylabel(r"$\Delta$ Log Mortalidad Perinatal (2018/19 vs 2015/17)")
plt.title("Reduced Form: Impacto del Shock en Mortalidad", pad=15)

plt.tight_layout()
plt.savefig(os.path.join(PATH_OUT_GRAFICOS, "Fig2_ReducedForm_Scatter.pdf"))
plt.close()
print("[ÉXITO] Faltantes generados.")
