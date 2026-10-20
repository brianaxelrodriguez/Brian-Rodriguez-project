$rPath = "C:\Program Files\R\R-4.5.0\bin\x64\R.exe"
if (Test-Path $rPath) {
    & $rPath --vanilla -s -e "cat(Sys.which('make'))"
} else {
    Write-Host "No se encontró R en la ruta especificada" -ForegroundColor Red
}
