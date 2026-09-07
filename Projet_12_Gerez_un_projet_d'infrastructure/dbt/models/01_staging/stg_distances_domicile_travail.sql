with source as (
    select * from {{ source('raw', 'distances_domicile_travail') }}
),

renamed as (
    select
        cast(id_salarie as integer) as id_salarie,
        trim(adresse_domicile) as adresse_domicile,
        trim(moyen_deplacement) as moyen_deplacement,
        trim(profil_ors) as profil_ors,
        cast(lon_domicile as numeric) as lon_domicile,
        cast(lat_domicile as numeric) as lat_domicile,
        trim(precision_geocodage) as precision_geocodage,
        cast(distance_km as numeric) as distance_km,
        trim(methode_calcul) as methode_calcul
    from source
)

select * from renamed
