{{ config(materialized='view') }}

with source as (
    select * from {{ ref('brz_infoclimat', version=1) }}
)

select
    id_station                              as station_id,
    dh_utc::timestamp without time zone     as observed_at,
    'infoclimat'                            as source_system,

    -- Mesures communes (ordre identique dans les 3 silver)
    temperature                             as temperature_c,
    pression                                as pressure_hpa,
    humidite                                as humidity_pct,
    point_de_rosee                          as dew_point_c,
    round((vent_moyen * 3.6)::numeric, 1)   as wind_speed_kmh,
    round((vent_rafales * 3.6)::numeric, 1) as wind_gust_kmh,
    vent_direction                          as wind_direction_deg,
    null::text                              as wind_direction_text,
    pluie_1h                                as precip_rate_mmh,
    null::numeric                           as precip_accum_mm,
    pluie_3h                                as precip_accum_3h_mm,
    null::numeric                           as uv_index,
    null::numeric                           as solar_radiation_wm2,

    -- Mesures spécifiques infoclimat
    visibilite                              as visibility_m,
    nebulosite                              as cloud_cover_oktas,
    neige_au_sol                            as snow_ground_cm,
    temps_omm                               as weather_code_omm

from source
