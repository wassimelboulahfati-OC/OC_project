select
    id_station,
    dh_utc,
    count(*) as nb_rows
from {{ ref('brz_wu_ichtegem') }}
group by 1, 2
having count(*) > 1
