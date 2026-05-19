with source as (

  select * from {{ source('raw_weather', 'infoclimat') }}

),

deduped as (

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
        temps_omm,
        ROW_NUMBER() OVER (
            PARTITION BY id_station, dh_utc
            ORDER BY _airbyte_extracted_at DESC
        ) AS rn
    FROM source

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
FROM deduped
WHERE rn = 1
