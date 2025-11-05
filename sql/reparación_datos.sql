/* ============================================================
   VADI – Reparación de atributos por overlay espacial
   Ejecutar en base: validador_db
   Tablas de trabajo:
     - core_chacra(numero, geom)  ← referencia con número de chacra
     - core_blockgrid(chacra, manzana, geom)
     - core_building(barrio, chacra, manzana, numero, letra, escalera, geom)
     - core_street(id, name, geom)
   ============================================================ */

SET search_path TO public;

-- 0) Extensiones (por las dudas)
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 1) Índices recomendados (no destructivos)
CREATE INDEX IF NOT EXISTS idx_chacra_geom     ON core_chacra    USING gist (geom);
CREATE INDEX IF NOT EXISTS idx_blockgrid_geom  ON core_blockgrid USING gist (geom);
CREATE INDEX IF NOT EXISTS idx_building_geom   ON core_building  USING gist (geom);
CREATE INDEX IF NOT EXISTS idx_street_geom     ON core_street    USING gist (geom);

-- 2) Completar core_blockgrid.chacra desde core_chacra (overlay)
--    Nota: usa bounding box (&&) + ST_Intersects para performance/corrección
UPDATE core_blockgrid bg
SET chacra = c.numero
FROM core_chacra c
WHERE bg.chacra IS NULL
  AND bg.geom && c.geom
  AND ST_Intersects(bg.geom, c.geom);

-- 3) (Diagnóstico) Ver cuánto quedó sin chacra
SELECT COUNT(*) AS bg_sin_chacra
FROM core_blockgrid
WHERE chacra IS NULL;

-- 4) Completar core_building.chacra por intersección con core_chacra
UPDATE core_building b
SET chacra = c.numero
FROM core_chacra c
WHERE b.chacra IS NULL
  AND b.geom && c.geom
  AND ST_Intersects(b.geom, c.geom);

-- 5) Completar core_building.manzana por intersección con core_blockgrid
--    Si hay múltiples intersecciones, nos quedamos con la de mayor área de solape.
--    Usamos una CTE para elegir la mejor coincidencia por building.id
WITH cand AS (
  SELECT
    b.id AS bid,
    bg.manzana,
    ST_Area(ST_Intersection(b.geom, bg.geom)::geography) AS area_solape,
    ROW_NUMBER() OVER (PARTITION BY b.id ORDER BY ST_Area(ST_Intersection(b.geom, bg.geom)::geography) DESC) AS rn
  FROM core_building b
  JOIN core_blockgrid bg
    ON b.geom && bg.geom
   AND ST_Intersects(b.geom, bg.geom)
  WHERE b.manzana IS NULL
),
pick AS (
  SELECT bid, manzana
  FROM cand
  WHERE rn = 1
)
UPDATE core_building b
SET manzana = p.manzana
FROM pick p
WHERE b.id = p.bid
  AND b.manzana IS NULL;

-- 6) (Diagnóstico) Cuántos edificios siguen sin chacra/manzana
SELECT
  SUM((b.chacra  IS NULL)::int)  AS edificios_sin_chacra,
  SUM((b.manzana IS NULL)::int)  AS edificios_sin_manzana
FROM core_building b;

-- 7) (Opcional) Asociar edificio a su calle más cercana (<= 20 m)
--    Agregar columna si no existe
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='core_building' AND column_name='street_id'
  ) THEN
    ALTER TABLE core_building ADD COLUMN street_id integer;
    CREATE INDEX IF NOT EXISTS idx_building_street_id ON core_building(street_id);
  END IF;
END$$;

--    Completar street_id por proximidad (top 1 por distancia)
UPDATE core_building b
SET street_id = s.id
FROM LATERAL (
  SELECT id
  FROM core_street
  WHERE ST_DWithin(b.geom, geom, 20)         -- radio 20 m, ajustable
  ORDER BY ST_Distance(b.geom, geom)
  LIMIT 1
) s
WHERE b.street_id IS NULL;

-- 8) (Resumen final)
SELECT
  (SELECT COUNT(*) FROM core_blockgrid WHERE chacra IS NULL)   AS bg_restantes_sin_chacra,
  (SELECT COUNT(*) FROM core_building  WHERE chacra IS NULL)   AS b_restantes_sin_chacra,
  (SELECT COUNT(*) FROM core_building  WHERE manzana IS NULL)  AS b_restantes_sin_manzana,
  (SELECT COUNT(*) FROM core_building  WHERE street_id IS NULL)AS b_restantes_sin_calle;
