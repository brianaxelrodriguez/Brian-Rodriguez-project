* ==============================================================================
* PAPER 2: HISTÉRESIS SANITARIA Y MORTALIDAD (2SLS / LATE / BLINDAJE TOP-TIER)
* ==============================================================================
clear all
set more off

* 1. Preparar Entorno e Instalar Paquetes Críticos (Solo se instalan si faltan)
cap ssc install psacalc
cap ssc install ivreg2
cap ssc install ranktest
cap ssc install avar
cap ssc install weakiv
cap ssc install boottest

* 2. Rutas y Carga de Datos
local path_data "C:\Users\brian\Documents\Proyectos_IA\data_raw\Procesados\BASE_FUSIONADA_VITALES_MASTER.csv"
local path_out "C:\Users\brian\Documents\Proyectos_IA\data_raw\PAPER 2\stata_output"
cap mkdir "`path_out'"

import delimited "`path_data'", clear

* Limpieza de ID
capture drop prov_id
encode provincia, gen(prov_id)
xtset prov_id anio

* ==============================================================================
* FEATURE ENGINEERING ESTRUCTURAL 
* ==============================================================================
* Variables Dependientes
capture drop ln_tasa_perinatal
gen ln_tasa_perinatal = log(tasa_perinatal)

capture drop ln_tasa_cancer 
capture drop tasa_cancer
gen tasa_cancer = (m_cancer_x / poblacion_lagrange) * 1000
gen ln_tasa_cancer = log(tasa_cancer + 1) 

* Variable Endógena: Capital / Obra Pública
capture drop ln_obra
gen ln_obra = log(obra_publica_pc_real)

* El Instrumento (Z): Obra Pública Histórica (Pre-2016) x Post-2018
gen post2018 = (anio >= 2018)
capture drop iv_obra_x_post
gen iv_obra_x_post = log(obra_hist_pc) * post2018

* Instrumento Placebo Temporal (Falsación 2016)
gen post2016 = (anio >= 2016)
capture drop iv_placebo_2016
gen iv_placebo_2016 = log(obra_hist_pc) * post2016

* Efectos fijos de año manuales (para ivreg2)
quietly tabulate anio, generate(year_)

* ==============================================================================
* PARTE I: MODELOS PRINCIPALES Y PLACEBOS (Exportación Matricial)
* ==============================================================================
disp "--- CORRIENDO MODELOS BASE ---"
matrix results = J(6, 4, .)

* 1: OLS SESGADO
xtreg ln_tasa_perinatal ln_obra i.anio, fe vce(cluster prov_id)
matrix results[1, 1] = _b[ln_obra]
matrix results[1, 2] = _se[ln_obra]
matrix results[1, 3] = 2 * ttail(e(df_r), abs(_b[ln_obra]/_se[ln_obra]))

* 2: FIRST STAGE 
xtreg ln_obra iv_obra_x_post i.anio, fe vce(cluster prov_id)
matrix results[2, 1] = _b[iv_obra_x_post]
matrix results[2, 2] = _se[iv_obra_x_post]
matrix results[2, 3] = 2 * ttail(e(df_r), abs(_b[iv_obra_x_post]/_se[iv_obra_x_post]))
test iv_obra_x_post = 0
matrix results[2, 4] = r(F) 

* 3: 2SLS (EFECTO CAUSAL LATE)
xtivreg ln_tasa_perinatal (ln_obra = iv_obra_x_post) i.anio, fe vce(cluster prov_id)
matrix results[3, 1] = _b[ln_obra]
matrix results[3, 2] = _se[ln_obra]
matrix results[3, 3] = 2 * normal(-abs(_b[ln_obra]/_se[ln_obra]))

* 4: REDUCED FORM
xtreg ln_tasa_perinatal iv_obra_x_post i.anio, fe vce(cluster prov_id)
matrix results[4, 1] = _b[iv_obra_x_post]
matrix results[4, 2] = _se[iv_obra_x_post]
matrix results[4, 3] = 2 * ttail(e(df_r), abs(_b[iv_obra_x_post]/_se[iv_obra_x_post]))

* 5: PLACEBO CÁNCER
xtivreg ln_tasa_cancer (ln_obra = iv_obra_x_post) i.anio, fe vce(cluster prov_id)
matrix results[5, 1] = _b[ln_obra]
matrix results[5, 2] = _se[ln_obra]
matrix results[5, 3] = 2 * normal(-abs(_b[ln_obra]/_se[ln_obra]))

* 6: PLACEBO TEMPORAL 2016
xtreg ln_tasa_perinatal iv_placebo_2016 i.anio if anio < 2018, fe vce(cluster prov_id)
matrix results[6, 1] = _b[iv_placebo_2016]
matrix results[6, 2] = _se[iv_placebo_2016]
matrix results[6, 3] = 2 * ttail(e(df_r), abs(_b[iv_placebo_2016]/_se[iv_placebo_2016]))

preserve
clear
svmat results
rename results1 coeficiente
rename results2 std_error
rename results3 p_valor
rename results4 f_stat
gen modelo = ""
replace modelo = "1_OLS_Sesgado" in 1
replace modelo = "2_First_Stage" in 2
replace modelo = "3_2SLS_Efecto_Causal" in 3
replace modelo = "4_Reduced_Form" in 4
replace modelo = "5_Placebo_Cancer" in 5
replace modelo = "6_Placebo_Temporal_2016" in 6
order modelo coeficiente std_error p_valor f_stat
export delimited using "`path_out'\modelos_2sls_resultados.csv", replace
restore
disp "[*] Modelos Base Exportados."

* ==============================================================================
* PARTE II: OSTER BOUNDS (Sensibilidad a Inobservables)
* ==============================================================================
disp "--- CALCULANDO LÍMITES DE OSTER ---"
quietly areg ln_tasa_perinatal ln_obra i.anio, absorb(prov_id)
local r2_obs = e(r2)
local rmax_calc = `r2_obs' * 1.3
if `rmax_calc' > 1 {
    local rmax_calc = 1
}

psacalc beta ln_obra, rmax(`rmax_calc') delta(1)
local beta_oster = r(beta)
psacalc delta ln_obra, rmax(`rmax_calc') beta(0)
local delta_oster = r(delta)

preserve
clear
set obs 1
gen beta_bound = `beta_oster'
gen delta_necesario_cero = `delta_oster'
export delimited using "`path_out'\oster_bounds.csv", replace
restore
disp "[*] Oster Bounds Exportados."

* ==============================================================================
* PARTE III: BLINDAJE WEAK-IV Y ROBUSTEZ MUESTRAL
* ==============================================================================
disp "--- KLEIBERGEN-PAAP Y ANDERSON-RUBIN TEST ---"
ivreg2 ln_tasa_perinatal year_2-year_9 (ln_obra = iv_obra_x_post), cluster(prov_id) partial(year_2-year_9)
weakiv ivreg2 ln_tasa_perinatal year_2-year_9 (ln_obra = iv_obra_x_post), cluster(prov_id) partial(year_2-year_9)

disp "--- ROBUSTEZ: EXCLUYENDO CABA Y PBA ---"
ivreg2 ln_tasa_perinatal year_2-year_9 (ln_obra = iv_obra_x_post) if provincia != "BUENOS AIRES" & provincia != "CABA", cluster(prov_id) partial(year_2-year_9)

disp "--- ROBUSTEZ: WILD CLUSTER BOOTSTRAP ---"
ivreg2 ln_tasa_perinatal year_2-year_9 (ln_obra = iv_obra_x_post), cluster(prov_id) partial(year_2-year_9)
boottest ln_obra, weighttype(webb) reps(999)

* ==============================================================================
* PARTE IV: EVENT STUDY DEL INSTRUMENTO (Pre-trends del Shift-Share)
* ==============================================================================
disp "--- CALCULANDO PRE-TRENDS DEL INSTRUMENTO ---"
forvalues y = 2011/2019 {
    if `y' != 2017 {
        capture drop iv_yr`y'
        gen iv_yr`y' = log(obra_hist_pc) * (anio == `y')
    }
}

quietly xtreg ln_tasa_perinatal iv_yr2011-iv_yr2016 iv_yr2018 iv_yr2019 i.anio, fe vce(cluster prov_id)

matrix res_iv_trends = J(8, 4, .)
local row = 1
foreach y in 2012 2013 2014 2015 2016 2018 2019 {
    matrix res_iv_trends[`row', 1] = `y'
    matrix res_iv_trends[`row', 2] = _b[iv_yr`y']
    local se = _se[iv_yr`y']
    matrix res_iv_trends[`row', 3] = _b[iv_yr`y'] - 1.96*`se'
    matrix res_iv_trends[`row', 4] = _b[iv_yr`y'] + 1.96*`se'
    local row = `row' + 1
}
matrix res_iv_trends[8, 1] = 2017
matrix res_iv_trends[8, 2] = 0
matrix res_iv_trends[8, 3] = 0
matrix res_iv_trends[8, 4] = 0

preserve
clear
svmat res_iv_trends
rename res_iv_trends1 anio
rename res_iv_trends2 coef_iv
rename res_iv_trends3 ci_low
rename res_iv_trends4 ci_high
sort anio
export delimited using "`path_out'\iv_pretrends.csv", replace
restore

disp "======================================================================="
disp " FIN DEL SCRIPT: PIPELINE DE INFERENCIA Y BLINDAJE P2 COMPLETADO."
disp "======================================================================="