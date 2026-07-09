import os

import pandas as pd

MASTER_PATH = (
    r"C:\Users\brian\Documents\Proyectos_IA\clean_data\master_panel_r_final.csv"
)


def comprobar_panel():
    if not os.path.exists(MASTER_PATH):
        print("❌ El archivo no existe.")
        return

    df = pd.read_csv(MASTER_PATH)

    print("--- Auditoría de Calidad del Master Panel ---")
    print(f"Filas: {len(df)} | Columnas: {len(df.columns)}")

    # 1. Verificar Nulos Críticos
    nulls = (
        df[
            [
                "gasto_real_pcapita",
                "tasa_mortalidad_mil",
                "score_farrell",
                "n_farmacias",
            ]
        ]
        .isnull()
        .sum()
    )
    print("\n🔍 Valores Faltantes:")
    print(nulls)

    # 2. Resumen Estadístico de Variables de Interés
    print("\n📊 Estadísticos Descriptivos (Check de rangos):")
    print(
        df[["score_farrell", "n_farmacias", "tasa_mortalidad_mil"]]
        .describe()
        .loc[["min", "mean", "max"]]
    )

    # 3. Detección de Outliers (Z-Score simple)
    # Útil para identificar si una provincia tiene un gasto imposible
    q_high = df["gasto_real_pcapita"].quantile(0.95)
    outliers = df[df["gasto_real_pcapita"] > q_high][
        ["anio", "provincia", "gasto_real_pcapita"]
    ]

    if not outliers.empty:
        print("\n⚠️ Top 5 observaciones de alto gasto (posibles outliers):")
        print(outliers.head())


if __name__ == "__main__":
    comprobar_panel()
