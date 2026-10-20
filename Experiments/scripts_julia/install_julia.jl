using Pkg
println(">>> ACTIVANDO ENTORNO...")
Pkg.activate(".") 

println(">>> INSTALANDO PAQUETES (Paciencia, Brian)...")
packages = ["DataFrames", "CSV", "Flux", "DifferentialEquations", "Turing", "Plots", "IJulia"]
Pkg.add(packages)

println(">>> PRECOMPILANDO...")
Pkg.precompile()
println(">>> LISTO! <<<")
