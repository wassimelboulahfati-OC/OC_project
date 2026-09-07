with distances as (
    select * from {{ ref('stg_distances_domicile_travail') }}
),

-- Récupère le plafond applicable (déjà calculé dans int_coherence_deplacement)
coherence as (
    select
        id_salarie,
        plafond_distance_km
    from {{ ref('int_coherence_deplacement') }}
),

final as (
    select
        d.id_salarie,
        d.adresse_domicile,
        d.moyen_deplacement,
        d.profil_ors,
        d.distance_km,
        d.precision_geocodage,
        d.methode_calcul,
        c.plafond_distance_km,

        -- La distance respecte-t-elle le plafond du mode de déplacement ?
        case
            when d.distance_km is null then null
            when d.distance_km <= c.plafond_distance_km then true
            else false
        end as distance_dans_plafond

    from distances d
    left join coherence c
        on d.id_salarie = c.id_salarie
)

select * from final
