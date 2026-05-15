"""
ingest.py
---------
Charge le CSV brut dans DuckDB sous le schéma `raw`.

C'est l'étape "E + L" du ELT moderne : on ingère les données telles quelles,
sans transformation, dans le warehouse. dbt s'occupera ensuite du "T".

Pourquoi un script Python séparé ?
- Sépare clairement l'ingestion (responsabilité Data Engineer) de la transformation
  (responsabilité dbt / Analytics Engineer)
- Permet de gérer des sources hétérogènes (CSV, API, S3, FTP) sans toucher à dbt
- Facile à orchestrer avec Airflow/Prefect ensuite

Usage :
    python scripts/ingest.py
"""

from pathlib import Path
import duckdb
import sys

ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT / "data" / "raw" / "popular_people.csv"
WAREHOUSE = ROOT / "warehouse" / "tmdb.duckdb"
WAREHOUSE.parent.mkdir(parents=True, exist_ok=True)


def ingest():
    if not RAW_CSV.exists():
        print(f"✗ CSV introuvable : {RAW_CSV}")
        sys.exit(1)

    print(f"▶ Connexion à DuckDB : {WAREHOUSE}")
    conn = duckdb.connect(str(WAREHOUSE))

    # Création d'un schéma `raw` pour bien séparer les données brutes des transformées
    conn.execute("CREATE SCHEMA IF NOT EXISTS raw;")

    # Drop + create depuis le CSV. DuckDB lit le CSV directement avec inférence de type.
    print(f"▶ Chargement de {RAW_CSV.name} dans raw.popular_people…")
    conn.execute("DROP TABLE IF EXISTS raw.popular_people;")
    conn.execute(f"""
        CREATE TABLE raw.popular_people AS
        SELECT * FROM read_csv_auto('{RAW_CSV.as_posix()}', header=true);
    """)

    # Stats de chargement
    n = conn.execute("SELECT COUNT(*) FROM raw.popular_people;").fetchone()[0]
    cols = conn.execute("DESCRIBE raw.popular_people;").fetchdf()
    print(f"   ✓ {n:,} lignes chargées")
    print(f"   Colonnes :")
    for _, row in cols.iterrows():
        print(f"     • {row['column_name']:25s} {row['column_type']}")

    # Audit : compter les lignes par genre pour vérifier la qualité
    print("\n▶ Audit qualité :")
    audit = conn.execute("""
        SELECT
            gender,
            COUNT(*) AS n_rows,
            COUNT(DISTINCT name) AS n_unique_names,
            ROUND(AVG(popularity), 2) AS avg_popularity
        FROM raw.popular_people
        GROUP BY gender
        ORDER BY gender;
    """).fetchdf()
    print(audit.to_string(index=False))

    conn.close()
    print("\n✨ Ingestion terminée — prochaine étape : `dbt run`")


if __name__ == "__main__":
    ingest()
