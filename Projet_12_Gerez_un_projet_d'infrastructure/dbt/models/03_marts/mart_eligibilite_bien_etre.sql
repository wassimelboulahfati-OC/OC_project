with rh as (
    select * from {{ ref('stg_rh') }}
),

activites as (
    select * from {{ ref('int_activites_par_salarie') }}
),

final as (
    select
        rh.id_salarie,
        rh.nom,
        rh.prenom,
        rh.business_unit,
        coalesce(a.nb_activites, 0) as nb_activites,
        a.distance_totale_km,
        a.duree_totale_min,

        -- Éligibilité bien-être : au moins {seuil} activités sur 12 mois
        case
            when coalesce(a.nb_activites, 0) >= {{ var('seuil_jours_bien_etre') }}
                then true
            else false
        end as eligible_bien_etre,

        -- Nombre de jours bien-être accordés (si éligible)
        case
            when coalesce(a.nb_activites, 0) >= {{ var('seuil_jours_bien_etre') }}
                then {{ var('nb_jours_bien_etre') }}
            else 0
        end as jours_bien_etre

    from rh
    left join activites a
        on rh.id_salarie = a.id_salarie
)

select * from final
