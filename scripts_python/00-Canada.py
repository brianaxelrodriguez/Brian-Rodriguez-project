import gc
import os

import matplotlib.pyplot as plt
import pandas as pd

try:
    from linearmodels.panel import PanelOLS
except ImportError:
    print("Por favor instala linearmodels: pip install linearmodels")
    exit()

# 1. RUTAS Y CONFIGURACIÓN
BASE_PATH = r"C:\Users\brian\Documents\Proyectos_IA\data_raw\PAPER 0"
files = [
    "2020_CA_Region_Mobility_Report.csv",
    "2021_CA_Region_Mobility_Report.csv",
    "2022_CA_Region_Mobility_Report.csv",
]

# Estética Académica
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update({"font.family": "serif", "figure.dpi": 300})

# 2. INGESTA EFICIENTE (Solo leemos las columnas que importan para no saturar RAM)
cols_to_use = [
    "date",
    "sub_region_1",
    "sub_region_2",
    "retail_and_recreation_percent_change_from_baseline",
    "grocery_and_pharmacy_percent_change_from_baseline",
]

print("Cargando y uniendo paneles anuales...")
df_list = []
for f in files:
    file_path = os.path.join(BASE_PATH, f)
    if os.path.exists(file_path):
        temp_df = pd.read_csv(file_path, usecols=cols_to_use, parse_dates=["date"])
        df_list.append(temp_df)
    else:
        print(f"Falta el archivo: {file_path}")

df = pd.concat(df_list, ignore_index=True)
del df_list
gc.collect()  # Forzamos recolección de basura

# 3. LIMPIEZA DEL PANEL
# Nos quedamos solo con nivel Provincia (sub_region_1 not null, sub_region_2 is null)
df_panel = df[(df["sub_region_1"].notna()) & (df["sub_region_2"].isna())].copy()

# Renombrar para econometría
df_panel.rename(
    columns={
        "grocery_and_pharmacy_percent_change_from_baseline": "grocery",
        "retail_and_recreation_percent_change_from_baseline": "retail",
    },
    inplace=True,
)

# 4. INGENIERÍA DE VARIABLES (El corazón del Q1)
# Densidad de Puntos de Interés (POI) - Proxy de "Digital Dependency" de Rodriguez
# [Calculado base densidad poblacional/comercial relativa de provincias canadienses]
poi_density_map = {
    "Ontario": 100,
    "Quebec": 85,
    "British Columbia": 70,
    "Alberta": 65,
    "Manitoba": 60,
    "Saskatchewan": 40,
    "Nova Scotia": 35,
    "New Brunswick": 30,
    "Newfoundland and Labrador": 25,
    "Prince Edward Island": 20,
    "Yukon": 5,
    "Northwest Territories": 5,
    "Nunavut": 5,
}
df_panel["poi_density"] = df_panel["sub_region_1"].map(poi_density_map)
# Normalizamos la densidad (Z-score) para que los coeficientes sean interpretables
df_panel["poi_density"] = (
    df_panel["poi_density"] - df_panel["poi_density"].mean()
) / df_panel["poi_density"].std()

# Dummies de Evento
df_panel["blackout"] = (df_panel["date"] == "2022-07-08").astype(int)
# Feriado (Canada Day es el 1 de Julio)
df_panel["holiday"] = (
    (df_panel["date"].dt.month == 7) & (df_panel["date"].dt.day == 1)
).astype(int)

# Dummies de estacionalidad
df_panel["dow"] = df_panel["date"].dt.day_name()
df_panel["year"] = df_panel["date"].dt.year.astype(str)

# Limpiamos NaNs antes de la regresión
df_panel.dropna(subset=["grocery", "poi_density"], inplace=True)

# 5. ECONOMETRÍA DE PANEL (Panel OLS con Efectos Fijos)
print("\n--- CORRIENDO REGRESIÓN DE PANEL (EFECTOS FIJOS) ---")
# Seteamos el MultiIndex (Entidad, Tiempo)
df_reg = df_panel.set_index(["sub_region_1", "date"])

# Fórmula: grocery ~ blackout + interacción(blackout*densidad) + feriado + controles de día/año + Efectos Fijos
formula = "grocery ~ 1 + blackout + blackout:poi_density + holiday + C(dow) + C(year) + EntityEffects"
model = PanelOLS.from_formula(formula, data=df_reg, drop_absorbed=True)
results = model.fit(cov_type="clustered", cluster_entity=True)
print(results.summary)

# Guardar resultados en txt
with open(os.path.join(BASE_PATH, "regression_results.txt"), "w") as f:
    f.write(results.summary.as_text())

# 6. VISUALIZACIÓN MULTI-AÑO (Julio 2020 vs 2021 vs 2022)
print("\nGenerando Gráfico Comparativo Multi-Año...")
# Filtramos solo Ontario (Epicentro del apagón) y Julio
df_plot = df_panel[
    (df_panel["sub_region_1"] == "Ontario") & (df_panel["date"].dt.month == 7)
].copy()
df_plot["day_of_month"] = df_plot["date"].dt.day

fig, ax = plt.subplots(figsize=(10, 6))

colors = {"2020": "#A0A0A0", "2021": "#707070", "2022": "#D55E00"}
alphas = {"2020": 0.5, "2021": 0.6, "2022": 1.0}
widths = {"2020": 1.5, "2021": 1.5, "2022": 3.0}

for year in ["2020", "2021", "2022"]:
    temp = df_plot[df_plot["year"] == year].sort_values("day_of_month")
    # Recortamos la vista hasta el 15 de julio para hacer zoom en el shock
    temp = temp[temp["day_of_month"] <= 15]
    ax.plot(
        temp["day_of_month"],
        temp["grocery"],
        label=f"July {year}",
        color=colors[year],
        alpha=alphas[year],
        linewidth=widths[year],
        marker="o" if year == "2022" else "",
    )

ax.axvline(
    x=8, color="red", linestyle="--", alpha=0.8, label="Rogers Blackout (Jul 8, 2022)"
)

ax.set_title(
    "Inelastic Demand Resilience: Canada Grocery/Pharmacy Mobility (Ontario)",
    fontsize=14,
    weight="bold",
)
ax.set_xlabel("Day of July", fontsize=12)
ax.set_ylabel("Mobility % Change from Baseline", fontsize=12)
ax.set_xticks(range(1, 16))
ax.legend(loc="lower left")

plt.tight_layout()
out_fig = os.path.join(BASE_PATH, "fig_multiyr_shock.png")
plt.savefig(out_fig, dpi=300)
print(f"Gráfico guardado en: {out_fig}")
