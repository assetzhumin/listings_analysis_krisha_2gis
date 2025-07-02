CREATE MATERIALIZED VIEW filter_listings AS
WITH filter_listings AS(
  SELECT
  link,
  (regexp_match(details, '^(\d+)-комнатная'))[1]::INT AS rooms,

  replace(
    (regexp_match(details, '·\s*([0-9]+(?:[.,][0-9]+)?)\s*м²'))[1],
    ',', '.'
  )::NUMERIC AS area_m2,

  nullif(
    regexp_replace(
      (regexp_match(details, '([0-9\u00A0\u202F ]+)\s*\|\s*〒'))[1],
      '\D', '', 'g'
    ),
    ''
  )::BIGINT AS price_kzt,

  (regexp_match(details, '·\s*([0-9]+)\s*/\s*[0-9]+\s*этаж'))[1]::INT AS floor,

  (regexp_match(details, '(\d{4})\s*г\.п\.'))[1]::INT AS year_built,

  COALESCE(
    (regexp_match(details, 'жил\.\s*комплекс\s*([^,|]+)'))[1],
    'не указано'
  ) AS residential_complex,

  CASE
    WHEN substring(details FROM '\|\s*〒\s*\|\s*р-н\s*([А-ЯЁа-яё\s-]+)') IS NOT NULL
      THEN substring(details FROM '\|\s*〒\s*\|\s*р-н\s*([А-ЯЁа-яё\s-]+)') || ' р-н'
    WHEN substring(details FROM '\|\s*〒\s*\|\s*([А-ЯЁа-яё\s-]+?)\s*р-н') IS NOT NULL
      THEN substring(details FROM '\|\s*〒\s*\|\s*([А-ЯЁа-яё\s-]+?)\s*р-н') || ' р-н'
    ELSE
      'не указано'
  END AS region

FROM listings
)

SELECT *
FROM filter_listings
