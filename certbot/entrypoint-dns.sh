#!/bin/sh
set -u

trap 'exit 0' TERM INT

log() { echo "[$(date -Iseconds)] certbot-dns-ovh: $*"; }

: "${DOMAIN:?DOMAIN env var is required}"
: "${API_DOMAIN:?API_DOMAIN env var is required}"
: "${CERTBOT_EMAIL:?CERTBOT_EMAIL env var is required}"

CREDENTIALS_FILE=/etc/letsencrypt/ovh.ini
umask 077
cat > "$CREDENTIALS_FILE" <<EOF
dns_ovh_endpoint = ${OVH_ENDPOINT:-ovh-eu}
dns_ovh_application_key = ${OVH_APPLICATION_KEY}
dns_ovh_application_secret = ${OVH_APPLICATION_SECRET}
dns_ovh_consumer_key = ${OVH_CONSUMER_KEY}
EOF
chmod 600 "$CREDENTIALS_FILE"

# Unlike the HTTP-01 setup, DNS-01 can issue the *initial* certificate on its
# own — no need to run `certbot certonly` by hand on the server first.
if [ ! -d "/etc/letsencrypt/live/${DOMAIN}" ]; then
  log "no certificate found for ${DOMAIN}, requesting an initial one via DNS-01"
  if certbot certonly \
    --non-interactive --agree-tos --no-eff-email \
    --email "${CERTBOT_EMAIL}" \
    --dns-ovh --dns-ovh-credentials "$CREDENTIALS_FILE" \
    --dns-ovh-propagation-seconds 60 \
    -d "${DOMAIN}" -d "${API_DOMAIN}"; then
    log "initial certificate issued"
    date +%s > /etc/letsencrypt/.reload
  else
    log "initial certificate request FAILED — will retry on the next loop"
  fi
fi

while :; do
  log "running certbot renew"
  if certbot renew --dns-ovh-credentials "$CREDENTIALS_FILE" --deploy-hook 'date +%s > /etc/letsencrypt/.reload'; then
    log "renew OK"
  else
    rc=$?
    log "renew FAILED (exit $rc) — retry in 12h"
  fi
  sleep 43200
done
