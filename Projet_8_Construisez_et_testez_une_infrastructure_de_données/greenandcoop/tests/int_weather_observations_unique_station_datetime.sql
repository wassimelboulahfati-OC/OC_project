select
    station_id,
    observed_at,
    count(*) as nb_rows
from {{ ref('int_weather_observations') }}
group by 1, 2
having count(*) > 1
