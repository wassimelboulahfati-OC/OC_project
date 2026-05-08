{{ config(materialized='view') }}

with source as (
    select * from {{ ref('brz_infoclimat', version=1) }}
)

select
    id_station                              as station_id,
    dh_utc::timestamp without time zone     as observed_at,
    'infoclimat'                            as source_system,

    -- Mesures communes (castées en numeric pour compatibilité UNION)
    temperature::numeric                    as temperature_c,
    pression::numeric                       as pressure_hpa,
    humidite::numeric                       as humidity_pct,
    point_de_rosee::numeric                 as dew_point_c,
    round((vent_moyen::numeric * 3.6)::numeric, 1)   as wind_speed_kmh,
    round((vent_rafales::numeric * 3.6)::numeric, 1)  as wind_gust_kmh,
    vent_direction::numeric                 as wind_direction_deg,
    null::text                              as wind_direction_text,
    pluie_1h::numeric                       as precip_rate_mmh,
    null::numeric                           as precip_accum_mm,
    pluie_3h::numeric                       as precip_accum_3h_mm,
    null::numeric                           as uv_index,
    null::numeric                           as solar_radiation_wm2,

    -- Mesures spécifiques infoclimat
    visibilite::numeric                     as visibility_m,
    nebulosite::numeric                     as cloud_cover_oktas,
    neige_au_sol::numeric                   as snow_ground_cm,
    temps_omm::numeric                      as weather_code_omm

from source
