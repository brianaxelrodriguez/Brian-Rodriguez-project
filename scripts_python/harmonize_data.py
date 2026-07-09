import pandas as pd
from sqlalchemy import create_engine, text

DB_CONNECTION = "postgresql+psycopg2://postgres:cure_1982@localhost:5432/local_db"
engine = create_engine(DB_CONNECTION)


def ejecutar_sql(nombre, sql):
    print(f"--- Ejecutando: {nombre} ---")
    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
        print(f"✅ {nombre} OK")
    except Exception as e:
        print(f"❌ Error en {nombre}: {e}")


# 1. FUNCIÓN DE LIMPIEZA MEJORADA (Quita espacios y estandariza)
sql_clean = """
CREATE OR REPLACE FUNCTION clean_prov(p_name text) RETURNS text AS $$
DECLARE
    p_clean text;
BEGIN
    p_clean := UPPER(TRIM(REPLACE(p_name, '_', ' ')));
    RETURN CASE 
        WHEN p_clean LIKE '%CABA%' OR p_clean LIKE '%CIUDAD AUTONOMA%' THEN 'CABA'
        WHEN p_clean LIKE '%BUENOS AIRES%' AND p_clean NOT LIKE '%CABA%' THEN 'BUENOS AIRES'
        WHEN p_clean LIKE '%ENTRE RIOS%' THEN 'ENTRE RIOS'
        WHEN p_clean LIKE '%RIO NEGRO%' THEN 'RIO NEGRO'
        WHEN p_clean LIKE '%SAN JUAN%' THEN 'SAN JUAN'
        WHEN p_clean LIKE '%SAN LUIS%' THEN 'SAN LUIS'
        WHEN p_clean LIKE '%SANTA CRUZ%' THEN 'SANTA CRUZ'
        WHEN p_clean LIKE '%SANTA FE%' THEN 'SANTA FE'
        WHEN p_clean LIKE '%SANTIAGO%' THEN 'SANTIAGO DEL ESTERO'
        WHEN p_clean LIKE '%TIERRA%' THEN 'TIERRA DEL FUEGO'
        WHEN p_clean LIKE '%LA PAMPA%' THEN 'LA PAMPA'
        WHEN p_clean LIKE '%LA RIOJA%' THEN 'LA RIOJA'
        ELSE p_clean
    END;
END;
$$ LANGUAGE plpgsql;
"""

# 2. AGREGACIONES (Sin cambios en lógica, pero con clean_prov más fuerte)
sql_agg_fiscal = "DROP TABLE IF EXISTS analytics_fiscal; CREATE TABLE analytics_fiscal AS SELECT anio, clean_prov(provincia_origen) as provincia, SUM(CASE WHEN LOWER(concepto) LIKE '%total%' THEN monto ELSE 0 END) as gasto_total_nominal FROM stg_fiscal_apnf_long GROUP BY 1, 2;"
sql_agg_mortalidad = "DROP TABLE IF EXISTS analytics_mortalidad; CREATE TABLE analytics_mortalidad AS SELECT anio, clean_prov(jurisdicion_residencia_nombre) as provincia, SUM(cantidad) as muertes_totales FROM stg_deis_mortalidad GROUP BY 1, 2;"
sql_agg_oferta = "DROP TABLE IF EXISTS analytics_oferta; CREATE TABLE analytics_oferta AS SELECT anio_reporte as anio, clean_prov(provincia) as provincia, COUNT(DISTINCT id_refes) as total_establecimientos FROM stg_sisa_refes GROUP BY 1, 2;"

# 3. MASTER PANEL (FORZANDO 24 PROVINCIAS)
sql_master = """
DROP TABLE IF EXISTS master_panel_analytics;
CREATE TABLE master_panel_analytics AS
SELECT 
    p.anio,
    p.provincia,
    p.poblacion,
    -- Normalización y Deflactación
    COALESCE((f.gasto_total_nominal / NULLIF(i.inflacion_anual_acumulada, 0)) / NULLIF(p.poblacion, 0), 0) as gasto_real_pcapita,
    COALESCE((m.muertes_totales::numeric / NULLIF(p.poblacion, 0)) * 1000, 0) as tasa_mortalidad_mil,
    COALESCE((o.total_establecimientos::numeric / NULLIF(p.poblacion, 0)) * 10000, 0) as establecimientos_diez_mil
FROM stg_macro_poblacion p
LEFT JOIN analytics_fiscal f ON p.anio = f.anio AND p.provincia = f.provincia
LEFT JOIN analytics_mortalidad m ON p.anio = m.anio AND p.provincia = m.provincia
LEFT JOIN analytics_oferta o ON p.anio = o.anio AND p.provincia = o.provincia
LEFT JOIN stg_macro_ipc i ON p.anio = i.anio
WHERE p.provincia IN (
    'BUENOS AIRES', 'CABA', 'CATAMARCA', 'CHACO', 'CHUBUT', 'CORDOBA', 
    'CORRIENTES', 'ENTRE RIOS', 'FORMOSA', 'JUJUY', 'LA PAMPA', 'LA RIOJA', 
    'MENDOZA', 'MISIONES', 'NEUQUEN', 'RIO NEGRO', 'SALTA', 'SAN JUAN', 
    'SAN LUIS', 'SANTA CRUZ', 'SANTA FE', 'SANTIAGO DEL ESTERO', 
    'TIERRA DEL FUEGO', 'TUCUMAN'
)
ORDER BY 1, 2;
"""

if __name__ == "__main__":
    ejecutar_sql("Limpia Provincias", sql_clean)
    ejecutar_sql("Fiscal", sql_agg_fiscal)
    ejecutar_sql("Mortalidad", sql_agg_mortalidad)
    ejecutar_sql("Oferta", sql_agg_oferta)
    ejecutar_sql("MASTER FINAL", sql_master)

    # Resumen Final
    print("\n--- PANEL FINALIZADO (Debería decir 24 provincias siempre) ---")
    df_res = pd.read_sql(
        "SELECT anio, count(*) as n_provs, AVG(tasa_mortalidad_mil) as avg_mortalidad FROM master_panel_analytics GROUP BY 1 ORDER BY 1",
        engine,
    )
    print(df_res.to_string())
