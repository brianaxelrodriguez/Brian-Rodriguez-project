lib_path <- 'C:/Users/brian/Documents/Proyectos_IA/R_library'
if(dir.exists(lib_path)) {
    pkgs <- installed.packages(lib.loc=lib_path)
    important <- pkgs[rownames(pkgs) %in% c('sf', 'terra', 'fixest', 'DoubleML', 'tidyverse', 'data.table'), c('Package', 'Version')]
    print(important)
} else {
    cat('Directorio de librer?a no encontrado')
}
