import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import statsmodels.api as sm

# Estilo académico
sns.set_context("paper", font_scale=1.4)
sns.set_style("whitegrid")

df = pd.read_csv(
    r"C:\Users\brian\Documents\Proyectos_IA\clean_data\DATA_TESIS_FINAL.csv"
)
df_plot = df[["ln_tmi", "ln_rho", "ln_friccion", "ln_medicos"]].dropna()

# 1. FIGURA 1: Regresión Parcial (Causalidad Residualizada)
# Eliminamos el ruido de fricción y médicos de ambas variables
res_y = (
    sm.OLS(df_plot["ln_tmi"], sm.add_constant(df_plot[["ln_friccion", "ln_medicos"]]))
    .fit()
    .resid
)
res_x = (
    sm.OLS(df_plot["ln_rho"], sm.add_constant(df_plot[["ln_friccion", "ln_medicos"]]))
    .fit()
    .resid
)

plt.figure(figsize=(9, 6))
plot = sns.regplot(
    x=res_x,
    y=res_y,
    scatter_kws={"alpha": 0.4, "color": "gray"},
    line_kws={"color": "red", "lw": 2.5},
)

plt.title("Efecto Neto de la Saturación sobre la Mortalidad Infantil", pad=20)
plt.xlabel("Log(Saturación Operativa) | Residualizado", labelpad=10)
plt.ylabel("Log(Tasa Mortalidad Infantil) | Residualizado", labelpad=10)
plt.axhline(0, color="black", lw=0.8, ls="--")
plt.axvline(0, color="black", lw=0.8, ls="--")

plt.tight_layout()
plt.savefig(
    r"C:\Users\brian\Documents\Proyectos_IA\clean_data\FIGURA_1_CAUSALIDAD.png", dpi=300
)
print("✅ Figura 1 generada: FIGURA_1_CAUSALIDAD.png")

# 2. FIGURA 2: Persistencia (Trend Plot)
plt.figure(figsize=(9, 6))
# Ejemplo con 3 provincias para no saturar el gráfico
subset = df[
    (df["provincia"].isin(["BUENOS AIRES", "SANTIAGO DEL ESTERO", "FORMOSA"]))
    & (df["anio"] >= 2010)
    & (df["anio"] <= 2019)
]

sns.lineplot(data=subset, x="anio", y="ln_rho", hue="provincia", marker="o", lw=2)
plt.xlim(2010, 2019)
plt.xticks(range(2010, 2020))

plt.title("Evolución del Estrés Operativo (Saturación) 2010-2019")
plt.ylabel("Log(Índice Rho)")
plt.xlabel("Año")
plt.legend(title="", frameon=True)
plt.tight_layout()
plt.savefig(
    r"C:\Users\brian\Documents\Proyectos_IA\clean_data\FIGURA_2_TENDENCIAS.png", dpi=300
)
print("✅ Figura 2 generada: FIGURA_2_TENDENCIAS.png")
