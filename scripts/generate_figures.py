"""
generate_figures.py
-------------------
Génère les figures PNG en lisant directement les marts dans DuckDB.

Démontre qu'on n'a pas besoin de recalculer : les marts sont la source de vérité.
"""

from pathlib import Path
import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = Path(__file__).resolve().parent.parent
WAREHOUSE = ROOT / "warehouse" / "tmdb.duckdb"
FIGURES = ROOT / "images" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 140, "savefig.bbox": "tight",
    "axes.titlesize": 14, "axes.titleweight": "bold", "axes.labelsize": 11,
})

GENDER_COLORS = {
    "female": "#E91E63", "male": "#2196F3",
    "non_binary": "#9C27B0", "not_specified": "#9E9E9E",
}

conn = duckdb.connect(str(WAREHOUSE), read_only=True)

# ============================================================
# Fig 1 : Top 15 par popularité
# ============================================================
df = conn.execute("""
    SELECT rank, person_name, department, popularity_score
    FROM main_marts.mart_top_100
    ORDER BY rank LIMIT 15
""").fetchdf().sort_values("popularity_score")

fig, ax = plt.subplots(figsize=(11, 7))
bars = ax.barh(df["person_name"] + " (" + df["department"] + ")", df["popularity_score"],
               color=sns.color_palette("rocket_r", len(df)), edgecolor="black")
for bar, val in zip(bars, df["popularity_score"]):
    ax.text(val + 0.3, bar.get_y() + bar.get_height()/2,
            f"{val:.1f}", va="center", fontweight="bold")
ax.set_title("Top 15 personnalités les plus populaires (TMDb)")
ax.set_xlabel("Score de popularité")
plt.savefig(FIGURES / "01_top15_celebrities.png")
plt.close()

# ============================================================
# Fig 2 : Nombre de personnes par département
# ============================================================
df = conn.execute("""
    SELECT department, n_people FROM main_marts.dim_department_stats
    ORDER BY n_people DESC
""").fetchdf()

# On sépare Acting (trop dominant) et le reste pour 2 sous-graphiques
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))

# Acting seul (avec échelle log)
ax1.barh(["Acting"], [df.iloc[0]["n_people"]], color="#3498db", edgecolor="black")
ax1.text(df.iloc[0]["n_people"], 0, f"  {df.iloc[0]['n_people']:,}",
         va="center", fontweight="bold", fontsize=14)
ax1.set_title("Acting domine très largement")
ax1.set_xlabel("Nombre de personnes")
ax1.set_xlim(0, df.iloc[0]["n_people"] * 1.15)

# Tous les autres
others = df.iloc[1:].sort_values("n_people")
bars = ax2.barh(others["department"], others["n_people"],
                color=sns.color_palette("viridis", len(others)), edgecolor="black")
for bar, val in zip(bars, others["n_people"]):
    ax2.text(val + 5, bar.get_y() + bar.get_height()/2,
             f"{int(val)}", va="center", fontweight="bold", fontsize=9)
ax2.set_title("Autres départements")
ax2.set_xlabel("Nombre de personnes")

plt.suptitle("Répartition des 9 980 personnalités par département", fontweight="bold", fontsize=15)
plt.savefig(FIGURES / "02_people_by_department.png")
plt.close()

# ============================================================
# Fig 3 : Répartition par genre
# ============================================================
df = conn.execute("""
    SELECT gender, n_people, pct_of_total, top_person_name
    FROM main_marts.dim_gender_stats
""").fetchdf()

fig, ax = plt.subplots(figsize=(9, 7))
colors = [GENDER_COLORS.get(g, "#888") for g in df["gender"]]
wedges, _, autotexts = ax.pie(
    df["n_people"], labels=df["gender"], autopct="%1.1f%%",
    colors=colors, startangle=90,
    wedgeprops=dict(width=0.4, edgecolor="white", linewidth=2),
    textprops={"fontweight": "bold", "fontsize": 11}
)
ax.set_title("Répartition des personnalités par genre")
plt.savefig(FIGURES / "03_gender_distribution.png")
plt.close()

# ============================================================
# Fig 4 : Popularité moyenne par département
# ============================================================
df = conn.execute("""
    SELECT department, avg_popularity, median_popularity, n_people
    FROM main_marts.dim_department_stats
    ORDER BY avg_popularity ASC
""").fetchdf()

fig, ax = plt.subplots(figsize=(11, 6))
bars = ax.barh(df["department"], df["avg_popularity"],
               color=sns.color_palette("flare", len(df)), edgecolor="black")
for bar, avg, med, n in zip(bars, df["avg_popularity"], df["median_popularity"], df["n_people"]):
    ax.text(avg + 0.03, bar.get_y() + bar.get_height()/2,
            f"moy={avg:.2f} | méd={med:.2f} (n={int(n)})",
            va="center", fontweight="bold", fontsize=9)
ax.set_title("Popularité moyenne par département")
ax.set_xlabel("Score de popularité moyen")
plt.savefig(FIGURES / "04_avg_popularity_by_department.png")
plt.close()

# ============================================================
# Fig 5 : Diversité (% femmes) par département
# ============================================================
df = conn.execute("""
    SELECT department, pct_female, n_people
    FROM main_marts.dim_department_stats
    WHERE n_people >= 5  -- exclure les très petits départements
    ORDER BY pct_female ASC
""").fetchdf()

fig, ax = plt.subplots(figsize=(11, 6))
colors_p = ["#c0392b" if p < 20 else "#f39c12" if p < 35 else "#27ae60" for p in df["pct_female"]]
bars = ax.barh(df["department"], df["pct_female"], color=colors_p, edgecolor="black")
ax.axvline(50, color="black", linestyle="--", linewidth=1, label="Parité (50%)")
for bar, val, n in zip(bars, df["pct_female"], df["n_people"]):
    ax.text(val + 0.5, bar.get_y() + bar.get_height()/2,
            f"{val:.1f}% (n={int(n)})", va="center", fontweight="bold", fontsize=9)
ax.set_title("Part des femmes par département\n(rouge < 20%, orange < 35%, vert ≥ 35%)")
ax.set_xlabel("% de femmes")
ax.legend()
plt.savefig(FIGURES / "05_diversity_by_department.png")
plt.close()

# ============================================================
# Fig 6 : Distribution de la popularité (histogramme + log scale)
# ============================================================
df = conn.execute("SELECT popularity_score FROM main_marts.fct_people").fetchdf()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

axes[0].hist(df["popularity_score"], bins=50, color="#3498db", edgecolor="black")
axes[0].set_title("Distribution brute (très skewed)")
axes[0].set_xlabel("Score de popularité")
axes[0].set_ylabel("Nombre de personnes")
axes[0].axvline(df["popularity_score"].mean(), color="red", linestyle="--",
                label=f"Moyenne = {df['popularity_score'].mean():.2f}")
axes[0].legend()

axes[1].hist(df["popularity_score"], bins=50, color="#2ecc71", edgecolor="black")
axes[1].set_yscale("log")
axes[1].set_title("Échelle log-Y (révèle la longue traîne)")
axes[1].set_xlabel("Score de popularité")
axes[1].set_ylabel("Nombre (log)")

plt.suptitle("Distribution du score de popularité TMDb", fontweight="bold", fontsize=15)
plt.savefig(FIGURES / "06_popularity_distribution.png")
plt.close()

# ============================================================
# Fig 7 : Heatmap département × genre
# ============================================================
df = conn.execute("""
    SELECT department, gender, n_people
    FROM main_marts.mart_department_gender_matrix
""").fetchdf()
pivot = df.pivot(index="department", columns="gender", values="n_people").fillna(0).astype(int)
# Trier par taille de département
pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]

fig, ax = plt.subplots(figsize=(11, 7))
sns.heatmap(pivot, annot=True, fmt="d", cmap="YlOrRd",
            cbar_kws={"label": "Nombre de personnes"}, ax=ax, linewidths=0.4)
ax.set_title("Matrice département × genre (effectifs)")
ax.set_xlabel("Genre"); ax.set_ylabel("")
plt.savefig(FIGURES / "07_dept_gender_heatmap.png")
plt.close()

# ============================================================
# Fig 8 : Répartition par popularity tier
# ============================================================
df = conn.execute("""
    SELECT popularity_tier, COUNT(*) AS n,
           ROUND(AVG(popularity_score), 2) AS avg_pop,
           ROUND(MIN(popularity_score), 2) AS min_pop,
           ROUND(MAX(popularity_score), 2) AS max_pop
    FROM main_marts.fct_people
    GROUP BY popularity_tier
    ORDER BY CASE popularity_tier WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END
""").fetchdf()

fig, ax = plt.subplots(figsize=(10, 6))
colors_t = ["#27ae60", "#f39c12", "#95a5a6"]
bars = ax.bar(df["popularity_tier"], df["n"], color=colors_t, edgecolor="black", linewidth=1.5)
for bar, val, mn, mx in zip(bars, df["n"], df["min_pop"], df["max_pop"]):
    pct = 100 * val / df["n"].sum()
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 100,
            f"{int(val):,}\n({pct:.1f}%)\n[{mn:.1f} → {mx:.1f}]",
            ha="center", fontweight="bold", fontsize=10)
ax.set_title("Répartition par tier de popularité\n(seuils définis dans dbt_project.yml)")
ax.set_ylabel("Nombre de personnes")
plt.savefig(FIGURES / "08_popularity_tiers.png")
plt.close()

# ============================================================
# Fig 9 : Top 10 femmes vs top 10 hommes
# ============================================================
fig, axes = plt.subplots(1, 2, figsize=(15, 7))

for ax, gender, color, title in zip(
    axes, ["female", "male"], ["#E91E63", "#2196F3"],
    ["Top 10 femmes", "Top 10 hommes"]
):
    df = conn.execute(f"""
        SELECT person_name, department, popularity_score
        FROM main_marts.fct_people
        WHERE gender = '{gender}'
        ORDER BY popularity_score DESC LIMIT 10
    """).fetchdf().sort_values("popularity_score")
    bars = ax.barh(df["person_name"] + " (" + df["department"] + ")",
                   df["popularity_score"], color=color, edgecolor="black", alpha=0.85)
    for bar, val in zip(bars, df["popularity_score"]):
        ax.text(val + 0.3, bar.get_y() + bar.get_height()/2,
                f"{val:.1f}", va="center", fontweight="bold", fontsize=9)
    ax.set_title(title)
    ax.set_xlabel("Popularité")

plt.suptitle("Top 10 par genre", fontweight="bold", fontsize=15)
plt.savefig(FIGURES / "09_top10_by_gender.png")
plt.close()

# ============================================================
# Fig 10 : Architecture dbt (schéma)
# ============================================================
fig, ax = plt.subplots(figsize=(13, 7))
ax.axis("off")

boxes = [
    # (x, y, w, h, color, label)
    (0.05, 0.4, 0.13, 0.20, "#FFCC80", "RAW\npopular_people.csv\n9 980 lignes"),
    (0.25, 0.4, 0.13, 0.20, "#90CAF9", "STAGING\nstg_popular_people\n(view)"),
    (0.45, 0.4, 0.13, 0.20, "#A5D6A7", "INTERMEDIATE\nint_people_enriched\n(view)"),
    (0.65, 0.65, 0.13, 0.10, "#F48FB1", "fct_people"),
    (0.65, 0.51, 0.13, 0.10, "#F48FB1", "dim_department_stats"),
    (0.65, 0.37, 0.13, 0.10, "#F48FB1", "dim_gender_stats"),
    (0.65, 0.23, 0.13, 0.10, "#F48FB1", "mart_top_100"),
    (0.85, 0.51, 0.13, 0.10, "#F48FB1", "mart_dept_gender"),
    (0.85, 0.37, 0.13, 0.10, "#F48FB1", "mart_global_kpis"),
]

for x, y, w, h, color, label in boxes:
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor=color,
                                edgecolor="black", linewidth=1.5))
    ax.text(x + w/2, y + h/2, label, ha="center", va="center",
            fontsize=9, fontweight="bold")

# Flèches
def arrow(x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", lw=2, color="#37474F"))

arrow(0.18, 0.50, 0.25, 0.50)   # raw → staging
arrow(0.38, 0.50, 0.45, 0.50)   # staging → intermediate
arrow(0.58, 0.55, 0.65, 0.70)   # intermediate → fct
arrow(0.58, 0.52, 0.65, 0.56)   # → dim_dept
arrow(0.58, 0.48, 0.65, 0.42)   # → dim_gender
arrow(0.58, 0.45, 0.65, 0.28)   # → mart_top_100
arrow(0.78, 0.45, 0.85, 0.56)   # fct → matrix
arrow(0.78, 0.45, 0.85, 0.42)   # fct → kpis

ax.text(0.5, 0.92, "Architecture dbt — Medallion (raw → staging → intermediate → marts)",
        ha="center", fontsize=15, fontweight="bold")
ax.text(0.5, 0.08, "Python ingest.py → dbt run → dbt test (43 tests) → CSV export → Looker Studio",
        ha="center", fontsize=11, style="italic", color="#555")

ax.set_xlim(0, 1); ax.set_ylim(0, 1)
plt.savefig(FIGURES / "10_dbt_architecture.png")
plt.close()

conn.close()
print(f"✓ 10 figures générées dans {FIGURES}")
