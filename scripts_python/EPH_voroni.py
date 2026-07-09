import pandas as pd
import statsmodels.formula.api as smf

PATH_DATA = (
    r"C:\Users\brian\Documents\Proyectos_IA\clean_data\master_final_geografico.csv"
)


def analisis_colas_y_deciles_v2():
    df = pd.read_csv(PATH_DATA)

    # 1. Crear deciles usando RANK para evitar el error de 'Bin edges must be unique'
    # Esto asigna un decil único incluso si los valores son 0
    df["decil_gasto"] = pd.qcut(
        df["gasto_real_pcapita"].rank(method="first"), 10, labels=False
    )

    # 2. Simulación de Parámetros de Teoría de Colas (G/M/m)
    # λ (Llegadas): Proporción de población sin cobertura (EPH)
    # m*μ (Capacidad): Gasto real como proxy de infraestructura operativa
    # Si no tienes la columna EPH, usamos una constante de vulnerabilidad para el ejemplo
    if "pct_publico_exclusivo" not in df.columns:
        # Generamos un proxy basado en el score de Farrell (inversa de eficiencia)
        df["pct_publico_exclusivo"] = 1 - df["score_farrell"]

    # Factor de Utilización rho = λ / (m * μ)
    # Evitamos división por cero con un epsilon
    df["rho_utilizacion"] = df["pct_publico_exclusivo"] / (
        df["gasto_real_pcapita"] + 0.1
    )

    # 3. Análisis de saturación por deciles
    resumen = (
        df.groupby("decil_gasto")
        .agg(
            {
                "tasa_infantil": "mean",
                "rho_utilizacion": "mean",
                "dispersion_hospitalaria": "mean",
            }
        )
        .reset_index()
    )

    print("--- ANÁLISIS DE SATURACIÓN Y COLAS POR DECILES ---")
    print(resumen)

    # 4. Regresión de la Fricción de Cobertura
    # El logaritmo de la mortalidad debería explotar cuando rho se acerca a 1 (saturación)
    model = smf.ols(
        "np.log(tasa_infantil + 1e-6) ~ rho_utilizacion + dispersion_hospitalaria",
        data=df,
    ).fit()

    print("\n" + "=" * 50)
    print("IMPACTO DEL FACTOR DE UTILIZACIÓN (SATURACIÓN)")
    print("=" * 50)
    print(model.summary())


if __name__ == "__main__":
    analisis_colas_y_deciles_v2()
