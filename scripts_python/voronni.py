import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


def analisis_colas_definitivo():
    df = pd.read_csv(
        r"C:\Users\brian\Documents\Proyectos_IA\clean_data\master_final_geografico.csv"
    )

    # 1. Deciles por Rango para evitar errores
    df["decil_gasto"] = pd.qcut(
        df["gasto_real_pcapita"].rank(method="first"), 10, labels=False
    )

    # 2. Parámetros de Colas (G/M/m)
    # λ = Vulnerabilidad (1 - eficiencia)
    # μ = Capacidad (Gasto)
    df["lambda_llegada"] = 1 - df["score_farrell"]
    # Evitamos división por cero para rho
    df["rho_utilizacion"] = df["lambda_llegada"] / (df["gasto_real_pcapita"] + 0.01)

    # 3. Limpieza de Outliers y preparación de Logs
    # Filtramos rho infinito o valores de Voronoi absurdos si los hay
    df = df[df["rho_utilizacion"] < 50]  # Filtro de estabilidad
    df["log_tasa"] = np.log(df["tasa_infantil"] + 1e-6)

    # 4. Regresión de Saturación
    # Si rho explica la tasa, demostramos que la "cola" es el problema
    model = smf.ols(
        "log_tasa ~ rho_utilizacion + dispersion_hospitalaria", data=df
    ).fit()

    print("\n" + "=" * 50)
    print("MODELO G/M/m: SATURACIÓN SISTÉMICA")
    print("=" * 50)
    print(model.summary())

    # Guardar para el paper
    df.to_csv(
        r"C:\Users\brian\Documents\Proyectos_IA\clean_data\master_teoria_colas.csv",
        index=False,
    )


if __name__ == "__main__":
    analisis_colas_definitivo()
