with source as (
    select * from {{ source('raw', 'sport') }}
),

renamed as (
    select
        cast("ID salarié" as integer) as id_salarie,
        trim("Pratique d'un sport") as sport_declare
    from source
    where "Pratique d'un sport" is not null
      and trim("Pratique d'un sport") <> ''
)

select * from renamed
