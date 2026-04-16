with source as (

  select * from {{ source('raw_weather', 'infoclimat_raw') }}

)

SELECT
    id_station,
    dh_utc,
    temperature,
    pression,
    humidite,
    point_de_rosee,
    visibilite,
    vent_moyen,
    vent_rafales,
    vent_direction,
    pluie_1h,
    pluie_3h,
    neige_au_sol,
    nebulosite,
    temps_omm
FROM source