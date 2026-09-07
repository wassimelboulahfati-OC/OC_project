with distances as (
    select
        id_salarie,
        adresse_domicile,
        moyen_deplacement,
        distance_km,
        plafond_distance_km,
        distance_dans_plafond,
        precision_geocodage,
        methode_calcul
    from {{ ref('int_distances_domicile_travail') }}
),

rh as (
    select id_salarie, nom, prenom, business_unit
    from {{ ref('stg_rh') }}
),

-- 1. Adresses imprécises (géocodage au niveau ville uniquement)
adresses_imprecises as (
    select
        d.id_salarie,
        'Adresse imprécise' as type_anomalie,
        'Adresse géocodée au niveau ville uniquement (distance approximative). '
        || 'À préciser dans le SIRH.' as detail,
        d.adresse_domicile as valeur_concernee
    from distances d
    where d.precision_geocodage = 'ville_approx'
),

-- 2. Géocodage totalement échoué (adresse inexploitable)
geocodage_echoue as (
    select
        d.id_salarie,
        'Géocodage impossible' as type_anomalie,
        'Adresse non localisable. Vérifier et corriger dans le SIRH.' as detail,
        d.adresse_domicile as valeur_concernee
    from distances d
    where d.methode_calcul = 'geocodage_echoue'
),

-- 3. Distance incohérente avec le mode de déplacement (hors plafond)
distance_hors_plafond as (
    select
        d.id_salarie,
        'Distance hors plafond' as type_anomalie,
        'Distance domicile-travail (' || d.distance_km || ' km) supérieure au '
        || 'plafond autorisé (' || d.plafond_distance_km || ' km) pour le mode "'
        || d.moyen_deplacement || '". À vérifier.' as detail,
        d.distance_km::text as valeur_concernee
    from distances d
    where d.distance_dans_plafond = false
),

-- Union de toutes les anomalies RH
union_anomalies as (
    select * from adresses_imprecises
    union all
    select * from geocodage_echoue
    union all
    select * from distance_hors_plafond
),

final as (
    select
        a.id_salarie,
        rh.nom,
        rh.prenom,
        rh.business_unit,
        a.type_anomalie,
        a.detail,
        a.valeur_concernee
    from union_anomalies a
    left join rh on a.id_salarie = rh.id_salarie
)

select * from final
order by type_anomalie, id_salarie
