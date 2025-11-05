/* ============================================================
   VADI – Diagnóstico rápido de calidad de datos (PostgreSQL/PostGIS)
   Ejecutar en base: validador_db
   Autor: Luis & Chatty
   ============================================================ */

-- Por las dudas:
SET search_path TO public;

-- Versión de Postgres / PostGIS
SELECT version();
SELECT PostGIS_Full_Version();

-- ============================
-- 0) Conteo por tabla núcleo
-- ============================
SELECT 'core_street'   AS tabla, COUNT(*) AS filas FROM core_street
UNION ALL
SELECT 'core_blockgrid', COUNT(*) FROM core_blockgrid
UNION ALL
SELECT 'core_building',  COUNT(*) FROM core_building
UNION ALL
SELECT 'core_parcel',    COUNT(*) FROM core_parcel
UNION ALL
SELECT 'core_querylog',  COUNT(*) FROM core_querylog
ORDER BY 1;

-- =========================================
-- 1) Estructura básica (columnas y tipos)
-- =========================================
-- Cambiá el table_name si querés otra tabla
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema='public' AND table_name='core_street'
ORDER BY ordinal_position;

-- =========================================
-- 2) Nulos y geometrías – core_street
-- =========================================
SELECT
  COUNT(*)                                 AS total,
  SUM((name  IS NULL OR name  = '')::int)  AS nulos_name,
  SUM((kind  IS NULL OR kind  = '')::int)  AS nulos_kind,
  SUM((geom  IS NULL)::int)                AS nulos_geom
FROM core_street;

SELECT kind, COUNT(*) AS c
FROM core_street
GROUP BY kind ORDER BY c DESC;

-- geometrías: tipo, SRID y validez
SELECT ST_GeometryType(geom) AS gtype, ST_SRID(geom) AS srid, COUNT(*) AS c
FROM core_street
GROUP BY 1,2
ORDER BY c DESC;

SELECT COUNT(*) AS invalid_geoms
FROM core_street
WHERE geom IS NOT NULL AND NOT ST_IsValid(geom);

-- Muestra aleatoria
SELECT id, kind, name
FROM core_street
ORDER BY random()
LIMIT 20;

-- =========================================
-- 3) Nulos y geometrías – core_blockgrid
-- (chacras / manzanas)
-- =========================================
SELECT
  COUNT(*)                                   AS total,
  SUM((chacra  IS NULL OR chacra  = '')::int)  AS nulos_chacra,
  SUM((manzana IS NULL OR manzana = '')::int)  AS nulos_manzana,
  SUM((geom    IS NULL)::int)                  AS nulos_geom
FROM core_blockgrid;

SELECT ST_GeometryType(geom) AS gtype, ST_SRID(geom) AS srid, COUNT(*) AS c
FROM core_blockgrid
GROUP BY 1,2 ORDER BY c DESC;

SELECT COUNT(*) AS invalid_geoms
FROM core_blockgrid
WHERE geom IS NOT NULL AND NOT ST_IsValid(geom);

SELECT id, chacra, manzana
FROM core_blockgrid
ORDER BY random()
LIMIT 20;

-- =========================================
-- 4) Nulos y geometrías – core_building
-- (monoblocks / edificios / casas puntuales)
-- =========================================
SELECT
  COUNT(*) AS total,
  SUM((barrio  IS NULL OR barrio  = '')::int)   AS nulos_barrio,
  SUM((chacra  IS NULL OR chacra  = '')::int)   AS nulos_chacra,
  SUM((manzana IS NULL OR manzana = '')::int)   AS nulos_manzana,
  SUM((numero  IS NULL OR numero  = '')::int)   AS nulos_numero,
  SUM((letra   IS NULL OR letra   = '')::int)   AS nulos_letra,
  SUM((escalera IS NULL OR escalera = '')::int) AS nulos_escalera,
  SUM((geom    IS NULL)::int)                   AS nulos_geom
FROM core_building;

SELECT ST_GeometryType(geom) AS gtype, ST_SRID(geom) AS srid, COUNT(*) AS c
FROM core_building
GROUP BY 1,2 ORDER BY c DESC;

SELECT COUNT(*) AS invalid_geoms
FROM core_building
WHERE geom IS NOT NULL AND NOT ST_IsValid(geom);

SELECT id, barrio, chacra, manzana, numero, letra, escalera
FROM core_building
ORDER BY random()
LIMIT 20;

-- =========================================
-- 5) Nulos y geometrías – core_parcel
-- (lotes)
-- =========================================
SELECT
  COUNT(*) AS total,
  SUM((chacra  IS NULL OR chacra  = '')::int)  AS nulos_chacra,
  SUM(('block'  IS NULL OR 'block' = '')::int)  AS nulos_manzana,
  SUM((lot    IS NULL OR lot    = '')::int)  AS nulos_lote,
  SUM((geom    IS NULL)::int)                  AS nulos_geom
FROM core_parcel;

SELECT ST_GeometryType(geom) AS gtype, ST_SRID(geom) AS srid, COUNT(*) AS c
FROM core_parcel
GROUP BY 1,2 ORDER BY c DESC;

SELECT COUNT(*) AS invalid_geoms
FROM core_parcel
WHERE geom IS NOT NULL AND NOT ST_IsValid(geom);

SELECT id, chacra, 'block', lot
FROM core_parcel
ORDER BY random()
LIMIT 20;

-- =========================================
-- 6) QueryLog – actividad del validador
-- =========================================
-- Últimas validaciones
SELECT id, created_at, user_id, result, raw_text, street_id, building_id
FROM core_querylog
ORDER BY created_at DESC
LIMIT 20;

-- Conteo por resultado
SELECT result, COUNT(*) AS c
FROM core_querylog
GROUP BY result
ORDER BY c DESC;

-- Por día (últimos 30)
SELECT DATE(created_at) AS dia, result, COUNT(*) AS c
FROM core_querylog
WHERE created_at >= NOW() - INTERVAL '30 day'
GROUP BY 1,2
ORDER BY 1 DESC, 2;

-- =========================================
-- 7) Búsquedas útiles rápidas
-- =========================================
-- ¿Existe 'Lavalle' (en nombre)?
SELECT id, kind, name
FROM core_street
WHERE name ILIKE '%lavall%'
LIMIT 20;

-- Calles más largas (aprox.)
SELECT id, name, kind, ROUND(ST_Length(geom::geography)) AS metros
FROM core_street
ORDER BY metros DESC
LIMIT 20;

-- Edificio + calle más cercana (si tenés columna street_id)
-- SELECT b.id, b.barrio, b.chacra, b.manzana, b.numero, s.name AS calle
-- FROM core_building b
-- LEFT JOIN core_street s ON s.id = b.street_id
-- LIMIT 20;

-- =========================================
-- 8) Geometrías con SRID inesperado
-- =========================================
SELECT 'core_street'   AS tabla, ST_SRID(geom) AS srid, COUNT(*) AS c
FROM core_street GROUP BY 1,2
UNION ALL
SELECT 'core_blockgrid', ST_SRID(geom), COUNT(*) FROM core_blockgrid GROUP BY 1,2
UNION ALL
SELECT 'core_building',  ST_SRID(geom), COUNT(*) FROM core_building  GROUP BY 1,2
UNION ALL
SELECT 'core_parcel',    ST_SRID(geom), COUNT(*) FROM core_parcel    GROUP BY 1,2
ORDER BY tabla, srid;

-- =========================================
-- 9) (Opcional) Índices recomendados
--    (copiar/pegar solo si decidís crearlos)
-- =========================================
CREATE INDEX IF NOT EXISTS idx_street_name_trgm ON core_street USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_street_geom      ON core_street USING gist (geom);
CREATE INDEX IF NOT EXISTS idx_blockgrid_geom   ON core_blockgrid USING gist (geom);
CREATE INDEX IF NOT EXISTS idx_building_geom    ON core_building  USING gist (geom);
CREATE INDEX IF NOT EXISTS idx_parcel_geom      ON core_parcel    USING gist (geom);
