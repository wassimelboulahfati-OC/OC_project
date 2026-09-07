with coherence as (
    select * from {{ ref('int_coherence_deplacement') }}
),

distances as (
    select
        id_salarie,
        distance_km,
        precision_geocodage,
        methode_calcul,
        distance_dans_plafond
    from {{ ref('int_distances_domicile_travail') }}
),

final as (
    select
        c.id_salarie,
        c.nom,
        c.prenom,
        c.business_unit,
        c.salaire_brut,
        c.moyen_deplacement,
        c.mode_sportif,
        c.plafond_distance_km,
        d.distance_km,
        d.distance_dans_plafond,
        d.precision_geocodage,

        -- Éligibilité à la prime : mode sportif ET distance dans le plafond
        case
            when c.mode_sportif = true
             and d.distance_dans_plafond = true
                then true
            else false
        end as eligible_prime,

        -- Montant de la prime = 5 % du salaire brut annuel (si éligible)
        case
            when c.mode_sportif = true
             and d.distance_dans_plafond = true
                then round(c.salaire_brut * {{ var('taux_prime') }}, 2)
            else 0
        end as montant_prime

    from coherence c
    left join distances d
        on c.id_salarie = d.id_salarie
)

select * from final
