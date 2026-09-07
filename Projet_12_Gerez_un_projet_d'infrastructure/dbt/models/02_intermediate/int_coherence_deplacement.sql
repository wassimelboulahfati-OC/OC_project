with rh as (
    select * from {{ ref('stg_rh') }}
),

classification as (
    select
        id_salarie,
        nom,
        prenom,
        business_unit,
        salaire_brut,
        adresse_domicile,
        moyen_deplacement,

        -- Le mode de déplacement est-il "sportif" (éligible à la prime) ?
        case
            when moyen_deplacement in ('Marche/running', 'Vélo/Trottinette/Autres')
                then true
            else false
        end as mode_sportif,

        -- Plafond de distance applicable selon le mode (en km).
        -- Variables paramétrables depuis dbt_project.yml.
        case
            when moyen_deplacement = 'Marche/running'
                then {{ var('plafond_marche_km') }}
            when moyen_deplacement = 'Vélo/Trottinette/Autres'
                then {{ var('plafond_velo_km') }}
            else null
        end as plafond_distance_km

    from rh
)

select * from classification
