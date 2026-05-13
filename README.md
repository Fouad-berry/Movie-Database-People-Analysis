# 🎬 TMDb People — dbt + DuckDB Data Warehouse

> Projet **Analytics Engineering** complet : transformation de **9 980 personnalités du cinéma** (TMDb) en un data warehouse propre avec **dbt + DuckDB**, architecture en 3 couches (staging → intermediate → marts), **43 tests** automatisés, et exports prêts pour Looker Studio.

![dbt](https://img.shields.io/badge/dbt-1.11-FF694B.svg)
![DuckDB](https://img.shields.io/badge/DuckDB-1.10-FFF000.svg)
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Tests](https://img.shields.io/badge/Tests-43_passing-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## 🎯 Objectif du projet

Démontrer une compétence **analytics engineering / data engineering** à travers un pipeline ELT moderne :

1. **E + L** (Python) : ingestion d'un CSV brut dans DuckDB sous le schéma `raw`
2. **T** (dbt) : transformation en 3 couches selon les conventions de l'industrie
3. **Tests** : 43 tests automatiques garantissent la qualité des données
4. **Doc auto-générée** par dbt (lineage, descriptions, tests)
5. **Exports** vers CSV pour brancher Looker Studio / autres BI

**Pourquoi cette stack ?**
- **dbt** est l'outil n°1 d'analytics engineering, présent dans 80 % des offres data engineer / analytics engineer 2024-2025
- **DuckDB** est devenu le standard pour les warehouses locaux (OLAP, hyper rapide, SQL ANSI)
- **Architecture medallion** (raw → staging → intermediate → marts) = pattern utilisé chez tous les éditeurs majeurs (Databricks, Snowflake…)

---

## 🏗️ Architecture du pipeline

![Architecture](images/figures/10_dbt_architecture.png)

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  CSV brut          DuckDB Warehouse                                 │
│  ───────           ─────────────────                                │
│                                                                     │
│  popular_         ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  people.csv  ──▶  │  raw     │  │ staging  │  │ inter-   │         │
│                   │          │  │          │  │ mediate  │         │
│  (9 980 lignes)   └──────────┘  └──────────┘  └──────────┘         │
│                        ▲             ▲             │                │
│                        │             │             ▼                │
│       Python script ───┘    dbt run -│    ┌────────────────┐        │
│       (ingest.py)                    │    │     MARTS      │        │
│                                       │    │  (6 tables)    │        │
│                                       │    └────────┬───────┘        │
│                                       │             │                │
│                                  43 dbt tests  ──── ▼ CSV exports    │
│                                                                      │
│                                              Looker Studio           │
└─────────────────────────────────────────────────────────────────────┘
```

### Les 3 couches dbt

| Couche | Matérialisation | Rôle | Modèles |
|--------|-----------------|------|---------|
| **staging** | `view` | Nettoyage, typage, mapping codes → libellés | `stg_popular_people` |
| **intermediate** | `view` | Features dérivées (tiers, ranks, percentiles, z-scores) | `int_people_enriched` |
| **marts** | `table` | Tables finales pour les consommateurs (Looker) | 6 marts |

---

## 📊 Aperçu des résultats

### Top 15 des personnalités les plus populaires

![Top 15](images/figures/01_top15_celebrities.png)

### Répartition par département

![Departments](images/figures/02_people_by_department.png)

> **Acting domine très largement** (9 320 personnes / 9 980, soit 93 %). Les autres départements sont marginaux.

### Diversité (% femmes) par département

![Diversity](images/figures/05_diversity_by_department.png)

> Acting est proche de la parité (48 % de femmes), mais **Directing (3 %)** et **Writing (13 %)** restent très masculins.

### Répartition par tier de popularité

![Tiers](images/figures/08_popularity_tiers.png)

> Le score TMDb suit une **distribution très skewed** : 87 % des personnes sont en "low" (< 3), seulement 0.7 % en "high" (≥ 10).

📁 **10 figures** générées automatiquement dans [`images/figures/`](images/figures/).

---

## 📁 Structure du projet

```
tmdb-people-dbt/
│
├── data/
│   ├── raw/popular_people.csv              # Dataset brut (9 980 lignes)
│   └── exports/                            # Marts exportés en CSV
│       ├── fct_people.csv
│       ├── dim_department_stats.csv
│       ├── dim_gender_stats.csv
│       ├── mart_top_100.csv
│       ├── mart_department_gender_matrix.csv
│       └── mart_global_kpis.csv
│
├── warehouse/                              # DuckDB database (gitignored)
│   └── tmdb.duckdb
│
├── dbt_project/                            # 🎯 Projet dbt
│   ├── dbt_project.yml                     # Config principale
│   ├── profiles.yml                        # Connexion DuckDB
│   ├── packages.yml                        # dbt_utils
│   │
│   ├── models/
│   │   ├── staging/
│   │   │   ├── _sources.yml                # Déclaration des sources
│   │   │   ├── _schema.yml                 # Tests + docs
│   │   │   └── stg_popular_people.sql
│   │   ├── intermediate/
│   │   │   ├── _schema.yml
│   │   │   └── int_people_enriched.sql
│   │   └── marts/
│   │       ├── _schema.yml
│   │       ├── fct_people.sql
│   │       ├── dim_department_stats.sql
│   │       ├── dim_gender_stats.sql
│   │       ├── mart_top_100.sql
│   │       ├── mart_department_gender_matrix.sql
│   │       └── mart_global_kpis.sql
│   │
│   ├── tests/                              # Tests singuliers custom
│   │   ├── assert_rank_within_department_size.sql
│   │   └── assert_ranks_are_contiguous.sql
│   │
│   ├── macros/                             # Macros Jinja réutilisables
│   │   └── categorize_score.sql
│   │
│   └── analyses/                           # Requêtes ad-hoc versionnées
│       └── top3_by_department.sql
│
├── scripts/
│   ├── ingest.py                           # ⭐ Charge CSV → DuckDB raw
│   ├── export_marts.py                     # ⭐ Marts DuckDB → CSV
│   └── generate_figures.py                 # ⭐ Génère les 10 PNG
│
├── notebooks/
│   └── 01_warehouse_exploration.ipynb      # Explorer DuckDB avec pandas
│
├── images/figures/                         # 10 PNG pré-générées
│
├── docs/                                   # Doc additionnelle
│   ├── data_dictionary.md
│   ├── dbt_concepts.md
│   └── methodology.md
│
├── dashboards/looker_studio_guide.md
│
├── Makefile                                # ⭐ Orchestration commandes
├── .gitignore
├── LICENSE
├── requirements.txt
└── README.md
```

---

## 🚀 Installation & utilisation

### Prérequis

- **Python 3.10+**
- **make** (optionnel mais recommandé)

### 1. Cloner et installer

```bash
git clone https://github.com/<ton-username>/tmdb-people-dbt.git
cd tmdb-people-dbt

# Environnement virtuel
python -m venv venv
source venv/bin/activate          # Linux/Mac
# venv\Scripts\activate           # Windows

# Dépendances
make install
# ou : pip install -r requirements.txt
```

### 2. Pipeline complet en une commande

```bash
make all
```

Ce qui équivaut à :
```bash
make ingest      # Python : CSV → DuckDB raw
make deps        # dbt deps (installe dbt_utils)
make run         # dbt run : construit staging → int → marts
make test        # dbt test : 43+ tests
make export      # Marts → CSV
make figures     # Génère les 10 figures
```

### 3. Explorer la doc dbt (lineage interactif)

```bash
make docs
```

Ouvre [http://localhost:8080](http://localhost:8080) pour naviguer dans :
- Le **graphe de dépendances** (DAG) des modèles
- La **documentation** auto-générée à partir des descriptions
- La **liste des tests** par modèle

### 4. Explorer le warehouse DuckDB

```python
import duckdb
conn = duckdb.connect('warehouse/tmdb.duckdb', read_only=True)

# Liste des tables marts
print(conn.execute("SHOW TABLES").fetchdf())

# KPIs globaux
print(conn.execute("SELECT * FROM main_marts.mart_global_kpis").fetchdf())

# Top 10
print(conn.execute("""
    SELECT rank, person_name, department, popularity_score
    FROM main_marts.mart_top_100 LIMIT 10
""").fetchdf())
```

---

## 🧱 Les 6 marts

| Mart | Grain | Cas d'usage Looker |
|------|-------|---------------------|
| `fct_people` | 1 ligne / personne | Source unique pour dashboards détaillés |
| `dim_department_stats` | 1 ligne / département | Bar charts par métier |
| `dim_gender_stats` | 1 ligne / genre | Analyses diversité |
| `mart_top_100` | top 100 personnes | Table classement |
| `mart_department_gender_matrix` | département × genre | Heatmap |
| `mart_global_kpis` | 1 ligne | Scorecards |

📄 Spec détaillée : [`docs/data_dictionary.md`](docs/data_dictionary.md).

---

## ✅ Qualité des données : 43 tests automatiques

Le pipeline tourne **43 tests** dbt à chaque run :

| Catégorie | Exemples | Nb |
|-----------|----------|-----|
| **Unicité** | `person_sk`, `rank`, `department` | 8 |
| **Non-null** | toutes les colonnes critiques | 21 |
| **Valeurs acceptées** | `gender ∈ {female, male, ...}`, `popularity_tier ∈ {low, medium, high}` | 6 |
| **Source freshness** | warning > 7 jours, error > 30 jours | 1 |
| **Tests singuliers custom** | `rank_within_department_size`, `ranks_are_contiguous` | 2 |
| **Sources** | tests appliqués à `raw.popular_people` | 5 |

Lancement : `make test` ou `dbt test`.

---

## 🛠️ Stack technique

- **Python 3.10+** · DuckDB · Pandas · Matplotlib · Seaborn
- **dbt-core 1.11** + **dbt-duckdb 1.10**
- **Jinja2** (templating dbt)
- **dbt_utils** (package communautaire)
- **Make** pour orchestration

---

## 🎓 Compétences démontrées

Ce projet montre la maîtrise de :

- ✅ **Architecture medallion** (raw → staging → intermediate → marts)
- ✅ **dbt** : modèles SQL, matérialisations, tests, macros, sources, ref(), var()
- ✅ **SQL avancé** : window functions, CTE, percent_rank, z-score
- ✅ **Data quality** : tests unique/not_null/accepted_values + tests singuliers custom
- ✅ **Documentation as code** : descriptions YAML, doc auto-générée
- ✅ **Versionning** : config centralisée (dbt_project.yml), seuils paramétrables (vars)
- ✅ **Orchestration** : Makefile + script Python d'ingestion
- ✅ **Pipeline reproductible** : `make all` reconstruit tout en < 5 secondes

---

## 📈 Dashboard Looker Studio

Le dashboard final consomme les 6 marts CSV exportés dans `data/exports/`.

**Structure recommandée — 4 pages :**

1. **Overview** — KPIs globaux + top 10 + répartition
2. **Departments** — Comparaison entre métiers
3. **Diversity** — Genre × département, parité par métier
4. **Browser** — Recherche libre dans les 9 980 personnes

📄 Guide complet : [`dashboards/looker_studio_guide.md`](dashboards/looker_studio_guide.md).

---

## 💡 Insights clés (data-driven)

- **Acting domine** : 93 % des entrées (9 320 / 9 980)
- **Eric Larson** (Visual Effects) est en tête avec un score de 47.98 (étonnant ! C'est probablement un effet de la popularité Disney)
- **Distribution très skewed** : 87 % des personnes sont en tier "low"
- **Diversité variable** : Acting proche parité (48 % femmes), Directing très masculin (3 %)
- **40 % des noms** ont une version traduite vs leur nom original

---

## 🚀 Pistes d'amélioration

- [ ] **Snapshots** dbt : tracker l'évolution de la popularité dans le temps (SCD type 2)
- [ ] **Seeds** : ajouter une table de mapping département → secteur (au-delà / en-deçà de la caméra)
- [ ] **CI/CD** : GitHub Actions qui lance `make all` à chaque push
- [ ] **dbt-elementary** ou **dbt-expectations** pour des tests de qualité avancés
- [ ] **Upgrade vers BigQuery** : migration du target DuckDB → BigQuery (déjà préparé dans `profiles.yml`)
- [ ] **Orchestration Airflow/Prefect** : remplacer le Makefile par un vrai DAG

---

## 📝 Licence

MIT — voir [`LICENSE`](LICENSE).

---

## 👤 Auteur

**[Fouad MOUTAIROU]**
- Portfolio : https://portfolio-fouad.netlify.app/
- LinkedIn : https://www.linkedin.com/in/fouad-moutairou-044460273/

---

## 🙏 Crédits

- Données : [**The Movie Database (TMDb)**](https://www.themoviedb.org/)
- Stack : [**dbt**](https://www.getdbt.com/) + [**DuckDB**](https://duckdb.org/)