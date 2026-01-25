#!/usr/bin/with-contenv bashio
# ==============================================================================
# Home Assistant Community Add-on: Amazon S3 Backup
# ==============================================================================
#bashio::log.level "debug"

bashio::log.info "Starting Amazon S3 Backup..."
bashio::log.info "start gunicorn"
exec gunicorn -b 0.0.0.0:8099 --access-logfile - --error-logfile - s3-backup.s3-backup:app

# bashio::log.info "Starting Amazon S3 Backup..."

# bucket_name="$(bashio::config 'bucket_name')"
# endpoint_url="$(bashio::config 'endpoint_url')"
# storage_class="$(bashio::config 'storage_class')"
# bucket_region="$(bashio::config 'bucket_region')"
# delete_local_backups="$(bashio::config 'delete_local_backups' 'true')"
# local_backups_to_keep="$(bashio::config 'local_backups_to_keep' '4')"
# monitor_path="/backup"
# jq_filter=".backups|=sort_by(.date)|.backups|reverse|.[$local_backups_to_keep:]|.[].slug"

# export AWS_ACCESS_KEY_ID="$(bashio::config 'aws_access_key_id')"
# export AWS_SECRET_ACCESS_KEY="$(bashio::config 'aws_secret_access_key')"

# storage_class_option=""
# if [[ -n "$storage_class" ]]; then
#     bashio::log.debug "The 'storage_class' is set"
#     storage_class_option="--storage-class \"$storage_class\""
#     bashio::log.debug "Storage class option: '$storage_class_option'"
# fi
# bucket_region_option=""
# if [[ -n "$bucket_region" ]]; then
#     bashio::log.debug "The 'bucket_region' is set"
#     bucket_region_option="--region \"$bucket_region\""
#     bashio::log.debug "Bucket region option: '$bucket_region_option'"
#     export AWS_REGION="$bucket_region"
# fi

# bashio::log.debug "Using AWS CLI version: '$(aws --version)'"
# bashio::log.debug "Command: 'aws --endpoint-url $endpoint_url s3 sync $monitor_path s3://$bucket_name/ --no-progress $bucket_region_option $storage_class_option"
# aws --endpoint-url $endpoint_url s3 sync $monitor_path s3://"$bucket_name"/ --no-progress $bucket_region_option $storage_class_option

# if bashio::var.true "${delete_local_backups}"; then
#     bashio::log.info "Will delete local backups except the '${local_backups_to_keep}' newest ones."
#     backup_slugs="$(bashio::api.supervisor "GET" "/backups" "false" "$jq_filter")"
#     bashio::log.debug "Backups to delete: '$backup_slugs'"

#     for s in $backup_slugs; do
#         bashio::log.info "Deleting Backup: '$s'"
#         bashio::api.supervisor "DELETE" "/backups/$s"
#     done
# else
#     bashio::log.info "Will not delete any local backups since 'delete_local_backups' is set to 'false'"
# fi

# bashio::log.info "Finished S3 Backup."
