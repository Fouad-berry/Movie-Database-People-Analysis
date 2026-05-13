# ============================================================
# Makefile — orchestration du pipeline data engineer
# ============================================================
# Usage :
#   make install   → installe les dépendances
#   make ingest    → charge le CSV dans DuckDB (raw.popular_people)
#   make deps      → installe les packages dbt (dbt_utils)
#   make run       → exécute tous les modèles dbt
#   make test      → exécute les 43+ tests dbt
#   make export    → exporte les marts en CSV pour Looker
#   make figures   → génère les 10 figures PNG
#   make docs      → génère la doc dbt + lance le serveur
#   make all       → ingest → run → test → export → figures
#   make clean     → supprime le warehouse et les artefacts dbt
# ============================================================

DBT_DIR := dbt_project
WAREHOUSE := warehouse/tmdb.duckdb

.PHONY: install ingest deps run test export figures docs all clean

install:
	pip install -r requirements.txt

ingest:
	python scripts/ingest.py

deps:
	cd $(DBT_DIR) && DBT_PROFILES_DIR=. dbt deps

run:
	cd $(DBT_DIR) && DBT_PROFILES_DIR=. dbt run

test:
	cd $(DBT_DIR) && DBT_PROFILES_DIR=. dbt test

export:
	python scripts/export_marts.py

figures:
	python scripts/generate_figures.py

# Génère la doc dbt et la sert sur http://localhost:8080
docs:
	cd $(DBT_DIR) && DBT_PROFILES_DIR=. dbt docs generate
	cd $(DBT_DIR) && DBT_PROFILES_DIR=. dbt docs serve

# Pipeline complet (équivalent CI/CD)
all: ingest run test export figures
	@echo ""
	@echo "✨ Pipeline complet terminé !"
	@echo "   → warehouse : $(WAREHOUSE)"
	@echo "   → exports   : data/exports/"
	@echo "   → figures   : images/figures/"

clean:
	rm -rf $(WAREHOUSE)
	rm -rf $(DBT_DIR)/target
	rm -rf $(DBT_DIR)/dbt_packages
	rm -rf $(DBT_DIR)/logs
	@echo "✓ Warehouse et artefacts dbt supprimés"