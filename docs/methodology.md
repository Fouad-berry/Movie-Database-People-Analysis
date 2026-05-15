# 🔬 Méthodologie

## 1. Choix de la stack

**Pourquoi dbt + DuckDB plutôt qu'autre chose ?**

| Critère | dbt + DuckDB | dbt + BigQuery/Snowflake | Pandas pur |
|---------|--------------|--------------------------|------------|
| Coût | **Gratuit** | ~$X/mois | Gratuit |
| Reproductibilité | **Excellente** (tout en local) | Bonne | Moyenne (pas de schéma) |
| Vitesse | < 5s pour ce dataset | < 5s | 30s+ (load CSV) |
| Compétence recherchée | **Top demande 2024-2025** | Top demande | Basique |
| Tests automatiques | **Oui** | Oui | Non (manuels) |

DuckDB est devenu la norme pour les projets locaux : OLAP, parquet natif, SQL ANSI, ~1ms par requête.

## 2. Modèle d'architecture (medallion light)

```
Bronze  →  Silver       →  Gold        ←  équivalent Databricks
RAW     →  STAGING + INT →  MARTS       ←  notre convention dbt
```

- **RAW** : copie 1:1 du CSV, aucune transformation. Permet de toujours revenir à la source.
- **STAGING** : nettoyage atomique, typage strict. **Une seule personne en charge** (data engineer).
- **INTERMEDIATE** : enrichissement, features dérivées. Pas consommé directement par la BI.
- **MARTS** : tables business prêtes à brancher. Consommées par data analysts, dashboards, ML.

**Règle d'or** : un consommateur (analyste, dashboard) lit UNIQUEMENT les marts. Jamais staging ou raw.

## 3. Conventions de nommage

Suivies dans tout le projet :

| Préfixe | Usage |
|---------|-------|
| `stg_` | Modèle staging |
| `int_` | Modèle intermediate |
| `fct_` | Table de faits (1 ligne = 1 événement/entité) |
| `dim_` | Table de dimension (1 ligne = 1 entité descriptive) |
| `mart_` | Table dérivée, agrégée, pour cas d'usage spécifique |

## 4. Qualité des données

**4 niveaux de tests** :

1. **Sources** : tests sur les données brutes avant transformation
   - `not_null` sur les colonnes critiques
   - `accepted_values` pour les enum
   - `freshness` pour détecter les retards d'ingestion

2. **Modèles** : tests à chaque étape de transformation
   - `unique` sur les clés
   - `accepted_values` sur les nouvelles catégorisations

3. **Tests métier custom** : règles business spécifiques
   - "Le rang d'une personne dans son département ne peut pas dépasser la taille du département"

4. **Test invariant** : règle constante du dataset
   - "Le total doit être 9 980 personnes"

→ Si **un seul test échoue**, le pipeline doit s'arrêter (en CI/CD).

## 5. Variables et paramètres

Toute valeur "business" qui pourrait changer est en `vars` dans `dbt_project.yml` :

```yaml
vars:
  high_popularity_threshold: 10.0
  medium_popularity_threshold: 3.0
```

Avantages :
- Une seule source de vérité (DRY)
- Audit-friendly (un commit Git change le seuil)
- Permet du staging dev vs prod facilement

## 6. Idempotence

Chaque exécution doit produire le même résultat. Pas de `INSERT INTO` dans dbt, uniquement des `CREATE TABLE AS SELECT` ou `CREATE VIEW`.

→ `make all` peut être lancé 100 fois, le résultat sera identique. Critère essentiel en data engineering.

## 7. Limitations actuelles

- **Pas de SCD** (Slowly Changing Dimensions) : le dataset est statique, on ne suit pas l'évolution dans le temps
- **Pas d'incremental** : on recompute tout à chaque run (acceptable pour 9 980 lignes, problématique pour 1M+)
- **Pas de CI/CD** : actuellement on lance manuellement `make all`
- **DuckDB local** : pas adapté à un usage multi-utilisateurs concurrent

## 8. Pistes d'évolution

### À court terme (1-2 jours)
- Ajouter des snapshots dbt pour tracker l'évolution
- Mettre en place GitHub Actions pour CI/CD
- Ajouter `dbt-elementary` pour des alertes de qualité

### À moyen terme (1 semaine)
- Migrer le target vers BigQuery (déjà préparé dans `profiles.yml`)
- Brancher Looker Studio sur BigQuery directement
- Mettre en place une orchestration Airflow / Prefect

### À long terme (1+ mois)
- Architecture Kafka → DuckDB pour streaming
- ML feature store basé sur les marts
- Self-service analytics via Lightdash ou Metabase

## 9. Ressources

- [dbt documentation officielle](https://docs.getdbt.com/)
- [DuckDB documentation](https://duckdb.org/docs/)
- [dbt Labs YouTube channel](https://www.youtube.com/@dbtLabs) — excellents tutos
- [Data engineering zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp) — cours gratuit complet