-- Test : pression hors plage physiquement plausible (870 hPa / 1085 hPa)
-- Records mondiaux : 870 hPa (typhon) et 1083.8 hPa (Sibérie)
select
    observation_id,
    station_id,
    observed_at,
    pressure_hpa,
    'pressure_hpa hors plage [870, 1085]' as raison
from {{ ref('fact_weather_observations') }}
where pressure_hpa is not null
  and (pressure_hpa < 870 or pressure_hpa > 1085)
