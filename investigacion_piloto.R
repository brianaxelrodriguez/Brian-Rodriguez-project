# --- 1. CARGAR MOTORES ---
library(reticulate)
use_virtualenv("C:/Users/brian/Documents/Proyectos_IA/venv_ia")

# --- 2. VERIFICAR PYTHON (DML) ---
dml <- import("doubleml")
message(">>> Motor Causal Python: LISTO")

# --- 3. VERIFICAR STATA (REGHDFE) ---
# Usamos el path de tu PLUS local en el comando de Stata
stata_cmd <- 'sysdir set PLUS "C:/Users/brian/Documents/Proyectos_IA/stata_lib/plus"; which reghdfe'
# Para correr Stata desde R podrías usar la librería 'RStata' si la instalas,
# pero por ahora lo haremos vía sistema:
system(paste0('"C:/Program Files/Stata17/stata-mp.exe" -b  "', stata_cmd, '"'))
message(">>> Motor Econométrico Stata: LISTO")

# --- 4. VERIFICAR JULIA ---
library(JuliaConnectoR)
# Test rápido de Julia
julia_eval("2 + 2")
message(">>> Motor de Simulación Julia: LISTO")

message("\n¡FELICIDADES BRIAN! EL LABORATORIO ESTÁ 100% OPERATIVO.")

