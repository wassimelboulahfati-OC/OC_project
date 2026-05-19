select
    station_id,
    observed_at,
    count(*) as nb_rows
from {{ ref('slv_wu_la_madeleine') }}
group by 1, 2
having count(*) > 1
