-- Test custom singulier
-- ----------------------
-- Vérifie qu'aucune personne n'a un rank dans son département supérieur
-- à la taille du département (incohérence logique impossible normalement).
-- Si ce test retourne des lignes, dbt échoue.

select
    person_name,
    department,
    popularity_rank_in_department,
    department_size
from {{ ref('int_people_enriched') }}
where popularity_rank_in_department > department_size
