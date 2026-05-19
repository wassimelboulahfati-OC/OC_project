{{ config(materialized='view') }}

with infoclimat as (
    select * from {{ ref('slv_infoclimat') }}
),

wu_ichtegem as (
    select * from {{ ref('slv_wu_ichtegem') }}
),

wu_la_madeleine as (
    select * from {{ ref('slv_wu_la_madeleine') }}
),

unioned as (
    select * from infoclimat
    union all
    select * from wu_ichtegem
    union all
    select * from wu_la_madeleine
)

select * from unioned
