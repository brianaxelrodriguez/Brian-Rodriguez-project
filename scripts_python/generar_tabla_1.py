import pandas as pd
import statsmodels.api as sm
from statsmodels.sandbox.regression.gmm import IV2SLS

# Cargar datos
df = pd.read_csv(
    r"C:\Users\brian\Documents\Proyectos_IA\clean_data\DATA_TESIS_FINAL.csv"
)
df.sort_values(["provincia", "anio"], inplace=True)
df["ln_tmi_lag"] = df.groupby("provincia")["ln_tmi"].shift(1)


def get_stats(model, var_name):
    if var_name in model.params:
        coef = model.params[var_name]
        pval = model.pvalues[var_name]
        stderr = model.bse[var_name]
        stars = (
            "***" if pval < 0.01 else "**" if pval < 0.05 else "*" if pval < 0.1 else ""
        )
        return f"{coef:.3f}{stars}\n({stderr:.3f})"
    return ""


# --- CORRER LOS 4 MODELOS ---
# 1. OLS
df1 = df[["ln_tmi", "ln_rho", "ln_friccion", "ln_medicos"]].dropna()
m1 = sm.OLS(
    df1["ln_tmi"], sm.add_constant(df1[["ln_rho", "ln_friccion", "ln_medicos"]])
).fit()

# 2. FE (Dummies de provincia)
df2 = df[["provincia", "ln_tmi", "ln_rho", "ln_friccion", "ln_medicos"]].dropna()
X2 = pd.concat(
    [
        df2[["ln_rho", "ln_friccion", "ln_medicos"]],
        pd.get_dummies(df2["provincia"], drop_first=True, dtype=float),
    ],
    axis=1,
)
m2 = sm.OLS(df2["ln_tmi"], sm.add_constant(X2)).fit()

# 3. Dinámico (FE + Lag)
df3 = df[
    ["provincia", "ln_tmi", "ln_tmi_lag", "ln_rho", "ln_friccion", "ln_medicos"]
].dropna()
X3 = pd.concat(
    [
        df3[["ln_tmi_lag", "ln_rho", "ln_friccion", "ln_medicos"]],
        pd.get_dummies(df3["provincia"], drop_first=True, dtype=float),
    ],
    axis=1,
)
m3 = sm.OLS(df3["ln_tmi"], sm.add_constant(X3)).fit()

# 4. FE-IV
df4 = df[
    ["provincia", "ln_tmi", "ln_rho", "ln_gasto_rez", "ln_friccion", "ln_medicos"]
].dropna()
dummies = pd.get_dummies(df4["provincia"], drop_first=True, dtype=float)
Z = sm.add_constant(
    pd.concat([df4[["ln_gasto_rez", "ln_friccion", "ln_medicos"]], dummies], axis=1)
)
X4 = sm.add_constant(
    pd.concat([df4[["ln_rho", "ln_friccion", "ln_medicos"]], dummies], axis=1)
)
m4 = IV2SLS(df4["ln_tmi"], X4, Z).fit()

# --- CONSTRUIR TABLA COMPARATIVA ---
filas = ["ln_rho", "ln_tmi_lag", "ln_friccion", "ln_medicos"]
tabla = pd.DataFrame(
    columns=["(1) OLS", "(2) FE", "(3) Dynamic", "(4) FE-IV"], index=filas
)

for var in filas:
    tabla.loc[var] = [
        get_stats(m1, var),
        get_stats(m2, var),
        get_stats(m3, var),
        get_stats(m4, var),
    ]

# Agregar diagnósticos
tabla.loc["Prov. Fixed Effects"] = ["No", "Yes", "Yes", "Yes"]
tabla.loc["Observations"] = [m1.nobs, m2.nobs, m3.nobs, m4.nobs]
tabla.loc["R-squared"] = [
    f"{m1.rsquared:.3f}",
    f"{m2.rsquared:.3f}",
    f"{m3.rsquared:.3f}",
    "---",
]

print("\nTABLA 1: DETERMINANTES DE LA MORTALIDAD INFANTIL")
print(tabla)
tabla.to_csv("TABLA_1_MAIN_RESULTS.csv")
