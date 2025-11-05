-- % nulos por columna
WITH cols AS (
  SELECT 'core_blockgrid'::text AS t, count(*) AS n FROM core_blockgrid), stats AS (SELECT 'core_blockgrid' AS t, 100.0*sum((chacra IS NULL)::int)/c.n AS p_null_chacra, 100.0*sum((manzana IS NULL)::int)/c.n AS p_null_manzana, 100.0*sum((geom IS NULL)::int)/c.n AS p_null_geom FROM core_blockgrid, cols c WHERE c.t='core_blockgrid') SELECT * FROM stats;

WITH cols AS (
  SELECT 'core_building'::text AS t, count(*) AS n FROM core_building
)
SELECT 100.0*sum((barrio IS NULL)::int)/c.n AS p_null_barrio,
       100.0*sum((chacra IS NULL)::int)/c.n AS p_null_chacra,
       100.0*sum((manzana IS NULL)::int)/c.n AS p_null_manzana,
       100.0*sum((numero IS NULL)::int)/c.n AS p_null_numero,
       100.0*sum((geom IS NULL)::int)/c.n AS p_null_geom
FROM core_building, cols c WHERE c.t='core_building';
