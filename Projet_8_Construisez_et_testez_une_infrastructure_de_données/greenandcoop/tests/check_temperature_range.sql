-- Test : températures hors plage physiquement plausible (-60°C / +60°C)
-- Retourne les lignes en anomalie => le test échoue si count > 0
select
    observation_id,
    station_id,
    observed_at,
    temperature_c,
    'temperature_c hors plage [-60, 60]' as raison
from {{ ref('fact_weather_observations') }}
where temperature_c is not null
  and (temperature_c < -60 or temperature_c > 60)
