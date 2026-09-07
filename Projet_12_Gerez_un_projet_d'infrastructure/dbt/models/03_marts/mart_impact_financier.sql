with prime as (
    select
        id_salarie,
        eligible_prime,
        montant_prime
    from {{ ref('mart_eligibilite_prime') }}
),

bien_etre as (
    select
        id_salarie,
        eligible_bien_etre,
        jours_bien_etre
    from {{ ref('mart_eligibilite_bien_etre') }}
),

rh as (
    select
        id_salarie,
        salaire_brut
    from {{ ref('stg_rh') }}
),

-- Détail par salarié : prime + valorisation des jours bien-être en euros
detail as (
    select
        rh.id_salarie,
        rh.salaire_brut,
        coalesce(p.montant_prime, 0) as montant_prime,
        coalesce(p.eligible_prime, false) as eligible_prime,
        coalesce(be.jours_bien_etre, 0) as jours_bien_etre,
        coalesce(be.eligible_bien_etre, false) as eligible_bien_etre,

        -- Coût des jours bien-être = salaire journalier x nb de jours accordés
        round(
            (rh.salaire_brut / {{ var('nb_jours_ouvres_an') }})
            * coalesce(be.jours_bien_etre, 0)
        , 2) as cout_jours_bien_etre

    from rh
    left join prime p on rh.id_salarie = p.id_salarie
    left join bien_etre be on rh.id_salarie = be.id_salarie
),

-- Synthèse globale (une seule ligne d'indicateurs)
synthese as (
    select
        count(*) as effectif_total,

        -- Prime sportive
        count(*) filter (where eligible_prime) as nb_beneficiaires_prime,
        sum(montant_prime) as cout_total_primes,

        -- Bien-être
        count(*) filter (where eligible_bien_etre) as nb_beneficiaires_bien_etre,
        sum(jours_bien_etre) as total_jours_bien_etre,
        sum(cout_jours_bien_etre) as cout_total_bien_etre,

        -- Impact financier global
        sum(montant_prime) + sum(cout_jours_bien_etre) as cout_total_dispositif,

        -- Salariés cumulant les deux avantages
        count(*) filter (where eligible_prime and eligible_bien_etre) as nb_double_avantage

    from detail
)

select * from synthese
