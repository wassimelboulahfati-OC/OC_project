{{ config(
    materialized='table',
    indexes=[
        {'columns': ['station_id'], 'unique': True, 'type': 'btree'},
        {'columns': ['source_system'],                   'type': 'btree'},
        {'columns': ['country'],                         'type': 'btree'},
    ]
) }}

select
    station_id,
    station_name,
    latitude,
    longitude,
    elevation_m,
    city,
    country,
    hardware,
    software,
    source_system
from {{ ref('dim_weather_stations_metadata') }}
