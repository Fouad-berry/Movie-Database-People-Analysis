"""
export_marts.py
---------------
Exporte les tables marts depuis DuckDB vers CSV pour Looker Studio.

Workflow complet :
    1. python scripts/ingest.py       → load CSV into raw.popular_people
    2. dbt run                         → build staging, intermediate, marts
    3. dbt test                        → validate everything
    4. python scripts/export_marts.py  → export to data/exports/ for BI tools
"""

from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parent.parent
WAREHOUSE = ROOT / "warehouse" / "tmdb.duckdb"
EXPORTS = ROOT / "data" / "exports"
EXPORTS.mkdir(parents=True, exist_ok=True)

# Liste des marts à exporter (schema, table, fichier_de_sortie)
TABLES = [
    ("main_marts", "fct_people",                    "fct_people.csv"),
    ("main_marts", "dim_department_stats",          "dim_department_stats.csv"),
    ("main_marts", "dim_gender_stats",              "dim_gender_stats.csv"),
    ("main_marts", "mart_top_100",                  "mart_top_100.csv"),
    ("main_marts", "mart_department_gender_matrix", "mart_department_gender_matrix.csv"),
    ("main_marts", "mart_global_kpis",              "mart_global_kpis.csv"),
]


def export():
    if not WAREHOUSE.exists():
        print(f"✗ Warehouse introuvable : {WAREHOUSE}")
        print("  Lance d'abord : `python scripts/ingest.py` puis `dbt run`")
        return

    conn = duckdb.connect(str(WAREHOUSE))
    for schema, table, filename in TABLES:
        out = EXPORTS / filename
        n = conn.execute(f"SELECT COUNT(*) FROM {schema}.{table}").fetchone()[0]
        conn.execute(f"COPY {schema}.{table} TO '{out.as_posix()}' (HEADER, DELIMITER ',');")
        print(f"   ✓ {filename:40s} ({n:>5} lignes)")

    conn.close()
    print(f"\n✨ {len(TABLES)} marts exportées dans {EXPORTS}/")


if __name__ == "__main__":
    print("▶ Export des marts DuckDB → CSV pour Looker Studio")
    export()
