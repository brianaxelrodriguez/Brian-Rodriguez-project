from sqlalchemy import create_engine

# Definimos la conexión
url = "postgresql://postgres:cure_1982@localhost:5432/local_db"

try:
    # Agregamos client_encoding para asegurar la charla con Postgres
    engine = create_engine(url, connect_args={"client_encoding": "utf8"})

    # Prueba de fuego: una consulta que solo devuelve texto simple
    with engine.connect() as conn:
        res = conn.execute("SELECT 'Conexión OK' as test")
        print(f"✅ {res.fetchone()[0]}")

except Exception as e:
    # Si falla aquí, imprimiremos el error de forma que no rompa la consola
    print(f"❌ Error detectado: {str(e).encode('ascii', 'ignore').decode('ascii')}")
