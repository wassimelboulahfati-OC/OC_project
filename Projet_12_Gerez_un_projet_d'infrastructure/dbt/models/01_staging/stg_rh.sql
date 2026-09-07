with source as (
    select * from {{ source('raw', 'rh') }}
),

renamed as (
    select
        cast("ID salarié" as integer) as id_salarie,
        trim("Nom") as nom,
        trim("Prénom") as prenom,
        cast("Date de naissance" as date) as date_naissance,
        trim("BU") as business_unit,
        cast("Date d'embauche" as date) as date_embauche,
        cast("Salaire brut" as numeric) as salaire_brut,
        trim("Type de contrat") as type_contrat,
        cast("Nombre de jours de CP" as integer) as nb_jours_cp,
        trim("Adresse du domicile") as adresse_domicile,
        trim("Moyen de déplacement") as moyen_deplacement
    from source
)

select * from renamed
