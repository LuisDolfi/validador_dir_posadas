SELECT id,
       district,
       section,
       block,
       lot,
       parcel,
       unit,
       gid,
       geom,
       chacra
FROM public.core_parcel
LIMIT 1000;