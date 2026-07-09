* ==============================================================================
* PAPER 1: FISCAL RIGIDITIES AND CAPITAL DECUMULATION
* SCRIPT DEFINITIVO DE PRODUCCIÓN (ADAPTADO AL CSV REAL)
* ==============================================================================
clear all
set more off

* 1. Rutas
local path_data "C:\Users\brian\Documents\Proyectos_IA\data_raw\Procesados\BASE_FUSIONADA_VITALES_MASTER.csv"
local path_out "C:\Users\brian\Documents\Proyectos_IA\data_raw\PAPER 1\stata_output"

import delimited "`path_data'", clear

* 2. Preparación del Panel
capture drop prov_id
encode provincia, gen(prov_id)
xtset prov_id anio

* ==============================================================================
* 3. CONSTRUCCIÓN DE VARIABLES (Adaptado a las columnas reales)
* ==============================================================================
* A. Gasto en Salud (Esfuerzo fiscal en el sector)
gen ln_gasto_salud = log(gasto_salud_pc_real)

* B. Capital (Proxy de K: Obra Pública Provincial Per Cápita)
* Si hay ceros u omitidos, sumamos 1 para no perder obs en el log
gen ln_gasto_capital = log(obra_publica_pc_real + 1)

* C. Empleo (Proxy de L: Médicos Per Cápita en lugar de gasto salarial)
gen medicos_pc = (medicos / poblacion_lagrange) * 1000
gen ln_medicos = log(medicos_pc)

* D. Exposición Histórica (tau_i)
* Usamos la Dependencia Fiscal estructural pre-shock (promedio 2011-2015)
bysort prov_id: egen tau_i = mean(indice_dependencia_fiscal) if anio < 2016
bysort prov_id: replace tau_i = tau_i[_n-1] if missing(tau_i)

* Dummy Post Shock 2018 e Interacción DiD Continuo
gen post2018 = (anio >= 2018)
gen tau_post = tau_i * post2018

* Interacciones Event Study (Base 2017)
forvalues y = 2011/2019 {
    capture drop tau_yr`y'
    if `y' != 2017 {
        gen tau_yr`y' = tau_i * (anio == `y')
    }
}

* ==============================================================================
* 4. ESTRATEGIA EMPÍRICA: RESULTADOS PRINCIPALES (Tabla 3 y 4 del Paper)
* ==============================================================================

* Modelo 1: Gasto Total en Salud
xtreg ln_gasto_salud tau_post i.anio, fe vce(cluster prov_id)
est store m_salud

* Modelo 2: Factor Trabajo (L) - Médicos
xtreg ln_medicos tau_post i.anio, fe vce(cluster prov_id)
est store m_medicos

* Modelo 3: Factor Capital (K) - Obra Pública
xtreg ln_gasto_capital tau_post i.anio, fe vce(cluster prov_id)
est store m_capital

disp "======================================================================="
disp "RESULTADOS ESTRUCTURALES: AJUSTE COMPOSICIONAL"
disp "======================================================================="
estout m_salud m_medicos m_capital, cells(b(star fmt(3)) se(par fmt(3))) stats(r2 N) ///
    title("Impacto del Shock Cambiario según Margen de Ajuste")

* ==============================================================================
* 5. EVENT STUDY PARA PYTHON (Figura 1)
* ==============================================================================
* Creamos matrices separadas para llenarlas inmediatamente post-regresión
matrix res_k = J(8, 3, .)
matrix res_l = J(8, 3, .)
local row = 1

* --- A. REGRESIÓN DE CAPITAL ---
quietly xtreg ln_gasto_capital tau_yr2011-tau_yr2016 tau_yr2018 tau_yr2019 i.anio, fe vce(cluster prov_id)
foreach y in 2012 2013 2014 2015 2016 2018 2019 {
    matrix res_k[`row', 1] = `y'
    matrix res_k[`row', 2] = _b[tau_yr`y']
    matrix res_k[`row', 3] = _se[tau_yr`y']
    local row = `row' + 1
}
* Año base 2017
matrix res_k[8, 1] = 2017
matrix res_k[8, 2] = 0
matrix res_k[8, 3] = 0

* --- B. REGRESIÓN DE MÉDICOS (L) ---
local row = 1
quietly xtreg ln_medicos tau_yr2011-tau_yr2016 tau_yr2018 tau_yr2019 i.anio, fe vce(cluster prov_id)
foreach y in 2012 2013 2014 2015 2016 2018 2019 {
    matrix res_l[`row', 1] = `y'
    matrix res_l[`row', 2] = _b[tau_yr`y']
    matrix res_l[`row', 3] = _se[tau_yr`y']
    local row = `row' + 1
}
* Año base 2017
matrix res_l[8, 1] = 2017
matrix res_l[8, 2] = 0
matrix res_l[8, 3] = 0

* --- C. UNIR Y EXPORTAR ---
preserve
clear
svmat res_k, names(k_)
svmat res_l, names(l_)

* Renombrar y organizar
rename k_1 anio
rename k_2 coef_capital
rename k_3 se_capital

rename l_2 coef_medicos
rename l_3 se_medicos
drop l_1 // Eliminamos el año duplicado

sort anio
export delimited using "`path_out'\event_study_final.csv", replace
restore
disp "[ÉXITO] Matriz de Event Study exportada mediante extracción robusta."

* ==============================================================================
* 6. TESTS DE ROBUSTEZ Y PLACEBO
* ==============================================================================

* A. PLACEBO TEST (Falso shock en 2015)
preserve
keep if anio < 2018
gen post2015 = (anio >= 2015)
gen tau_placebo = tau_i * post2015

quietly xtreg ln_gasto_capital tau_placebo i.anio, fe vce(cluster prov_id)
disp "======================================================================="
disp "TEST PLACEBO 2015 (Dependiente: Capital)"
disp "Si la identificación es correcta, el coeficiente debe ser NO significativo."
disp "Coeficiente: " _b[tau_placebo] " | P-valor: " 2 * ttail(e(df_r), abs(_b[tau_placebo]/_se[tau_placebo]))
disp "======================================================================="
restore

* B. JACKKNIFE (Excluyendo provincias para ver sensibilidad de Capital)
preserve
matrix JK = J(24, 4, .)
levelsof prov_id, local(provincias)
local i = 1

foreach p of local provincias {
    quietly xtreg ln_gasto_capital tau_post i.anio if prov_id != `p', fe vce(cluster prov_id)
    matrix JK[`i', 1] = `p'
    matrix JK[`i', 2] = _b[tau_post]
    matrix JK[`i', 3] = _b[tau_post] - 1.96*_se[tau_post]
    matrix JK[`i', 4] = _b[tau_post] + 1.96*_se[tau_post]
    local i = `i' + 1
}

clear
svmat JK
rename JK1 prov_excluida
rename JK2 coef_jk
rename JK3 ci_low_jk
rename JK4 ci_up_jk
sort coef_jk
export delimited using "`path_out'\jackknife_capital.csv", replace
restore
disp "[ÉXITO] Jackknife exportado. Fin del Script."