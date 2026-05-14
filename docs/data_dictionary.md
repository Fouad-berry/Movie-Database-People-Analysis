# 📖 Data Dictionary

## Source : `popular_people.csv`

Dataset téléchargé depuis [The Movie Database (TMDb)](https://www.themoviedb.org/). **9 980 lignes** représentant les personnalités les plus populaires du cinéma mondial.

### Colonnes brutes

| Colonne | Type | Description |
|---------|------|-------------|
| `name` | string | Nom affiché de la personne |
| `gender` | int | Code de genre TMDb (0/1/2/3) |
| `known_for_department` | string | Département principal d'activité |
| `original_name` | string | Nom original (avant traduction) |
| `popularity` | float | Score de popularité TMDb |

### Code `gender` (TMDb)

| Code | Libellé |
|------|---------|
| 0 | Non spécifié |
| 1 | Femme |
| 2 | Homme |
| 3 | Non-binaire |

### Départements rencontrés (14)

Acting (9 320), Directing (329), Writing (174), Production (43), Sound (27), Editing (18), Visual Effects (17), Crew (16), Art (8), Costume & Make-Up (8), Camera (7), Lighting (5), Creator (3), Unknown (5 ← NULL remplacés).

---

## Couche `staging` : `stg_popular_people`

**Grain** : 1 ligne = 1 personne · **Matérialisation** : view

| Colonne | Type | Source / transformation |
|---------|------|------------------------|
| `person_sk` | bigint | `row_number() over (order by popularity desc, name)` |
| `person_name` | varchar | `trim(name)` |
| `original_name` | varchar | `trim(original_name)` |
| `gender` | varchar | Mapping 0/1/2/3 → 'not_specified'/'female'/'male'/'non_binary' |
| `gender_code` | int | Code original conservé |
| `department` | varchar | NULL → 'Unknown' |
| `popularity_score` | numeric(10,4) | `cast(popularity as numeric)` |
| `has_translated_name` | bool | `name <> original_name` |

---

## Couche `intermediate` : `int_people_enriched`

**Grain** : identique à staging · **Matérialisation** : view

Ajoute les features dérivées :

| Colonne | Calcul |
|---------|--------|
| `popularity_tier` | `low` (< 3) / `medium` (3-10) / `high` (≥ 10) |
| `popularity_rank_overall` | rang global décroissant |
| `popularity_rank_in_department` | rang dans le département |
| `popularity_rank_in_gender` | rang dans le genre |
| `popularity_percentile` | `percent_rank()` |
| `popularity_zscore_in_department` | (x − μ_dept) / σ_dept |
| `is_top_1_pct` | True si rang ≤ 1 % du total |
| `department_size` | count par département |
| `gender_size` | count par genre |

Les seuils `high_popularity_threshold` et `medium_popularity_threshold` sont définis dans `dbt_project.yml` :

```yaml
vars:
  high_popularity_threshold: 10.0
  medium_popularity_threshold: 3.0
```

→ pour les changer, **inutile de modifier le SQL**, on change juste la config.

---

## Couche `marts`

### `fct_people` (9 980 lignes)

Table de faits principale, sélection de toutes les colonnes intermediate pertinentes pour les dashboards.

### `dim_department_stats` (14 lignes)

| Colonne | Description |
|---------|-------------|
| `department`, `n_people` | Identité + taille |
| `n_female`, `n_male`, `n_non_binary`, `n_not_specified` | Décompte genre |
| `avg_popularity`, `median_popularity`, `max_popularity`, `min_popularity`, `stddev_popularity`, `sum_popularity` | Stats popularité |
| `n_high_tier`, `n_medium_tier`, `n_low_tier` | Répartition tiers |
| `pct_female` | KPI diversité |
| `top_person_name`, `top_person_popularity` | Star du département |

### `dim_gender_stats` (4 lignes)

Mêmes principes mais agrégé par genre.

### `mart_top_100` (100 lignes)

Top 100 par popularité décroissante : `rank`, `person_name`, `department`, `popularity_score`, etc.

### `mart_department_gender_matrix` (38 lignes)

Format long pour heatmap : (`department`, `gender`, `n_people`, `avg_popularity`, `pct_of_department`, …).

### `mart_global_kpis` (1 ligne)

Scorecards : `total_people`, `n_departments`, `avg_popularity_score`, `pct_female`, `top_person_name`, etc.

---

## Tests appliqués (43 total)

| Modèle | # tests |
|--------|---------|
| `raw.popular_people` (sources) | 5 |
| `stg_popular_people` | 12 |
| `int_people_enriched` | 7 |
| `fct_people` | 4 |
| `dim_department_stats` | 3 |
| `dim_gender_stats` | 2 |
| `mart_top_100` | 3 |
| `mart_department_gender_matrix` | 2 |
| `mart_global_kpis` | 1 |
| Tests singuliers custom | 2 |
| **Total** | **43** |

Pour voir le détail : `dbt test --select <model_name>`.