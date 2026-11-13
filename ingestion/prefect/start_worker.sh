#!/usr/bin/env bash
set -euo pipefail

POOL_NAME="ingestion-pool"
FLOWS_FILE="/app/ingestion/prefect/flows.py"

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
	--description "Scraping Allocine manuel, max_films=10 par defaut, sans Airbyte ni dbt." \
	--concurrency-limit 1 \
	--pool "${POOL_NAME}" >/tmp/prefect-deploy-allocine.log 2>&1 || {
	cat /tmp/prefect-deploy-allocine.log
	exit 1
}

prefect --no-prompt deploy "${FLOWS_FILE}:run_mubi_cnc_scraping" \
	--name "lancer-scrapping-mubi" \
	--description "Scraping Mubi manuel, max_films=10 films CNC par defaut et editions associees, sans Airbyte ni dbt." \
	--concurrency-limit 1 \
	--pool "${POOL_NAME}" >/tmp/prefect-deploy-mubi.log 2>&1 || {
	cat /tmp/prefect-deploy-mubi.log
	exit 1
}

prefect --no-prompt deploy "${FLOWS_FILE}:dispatch_ingestion_requests" \
	--name "traiter-les-demandes-ingestion" \
	--description "Poll les demandes Metabase dans ops.ingestion_run_requests, claim une ligne et declenche le deployment principal." \
	--concurrency-limit 1 \
	--interval "${INGESTION_REQUEST_POLL_INTERVAL_SECONDS:-300}" \
	--pool "${POOL_NAME}" >/tmp/prefect-deploy-dispatch.log 2>&1 || {
	cat /tmp/prefect-deploy-dispatch.log
	exit 1
}

exec prefect worker start --pool "${POOL_NAME}" --type process
