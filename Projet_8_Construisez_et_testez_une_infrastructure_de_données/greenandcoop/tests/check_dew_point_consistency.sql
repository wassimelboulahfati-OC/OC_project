-- Test : cohérence température / point de rosée
-- Le point de rosée ne peut pas être supérieur à la température (loi physique)
select
    observation_id,
    station_id,
    observed_at,
    temperature_c,
    dew_point_c,
    'dew_point_c > temperature_c (impossible physiquement)' as raison
from {{ ref('fact_weather_observations') }}
where temperature_c is not null
  and dew_point_c is not null
  and dew_point_c > temperature_c + 1  -- tolérance 1°C pour les arrondis
