import os

import matplotlib.pyplot as plt
import pandas as pd

print("=== INICIANDO CAPA DE SERVING: TABLAS PAPER 2 (LATEX, TXT, PDF) ===")

PATH_STATA = r"C:\Users\brian\Documents\Proyectos_IA\data_raw\PAPER 2\stata_output"
PATH_OUT = r"C:\Users\brian\Documents\Proyectos_IA\data_raw\PAPER 2\tablas"
os.makedirs(PATH_OUT, exist_ok=True)


# Función auxiliar de exportación
def guardar_tabla_txt_pdf(df_tabla, nombre_archivo, titulo):
    ruta_txt = os.path.join(PATH_OUT, f"{nombre_archivo}.txt")
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
        os.path.join(PATH_OUT, f"{nombre_archivo}.pdf"),
        format="pdf",
        bbox_inches="tight",
    )
    plt.close()


# -----------------------------------------------------------------------------
# TABLA 1: IV y Efectos Principales
# -----------------------------------------------------------------------------
def generar_tabla_principal_iv():
    archivo = os.path.join(PATH_STATA, "modelos_2sls_resultados.csv")
    df = pd.read_csv(archivo, index_col="modelo")

    # Extraer coeficientes y errores
    ols = df.loc["1_OLS_Sesgado"]
    fs = df.loc["2_First_Stage"]
    rf = df.loc["4_Reduced_Form"]
    iv = df.loc["3_2SLS_Efecto_Causal"]

    tabla = pd.DataFrame(
        {
            "OLS (Sesgado)": [
                f"{ols['coeficiente']:.3f}",
                f"({ols['std_error']:.3f})",
                "-",
                "-",
            ],
            "First Stage": [
                f"{fs['coeficiente']:.3f}",
                f"({fs['std_error']:.3f})",
                f"{fs['f_stat']:.2f}",
                "-",
            ],
            "Reduced Form": [
                f"{rf['coeficiente']:.3f}",
                f"({rf['std_error']:.3f})",
                "-",
                "-",
            ],
            "2SLS (IV)": [
                f"{iv['coeficiente']:.3f}",
                f"({iv['std_error']:.3f})",
                "-",
                f"{iv['p_valor']:.3f}",
            ],
        },
        index=["Coeficiente", "Std. Error", "KP F-Stat", "P-Valor (Asintótico)"],
    )

    latex = tabla.to_latex(
        caption="Resultados Principales (Capital Físico y Mortalidad)",
        label="tab:iv_results",
        column_format="lcccc",
    )
    with open(
        os.path.join(PATH_OUT, "Tabla_1_IV_Resultados.tex"), "w", encoding="utf-8"
    ) as f:
        f.write(latex)
    guardar_tabla_txt_pdf(tabla, "Tabla_1_IV_Resultados", "Resultados Principales IV")
    print("[*] Tabla 1 (IV) generada.")


# -----------------------------------------------------------------------------
# TABLA 2: Placebos y Falsación
# -----------------------------------------------------------------------------
def generar_tabla_placebos():
    archivo = os.path.join(PATH_STATA, "modelos_2sls_resultados.csv")
    df = pd.read_csv(archivo, index_col="modelo")

    placebo_cancer = df.loc["5_Placebo_Cancer"]
    placebo_2016 = df.loc["6_Placebo_Temporal_2016"]

    tabla = pd.DataFrame(
        {
            "Placebo Exclusión (Cáncer)": [
                f"{placebo_cancer['coeficiente']:.3f}",
                f"({placebo_cancer['std_error']:.3f})",
                f"{placebo_cancer['p_valor']:.3f}",
            ],
            "Placebo Temporal (2016)": [
                f"{placebo_2016['coeficiente']:.3f}",
                f"({placebo_2016['std_error']:.3f})",
                f"{placebo_2016['p_valor']:.3f}",
            ],
        },
        index=["Coeficiente", "Std. Error", "P-Valor"],
    )

    latex = tabla.to_latex(
        caption="Tests de Falsación", label="tab:placebos", column_format="lcc"
    )
    with open(
        os.path.join(PATH_OUT, "Tabla_2_Placebos.tex"), "w", encoding="utf-8"
    ) as f:
        f.write(latex)
    guardar_tabla_txt_pdf(
        tabla, "Tabla_2_Placebos", "Tests de Falsación (Cáncer y 2016)"
    )
    print("[*] Tabla 2 (Placebos) generada.")


generar_tabla_principal_iv()
generar_tabla_placebos()
print("[ÉXITO] Ejecución de capa de tablas (Paper 2) finalizada.")
