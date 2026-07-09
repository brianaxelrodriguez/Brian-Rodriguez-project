import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Configuración de rutas
CLEAN_DIR = r"C:\Users\brian\Documents\Proyectos_IA\clean_data"
# Usamos el archivo que debería tener toda la info integrada
PATH_DATA = os.path.join(CLEAN_DIR, "master_teoria_colas.csv")


def generar_analisis_granular():
    if not os.path.exists(PATH_DATA):
        print(
            "❌ Archivo no encontrado. Asegúrate de que el merge temporal se ejecutó."
        )
        return

    df = pd.read_csv(PATH_DATA)

    # Aseguramos que existan las columnas clave para el DiD y EPH
    # Si 'anio' no está, el DiD es solo un corte transversal
    if "anio" not in df.columns:
        print("⚠️ Advertencia: No hay columna de tiempo. El DiD será limitado.")
        # Intentamos recuperar años si están en el master original

    sns.set_theme(style="whitegrid")

    # --- 1. VORONOI POR PROVINCIA (Identificación de la Fricción Fija) ---
    plt.figure(figsize=(12, 8))
    # Aquí no promediamos, vemos la dispersión por provincia
    df_rank = (
        df.groupby("provincia")["dispersion_hospitalaria"]
        .last()
        .sort_values(ascending=False)
        .reset_index()
    )
    sns.barplot(
        data=df_rank, x="dispersion_hospitalaria", y="provincia", palette="viridis"
    )
    plt.xscale("log")
    plt.title("Identificación de Fricción Geográfica por Jurisdicción", fontsize=14)
    plt.savefig(os.path.join(CLEAN_DIR, "voronoi_identidad.png"), bbox_inches="tight")

    # --- 2. EVOLUCIÓN TEMPORAL (Intra e Inter Provincias) ---
    plt.figure(figsize=(14, 8))
    # Seleccionamos provincias representativas para no empastar el gráfico
    prov_interes = [
        "CABA",
        "BUENOS AIRES",
        "CHACO",
        "FORMOSA",
        "SALTA",
        "SANTA CRUZ",
        "CORDOBA",
    ]
    df_did = df[df["provincia"].isin(prov_interes)]

    sns.lineplot(
        data=df_did,
        x="anio",
        y="tasa_infantil",
        hue="provincia",
        marker="o",
        linewidth=2.5,
    )
    plt.title("Trayectorias de Mortalidad Infantil (Evidencia para DiD)", fontsize=14)
    plt.ylabel("Mortalidad Infantil")
    plt.xlabel("Evolución Temporal")
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.savefig(os.path.join(CLEAN_DIR, "did_trayectorias.png"), bbox_inches="tight")

    # --- 3. EL GRÁFICO DE COBERTURA (EPH) ---
    # Si lograste integrar la EPH, aquí vemos la fricción real
    if "pct_publico_exclusivo" in df.columns:
        plt.figure(figsize=(12, 8))
        # Scatter con nombres de provincias
        p1 = sns.scatterplot(
            data=df,
            x="pct_publico_exclusivo",
            y="tasa_infantil",
            hue="dispersion_hospitalaria",
            size="gasto_real_pcapita",
            sizes=(40, 400),
        )

        # Etiquetado dinámico para evitar solapamiento (top 15)
        for i in range(df.shape[0]):
            if i % 2 == 0:  # Filtro para no saturar todas las etiquetas
                plt.text(
                    df.pct_publico_exclusivo.iloc[i],
                    df.tasa_infantil.iloc[i],
                    df.provincia.iloc[i],
                    fontsize=8,
                    alpha=0.7,
                )

        plt.title("Fricción EPH: Cobertura Pública vs Resultado Sanitario", fontsize=14)
        plt.savefig(
            os.path.join(CLEAN_DIR, "friccion_eph_nombres.png"), bbox_inches="tight"
        )

    print("✅ Gráficos granulares generados con éxito.")


if __name__ == "__main__":
    generar_analisis_granular()
