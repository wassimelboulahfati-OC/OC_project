{{ config(materialized='view') }}

-- Extraction de la partie numérique et conversions impérial → métrique
-- Données WU : °F → °C, inHg → hPa, mph → km/h, pouces → mm

with source as (
    select * from {{ ref('brz_wu_ichtegem', version=1) }}
)

select
    id_station                                                                              as station_id,
    dh_utc::timestamp without time zone                                                     as observed_at,
    'weather_underground'                                                                   as source_system,

    -- Température °F → °C
    round(((nullif(regexp_replace(temperature, '[^0-9.-]', '', 'g'), '')::numeric - 32) * 5.0 / 9.0)::numeric, 2)
                                                                                            as temperature_c,
    -- Pression inHg → hPa
    round((nullif(regexp_replace(pressure, '[^0-9.-]', '', 'g'), '')::numeric * 33.8639)::numeric, 1)
                                                                                            as pressure_hpa,
    -- Humidité %
    nullif(regexp_replace(humidity, '[^0-9.-]', '', 'g'), '')::numeric                     as humidity_pct,

    -- Point de rosée °F → °C
    round(((nullif(regexp_replace(dew_point, '[^0-9.-]', '', 'g'), '')::numeric - 32) * 5.0 / 9.0)::numeric, 2)
                                                                                            as dew_point_c,
    -- Vitesse vent mph → km/h
    round((nullif(regexp_replace(speed, '[^0-9.-]', '', 'g'), '')::numeric * 1.60934)::numeric, 1)
                                                                                            as wind_speed_kmh,
    -- Rafales mph → km/h
    round((nullif(regexp_replace(gust, '[^0-9.-]', '', 'g'), '')::numeric * 1.60934)::numeric, 1)
                                                                                            as wind_gust_kmh,

    null::numeric                                                                           as wind_direction_deg,
    wind                                                                                    as wind_direction_text,

    -- Précipitations in/h → mm/h
    round((nullif(regexp_replace(precip__rate_, '[^0-9.-]', '', 'g'), '')::numeric * 25.4)::numeric, 3)
                                                                                            as precip_rate_mmh,
    -- Cumul précipitations in → mm
    round((nullif(regexp_replace(precip__accum_, '[^0-9.-]', '', 'g'), '')::numeric * 25.4)::numeric, 2)
                                                                                            as precip_accum_mm,
    null::numeric                                                                           as precip_accum_3h_mm,

    uv                                                                                      as uv_index,
    nullif(regexp_replace(solar, '[^0-9.-]', '', 'g'), '')::numeric                        as solar_radiation_wm2,

    -- Colonnes infoclimat absentes
    null::numeric                                                                           as visibility_m,
    null::numeric                                                                           as cloud_cover_oktas,
    null::numeric                                                                           as snow_ground_cm,
    null::numeric                                                                           as weather_code_omm

from source
