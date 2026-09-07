with activites as (
    select * from {{ ref('stg_activites') }}
),

-- On ne conserve que les activités des 12 derniers mois glissants.
-- La fenêtre est calculée dynamiquement -> reproductible même avec un
-- historique plus long à l'avenir.
activites_12_mois as (
    select *
    from activites
    where date_activite >= (current_date - interval '12 months')
),

agrege as (
    select
        id_salarie,
        count(*) as nb_activites,
        count(distinct type_activite) as nb_types_differents,
        sum(coalesce(distance_km, 0)) as distance_totale_km,
        sum(duree_min) as duree_totale_min,
        min(date_activite) as premiere_activite,
        max(date_activite) as derniere_activite
    from activites_12_mois
    group by id_salarie
)

select * from agrege
