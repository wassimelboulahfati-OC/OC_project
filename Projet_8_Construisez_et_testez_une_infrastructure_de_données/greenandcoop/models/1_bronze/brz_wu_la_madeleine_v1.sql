with source as (

    select * from {{ source('raw_weather', 'wu_la_madeleine_raw') }}

),

deduped as (

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
        "Solar"         AS solar,
        ROW_NUMBER() OVER (
            PARTITION BY id_station, dh_utc
            ORDER BY _airbyte_extracted_at DESC
        ) AS rn
    FROM source

)

SELECT
    id_station,
    dh_utc,
    date,
    time,
    temperature,
    dew_point,
    humidity,
    wind,
    speed,
    gust,
    pressure,
    precip__rate_,
    precip__accum_,
    uv,
    solar
FROM deduped
WHERE rn = 1
