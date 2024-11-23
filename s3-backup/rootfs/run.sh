#!/usr/bin/with-contenv bashio

bashio::log.info "Starting S3 Backup add-on..."

export PATH="/opt/venv/bin:$PATH"
export PYTHONPATH=/

exec python3 -m app
