with source as (
    select * from {{ source('raw', 'activites') }}
),

nettoye as (
    select
        cast(id_activite as integer) as id_activite,
        cast(id_salarie as integer) as id_salarie,
        cast(date_activite as timestamp) as date_activite,

        -- Correction des fautes d'orthographe / normalisation
        case
            when lower(trim(type_activite)) = 'runing' then 'Running'
            when lower(trim(type_activite)) = 'running' then 'Running'
            else trim(type_activite)
        end as type_activite,

        cast(distance_km as numeric) as distance_km,
        cast(duree_min as integer) as duree_min,
        commentaire
    from source

    -- Filtrage des anomalies détectées par Great Expectations (Phase 3)
    where (distance_km is null or distance_km >= 0)  -- pas de distance négative
      and duree_min > 0                              -- durée strictement positive
      and date_activite <= now()                     -- pas de date future
      and id_salarie < 900000                        -- id salarié valide (référentiel RH)
)

select * from nettoye
