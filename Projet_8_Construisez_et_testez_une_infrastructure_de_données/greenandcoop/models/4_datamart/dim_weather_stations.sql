{{ config(materialized='table') }}

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
