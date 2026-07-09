clear all
local path_data "C:\Users\brian\Documents\Proyectos_IA\data_raw\Procesados\BASE_FUSIONADA_VITALES_MASTER.csv"
import delimited "`path_data'", clear
xtset prov_id anio

* 1. Diccionario de provincias
preserve
keep prov_id provincia
duplicates drop
tempfile dic_provs
save `dic_provs'
restore

* 2. Setup de variables y EFECTOS FIJOS MANUALES
capture drop ln_tasa_perinatal
gen ln_tasa_perinatal = log(tasa_perinatal)
capture drop ln_obra
gen ln_obra = log(obra_publica_pc_real)
gen post2018 = (anio >= 2018)

* Dummies de año
quietly tabulate anio, generate(year_)
* Dummies de provincia (EL FIX DEL BUG)
quietly tabulate prov_id, generate(prov_)

* Instrumento Original
capture drop iv_original
gen iv_original = log(obra_hist_pc) * post2018

* ======================================================================
* JACKKNIFE 2SLS CON TWFE (EFECTOS FIJOS BIDIRECCIONALES)
* ======================================================================
disp "INICIANDO JACKKNIFE CORREGIDO (CON EFECTOS FIJOS PROVINCIALES)..."
matrix jack_res = J(24, 4, .)
local row = 1

levelsof prov_id, local(provs)
quietly foreach p of local provs {
    
    * Corremos el 2SLS parcializando (absorbiendo) años y TODAS las provincias excepto la omitida
    * Esto replica exactamente el xtreg, fe
    quietly ivreg2 ln_tasa_perinatal prov_2-prov_24 year_2-year_9 (ln_obra = iv_original) if prov_id != `p', cluster(prov_id) partial(prov_2-prov_24 year_2-year_9)
    
    matrix jack_res[`row', 1] = `p'
    matrix jack_res[`row', 2] = _b[ln_obra]
    matrix jack_res[`row', 3] = _se[ln_obra]
    matrix jack_res[`row', 4] = 2 * normal(-abs(_b[ln_obra]/_se[ln_obra]))
    
    local row = `row' + 1
}

* ======================================================================
* EXPORTAR RESULTADOS
* ======================================================================
preserve
clear
svmat jack_res
rename jack_res1 prov_id
rename jack_res2 coef_beta
rename jack_res3 se_beta
rename jack_res4 p_valor

merge 1:1 prov_id using `dic_provs'
drop _merge

gen ci_low = coef_beta - 1.96 * se_beta
gen ci_high = coef_beta + 1.96 * se_beta
sort coef_beta

export delimited using "C:\Users\brian\Documents\Proyectos_IA\data_raw\jackknife_twfe_corregido.csv", replace
restore
disp "======================================================================"
disp "[ÉXITO] Jackknife TWFE guardado en: jackknife_twfe_corregido.csv"
disp "======================================================================"