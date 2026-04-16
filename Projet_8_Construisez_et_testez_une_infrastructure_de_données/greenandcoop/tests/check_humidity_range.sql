-- Test : humidité hors plage physiquement plausible (0% / 100%)
select
    observation_id,
    station_id,
    observed_at,
    humidity_pct,
    'humidity_pct hors plage [0, 100]' as raison
from {{ ref('fact_weather_observations') }}
where humidity_pct is not null
  and (humidity_pct < 0 or humidity_pct > 100)
