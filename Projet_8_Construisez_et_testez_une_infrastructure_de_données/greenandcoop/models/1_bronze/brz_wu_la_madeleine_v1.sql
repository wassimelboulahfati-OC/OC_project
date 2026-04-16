with source as (

    select * from {{ source('raw_weather', 'wu_la_madeleine_raw') }}

)

SELECT
    id_station,
    dh_utc,
    date,
    "Time"          AS time,
    "Temperature"   AS temperature,
    "Dew_Point"     AS dew_point,
    "Humidity"      AS humidity,
    "Wind"          AS wind,
    "Speed"         AS speed,
    "Gust"          AS gust,
    "Pressure"      AS pressure,
    "Precip__Rate_" AS precip__rate_,
    "Precip__Accum_" AS precip__accum_,
    "UV"            AS uv,
    "Solar"         AS solar
FROM source
