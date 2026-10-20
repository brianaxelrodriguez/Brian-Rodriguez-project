-- Extensiones para análisis avanzado
CREATE EXTENSION IF NOT EXISTS pgrouting;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS tablefunc;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 1. GEOLOCALIZACIÓN
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch; 
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. PARALELISMO (Optimizado para tu Ryzen 9)
ALTER SYSTEM SET max_parallel_workers_per_gather = 8;
ALTER SYSTEM SET max_worker_processes = 16;

-- 3. VECTORES (pgvector)
DO $$ 
BEGIN 
    CREATE EXTENSION IF NOT EXISTS vector; 
EXCEPTION 
    WHEN undefined_file THEN 
        RAISE NOTICE 'ALERTA: pgvector no instalado en el sistema operativo.'; 
END $$;