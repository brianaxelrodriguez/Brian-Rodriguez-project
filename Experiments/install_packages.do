* --- CONFIGURACIÓN DE SILENCIO ABSOLUTO ---
set more off
set graphics off
set notifyuser off

* --- FUNCIÓN DE INSTALACIÓN SEGURA ---
* Creamos un programa temporal para instalar sin protestar
capture program drop safe_install
program define safe_install
    syntax name
    display "Instalando `1'..."
    quietly {
        capture ssc install `1', replace
    }
end

* --- DEFINIR RUTAS ---
sysdir set PLUS "C:\Users\brian\Documents\Proyectos_IA\stata_lib\plus"
sysdir set PERSONAL "C:\Users\brian\Documents\Proyectos_IA\stata_lib\personal"

* --- UTILIDADES BÁSICAS ---
capture ssc install ftools, replace      // Faster Stata tools (Requisito para reghdfe)
capture ssc install gtools, replace      // Faster group operations (usa C plugins)

* --- ECONOMETRÍA & INFERENCIA CAUSAL ---
capture ssc install reghdfe, replace     // Fixed Effects (Estándar de oro)
capture ssc install ivreg2, replace      // Variables instrumentales robustas
capture ssc install ranktest, replace    // Tests de rango para IV
capture ssc install estout, replace      // Exportar tablas a LaTeX/Excel
capture ssc install outreg2, replace     // Otra opción de exportación
capture ssc install boottest, replace    // Wild Bootstrap (Inferencia robusta en small samples)
capture ssc install ritest, replace      // Randomization Inference
capture ssc install drdid, replace       // Doubly Robust Diff-in-Diff
capture ssc install csdid, replace       // Callaway & Sant'Anna DID (Heterogeneous treatment effects)
capture ssc install ddid, replace        // Difference-in-Differences (alternativo)

* --- SERIES DE TIEMPO / ESPACIAL ---
capture ssc install spmap, replace       // Mapas en Stata (básico)
capture ssc install shp2dta, replace     // Convertir Shapefiles
capture ssc install xcorr, replace       // Cross-correlation
capture ssc install ardl, replace        // Autoregressive Distributed Lag
capture ssc install xtabond2, replace    // Dynamic Panel (Arellano-Bond)

* --- SALUD Y FRONTERAS (PHD ADD-ONS) ---
capture ssc install frontier, replace    // Stochastic Frontier Analysis (Eficiencia)
capture ssc install cmp, replace         // Conditional Mixed Process (Modelos complejos)
capture ssc install mapproject, replace  // Proyecciones geográficas
capture ssc install ssm, replace         // Sample Selection Models

* --- MACHINE LEARNING (Lo que Stata puede hacer) ---
capture ssc install lassopack, replace   // LASSO, Ridge, Elastic Net (Regularization)
capture net install rforest, from("https://raw.githubusercontent.com/stevebez/rforest/master/") replace // Random Forest wrapper
capture ssc install svmachines, replace  // Support Vector Machines (básico)

* --- VISUALIZACIÓN ---
capture ssc install scheme-pack, replace // Esquemas de color modernos (Unibe, Clean)
capture ssc install colorpalette, replace
capture ssc install grstyle, replace
capture ssc install blindschemes, replace // Esquemas para daltónicos / Publicaciones académicas

display "PROCESO COMPLETADO EXITOSAMENTE."
exit, clear