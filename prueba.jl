using Pkg
# Activamos tu entorno de proyecto
Pkg.activate(".") 

# Cargamos las librerías (esto es lo que faltaba en tu último intento)
using LibPQ
using DataFrames

try
    # Conexión directa
    conn = LibPQ.Connection("host=localhost user=postgres password=cure_1982 dbname=local_db")
    println("✅ ¡CONECTADO!")

    # Leemos la tabla que creó Python
    res = execute(conn, "SELECT * FROM test_stata;")
    df = DataFrame(res)
    
    println("\n📊 Datos de la EPH/Prueba:")
    display(df)

    close(conn)
catch e
    @error "No se pudo conectar" exception=e
end