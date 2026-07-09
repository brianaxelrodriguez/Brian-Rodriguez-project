import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor

# 1. Carga y Limpieza rápida
df = pd.read_csv(
    r"C:\Users\brian\Documents\Proyectos_IA\data_raw\Procesados\BASE_MASTER_FINAL.csv"
)

# Seleccionamos variables que REALMENTE influyen (Recursos vs Contexto)
# Quitamos las que tienen leaks (como M_TOTAL o M_NEO_REDUCIBLE que son parte del target)
features = [
    "MEDICOS",
    "ENFERMEROS",
    "TOTAL_FARMACIAS",
    "REFES_PUBLICOS",
    "GASTOS_TOTALES_REAL_2023",
    "HACINAMIENTO_CRITICO",
    "BENEFICIARIOS_SUMAR",
    "POBLACION_LAGRANGE",
    "RATIO_BAJO_PESO",
]

# Filtramos datos sin nulos en estas columnas
data_model = df[features + ["TASA_NEO_REDUCIBLE"]].dropna()

X = data_model[features]
y = data_model["TASA_NEO_REDUCIBLE"]

# 2. Entrenar el Random Forest
# Usamos 1000 árboles para que la importancia sea estable
rf = RandomForestRegressor(n_estimators=1000, random_state=42)
rf.fit(X, y)

# 3. Extraer y Graficar Importancia
importances = pd.DataFrame(
    {"Variable": X.columns, "Importancia": rf.feature_importances_}
).sort_values("Importancia", ascending=False)

# 4. Gráfico para el Tuit 3
plt.figure(figsize=(12, 7))
sns.set_style("whitegrid")

# Traducimos nombres para el público de Twitter
name_map = {
    "MEDICOS": "Cantidad de Médicos",
    "RATIO_BAJO_PESO": "% Bajo Peso al Nacer",
    "HACINAMIENTO_CRITICO": "Hacinamiento Crítico",
    "GASTOS_TOTALES_REAL_2023": "Presupuesto Real (Salud)",
    "ENFERMEROS": "Enfermeros",
    "TOTAL_FARMACIAS": "Farmacias",
    "REFES_PUBLICOS": "Centros de Salud Públicos",
    "BENEFICIARIOS_SUMAR": "Cobertura Plan Sumar",
    "POBLACION_LAGRANGE": "Tamaño Poblacional",
}
importances["Variable"] = importances["Variable"].map(name_map)

sns.barplot(x="Importancia", y="Variable", data=importances, palette="magma")

# Añadir los porcentajes en las barras
for i, v in enumerate(importances["Importancia"]):
    plt.text(
        v + 0.005, i, f"{v * 100:.1f}%", va="center", fontweight="bold", fontsize=11
    )

plt.title(
    "¿Qué explica la mortalidad infantil evitable? (Random Forest)",
    fontsize=16,
    fontweight="bold",
)
plt.xlabel("Poder Predictivo (Importancia Relativa)", fontsize=12)
plt.ylabel("")

plt.tight_layout()
plt.show()
