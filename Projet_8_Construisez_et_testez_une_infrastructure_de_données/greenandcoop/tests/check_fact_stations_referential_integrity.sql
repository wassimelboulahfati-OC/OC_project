-- Test : toutes les stations présentes dans la fact doivent exister dans la dimension
-- Complète le test 'relationships' du YAML pour une vérification inverse
select distinct
    f.station_id
from {{ ref('fact_weather_observations') }} f
left join {{ ref('dim_weather_stations') }} d on f.station_id = d.station_id
where d.station_id is null
