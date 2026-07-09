using CSV, DataFrames, DataEnvelopmentAnalysis, FixedEffectModels, Statistics

# 1. Cargar el Panel Maestro
path = "C:/Users/brian/Documents/Proyectos_IA/master_panel_final.csv"
if !isfile(path)
    error("❌ No se encontró el archivo CSV.")
end

df = CSV.read(path, DataFrame)

# 2. Limpieza Rigurosa
# Filtramos años válidos y evitamos valores Missing o Inf
df_clean = filter(row -> 
    row.anio <= 2022 && 
    !ismissing(row.tasa_mortalidad_mil) && row.tasa_mortalidad_mil > 0 &&
    !ismissing(row.gasto_real_pcapita) && row.gasto_real_pcapita > 0, 
df)

println("--- Analizando Panel: $(size(df_clean, 1)) observaciones válidas ---")

# --- PARTE 1: DEA (Data Envelopment Analysis) ---
# X: Gasto Real (Input) | Y: Salud (Output = 1/Mortalidad)
X = Matrix{Float64}(df_clean[:, [:gasto_real_pcapita]])
Y_inv = Matrix{Float64}(1.0 ./ df_clean[:, [:tasa_mortalidad_mil]])

# VRS: Retornos Variables a Escala | orient=:Output (Con Mayúscula)
# Nota: Si falla por el optimizador, la librería usa GLPK por defecto
dea_model = dea(X, Y_inv, orient=:Output, rts=:VRS)
df_clean.eficiencia_dea = efficiency(dea_model)

println("\n⭐ RANKING DE EFICIENCIA PROMEDIO (2011-2022):")
resumen_dea = combine(groupby(df_clean, :provincia), :eficiencia_dea => mean => :score)
sort!(resumen_dea, :score, rev=true)
show(resumen_dea, allrows=true)

# --- PARTE 2: REGRESIÓN DE PANEL (Efectos Fijos) ---
# Creamos variables en logaritmos para elasticidades
df_clean.log_mortalidad = log.(df_clean.tasa_mortalidad_mil)
df_clean.log_gasto = log.(df_clean.gasto_real_pcapita)

# Modelo con efectos fijos cruzados (Provincia + Año)
model_fe = reg(df_clean, @formula(log_mortalidad ~ log_gasto + establecimientos_diez_mil + fe(provincia) + fe(anio)))

println("\n\n--- RESULTADOS ECONOMÉTRICOS ---")
println(model_fe)

# 3. Exportar resultados
CSV.write("C:/Users/brian/Documents/Proyectos_IA/resultados_eficiencia_final.csv", df_clean)
println("\n✅ Proceso terminado. Datos guardados en 'resultados_eficiencia_final.csv'")

