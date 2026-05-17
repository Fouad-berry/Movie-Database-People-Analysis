{{
    config(
        materialized='table',
        description='Dimension agrégée par département : KPIs par métier du cinéma.'
    )
}}

-- ============================================================
-- dim_department_stats
-- ============================================================
-- Statistiques agrégées par département.
-- Idéal pour les bar charts "popularité moyenne par métier".
-- ============================================================

select
    department,

    count(*) as n_people,
    sum(case when gender = 'female' then 1 else 0 end) as n_female,
    sum(case when gender = 'male' then 1 else 0 end) as n_male,
    sum(case when gender = 'non_binary' then 1 else 0 end) as n_non_binary,
    sum(case when gender = 'not_specified' then 1 else 0 end) as n_not_specified,

    -- Métriques de popularité
    round(avg(popularity_score), 3) as avg_popularity,
    round(median(popularity_score), 3) as median_popularity,
    round(max(popularity_score), 3) as max_popularity,
    round(min(popularity_score), 3) as min_popularity,
    round(stddev(popularity_score), 3) as stddev_popularity,
    round(sum(popularity_score), 3) as sum_popularity,

    -- Répartition par tier
    sum(case when popularity_tier = 'high' then 1 else 0 end) as n_high_tier,
    sum(case when popularity_tier = 'medium' then 1 else 0 end) as n_medium_tier,
    sum(case when popularity_tier = 'low' then 1 else 0 end) as n_low_tier,

    -- % de femmes dans le département (KPI diversité)
    round(
        100.0 * sum(case when gender = 'female' then 1 else 0 end) / count(*),
        2
    ) as pct_female,

    -- Top star du département
    (array_agg(person_name order by popularity_score desc))[1] as top_person_name,
    round(max(popularity_score), 3) as top_person_popularity

from {{ ref('int_people_enriched') }}
group by department
order by n_people desc
