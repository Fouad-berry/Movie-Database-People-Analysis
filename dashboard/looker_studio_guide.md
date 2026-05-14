# 📊 Guide Looker Studio

## 🔗 Lien du dashboard

> **[👉 Ouvrir le dashboard](https://lookerstudio.google.com/)** *(à remplacer par ton lien)*

---

## 🚀 Connexion des données

### Option A — Upload CSV (rapide)

Après avoir lancé `make all`, les 6 marts sont dans `data/exports/`. Upload-les un par un :

1. [lookerstudio.google.com](https://lookerstudio.google.com/) → **Créer** → **Source de données** → **File Upload**
2. Uploader :
   - `fct_people.csv` (9 980 lignes, source principale)
   - `mart_top_100.csv`
   - `dim_department_stats.csv`
   - `dim_gender_stats.csv`
   - `mart_department_gender_matrix.csv`
   - `mart_global_kpis.csv`

### Option B — MotherDuck / BigQuery (production)

Le warehouse DuckDB local peut être migré vers :
- **MotherDuck** (DuckDB managé, branchement direct Looker)
- **BigQuery** (changer le `target` dans `profiles.yml`)

---

## 🎨 Structure recommandée — 4 pages

### 📄 Page 1 — Overview

Source : `mart_global_kpis.csv` + `fct_people.csv`

- **6 scorecards** : total_people, n_departments, pct_female, max_popularity_score, top_person_name, n_high_tier
- **Bar chart horizontal** : top 15 par popularité
- **Pie chart** : répartition par tier (high/medium/low)
- **Pie chart** : répartition par genre

### 📄 Page 2 — Departments

Source : `dim_department_stats.csv`

- **Bar chart horizontal** : nombre de personnes par département (échelle log car Acting domine)
- **Bar chart** : popularité moyenne par département
- **Table** : tous les KPIs par département
- **Filtre** : taille minimale du département

### 📄 Page 3 — Diversity

Source : `dim_gender_stats.csv` + `mart_department_gender_matrix.csv`

- **Pie chart** : genre global
- **Heatmap** : département × genre (avec `pct_of_department`)
- **Bar chart** : % de femmes par département (avec ligne de parité à 50%)
- **Table** : top star par genre

### 📄 Page 4 — Browser (recherche libre)

Source : `fct_people.csv`

- **Table interactive** : 9 980 personnes triables par toutes les colonnes
- **Filtres** : département, genre, popularity_tier, plage de score
- **Recherche par nom**
- **Bar chart latéral** : popularité de la personne sélectionnée par rapport à son département

---

## 🎛️ Filtres globaux (haut de page)

- **Department** (multi-select)
- **Gender** (boutons : female / male / non-binary / not specified)
- **Popularity Tier** (boutons)
- **Min popularity** (slider 0–48)

---

## 🎨 Palette de couleurs

**Genres** (cohérent avec les figures Python) :
- Female : `#E91E63`
- Male : `#2196F3`
- Non-binary : `#9C27B0`
- Not specified : `#9E9E9E`

**Popularity tiers** :
- High : `#27ae60` (vert)
- Medium : `#f39c12` (orange)
- Low : `#95a5a6` (gris)

---

## 💡 Champs calculés utiles

À ajouter dans Looker pour enrichir :

```sql
-- Catégorie de carrière
career_seniority = CASE
    WHEN popularity_score >= 20 THEN "A-list"
    WHEN popularity_score >= 10 THEN "Star"
    WHEN popularity_score >= 3  THEN "Established"
    ELSE "Rising"
END

-- Flag diversité
is_underrepresented = IF(gender IN ("female", "non_binary"), 1, 0)
```

---

## 📸 Captures d'écran

```markdown
![Page 1 — Overview](../images/dashboard_01_overview.png)
![Page 2 — Departments](../images/dashboard_02_departments.png)
![Page 3 — Diversity](../images/dashboard_03_diversity.png)
![Page 4 — Browser](../images/dashboard_04_browser.png)
```