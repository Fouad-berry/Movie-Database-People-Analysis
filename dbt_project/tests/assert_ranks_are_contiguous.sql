-- Vérifie que les rangs globaux sont bien contigus (1 à N sans trou).

with ranked as (
    select popularity_rank_overall from {{ ref('int_people_enriched') }}
)

select 'gap in global ranks' as failure
where (select max(popularity_rank_overall) from ranked) <>
      (select count(*) from ranked)
