#!/usr/bin/env bash
set -euo pipefail

POOL_NAME="ingestion-pool"
FLOWS_FILE="/app/ingestion/prefect/flows.py"

# Docker redémarre les conteneurs sans appliquer les depends_on de Compose.
# Attendre l'API avant toute création ou suppression de déploiement.
if [[ -n "${PREFECT_API_URL:-}" ]]; then
	python - <<'PY'
import os
import time
import urllib.error
import urllib.request

health_url = os.environ["PREFECT_API_URL"].rstrip("/") + "/health"
for attempt in range(1, 61):
    try:
        with urllib.request.urlopen(health_url, timeout=5):
            break
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        if attempt == 60:
            raise SystemExit("API Prefect indisponible après 60 tentatives.") from None
        print("Attente de l'API Prefect avant initialisation du worker...", flush=True)
        time.sleep(5)
PY
fi

delete_deployment_if_exists() {
	local deployment_name="$1"
	prefect deployment delete "$deployment_name" >/tmp/prefect-deployment-delete.log 2>&1 || true
}

prefect work-pool create "${POOL_NAME}" --type process --overwrite >/tmp/prefect-work-pool.log 2>&1 || {
	cat /tmp/prefect-work-pool.log
	exit 1
}

delete_deployment_if_exists "Synchroniser les sources/synchroniser-les-sources"
delete_deployment_if_exists "Preparer les donnees/preparer-les-donnees"
delete_deployment_if_exists "Recuperer les donnees Allocine/recuperer-les-donnees-allocine"
delete_deployment_if_exists "Finaliser les donnees/finaliser-les-donnees"
delete_deployment_if_exists "Recuperer les donnees Mubi/lancer-scraping-mubi"
delete_deployment_if_exists "Recuperer les donnees Mubi (CNC)/lancer-scraping-mubi-cnc"
delete_deployment_if_exists "Traiter les demandes d'ingestion/traiter-les-demandes-d-ingestion"
delete_deployment_if_exists "Traiter les demandes d'ingestion/traiter-les-demandes-ingestion"
delete_deployment_if_exists "Requeue les demandes d'ingestion stale/requeue-les-demandes-d-ingestion-stale"

# Supprimer les anciens noms et tout calendrier conservé sur les trois runs manuels.
# Les quatre déploiements gérés sont recréés avec leurs paramètres par défaut.
delete_deployment_if_exists "Lancer l'ingestion complete/lancer-ingestion-donnees"
delete_deployment_if_exists "Lancer l'ingestion complete/lancer-ingestion-complete"
delete_deployment_if_exists "Recuperer les donnees Allocine/lancer-scraping-allocine"
delete_deployment_if_exists "Recuperer les donnees Allocine/lancer-scrapping-allocine"
delete_deployment_if_exists "Recuperer les donnees Mubi (CNC)/lancer-scrapping-mubi"

prefect --no-prompt deploy "${FLOWS_FILE}:main_ingestion_flow" \
	--name "lancer-ingestion-complete" \
	--description "Execution manuelle Airbyte puis dbt, sans scraping." \
	--pool "${POOL_NAME}" >/tmp/prefect-deploy-main.log 2>&1 || {
	cat /tmp/prefect-deploy-main.log
	exit 1
}

# Scrapers manuels : aucun calendrier ni lancement au démarrage du worker.
prefect --no-prompt deploy "${FLOWS_FILE}:run_allocine_scraping" \
	--name "lancer-scrapping-allocine" \
	--description "Allocine manuel : Airbyte puis scraping par lot (max_films=10) ; avec visa_number, scraping cible et dbt inclus." \
	--concurrency-limit 1 \
	--pool "${POOL_NAME}" >/tmp/prefect-deploy-allocine.log 2>&1 || {
	cat /tmp/prefect-deploy-allocine.log
	exit 1
}

prefect --no-prompt deploy "${FLOWS_FILE}:run_mubi_cnc_scraping" \
	--name "lancer-scrapping-mubi" \
	--description "Mubi CNC manuel : Airbyte, palmares et editions associees, puis dbt. max_films=10, ciblage par visa disponible." \
	--concurrency-limit 1 \
	--pool "${POOL_NAME}" >/tmp/prefect-deploy-mubi.log 2>&1 || {
	cat /tmp/prefect-deploy-mubi.log
	exit 1
}

prefect --no-prompt deploy "${FLOWS_FILE}:dispatch_ingestion_requests" \
	--name "traiter-les-demandes-ingestion" \
	--description "Poll les demandes Metabase dans ops.ingestion_run_requests, claim une ligne et declenche ingestion ou Allocine selon request_type." \
	--concurrency-limit 1 \
	--interval "${INGESTION_REQUEST_POLL_INTERVAL_SECONDS:-300}" \
	--pool "${POOL_NAME}" >/tmp/prefect-deploy-dispatch.log 2>&1 || {
	cat /tmp/prefect-deploy-dispatch.log
	exit 1
}

exec prefect worker start --pool "${POOL_NAME}" --type process
