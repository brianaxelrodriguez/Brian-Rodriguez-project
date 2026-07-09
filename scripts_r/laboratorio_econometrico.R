# Carga de Librerías
if (!require("pacman")) install.packages("pacman")
pacman::p_load(tidyverse, AER, quantreg, stargazer, broom)

# 1. Carga y Preparación
df <- read.csv("C:/Users/brian/Documents/Proyectos_IA/clean_data/master_ready_for_r.csv") %>%
    filter(tasa_mortalidad_mil > 0) %>% # Solo años con datos reales de salud
    mutate(
        log_gasto = log(gasto_real_pcapita),
        log_mortalidad = log(tasa_mortalidad_mil),
        farmacias_10k = (n_farmacias / poblacion) * 10000
    )

# 2. MODELO A: OLS de Referencia (Base)
modelo_ols <- lm(log_mortalidad ~ log_gasto + score_farrell + establecimientos_diez_mil, data = df)

# 3. MODELO B: 2SLS (Variables Instrumentales)
# Instrumentamos el gasto con la densidad de farmacias (Proxy de acceso/logística)
modelo_iv <- ivreg(log_mortalidad ~ log_gasto + score_farrell |
    farmacias_10k + score_farrell, data = df)

# 4. MODELO C: Regresión por Cuantiles (Impacto en extremos)
# ¿El gasto es más efectivo en provincias con mortalidad crítica (Tau 0.9)?
modelo_qr <- rq(log_mortalidad ~ log_gasto + score_farrell,
    tau = c(0.1, 0.5, 0.9), data = df
)

# --- SALIDA DE RESULTADOS ---
cat("\n--- RESULTADO 2SLS (Causalidad) ---\n")
summary(modelo_iv, diagnostics = TRUE)

cat("\n--- COMPARATIVA DE MODELOS ---\n")
stargazer(modelo_ols, modelo_iv,
    type = "text",
    column.labels = c("OLS", "2SLS"),
    dep.var.labels = "Log(Mortalidad)"
)

cat("\n--- REGRESIÓN POR CUANTILES ---\n")
summary(modelo_qr)
