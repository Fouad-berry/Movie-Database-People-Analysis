# 🎓 Concepts dbt utilisés dans ce projet

Ce document explique les concepts dbt employés, pour servir de référence et démontrer la compréhension lors d'entretiens.

## 1. Architecture en 3 couches (medallion)

| Couche | Convention de nommage | Matérialisation | Rôle |
|--------|----------------------|-----------------|------|
| **staging** (`stg_*`) | 1 modèle = 1 source | view | Nettoyage atomique : trim, cast, mapping codes |
| **intermediate** (`int_*`) | Réutilisable, jamais consommé direct | view | Jointures, features dérivées, logique commune |
| **marts** (`fct_*` / `dim_*` / `mart_*`) | Consommé par BI/dashboards | table | Tables finales, optimisées pour requêtes |

C'est la convention dbt Labs officielle, suivie par 90 % des équipes data.

## 2. Sources

Déclarées dans `models/staging/_sources.yml` :

```yaml
sources:
  - name: raw
    schema: raw
    tables:
      - name: popular_people
        freshness: { warn_after: { count: 7, period: day } }
```

Pourquoi ? On ne référence jamais directement `raw.popular_people` dans le SQL. À la place :

```sql
select * from {{ source('raw', 'popular_people') }}
```

→ dbt sait que ce modèle dépend d'une source externe et peut tester sa fraîcheur.

## 3. ref()

À l'intérieur de dbt, on n'écrit JAMAIS le nom de table en dur :

```sql
-- ❌ MAUVAIS
select * from main_staging.stg_popular_people

-- ✅ BON
select * from {{ ref('stg_popular_people') }}
```

Bénéfices :
- **Lineage automatique** : dbt sait quel modèle dépend de quel autre
- **Portabilité** : marche peu importe le schéma cible (dev/prod)
- **Ordre d'exécution** : dbt résout automatiquement le DAG

## 4. Tests dbt

Deux types de tests :

### Tests génériques (déclaratifs en YAML)

```yaml
columns:
  - name: person_sk
    data_tests: [unique, not_null]
  - name: gender
    data_tests:
      - accepted_values:
          values: ['female', 'male', 'non_binary', 'not_specified']
```

### Tests singuliers (SQL custom dans `tests/`)

```sql
-- Si cette query retourne ≥ 1 ligne, le test ÉCHOUE
select *
from {{ ref('int_people_enriched') }}
where popularity_rank_in_department > department_size
```

## 5. Variables (vars)

Définies dans `dbt_project.yml` :

```yaml
vars:
  high_popularity_threshold: 10.0
  medium_popularity_threshold: 3.0
```

Utilisées dans les modèles via `{{ var('high_popularity_threshold') }}`.

→ Permet de **changer la business logic sans toucher au SQL** (utile en revue de code, A/B testing, etc.).

## 6. Macros (Jinja réutilisable)

Macros = fonctions SQL :

```sql
{% macro categorize_score(column, high, medium) %}
    case
        when {{ column }} >= {{ high }} then 'high'
        when {{ column }} >= {{ medium }} then 'medium'
        else 'low'
    end
{% endmacro %}
```

Appel : `{{ categorize_score('popularity_score', 10.0, 3.0) }}`.

## 7. Materializations

| Type | Quand l'utiliser | Coût |
|------|------------------|------|
| `view` | Modèle léger, rarement requêté | Aucun (juste un alias SQL) |
| `table` | Modèle souvent requêté en BI | Stockage + recalcul à chaque run |
| `incremental` | Données volumineuses, append-only | Optimal sur gros volumes |
| `ephemeral` | Modèle utilisé une seule fois | Inliné comme CTE |

Dans ce projet : staging/intermediate = `view`, marts = `table` (pour performance Looker).

## 8. Schemas (séparation logique)

Dans `dbt_project.yml` :

```yaml
models:
  tmdb_people:
    staging: { +schema: staging }
    intermediate: { +schema: intermediate }
    marts: { +schema: marts }
```

→ Crée automatiquement `main_staging`, `main_intermediate`, `main_marts` dans DuckDB. Indispensable pour organiser un warehouse réel.

## 9. dbt docs

```bash
dbt docs generate
dbt docs serve
```

→ Génère un site web interactif avec :
- **Graphe de dépendances** (DAG cliquable)
- **Schéma de chaque table** avec descriptions
- **Liste des tests** par modèle
- **Code source** SQL/YAML

C'est LA différence entre "j'ai écrit du SQL" et "j'ai produit un projet data professionnel".

## 10. Commandes utiles

```bash
# Exécuter un seul modèle
dbt run --select stg_popular_people

# Exécuter un modèle + tous ses descendants
dbt run --select stg_popular_people+

# Exécuter un modèle + tous ses ancêtres
dbt run --select +mart_global_kpis

# Tester un seul modèle
dbt test --select fct_people

# Tester seulement les sources
dbt test --select source:raw

# Compiler sans exécuter (vérifier la syntaxe)
dbt compile

# Voir le SQL généré
cat target/compiled/tmdb_people/models/staging/stg_popular_people.sql

# Voir le DAG en ASCII
dbt list --output graph
```