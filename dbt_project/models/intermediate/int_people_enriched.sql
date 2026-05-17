{{
    config(
        materialized='view',
        description='Couche intermediate : features dérivées et catégorisation business.'
    )
}}

-- ============================================================
-- int_people_enriched
-- ============================================================
-- Rôle de la couche intermediate :
--   • Calculer les features dérivées (catégories, percentiles, flags)
--   • Préparer le terrain pour les marts sans dupliquer la logique
--   • Garder le grain "1 personne" comme staging
--
-- Les seuils high_popularity_threshold / medium_popularity_threshold viennent
-- de dbt_project.yml — modifiables sans toucher au SQL.
-- ============================================================

with people as (
    select * from {{ ref('stg_popular_people') }}
),

with_metrics as (
    select
        *,

        -- Catégorisation business de la popularité (selon variables du projet)
        case
            when popularity_score >= {{ var('high_popularity_threshold') }} then 'high'
            when popularity_score >= {{ var('medium_popularity_threshold') }} then 'medium'
            else 'low'
        end as popularity_tier,

        -- Rangs (utile pour les top N)
        row_number() over (order by popularity_score desc) as popularity_rank_overall,

        row_number() over (
            partition by department
            order by popularity_score desc
        ) as popularity_rank_in_department,

        row_number() over (
            partition by gender
            order by popularity_score desc
        ) as popularity_rank_in_gender,

        -- Percentile de popularité (utile pour normaliser)
        percent_rank() over (order by popularity_score)::numeric(5, 4)
            as popularity_percentile,

        -- Z-score par département (popularité relative à son métier)
        case
            when stddev(popularity_score) over (partition by department) > 0 then
                ((popularity_score
                  - avg(popularity_score) over (partition by department))
                 / stddev(popularity_score) over (partition by department))::numeric(8, 4)
            else 0
        end as popularity_zscore_in_department,

        -- Flag : est-ce une star (top 1 % global) ?
        case
            when row_number() over (order by popularity_score desc)
                 <= ceil(count(*) over () * 0.01)
            then true else false
        end as is_top_1_pct,

        -- Total dans le département (utile pour pondérations en BI)
        count(*) over (partition by department) as department_size,
        count(*) over (partition by gender) as gender_size

    from people
)

select * from with_metrics
