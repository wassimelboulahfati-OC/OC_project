{{ config(
    materialized='table',
    indexes=[
        {'columns': ['observation_id'], 'unique': True,  'type': 'btree'},
        {'columns': ['station_id'],                      'type': 'btree'},
        {'columns': ['observed_at'],                     'type': 'btree'},
        {'columns': ['observation_date'],                'type': 'btree'},
        {'columns': ['station_id', 'observed_at'],       'type': 'btree'},
        {'columns': ['station_id', 'observation_date'],  'type': 'btree'},
    ]
) }}

with observations as (
    select * from {{ ref('int_weather_observations') }}
)

select
    -- Clé de substitution
    md5(station_id || '_' || observed_at::text)     as observation_id,

    -- Clés de dimension
    station_id,
    observed_at,
    observed_at::date                               as observation_date,
    date_part('year',  observed_at)::int            as year,
    date_part('month', observed_at)::int            as month,
    date_part('hour',  observed_at)::int            as hour,

    -- Source
    source_system,

    -- Température & Humidité
    temperature_c,
    dew_point_c,
    humidity_pct,

    -- Pression
    pressure_hpa,

    -- Vent
    wind_speed_kmh,
    wind_gust_kmh,
    wind_direction_deg,
    wind_direction_text,

    -- Précipitations
    precip_rate_mmh,
    precip_accum_mm,
    precip_accum_3h_mm,

    -- Rayonnement (WU uniquement)
    uv_index,
    solar_radiation_wm2,

    -- Visibilité & Couverture nuageuse (infoclimat uniquement)
    visibility_m,
    cloud_cover_oktas,
    snow_ground_cm,
    weather_code_omm

from observations
